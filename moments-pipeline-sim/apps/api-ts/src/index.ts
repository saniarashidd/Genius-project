import "dotenv/config";
import express from "express";

import { logger } from "./lib/logger.js";
import { healthRouter } from "./routes/health.js";
import { momentsRouter } from "./routes/moments.js";

const app = express();
app.use(express.json({ limit: "1mb" }));

app.use(healthRouter);
app.use(momentsRouter);

const port = Number(process.env.PORT ?? 3000);
app.listen(port, () => {
  logger.info({ port }, "moments api started");
});
