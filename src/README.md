# GridGuard AI

Power Outage Prediction & Grid Equipment Failure Advisor

## Description

GridGuard AI is a hackathon prototype designed to predict power outages and advise on grid equipment failures.

## Tech Stack

- Python
- Flask
- SQLite
- SQLAlchemy
- Pandas
- NumPy
- Scikit-learn
- HTML, CSS, JavaScript (Frontend)

## Project Structure

```
GridGuard-AI/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── config.py           # Application configuration
├── database/           # Database files
├── models/             # SQLAlchemy models
├── routes/             # Flask routes
├── services/           # Business logic services
├── ml/                 # Machine learning modules
├── data/               # Data files
├── templates/          # HTML templates
├── static/             # Static assets
│   ├── css/            # CSS stylesheets
│   └── js/             # JavaScript files
└── README.md           # This file
```

## Installation

1. Navigate to the project directory:
   ```
   cd D:\IBM\GridGuard-AI
   ```

2. Install the required dependencies:
   ```
   python -m pip install -r requirements.txt
   ```

3. Initialize the SQLite database from the bundled demonstration CSV files:
   ```
   python init_db.py
   ```

The demo datasets are stored in `data/`: `assets.csv`, `sensor_readings.csv`,
`incidents.csv`, `weather.csv`, and `crews.csv`.

## Running the Application

```powershell
python app.py
```

Open http://127.0.0.1:5000/ in a browser. There is no login or API key.

## Retrain The Model

Regenerate the Random Forest model and metrics from the current SQLite data:

```powershell
python ml\train_model.py
```

The generated artifacts are written to `ml/gridguard_rf_model.joblib`,
`ml/model_metrics.json`, and `ml/feature_info.json`.

## Replace Demo Data

Replace the CSV files in `data/` while preserving their headers and required
IDs, then import them:

```powershell
python init_db.py
python ml\train_model.py
```

For a fresh synthetic demonstration set, run `python generate_demo_data.py`
before `init_db.py`. The importer is idempotent and skips existing IDs; use a
new SQLite database or remove `database\gridguard.db` when replacing records
with the same IDs.

## Main API Endpoints

- `GET /api/assets`
- `GET /api/weather`
- `GET /api/incidents`
- `GET /api/crews`
- `GET /api/model-metrics`
- `POST /api/predict` with `{"asset_id":"AST-0001"}`
- `GET /api/risk-ranking`
- `GET /api/maintenance-recommendations?persist=false`
- `GET /api/crew-recommendations`
- `GET /api/grid-advisor`
- `POST /api/scenario-simulation`

## Architecture

Flask serves the single-page dashboard and JSON API. SQLAlchemy maps the
SQLite database, while Pandas services calculate grid impact, weather risk,
priority ranking, maintenance recommendations, crew positioning, alerts, and
temporary scenarios. Leaflet renders OpenStreetMap-backed geographic data and
Chart.js renders the analytics charts.

## ML And Priority Logic

The ML layer uses a scikit-learn `RandomForestClassifier` with imputation and
standardization. It combines sensor readings, asset metadata, and nearby
weather observations to estimate failure probability.

Priority is calculated as:

```text
priority_score = 0.50 * failure_risk
               + 0.30 * grid_impact_score
               + 0.20 * weather_risk
```

Scores map to Low (0-30), Medium (31-60), High (61-80), or Critical (above
80). Scenario simulations operate on copied in-memory data and do not persist
their changed conditions.

The application will be available at: http://127.0.0.1:5000/
