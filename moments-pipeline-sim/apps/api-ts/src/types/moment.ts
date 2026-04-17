export type MomentType =
  | "goal"
  | "lead_change"
  | "timeout"
  | "clutch_play"
  | "milestone";

export interface MomentEvent {
  event_id: string;
  event_time: string;
  ingest_time?: string;
  league: string;
  game_id: string;
  team_id?: string;
  player_id?: string;
  moment_type: MomentType;
  importance_score: number;
  metadata: Record<string, unknown>;
}
