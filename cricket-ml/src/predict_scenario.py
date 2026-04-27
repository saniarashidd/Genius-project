from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd

from features import LABEL_COLUMN, build_feature_frame


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one-scenario inference for boundary probability."
    )
    parser.add_argument(
        "--model-path",
        default="artifacts/boundary_model.joblib",
        help="Path to trained model artifact.",
    )
    parser.add_argument(
        "--scenario",
        required=True,
        help=(
            "JSON string describing ball state, e.g. "
            '\'{"match_id":"M00001","format":"T20","innings":1,'
            '"batting_team":"India","bowling_team":"Australia",'
            '"venue":"Wankhede","toss_winner":"India","toss_decision":"bat",'
            '"over":14,"ball_in_over":3,"ball_index":81,'
            '"batter_hand":"R","bowler_style":"pace","score":123,'
            '"wickets":4,"runs_this_ball":0,"is_wicket":0,'
            '"run_rate":9.11,"target":170}' + "'"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_path = Path(args.model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at: {model_path}")

    model = joblib.load(model_path)
    scenario_dict = json.loads(args.scenario)

    # Label is unknown at inference; set a dummy placeholder.
    scenario_dict[LABEL_COLUMN] = int(scenario_dict.get(LABEL_COLUMN, 0))
    row = pd.DataFrame([scenario_dict])
    feature_set = build_feature_frame(row)
    features = feature_set.X

    if hasattr(model, "predict_proba"):
        boundary_prob = float(model.predict_proba(features)[0][1])
    else:
        boundary_prob = float(model.predict(features)[0])

    print(
        json.dumps(
            {
                "scenario": scenario_dict,
                "predicted_boundary_probability": round(boundary_prob, 4),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
