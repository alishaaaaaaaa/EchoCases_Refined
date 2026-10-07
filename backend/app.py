import os
# Fix for the "huggingface/tokenizers" deadlock warning on Python 3.8
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.cluster import HDBSCAN
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from datetime import datetime
from dateutil import parser as date_parser
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app)

# --- GEMINI INITIALIZATION (Python 3.8 Compatible) ---
gemini_model = None
api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')

if api_key:
    try:
        genai.configure(api_key=api_key)
        # Using gemini-1.5-flash for speed and reliability
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        print("Gemini AI initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize Gemini: {e}")
else:
    print("Warning: No API Key found. Check your .env file.")

# --- ML SETUP ---
print("Loading NLP embedding model...")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Global storage for dataset
cases_df = None
embeddings = None

# --- AI ENDPOINT ---

@app.route('/api/analyze/<case_id>', methods=['GET'])
def analyze_case(case_id):
    """Generates investigative analysis using Gemini"""
    if gemini_model is None:
        return jsonify({"error": "AI not initialized. Check API Key and Python version."}), 503

    if cases_df is None:
        return jsonify({"error": "No cases loaded"}), 400

    # 1. Fetch case data
    target = cases_df[cases_df['case_id'] == case_id]
    if target.empty:
        return jsonify({"error": "Case not found"}), 404
    
    case = target.iloc[0].to_dict()

    # 2. Build the investigative prompt with structured output
    prompt = f"""
    As a criminal profiler and investigative analyst, provide a detailed analysis of this cold case. 
    Format your response as a structured analysis with the following sections:

    Case Details:
    ID: {case['case_id']}
    Category: {case['category']}
    Location: {case['city']}, {case['state']}
    Weapon: {case.get('weapon', 'Unknown')}
    Entry Method: {case.get('entry_method', 'Unknown')}
    Narrative: {case['narrative']}
    
    Please provide analysis in these specific categories:

    BEHAVIORAL_PATTERNS:
    Analyze the offender's behavioral signature, modus operandi, and psychological profile.

    VICTIMOLOGY:
    Analyze victim selection, vulnerability factors, and relationship to offender.

    GEOGRAPHIC_PROFILE:
    Analyze location significance, travel patterns, and anchor points.

    TEMPORAL_PATTERNS:
    Analyze timing, frequency, and escalation patterns.

    OVERLOOKED_ANGLES:
    Identify evidence or investigative angles that may have been overlooked.

    LINKAGE_ASSESSMENT:
    Assess potential connections to other cases and similar crime patterns.

    RECOMMENDED_ACTIONS:
    Provide 3-5 specific, actionable investigative recommendations.
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
        
        # Simple parsing - split by section headers
        current_section = None
        for line in analysis_text.split('\n'):
            line_upper = line.upper().strip()
            if 'BEHAVIORAL' in line_upper and 'PATTERN' in line_upper:
                current_section = 'behavioral_patterns'
            elif 'VICTIMOLOGY' in line_upper:
                current_section = 'victimology'
            elif 'GEOGRAPHIC' in line_upper:
                current_section = 'geographic_profile'
            elif 'TEMPORAL' in line_upper:
                current_section = 'temporal_patterns'
            elif 'OVERLOOKED' in line_upper:
                current_section = 'overlooked_angles'
            elif 'LINKAGE' in line_upper:
                current_section = 'linkage_assessment'
            elif 'RECOMMENDED' in line_upper or 'ACTION' in line_upper:
                current_section = 'recommended_actions'
            elif current_section and line.strip():
                sections[current_section] += line + '\n'
        
        # Clean up sections
        for key in sections:
            sections[key] = sections[key].strip()
            if not sections[key]:
                sections[key] = 'Analysis pending additional data.'
        
        return jsonify({
            "case_id": case_id,
            "ai_analysis": sections,
            "ai_provider": "Gemini 1.5 Flash",
            "raw_analysis": analysis_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- DATA ROUTES ---

@app.route('/api/similar/<case_id>', methods=['GET'])
def get_similar_cases(case_id):
    """Find similar cases using embeddings"""
    if cases_df is None or embeddings is None:
        return jsonify({"error": "No cases loaded"}), 400
    
    # Find the target case - use positional index for embeddings
    target_mask = cases_df['case_id'] == case_id
    if not target_mask.any():
        return jsonify({"error": "Case not found"}), 404
    
    # Get the positional index (row number) for embeddings array
    target_pos = target_mask.values.nonzero()[0][0]
    target_case = cases_df.iloc[target_pos]
    
    # Calculate cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    target_embedding = embeddings[target_pos].reshape(1, -1)
    similarities = cosine_similarity(target_embedding, embeddings)[0]
    
    # Exclude the target case by setting its similarity to -1
    similarities[target_pos] = -1
    
    # Get top_k similar cases
    top_k = int(request.args.get('top_k', 10))
    similar_indices = np.argsort(similarities)[::-1][:top_k]
    
    # Calculate haversine distance
    def haversine(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6371 * c
        return km
    
    # Build similar cases list
    similar_cases = []
    print(f"DEBUG - Top similarity scores: {[float(similarities[i]) for i in similar_indices[:5]]}")  # Debug line
    print(f"DEBUG - Target narrative: {target_case['narrative'][:100]}...")  # Show first 100 chars
    print(f"DEBUG - First similar narrative: {cases_df.iloc[similar_indices[0]]['narrative'][:100]}...")
    for idx in similar_indices:
        similar = cases_df.iloc[idx].to_dict()
        similar['score'] = float(similarities[idx])
        
        # Calculate geographic distance
        similar['geo_distance_km'] = haversine(
            target_case['lon'], target_case['lat'],
            similar['lon'], similar['lat']
        )
        
        # Calculate time distance
        target_time = date_parser.parse(target_case['timestamp'])
        similar_time = date_parser.parse(similar['timestamp'])
        similar['time_distance_days'] = abs((similar_time - target_time).days)
        
        # Extract shared keywords (simple approach)
        target_words = set(target_case['narrative'].lower().split())
        similar_words = set(similar['narrative'].lower().split())
        shared = list(target_words & similar_words - {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'})
        similar['explanation'] = {
            'shared_keywords': shared[:10],
            'category_match': similar['category'] == target_case['category'],
            'weapon_match': similar.get('weapon') == target_case.get('weapon')
        }
        
        similar_cases.append(similar)
    
    return jsonify({
        "case_id": case_id,
        "similar_cases": similar_cases
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
                lon1, lat1 = radians(lons[i]), radians(lats[i])
                lon2, lat2 = radians(lons[j]), radians(lats[j])
                dlon = lon2 - lon1
                dlat = lat2 - lat1
                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * asin(sqrt(a))
                dist = 6371 * c
                max_dist = max(max_dist, dist)
        
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

@app.route('/api/cases', methods=['GET'])
def get_cases():
    return jsonify(cases_df.to_dict('records')) if cases_df is not None else jsonify([])

@app.route('/api/upload', methods=['POST'])
def upload_dataset():
    global cases_df, embeddings
    file = request.files['file']
    cases_df = pd.read_csv(file).fillna('')
    embeddings = embedding_model.encode(cases_df['narrative'].tolist())
    
    # Run clustering to detect crime series
    clusterer = HDBSCAN(min_cluster_size=3, min_samples=2)
    cases_df['cluster_id'] = clusterer.fit_predict(embeddings)
    num_clusters = len([c for c in cases_df['cluster_id'].unique() if c != -1])
    print(f"Detected {num_clusters} crime series clusters")
    
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
        cases_df = pd.read_csv('cases.csv').fillna('')
        embeddings = embedding_model.encode(cases_df['narrative'].tolist())
        clusterer = HDBSCAN(min_cluster_size=5)
        cases_df['cluster_id'] = clusterer.fit_predict(embeddings)
        print(f"Loaded {len(cases_df)} cases from local storage.")
        
    app.run(debug=True, port=5000)