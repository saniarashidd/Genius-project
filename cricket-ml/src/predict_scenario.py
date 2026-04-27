from __future__ import annotations

import argparse
import json

from inference import load_model, predict_single_scenario


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
    model = load_model(args.model_path)
    scenario_dict = json.loads(args.scenario)
    result = predict_single_scenario(model, scenario_dict)

    print(
        json.dumps(
            {
                "scenario": result.enriched_row,
                "predicted_boundary_probability": round(result.boundary_probability, 4),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
