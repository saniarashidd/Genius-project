import mysql from "mysql2/promise";

const pool = mysql.createPool({
  host: process.env.MYSQL_HOST ?? "127.0.0.1",
  port: Number(process.env.MYSQL_PORT ?? 3306),
  user: process.env.MYSQL_USER ?? "root",
  password: process.env.MYSQL_PASSWORD ?? "root",
  database: process.env.MYSQL_DATABASE ?? "moments",
  connectionLimit: 10
});

export async function getRecentMoments(league?: string, limit = 50) {
  const safeLimit = Number.isFinite(limit) ? Math.min(Math.max(limit, 1), 200) : 50;

  const where = league ? "WHERE league = ?" : "";
  const params = league ? [league, safeLimit] : [safeLimit];

  const [rows] = await pool.query(
    `SELECT event_id, event_time, league, game_id, moment_type, importance_score, metadata
     FROM moments_raw
     ${where}
     ORDER BY event_time DESC
     LIMIT ?`,
    params
  );
  return rows;
}

export async function getCampaignTriggers(campaignId: string, from: string, to: string) {
  const [rows] = await pool.query(
    `SELECT event_id, campaign_id, triggered, trigger_reason, triggered_at
     FROM ad_triggers
     WHERE campaign_id = ? AND triggered_at BETWEEN ? AND ?
     ORDER BY triggered_at DESC`,
    [campaignId, from, to]
  );
  return rows;
}
