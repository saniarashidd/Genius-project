use crate::moment::MomentEvent;

pub fn score_moment(event: &MomentEvent) -> f64 {
    let type_bonus = match event.moment_type.as_str() {
        "clutch_play" => 0.20,
        "lead_change" => 0.15,
        "goal" => 0.10,
        "milestone" => 0.08,
        "timeout" => 0.02,
        _ => 0.0,
    };
    (event.importance_score + type_bonus).min(1.0)
}

pub fn should_trigger(score: f64) -> bool {
    score >= 0.65
}
