# EchoCases

## The Problem 
The clearance rate for violent crime in North America is only about 50%,  but for minority and underserved communities, clearance rates are often lower due to case deprioritization and limited investigative resources. As a result, many families are left without answers for years, sometimes decades.

## We built EchoCases to change that 

Our mission is to democratize investigative intelligence, giving community advocates, independent researchers, and under-resourced agencies the same pattern-recognition capabilities that well-funded departments take for granted. By making cold case analysis 10x more efficient, we aim to give voice to the voiceless and bring attention back to the cases that have been forgotten.


## What it does
EchoCases is an AI-powered cold case intelligence platform that functions as an investigative pattern-recognition system, analyzing case narratives to surface hidden connections across time and geography.

Its core features include:

- **Interactive Case Mapping**: A Mapbox-powered interface displays cold cases geographically, allowing investigators to visualize spatial patterns and filter by date, category, and location.

- **Semantic Pattern Matching**: Using sentence embeddings and cosine similarity, EchoCases identifies cases with similar narratives, MOs, and circumstances even when they occur in different jurisdictions or use different terminology.

- **Retrieval-Augmented AI Investigation (RAG)**: For the case under review, EchoCases retrieves the most similar cases from the embedding index and passes them to Gemini with the target case. The analysis (behavioral patterns, victimology, geographic profiling, temporal analysis, overlooked angles, next steps) is grounded in those retrieved cases, and the linkage assessment rates each one by case ID. The response lists the retrieved cases and which ones the model cited.

- **Crime Series Detection**: HDBSCAN clustering automatically identifies potential serial patterns, grouping cases that may be linked but were never connected.

- **Measured Clustering Quality**: The synthetic dataset plants 10 known crime series, so series detection is scored against ground truth: how many series are recovered, plus pairwise precision, recall and F1 (see *Evaluation* below).

- **Dual Interface Modes**:  Switch between Tactical (hacker aesthetic) and Standard (government/professional) themes.

- **Temporal Animation**: An animated timeline reveals how cases unfold over time, exposing escalation patterns and cooling-off periods that might indicate serial behavior


## How we built it
EchoCases is a full-stack application built on a technology stack that supports scalable analysis and interactive visualization. 

### The tech stack
**Backend:**
- Python
- Flask (RESTful API)
- Sentence-Transformers (`all-MiniLM-L6-v2` for semantic embeddings)
- scikit-learn (cosine similarity, HDBSCAN clustering)
- Pandas & NumPy (data processing)
- Google Gemini AI (advanced investigative analysis)

**Frontend:**
- React 18
- Mapbox GL JS (interactive mapping)
- Lucide React (iconography)
- Custom CSS with dual-theme support

## Quick Start
**Prerequisites**
- Python 3.8+
- Node.js 16+
- Mapbox API token

**Backend Setup**
git clone https://github.com/alishaaaaaaaa/EchoCases
cd echocases/backend

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Add your API keys

python app.py

**Frontend Setup**
cd frontend

npm install

echo "REACT_APP_MAPBOX_TOKEN=your_token_here" > .env

npm start

**Evaluation**

`generate_cases.py` plants 10 series among 150 unlinked background cases. To score series detection against them:

```
cd backend
python generate_cases.py            # writes cases.csv
python evaluate_clustering.py       # report + eval_results.json
python evaluate_clustering.py --sweep     # compare HDBSCAN settings
python evaluate_clustering.py --seeds 5   # average over 5 regenerated datasets
```

A series counts as *recovered* when one cluster holds a majority of its cases and that cluster is mostly that series. Pairwise precision is the share of case pairs put in the same cluster that truly belong to the same series; pairwise recall is the share of same-series pairs that were put together. With the backend running, `GET /api/evaluation` returns the same metrics for the loaded dataset.

**API additions**
- `GET /api/analyze/<case_id>?k=5`: RAG analysis; `k` sets how many retrieved cases go into the prompt. Set `GEMINI_MODEL` in `.env` to change the Gemini model.
- `GET /api/evaluation`: clustering metrics against the planted series.

**Usage**
1. Upload your dataset
2. Explore cases on the map
3. View pattern matches
4. Request AI analysis
5. Explore clusters
6. Animate timelines


