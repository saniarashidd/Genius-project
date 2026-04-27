from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import pandas as pd


NUMERIC_FEATURES: List[str] = [
    "over",
    "ball_in_over",
    "wickets",
    "score",
    "run_rate",
    "balls_remaining",
    "required_run_rate",
    "pressure_index",
]

CATEGORICAL_FEATURES: List[str] = [
    "phase",
    "format",
    "batting_team",
    "bowling_team",
    "batter_hand",
    "bowler_style",
    "venue",
]

LABEL_COLUMN = "is_boundary"


@dataclass
class FeatureSet:
    X: pd.DataFrame
    y: pd.Series
    numeric: Sequence[str]
    categorical: Sequence[str]


def _max_balls_for_format(format_name: str) -> int:
    return 300 if str(format_name).upper() == "ODI" else 120


def _derive_phase(df: pd.DataFrame) -> pd.Series:
    format_is_odi = df["format"].astype(str).str.upper().eq("ODI")
    phase = pd.Series("middle", index=df.index)

    # T20 phase buckets.
    t20_idx = ~format_is_odi
    phase.loc[t20_idx & (df["over"] <= 6)] = "powerplay"
    phase.loc[t20_idx & (df["over"] >= 16)] = "death"

    # ODI phase buckets.
    phase.loc[format_is_odi & (df["over"] <= 10)] = "powerplay"
    phase.loc[format_is_odi & (df["over"] >= 41)] = "death"
    return phase


def enrich_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    if "ball_index" not in out.columns:
        out["ball_index"] = ((out["over"] - 1) * 6 + out["ball_in_over"]).clip(lower=1)

    if "format" not in out.columns:
        out["format"] = "T20"

    out["max_balls"] = out["format"].map(_max_balls_for_format)

    if "balls_remaining" not in out.columns:
        out["balls_remaining"] = (out["max_balls"] - out["ball_index"]).clip(lower=0)

    if "run_rate" not in out.columns:
        out["run_rate"] = (out["score"] / (out["ball_index"] / 6.0)).fillna(0.0)

    if "required_run_rate" not in out.columns:
        denom_overs = (out["balls_remaining"] / 6.0).replace(0, 1e-6)
        out["required_run_rate"] = ((out["target"] - out["score"]).clip(lower=0) / denom_overs).fillna(0.0)

    if "phase" not in out.columns:
        out["phase"] = _derive_phase(out)

    # A compact pressure proxy for training/inference.
    out["pressure_index"] = (
        out["required_run_rate"] * 0.45
        + out["wickets"] * 0.25
        + (out["balls_remaining"] / out["max_balls"]) * 2.0
    ).round(4)

    return out


def build_feature_frame(df: pd.DataFrame) -> FeatureSet:
    working = enrich_columns(df)
    required = [*NUMERIC_FEATURES, *CATEGORICAL_FEATURES, LABEL_COLUMN]
    missing = [col for col in required if col not in working.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    X = working[[*NUMERIC_FEATURES, *CATEGORICAL_FEATURES]].copy()
    y = working[LABEL_COLUMN].astype(int)
    return FeatureSet(X=X, y=y, numeric=NUMERIC_FEATURES, categorical=CATEGORICAL_FEATURES)
