use anyhow::Result;
use mysql::{params, prelude::Queryable, Pool, PooledConn};

use crate::moment::MomentEvent;

pub struct MysqlRepo {
    pool: Pool,
}

impl MysqlRepo {
    pub fn new(database_url: &str) -> Result<Self> {
        let pool = Pool::new(database_url)?;
        Ok(Self { pool })
    }

    fn conn(&self) -> Result<PooledConn> {
        Ok(self.pool.get_conn()?)
    }

    pub fn insert_raw_moment(&self, event: &MomentEvent) -> Result<()> {
        let mut conn = self.conn()?;
        let metadata_json = serde_json::to_string(&event.metadata)?;
        conn.exec_drop(
            r"INSERT INTO moments_raw
              (event_id, event_time, ingest_time, league, game_id, team_id, player_id, moment_type, importance_score, metadata)
              VALUES
              (:event_id, :event_time, COALESCE(:ingest_time, NOW(3)), :league, :game_id, :team_id, :player_id, :moment_type, :importance_score, CAST(:metadata AS JSON))
              ON DUPLICATE KEY UPDATE event_id = event_id",
            params! {
                "event_id" => &event.event_id,
                "event_time" => &event.event_time,
                "ingest_time" => &event.ingest_time,
                "league" => &event.league,
                "game_id" => &event.game_id,
                "team_id" => &event.team_id,
                "player_id" => &event.player_id,
                "moment_type" => &event.moment_type,
                "importance_score" => event.importance_score,
                "metadata" => metadata_json,
            },
        )?;
        Ok(())
    }

    pub fn insert_scored(&self, event_id: &str, score: f64, accepted: bool, reason: &str) -> Result<()> {
        let mut conn = self.conn()?;
        conn.exec_drop(
            r"INSERT INTO moments_scored (event_id, score, accepted, reason)
              VALUES (:event_id, :score, :accepted, :reason)
              ON DUPLICATE KEY UPDATE score = VALUES(score), accepted = VALUES(accepted), reason = VALUES(reason)",
            params! {
                "event_id" => event_id,
                "score" => score,
                "accepted" => accepted,
                "reason" => reason,
            },
        )?;
        Ok(())
    }

    pub fn insert_trigger(&self, event_id: &str, campaign_id: &str, triggered: bool, trigger_reason: &str) -> Result<()> {
        let mut conn = self.conn()?;
        conn.exec_drop(
            r"INSERT INTO ad_triggers (event_id, campaign_id, triggered, trigger_reason)
              VALUES (:event_id, :campaign_id, :triggered, :trigger_reason)",
            params! {
                "event_id" => event_id,
                "campaign_id" => campaign_id,
                "triggered" => triggered,
                "trigger_reason" => trigger_reason,
            },
        )?;
        Ok(())
    }
}
