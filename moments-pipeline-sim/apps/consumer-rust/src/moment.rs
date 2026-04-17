use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Debug, Deserialize, Serialize, Clone)]
pub struct MomentEvent {
    pub event_id: String,
    pub event_time: String,
    pub ingest_time: Option<String>,
    pub league: String,
    pub game_id: String,
    pub team_id: Option<String>,
    pub player_id: Option<String>,
    pub moment_type: String,
    pub importance_score: f64,
    pub metadata: Value,
}
