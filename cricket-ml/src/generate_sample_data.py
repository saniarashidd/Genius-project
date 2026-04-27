#!/usr/bin/env python3
"""Generate deterministic sample cricket ball-by-ball data for ML experiments."""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class MatchConfig:
    match_id: str
    format_name: str
    innings_count: int
    balls_per_innings: int
    venue: str
    toss_winner: str
    toss_decision: str


VENUES = [
    "Eden Gardens",
    "MCG",
    "Lords",
    "Wankhede",
    "Gaddafi Stadium",
    "The Oval",
]

TEAMS = [
    "India",
    "Australia",
    "England",
    "Pakistan",
    "South Africa",
    "New Zealand",
]

BATTER_HANDS = ["R", "L"]
BOWLER_STYLES = ["pace", "spin"]


def choose_boundary_probability(
    *,
    phase: str,
    bowler_style: str,
    batter_hand: str,
    wickets: int,
) -> float:
    """Heuristic probability to make synthetic data non-random."""
    base = 0.12
    if phase == "powerplay":
        base += 0.07
    elif phase == "death":
        base += 0.05
    if bowler_style == "spin":
        base -= 0.01
    if batter_hand == "L":
        base += 0.01
    if wickets >= 7:
        base -= 0.03
    return max(0.03, min(0.42, base))


def choose_wicket_probability(*, phase: str, bowler_style: str) -> float:
    base = 0.045
    if phase == "powerplay":
        base += 0.01
    elif phase == "death":
        base += 0.015
    if bowler_style == "pace":
        base += 0.008
    return max(0.01, min(0.12, base))


def determine_phase(over: int) -> str:
    if over <= 6:
        return "powerplay"
    if over >= 16:
        return "death"
    return "middle"


def simulate_match(cfg: MatchConfig, rng: random.Random) -> Iterable[dict]:
    teams = rng.sample(TEAMS, 2)
    home_team, away_team = teams[0], teams[1]
    for innings in range(1, cfg.innings_count + 1):
        batting_team = home_team if innings == 1 else away_team
        bowling_team = away_team if innings == 1 else home_team
        score = 0
        wickets = 0
        ball_index = 0

        for over in range(1, (cfg.balls_per_innings // 6) + 1):
            phase = determine_phase(over)
            for ball_in_over in range(1, 7):
                if ball_index >= cfg.balls_per_innings or wickets >= 10:
                    break
                ball_index += 1

                batter_hand = rng.choice(BATTER_HANDS)
                bowler_style = rng.choice(BOWLER_STYLES)

                boundary_prob = choose_boundary_probability(
                    phase=phase,
                    bowler_style=bowler_style,
                    batter_hand=batter_hand,
                    wickets=wickets,
                )
                wicket_prob = choose_wicket_probability(
                    phase=phase,
                    bowler_style=bowler_style,
                )

                is_wicket = 1 if rng.random() < wicket_prob else 0
                if is_wicket:
                    wickets += 1

                # If wicket happens, runs are usually low on that ball.
                if is_wicket:
                    runs = rng.choice([0, 0, 1, 2])
                else:
                    is_boundary = 1 if rng.random() < boundary_prob else 0
                    if is_boundary:
                        runs = rng.choice([4, 6])
                    else:
                        runs = rng.choice([0, 1, 1, 2, 3])

                score += runs
                run_rate = score / (ball_index / 6.0)

                row = {
                    "match_id": cfg.match_id,
                    "format": cfg.format_name,
                    "innings": innings,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "venue": cfg.venue,
                    "toss_winner": cfg.toss_winner,
                    "toss_decision": cfg.toss_decision,
                    "over": over,
                    "ball_in_over": ball_in_over,
                    "ball_index": ball_index,
                    "phase": phase,
                    "batter_hand": batter_hand,
                    "bowler_style": bowler_style,
                    "score": score,
                    "wickets": wickets,
                    "runs_this_ball": runs,
                    "is_wicket": is_wicket,
                    "run_rate": round(run_rate, 4),
                    "target": 170 if cfg.format_name == "T20" else 280,
                }
                row["is_boundary"] = 1 if runs in (4, 6) else 0
                yield row


def build_match_configs(match_count: int, rng: random.Random) -> list[MatchConfig]:
    configs: list[MatchConfig] = []
    for i in range(match_count):
        format_name = "T20" if rng.random() < 0.8 else "ODI"
        innings_count = 2
        balls_per_innings = 120 if format_name == "T20" else 300
        venue = rng.choice(VENUES)
        toss_winner = rng.choice(TEAMS)
        toss_decision = rng.choice(["bat", "bowl"])
        configs.append(
            MatchConfig(
                match_id=f"M{i+1:05d}",
                format_name=format_name,
                innings_count=innings_count,
                balls_per_innings=balls_per_innings,
                venue=venue,
                toss_winner=toss_winner,
                toss_decision=toss_decision,
            )
        )
    return configs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate synthetic cricket data.")
    parser.add_argument(
        "--matches",
        type=int,
        default=300,
        help="Number of synthetic matches to generate.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic generation.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/ball_by_ball_sample.csv"),
        help="Output CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    configs = build_match_configs(args.matches, rng)
    rows: list[dict] = []
    for cfg in configs:
        rows.extend(simulate_match(cfg, rng))

    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df):,} rows to {output_path}")


if __name__ == "__main__":
    main()
