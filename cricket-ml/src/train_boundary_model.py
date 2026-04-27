#!/usr/bin/env python3
"""Train a baseline model to predict next-ball boundary probability."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from features import CATEGORICAL_FEATURES, LABEL_COLUMN, NUMERIC_FEATURES, build_feature_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train cricket next-ball boundary prediction baseline model."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/ball_by_ball_sample.csv"),
        help="Input ball-by-ball CSV path.",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts"),
        help="Directory to store model and metadata artifacts.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Holdout ratio for evaluation.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args()


def build_pipeline() -> Pipeline:
    preprocess = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    model = HistGradientBoostingClassifier(
        max_depth=6,
        learning_rate=0.08,
        max_iter=220,
        random_state=42,
    )

    return Pipeline(
        steps=[
            ("preprocess", preprocess),
            ("model", model),
        ]
    )


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise FileNotFoundError(
            f"Input data not found: {args.input}. "
            "Run src/generate_sample_data.py first."
        )

    raw_df = pd.read_csv(args.input)
    feature_set = build_feature_frame(raw_df)
    X = feature_set.X
    y = feature_set.y

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.seed,
        stratify=y,
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    probs = pipeline.predict_proba(X_test)[:, 1]
    preds = (probs >= 0.5).astype(int)

    metrics = {
        "rows_total": int(len(raw_df)),
        "rows_train": int(len(X_train)),
        "rows_test": int(len(X_test)),
        "positive_rate": float(y.mean()),
        "accuracy": float(accuracy_score(y_test, preds)),
        "roc_auc": float(roc_auc_score(y_test, probs)),
        "average_precision": float(average_precision_score(y_test, probs)),
        "label_column": LABEL_COLUMN,
        "numeric_features": list(NUMERIC_FEATURES),
        "categorical_features": list(CATEGORICAL_FEATURES),
    }

    args.artifacts_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.artifacts_dir / "boundary_model.joblib"
    metrics_path = args.artifacts_dir / "metrics.json"

    joblib.dump(pipeline, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Saved model to {model_path}")
    print(f"Saved metrics to {metrics_path}")
    print(
        "Evaluation -> "
        f"accuracy={metrics['accuracy']:.4f}, "
        f"roc_auc={metrics['roc_auc']:.4f}, "
        f"avg_precision={metrics['average_precision']:.4f}"
    )


if __name__ == "__main__":
    main()
