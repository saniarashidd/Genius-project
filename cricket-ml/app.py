#!/usr/bin/env python3
"""Streamlit UI for cricket boundary probability model."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.inference import (
    InferenceResult,
    load_metrics,
    load_model,
    predict_dataframe,
    predict_single_scenario,
)

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "boundary_model.joblib"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"

TEAMS = ["India", "Australia", "England", "Pakistan", "South Africa", "New Zealand"]
VENUES = ["Eden Gardens", "MCG", "Lords", "Wankhede", "Gaddafi Stadium", "The Oval"]
FORMATS = ["T20", "ODI"]


def ensure_model_ready() -> bool:
    if MODEL_PATH.exists():
        return True
    st.error(
        "Model artifact not found. Train first:\n\n"
        "`python3 src/generate_sample_data.py --matches 120 --output data/ball_by_ball_sample.csv`\n\n"
        "`python3 src/train_boundary_model.py --input data/ball_by_ball_sample.csv --artifacts-dir artifacts`"
    )
    return False


def default_scenario() -> dict[str, object]:
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


def aggregate_prediction_stats(df: pd.DataFrame) -> dict[str, float]:
    if df.empty:
        return {"rows": 0, "avg_probability": 0.0, "high_prob_count": 0}
    high_prob_count = int((df["predicted_boundary_probability"] >= 0.30).sum())
    return {
        "rows": int(len(df)),
        "avg_probability": float(df["predicted_boundary_probability"].mean()),
        "high_prob_count": high_prob_count,
    }


def render_single_state_tab() -> None:
    st.subheader("Single ball-state prediction")
    base = default_scenario()

    c1, c2, c3 = st.columns(3)
    with c1:
        format_name = st.selectbox("Format", FORMATS, index=0)
        innings = st.selectbox("Innings", [1, 2], index=1)
        over = st.number_input("Over", min_value=1, max_value=50, value=18)
        ball_in_over = st.number_input("Ball in over", min_value=1, max_value=6, value=2)
    with c2:
        batting_team = st.selectbox("Batting team", TEAMS, index=0)
        bowling_team = st.selectbox("Bowling team", TEAMS, index=1)
        venue = st.selectbox("Venue", VENUES, index=3)
        batter_hand = st.selectbox("Batter hand", ["R", "L"], index=0)
    with c3:
        bowler_style = st.selectbox("Bowler style", ["pace", "spin"], index=0)
        score = st.number_input("Score", min_value=0, max_value=500, value=158)
        wickets = st.number_input("Wickets", min_value=0, max_value=10, value=5)
        target = st.number_input("Target", min_value=1, max_value=500, value=170)

    ball_index = (int(over) - 1) * 6 + int(ball_in_over)
    run_rate = round(float(score) / max(ball_index / 6.0, 1e-6), 4)

    scenario = {
        **base,
        "format": format_name,
        "innings": int(innings),
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "venue": venue,
        "over": int(over),
        "ball_in_over": int(ball_in_over),
        "ball_index": int(ball_index),
        "batter_hand": batter_hand,
        "bowler_style": bowler_style,
        "score": int(score),
        "wickets": int(wickets),
        "target": int(target),
        "run_rate": run_rate,
    }

    model = load_model(MODEL_PATH)
    result: InferenceResult = predict_single_scenario(model, scenario)
    st.metric("Predicted boundary probability", f"{result.boundary_probability * 100:.2f}%")
    st.caption(
        "Derived stats: "
        f"phase={result.enriched_row.get('phase')}, "
        f"balls_remaining={result.enriched_row.get('balls_remaining')}, "
        f"required_rr={result.enriched_row.get('required_run_rate')}"
    )

    with st.expander("Scenario payload"):
        st.json(scenario)


def render_csv_analysis_tab() -> None:
    st.subheader("Analyze an uploaded game CSV")
    st.caption(
        "Upload ball-by-ball rows with columns used by training "
        "(format, over, ball_in_over, batting_team, bowling_team, venue, "
        "batter_hand, bowler_style, score, wickets, target, etc.)."
    )

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is None:
        return

    try:
        df = pd.read_csv(uploaded)
    except Exception as exc:  # pragma: no cover - streamlit runtime path
        st.error(f"Could not parse CSV: {exc}")
        return

    if df.empty:
        st.warning("CSV is empty.")
        return

    model = load_model(MODEL_PATH)
    pred_df = predict_dataframe(model, df)

    stats = aggregate_prediction_stats(pred_df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows analyzed", f"{stats['rows']}")
    c2.metric("Avg boundary prob", f"{stats['avg_probability'] * 100:.2f}%")
    c3.metric("High-risk balls (>=30%)", f"{stats['high_prob_count']}")

    st.markdown("#### Top high-probability moments")
    top_cols = [
        "match_id",
        "innings",
        "over",
        "ball_in_over",
        "batting_team",
        "bowling_team",
        "score",
        "wickets",
        "predicted_boundary_probability",
    ]
    available_cols = [c for c in top_cols if c in pred_df.columns]
    top_df = pred_df.sort_values("predicted_boundary_probability", ascending=False).head(25)
    st.dataframe(top_df[available_cols], use_container_width=True)

    csv_bytes = pred_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download predictions CSV",
        data=csv_bytes,
        file_name="cricket_boundary_predictions.csv",
        mime="text/csv",
    )


def main() -> None:
    st.set_page_config(page_title="Cricket ML Analyzer", page_icon="🏏", layout="wide")
    st.title("🏏 Cricket Boundary Probability Analyzer")
    st.write(
        "Enter a game state or upload ball-by-ball data to estimate next-ball boundary chances."
    )

    if not ensure_model_ready():
        return

    with st.expander("Model evaluation snapshot", expanded=False):
        metrics = load_metrics(METRICS_PATH)
        if not metrics:
            st.info("No metrics.json found yet. Train the model to populate evaluation stats.")
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Accuracy", f"{metrics.get('accuracy', 0.0):.3f}")
            c2.metric("ROC-AUC", f"{metrics.get('roc_auc', 0.0):.3f}")
            c3.metric("Avg precision", f"{metrics.get('average_precision', 0.0):.3f}")

    tab_single, tab_csv = st.tabs(["Single state", "CSV analysis"])
    with tab_single:
        render_single_state_tab()
    with tab_csv:
        render_csv_analysis_tab()


if __name__ == "__main__":
    main()
