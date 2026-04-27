from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.features import LABEL_COLUMN, build_feature_frame, enrich_columns


@dataclass
class InferenceResult:
    boundary_probability: float
    enriched_row: dict[str, Any]


def _ensure_label(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if LABEL_COLUMN not in out.columns:
        out[LABEL_COLUMN] = 0
    return out


def load_model(model_path: str | Path):
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model not found at: {path}")
    return joblib.load(path)


def predict_single_scenario(model, scenario: dict[str, Any]) -> InferenceResult:
    row = pd.DataFrame([scenario])
    row = _ensure_label(row)
    feature_set = build_feature_frame(row)
    features = feature_set.X

    if hasattr(model, "predict_proba"):
        probability = float(model.predict_proba(features)[0][1])
    else:
        probability = float(model.predict(features)[0])

    enriched = enrich_columns(row).iloc[0].to_dict()
    return InferenceResult(
        boundary_probability=probability,
        enriched_row=enriched,
    )


def predict_dataframe(model, df: pd.DataFrame) -> pd.DataFrame:
    working = _ensure_label(df)
    feature_set = build_feature_frame(working)
    features = feature_set.X

    if hasattr(model, "predict_proba"):
        boundary_probs = model.predict_proba(features)[:, 1]
    else:
        boundary_probs = model.predict(features)

    enriched = enrich_columns(working)
    enriched = enriched.copy()
    enriched["predicted_boundary_probability"] = boundary_probs
    enriched["predicted_is_boundary"] = (enriched["predicted_boundary_probability"] >= 0.5).astype(int)
    return enriched


def load_metrics(metrics_path: str | Path) -> dict[str, Any]:
    path = Path(metrics_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def default_scenario() -> dict[str, Any]:
    return {
        "match_id": "M00001",
        "format": "T20",
        "innings": 2,
        "batting_team": "India",
        "bowling_team": "Australia",
        "venue": "Wankhede",
        "toss_winner": "India",
        "toss_decision": "bat",
        "over": 18,
        "ball_in_over": 2,
        "ball_index": 110,
        "batter_hand": "R",
        "bowler_style": "pace",
        "score": 158,
        "wickets": 5,
        "runs_this_ball": 0,
        "is_wicket": 0,
        "run_rate": 8.62,
        "target": 170,
    }


def predict_single(model_path: str | Path, scenario: dict[str, Any]) -> float:
    model = load_model(model_path)
    result = predict_single_scenario(model, scenario)
    return result.boundary_probability


def predict_batch(model_path: str | Path, df: pd.DataFrame) -> pd.Series:
    model = load_model(model_path)
    predicted = predict_dataframe(model, df)
    return predicted["predicted_boundary_probability"]


def aggregate_prediction_stats(df: pd.DataFrame) -> dict[str, Any]:
    if "predicted_boundary_probability" not in df.columns:
        raise ValueError("Missing required column: predicted_boundary_probability")
    probs = df["predicted_boundary_probability"]
    return {
        "rows": int(len(df)),
        "avg_probability": float(probs.mean()),
        "high_prob_count": int((probs >= 0.30).sum()),
    }
