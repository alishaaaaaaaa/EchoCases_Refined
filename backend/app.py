import os
# Fix for the "huggingface/tokenizers" deadlock warning on Python 3.8
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dateutil import parser as date_parser
from math import radians, cos, sin, asin, sqrt

from clustering import (
    case_texts,
    cluster_embeddings,
    evaluate_clustering,
    ground_truth_labels,
    load_config,
)

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app)

# --- GEMINI INITIALIZATION (Python 3.8 Compatible) ---
gemini_model = None
GEMINI_MODEL_NAME = os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

if api_key:
    try:
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        print(f"Gemini AI initialized successfully ({GEMINI_MODEL_NAME})!")
    except Exception as e:
        print(f"Failed to initialize Gemini: {e}")
else:
    print("Warning: No API Key found. Check your .env file.")

# --- ML SETUP ---
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'
print("Loading NLP embedding model...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# Embedding text and clustering settings (cluster_config.json if present,
# written by `python evaluate_clustering.py --compare`)
CLUSTER_CONFIG = load_config()
print(f"Clustering settings: {CLUSTER_CONFIG}")

# How many retrieved cases are put in front of Gemini (override with ?k=)
RAG_TOP_K = 5
# Narratives are truncated in the prompt to keep it bounded
RAG_NARRATIVE_CHARS = 600

# Global storage for dataset
cases_df = None
embeddings = None


def load_dataset(df):
    """Embed narratives and detect crime series. Used by startup and /api/upload."""
    global cases_df, embeddings
    cases_df = df.fillna('').reset_index(drop=True)
    embeddings = embedding_model.encode(case_texts(cases_df, CLUSTER_CONFIG['text']))
    cases_df['cluster_id'] = cluster_embeddings(embeddings, CLUSTER_CONFIG)
    num_clusters = len([c for c in cases_df['cluster_id'].unique() if c != -1])
    print(f"Loaded {len(cases_df)} cases, detected {num_clusters} crime series clusters")
    return num_clusters


# --- RETRIEVAL ---

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371 * 2 * asin(sqrt(a))


def case_position(case_id):
    """Row number of a case in cases_df / embeddings, or None."""
    mask = cases_df['case_id'] == case_id
    if not mask.any():
        return None
    return int(mask.values.nonzero()[0][0])


def retrieve_similar(target_pos, top_k):
    """
    Top-k most similar cases to the case at target_pos, by cosine similarity of
    narrative embeddings, with geographic / temporal distance and simple
    explanations attached. This is the retrieval step for both the similar-cases
    view and the RAG analysis.
    """
    target_case = cases_df.iloc[target_pos]
    target_embedding = embeddings[target_pos].reshape(1, -1)
    similarities = cosine_similarity(target_embedding, embeddings)[0]
    similarities[target_pos] = -1  # exclude the case itself

    similar_indices = np.argsort(similarities)[::-1][:top_k]
    target_time = date_parser.parse(str(target_case['timestamp']))
    target_words = set(str(target_case['narrative']).lower().split())
    stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}

    results = []
    for idx in similar_indices:
        similar = cases_df.iloc[idx].to_dict()
        similar['score'] = float(similarities[idx])
        similar['geo_distance_km'] = haversine(
            target_case['lon'], target_case['lat'], similar['lon'], similar['lat']
        )
        similar_time = date_parser.parse(str(similar['timestamp']))
        similar['time_distance_days'] = abs((similar_time - target_time).days)

        similar_words = set(str(similar['narrative']).lower().split())
        shared = list(target_words & similar_words - stopwords)
        similar['explanation'] = {
            'shared_keywords': shared[:10],
            'category_match': similar['category'] == target_case['category'],
            'weapon_match': similar.get('weapon') == target_case.get('weapon')
        }
        results.append(similar)
    return results


def format_case_for_prompt(case):
    return (
        f"ID: {case['case_id']}\n"
        f"Date: {case.get('timestamp', 'Unknown')}\n"
        f"Category: {case.get('category', 'Unknown')}\n"
        f"Location: {case.get('city', '')}, {case.get('state', '')}\n"
        f"Weapon: {case.get('weapon') or 'Unknown'}\n"
        f"Entry Method: {case.get('entry_method') or 'Unknown'}\n"
        f"Narrative: {str(case['narrative'])[:RAG_NARRATIVE_CHARS]}"
    )


def build_rag_context(retrieved, target_cluster):
    """Render retrieved cases as a numbered context block for the prompt."""
    blocks = []
    for i, c in enumerate(retrieved, 1):
        same_series = (
            "yes" if target_cluster != -1 and c.get('cluster_id') == target_cluster else "no"
        )
        blocks.append(
            f"[{i}] {format_case_for_prompt(c)}\n"
            f"Similarity to target: {c['score']:.2f} (cosine, 0-1)\n"
            f"Distance from target: {c['geo_distance_km']:.0f} km, "
            f"{c['time_distance_days']} days apart\n"
            f"Placed in same detected series by clustering: {same_series}"
        )
    return "\n\n".join(blocks)


# --- AI ENDPOINT (retrieval-augmented) ---

@app.route('/api/analyze/<case_id>', methods=['GET'])
def analyze_case(case_id):
    """
    Retrieval-augmented analysis: retrieve the most similar cases from the
    embedding index, put them in the prompt alongside the target case, and have
    Gemini ground its linkage assessment in those retrieved cases.
    """
    if gemini_model is None:
        return jsonify({"error": "AI not initialized. Check API Key and Python version."}), 503

    if cases_df is None:
        return jsonify({"error": "No cases loaded"}), 400

    # 1. Fetch the target case
    target_pos = case_position(case_id)
    if target_pos is None:
        return jsonify({"error": "Case not found"}), 404
    case = cases_df.iloc[target_pos].to_dict()
    target_cluster = int(case.get('cluster_id', -1))

    # 2. Retrieve similar cases (the "R" in RAG)
    top_k = max(0, min(int(request.args.get('k', RAG_TOP_K)), 20))
    retrieved = retrieve_similar(target_pos, top_k) if top_k else []
    context = build_rag_context(retrieved, target_cluster) if retrieved else "(none retrieved)"

    # 3. Augment the prompt with the retrieved cases
    prompt = f"""
    As a criminal profiler and investigative analyst, provide a detailed analysis of this cold case.
    Format your response as a structured analysis with the following sections.

    TARGET CASE:
    {format_case_for_prompt(case)}

    RETRIEVED SIMILAR CASES:
    The following cases were retrieved from the case database by semantic similarity
    of their narratives. They are candidates for linkage, not confirmed links.
    Similarity alone does not prove a connection; weigh it against distance, time
    gap, weapon and method.

    {context}

    Grounding rules:
    - When you refer to another case, cite it by its ID exactly as given above.
    - Only refer to cases listed above. Do not invent other cases.
    - If none of the retrieved cases appear genuinely linked, say so plainly.

    Please provide analysis in these specific categories:

    BEHAVIORAL_PATTERNS:
    Analyze the offender's behavioral signature, modus operandi, and psychological profile.
    Note where the retrieved cases share or contradict that signature.

    VICTIMOLOGY:
    Analyze victim selection, vulnerability factors, and relationship to offender.

    GEOGRAPHIC_PROFILE:
    Analyze location significance, travel patterns, and anchor points, using the
    locations of any retrieved cases you judge to be linked.

    TEMPORAL_PATTERNS:
    Analyze timing, frequency, and escalation patterns across the target and any linked cases.

    OVERLOOKED_ANGLES:
    Identify evidence or investigative angles that may have been overlooked.

    LINKAGE_ASSESSMENT:
    For each retrieved case, give its ID, a likelihood of linkage (high / medium / low),
    and the specific shared or conflicting details behind that rating.

    RECOMMENDED_ACTIONS:
    Provide 3-5 specific, actionable investigative recommendations, citing case IDs where relevant.
    """

    try:
        response = gemini_model.generate_content(prompt)
        analysis_text = response.text

        # Parse the response into structured sections
        sections = {
            'behavioral_patterns': '',
            'victimology': '',
            'geographic_profile': '',
            'temporal_patterns': '',
            'overlooked_angles': '',
            'linkage_assessment': '',
            'recommended_actions': ''
        }

        # Simple parsing - only treat short lines as section headers, so body
        # text that mentions e.g. "linkage" or "geographic" isn't misread.
        current_section = None
        for line in analysis_text.split('\n'):
            line_upper = line.upper().strip().strip('#*: ')
            is_header = len(line_upper) <= 40
            if is_header and 'BEHAVIORAL' in line_upper:
                current_section = 'behavioral_patterns'
            elif is_header and 'VICTIMOLOGY' in line_upper:
                current_section = 'victimology'
            elif is_header and 'GEOGRAPHIC' in line_upper:
                current_section = 'geographic_profile'
            elif is_header and 'TEMPORAL' in line_upper:
                current_section = 'temporal_patterns'
            elif is_header and 'OVERLOOKED' in line_upper:
                current_section = 'overlooked_angles'
            elif is_header and 'LINKAGE' in line_upper:
                current_section = 'linkage_assessment'
            elif is_header and 'RECOMMENDED' in line_upper:
                current_section = 'recommended_actions'
            elif current_section and line.strip():
                sections[current_section] += line + '\n'

        # Clean up sections
        for key in sections:
            sections[key] = sections[key].strip()
            if not sections[key]:
                sections[key] = 'Analysis pending additional data.'

        # Which retrieved cases did the model actually cite?
        cited = [c['case_id'] for c in retrieved if str(c['case_id']) in analysis_text]

        return jsonify({
            "case_id": case_id,
            "ai_analysis": sections,
            "ai_provider": GEMINI_MODEL_NAME,
            "raw_analysis": analysis_text,
            "rag": {
                "retriever": f"{EMBEDDING_MODEL_NAME} cosine similarity",
                "top_k": top_k,
                "cited_case_ids": cited,
            },
            "retrieved_cases": [
                {
                    "case_id": c['case_id'],
                    "score": round(c['score'], 3),
                    "category": c.get('category'),
                    "city": c.get('city'),
                    "state": c.get('state'),
                    "geo_distance_km": round(c['geo_distance_km'], 1),
                    "time_distance_days": c['time_distance_days'],
                    "cluster_id": int(c.get('cluster_id', -1)),
                    "same_series": target_cluster != -1 and int(c.get('cluster_id', -1)) == target_cluster,
                }
                for c in retrieved
            ],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DATA ROUTES ---

@app.route('/api/similar/<case_id>', methods=['GET'])
def get_similar_cases(case_id):
    """Find similar cases using embeddings"""
    if cases_df is None or embeddings is None:
        return jsonify({"error": "No cases loaded"}), 400

    target_pos = case_position(case_id)
    if target_pos is None:
        return jsonify({"error": "Case not found"}), 404

    top_k = int(request.args.get('top_k', 10))
    return jsonify({
        "case_id": case_id,
        "similar_cases": retrieve_similar(target_pos, top_k)
    })

@app.route('/api/clusters', methods=['GET'])
def get_clusters():
    """Get crime series clusters"""
    if cases_df is None or 'cluster_id' not in cases_df.columns:
        return jsonify([])

    clusters = []
    for cluster_id in cases_df['cluster_id'].unique():
        if cluster_id == -1:  # Skip noise points
            continue

        cluster_cases = cases_df[cases_df['cluster_id'] == cluster_id]

        # Calculate cluster statistics
        cluster_info = {
            'cluster_id': int(cluster_id),
            'num_cases': len(cluster_cases),
            'center_lat': float(cluster_cases['lat'].mean()),
            'center_lon': float(cluster_cases['lon'].mean()),
            'common_mo': ', '.join(cluster_cases['category'].value_counts().head(3).index.tolist()),
            'common_keywords': []
        }

        # Calculate geographic spread
        lats = cluster_cases['lat'].values
        lons = cluster_cases['lon'].values
        max_dist = 0
        for i in range(len(lats)):
            for j in range(i+1, len(lats)):
                max_dist = max(max_dist, haversine(lons[i], lats[i], lons[j], lats[j]))

        cluster_info['geo_spread_km'] = float(max_dist)

        # Extract common keywords
        all_words = []
        for narrative in cluster_cases['narrative']:
            words = [w.lower() for w in str(narrative).split() if len(w) > 4]
            all_words.extend(words)

        from collections import Counter
        common = Counter(all_words).most_common(10)
        cluster_info['common_keywords'] = [word for word, count in common if count > 1]

        clusters.append(cluster_info)

    return jsonify(clusters)

@app.route('/api/evaluation', methods=['GET'])
def get_evaluation():
    """
    Score the current clustering against ground truth, when the dataset has it
    (the planted series from generate_cases.py). Real datasets without series
    labels return 404.
    """
    if cases_df is None or 'cluster_id' not in cases_df.columns:
        return jsonify({"error": "No cases loaded"}), 400

    truth = ground_truth_labels(cases_df)
    if truth is None:
        return jsonify({"error": "Dataset has no ground-truth series labels"}), 404

    metrics = evaluate_clustering(truth, cases_df['cluster_id'].tolist())
    metrics['cluster_config'] = CLUSTER_CONFIG
    metrics['embedding_model'] = EMBEDDING_MODEL_NAME
    return jsonify(metrics)

@app.route('/api/cases', methods=['GET'])
def get_cases():
    return jsonify(cases_df.to_dict('records')) if cases_df is not None else jsonify([])

@app.route('/api/upload', methods=['POST'])
def upload_dataset():
    file = request.files['file']
    num_clusters = load_dataset(pd.read_csv(file))
    return jsonify({'status': 'success', 'count': len(cases_df), 'num_clusters': num_clusters})

# Serve the React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    # Auto-load local data if it exists
    if os.path.exists('cases.csv'):
        load_dataset(pd.read_csv('cases.csv'))

    app.run(debug=True, port=5000)
