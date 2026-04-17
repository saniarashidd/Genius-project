import { Router } from "express";
import { z } from "zod";

import { getCampaignTriggers, getRecentMoments } from "../lib/db.js";
import { logger } from "../lib/logger.js";
import { getProducer } from "../lib/pulsar.js";

const momentTypeSchema = z.enum([
  "goal",
  "lead_change",
  "timeout",
  "clutch_play",
  "milestone"
]);

const momentEventSchema = z.object({
  event_id: z.string().min(8),
  event_time: z.string().datetime(),
  ingest_time: z.string().datetime().optional(),
  league: z.string().min(1),
  game_id: z.string().min(1),
  team_id: z.string().optional(),
  player_id: z.string().optional(),
  moment_type: momentTypeSchema,
  importance_score: z.number().min(0).max(1),
  metadata: z.record(z.unknown())
});

const queryRangeSchema = z.object({
  from: z.string().datetime(),
  to: z.string().datetime()
});

export const momentsRouter = Router();

momentsRouter.post("/moments/ingest", async (req, res) => {
  const parsed = momentEventSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "invalid_moment_event", details: parsed.error.flatten() });
  }

  const moment = {
    ...parsed.data,
    ingest_time: parsed.data.ingest_time ?? new Date().toISOString()
  };

  const producer = await getProducer();
  await producer.send({
    data: Buffer.from(JSON.stringify(moment)),
    partitionKey: `${moment.game_id}:${moment.moment_type}`
  });

  logger.info({ eventId: moment.event_id, gameId: moment.game_id }, "published moment event");

  return res.status(202).json({ accepted: true, event_id: moment.event_id });
});

momentsRouter.get("/moments/recent", async (req, res) => {
  const league = typeof req.query.league === "string" ? req.query.league : undefined;
  const limit = typeof req.query.limit === "string" ? Number(req.query.limit) : 50;
  const rows = await getRecentMoments(league, limit);
  return res.status(200).json(rows);
});

momentsRouter.get("/campaigns/:campaignId/triggers", async (req, res) => {
  const parsedRange = queryRangeSchema.safeParse({
    from: req.query.from,
    to: req.query.to
  });
  if (!parsedRange.success) {
    return res.status(400).json({ error: "invalid_range", details: parsedRange.error.flatten() });
  }

  const rows = await getCampaignTriggers(
    req.params.campaignId,
    parsedRange.data.from,
    parsedRange.data.to
  );
  return res.status(200).json(rows);
});
