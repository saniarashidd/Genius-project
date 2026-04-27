# Cricket ML Starter (Dockerless)

This module pivots the project toward a cricket-focused machine learning workflow
that runs locally without Docker.

## Goal

Train a baseline model that predicts whether the **next ball is a boundary**
(4 or 6) from live match context.

## What is included

- `src/generate_sample_data.py`
  - Generates synthetic ball-by-ball data so you can run immediately.
- `src/features.py`
  - Shared feature engineering logic used by both training and inference.
- `src/train_boundary_model.py`
  - Trains a baseline classifier and writes model + metrics artifacts.
- `src/predict_scenario.py`
  - Loads the trained model and predicts boundary probability for one scenario.
- `requirements.txt`
  - Python dependencies.

## Directory layout

```text
cricket-ml/
  data/
    ball_by_ball_sample.csv         # generated
  artifacts/
    boundary_model.joblib           # generated
    metrics.json                    # generated
  src/
    generate_sample_data.py
    features.py
    train_boundary_model.py
    predict_scenario.py
  requirements.txt
```

## Quick start

From repo root:

```bash
cd cricket-ml
python3 -m pip install --upgrade pip --break-system-packages
python3 -m pip install -r requirements.txt --break-system-packages
python3 src/generate_sample_data.py --matches 120 --seed 42 --output data/ball_by_ball_sample.csv
python3 src/train_boundary_model.py --input data/ball_by_ball_sample.csv --artifacts-dir artifacts --seed 42
python3 src/predict_scenario.py --model-path artifacts/boundary_model.joblib --scenario '{"match_id":"M00001","format":"T20","innings":1,"batting_team":"India","bowling_team":"Australia","venue":"Wankhede","toss_winner":"India","toss_decision":"bat","over":18,"ball_in_over":2,"ball_index":110,"batter_hand":"R","bowler_style":"pace","score":158,"wickets":5,"runs_this_ball":0,"is_wicket":0,"run_rate":8.62,"target":170}'
```

If you prefer a virtual environment, install `python3-venv` first and then use
`.venv` as usual.

## Expected outputs

After training, you get:

- `artifacts/boundary_model.joblib`
- `artifacts/metrics.json`

`metrics.json` includes:
- accuracy
- ROC-AUC
- average precision
- feature lists used by the model

## Input schema for training

The training/inference feature layer expects these fields (some can be derived):

- `format` (`T20` or `ODI`)
- `over`, `ball_in_over`, `ball_index`
- `score`, `wickets`, `target`
- `run_rate` (or it can be derived)
- `batting_team`, `bowling_team`, `venue`
- `batter_hand`, `bowler_style`
- `is_boundary` (label; required for training, dummy value for inference)

`features.py` derives:
- `balls_remaining`
- `required_run_rate`
- `phase` (`powerplay`, `middle`, `death`)
- `pressure_index`

## How this translates to your cricket learning goal

This gives you the full ML loop:
- data generation/ingestion
- feature engineering
- model training and evaluation
- single-event inference

Later, you can replace synthetic data with real cricket datasets (Cricinfo/CricSheet-style),
and swap the baseline model for XGBoost/LightGBM or sequence models.
