# People Analytics MLOps

Production-style HR Data Science platform for:
- employee churn prediction
- promotion prediction
- performance analytics
- compensation analytics

## Tech Stack & Env
- Python
- FastAPI
- PostgreSQL
- Docker Compose
- SQLAlchemy
- scikit-learn / XGBoost
- Dash / Plotly
- MLflow
- PyCharm
- DBeaver



## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
mkdir -p app/api app/core app/db app/ml app/dashboard scripts sql tests
touch app/api/main.py app/core/config.py app/db/base.py app/db/models.py app/db/session.py
touch app/ml/placeholder.py app/dashboard/placeholder.py
touch scripts/init_db.py scripts/seed_data.py
touch sql/init.sql
touch tests/test_health.py
touch .env .env.example .gitignore docker-compose.yml Dockerfile requirements.txt README.md ruh.sh 
pip install -r "requirements.txt"
cp .env.example .env 
docker compose up -d
python scripts/init_db.py
python scripts/seed_data.py
uvicorn app.api.main:app --reload
