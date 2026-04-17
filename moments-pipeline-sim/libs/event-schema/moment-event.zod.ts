import { z } from "zod";

export const momentTypeSchema = z.enum([
  "goal",
  "lead_change",
  "timeout",
  "clutch_play",
  "milestone"
]);

export const momentEventSchema = z.object({
  event_id: z.string().min(8),
  event_time: z.string().datetime(),
  ingest_time: z.string().datetime().optional(),
  league: z.string().min(1),
  game_id: z.string().min(1),
  team_id: z.string().min(1).optional(),
  player_id: z.string().min(1).optional(),
  moment_type: momentTypeSchema,
  importance_score: z.number().min(0).max(1),
  metadata: z.record(z.unknown())
});

export type MomentEvent = z.infer<typeof momentEventSchema>;
