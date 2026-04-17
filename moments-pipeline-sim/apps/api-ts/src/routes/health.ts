import { Router } from "express";

export const healthRouter = Router();

healthRouter.get("/healthz", (_req, res) => {
  res.status(200).json({
    ok: true,
    service: "moments-api-ts",
    time: new Date().toISOString()
  });
});
