# EchoCases

## The Problem 
The clearance rate for violent crime in North America is only about 50%,  but for minority and underserved communities, clearance rates are often lower due to case deprioritization and limited investigative resources. As a result, many families are left without answers for years, sometimes decades.

## EchoCases was Built to change that 

The mission of EchoCases is to democratize investigative intelligence, giving community advocates, independent researchers, and under-resourced agencies the same pattern-recognition capabilities that well-funded departments take for granted. By making cold case analysis 10x more efficient, EchoCases aims to give voice to the voiceless and bring attention back to the cases that have been forgotten.


## What it does
EchoCases is an AI-powered cold case intelligence platform that functions as an investigative pattern-recognition system, analyzing case narratives to surface hidden connections across time and geography.

Its core features include:

- **Interactive Case Mapping**: A Mapbox-powered interface displays cold cases geographically, allowing investigators to visualize spatial patterns and filter by date, category, and location.

- **Semantic Pattern Matching**: Using sentence embeddings and cosine similarity, EchoCases identifies cases with similar narratives, MOs, and circumstances even when they occur in different jurisdictions or use different terminology.

- **Retrieval-Augmented AI Investigation (RAG)**: For the case under review, EchoCases retrieves the most similar cases from the embedding index and passes them to Gemini with the target case. The analysis (behavioral patterns, victimology, geographic profiling, temporal analysis, overlooked angles, next steps) is grounded in those retrieved cases, and the linkage assessment rates each one by case ID. The response lists the retrieved cases and which ones the model cited.

- **Crime Series Detection**: HDBSCAN clustering automatically identifies potential serial patterns, grouping cases that may be linked but were never connected.

- **Measured Clustering Quality**: The synthetic dataset plants 10 known crime series, so series detection is scored against ground truth: how many series are recovered, plus pairwise precision, recall and F1 (see *Evaluation* below).

- **Authentication & Role-Based Access**: Case data is behind a login. Investigators can view cases and run analysis; only admins can upload datasets, manage accounts and read the audit log. Every access is audit-logged (see *Security* below).

- **Dual Interface Modes**:  Switch between Tactical (hacker aesthetic) and Standard (government/professional) themes.

- **Temporal Animation**: An animated timeline reveals how cases unfold over time, exposing escalation patterns and cooling-off periods that might indicate serial behavior


## How it was Built
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
# Add your Gemini key, and set ECHOCASES_SECRET_KEY to the output of:
python -c "import secrets; print(secrets.token_hex(32))"

# Create the first admin account (you'll be asked for a password)
python manage_users.py create yourname --role admin

python app.py

**Frontend Setup**
cd frontend

npm install

echo "REACT_APP_MAPBOX_TOKEN=your_token_here" > .env

npm start

**Evaluation**

`generate_cases.py` plants 10 series among 150 unlinked background cases (each with a distinct narrative). To score series detection against them:

```
cd backend
python generate_cases.py                  # writes cases.csv (add a number to fix the seed)
python evaluate_clustering.py             # report on cases.csv
python evaluate_clustering.py --seeds 5   # average over 5 regenerated datasets
python evaluate_clustering.py --compare   # choose pipeline settings, save cluster_config.json
python evaluate_clustering.py --retrieval # score the similar-case search behind RAG
```

`--compare` tries combinations of embedding text (narrative alone, or with category, weapon and entry method), PCA dimension reduction and HDBSCAN settings on 5 tuning datasets, then reports the winner and the default on 5 held-out datasets that played no part in the choice. If the winner is better on held-out data it is saved to `cluster_config.json`, which the app loads at startup.

`--retrieval` scores the similar-case search that supplies RAG context. Each case in a planted series is used as a query, every other case is ranked by cosine similarity (as the app does), and it reports precision@k (share of the top k results from the same series), recall@k and MRR, alongside the random-ranking baseline and the best score possible given series sizes. It runs on the held-out datasets by default.

A series counts as *recovered* when one cluster holds a majority of its cases and that cluster is mostly that series. Pairwise precision is the share of case pairs put in the same cluster that truly belong to the same series; pairwise recall is the share of same-series pairs that were put together. With the backend running, `GET /api/evaluation` returns the same metrics for the loaded dataset.

**API additions**
- `GET /api/analyze/<case_id>?k=5`: RAG analysis; `k` sets how many retrieved cases go into the prompt. Set `GEMINI_MODEL` in `.env` to change the Gemini model.
- `GET /api/evaluation`: clustering metrics against the planted series.

**Security**

- **Login required.** Every `/api` route except login needs a signed JWT (`Authorization: Bearer <token>`), which expires after 8 hours. Passwords are stored salted and hashed (scrypt); there is no public sign-up.
- **Two roles.** `investigator`: view cases, similar cases, clusters, AI analysis. `admin`: everything an investigator can do, plus dataset upload, user management (`/api/admin/users`) and the audit log (`/api/admin/audit`).
- **Immediate revocation.** The user is re-checked on every request, so deactivating an account, changing a role or resetting a password takes effect at once; password resets and deactivation invalidate existing tokens.
- **Login throttling.** 5 failed attempts for a username from one IP locks that pair out for 15 minutes.
- **Audit log.** Every API request (allowed or denied), login, failed login and lockout is recorded with user, role, action, case ID, status and IP.
- **Locked-down CORS.** Only origins listed in `ALLOWED_ORIGINS` can call the API from a browser.
- **Upload checks.** Admin-only, `.csv` only, size-capped (`MAX_UPLOAD_MB`), and rejected if required columns are missing.
- **Safer defaults.** The Flask debugger is off unless `FLASK_DEBUG=1`; API responses are sent with `no-store` and other security headers; the app refuses to start without a strong `ECHOCASES_SECRET_KEY`.

Manage accounts from `backend/`:

```
python manage_users.py create <name> --role investigator
python manage_users.py list
python manage_users.py set-password <name>
python manage_users.py set-role <name> admin
python manage_users.py deactivate <name>
```

Known limits for a real deployment: serve over HTTPS, move users and the audit log to a managed database, and keep the token out of reach of injected scripts (an HttpOnly cookie is the next step up from sessionStorage).

**Usage**
1. Sign in; an admin uploads the dataset
2. Explore cases on the map
3. View pattern matches
4. Request AI analysis
5. Explore clusters
6. Animate timelines


