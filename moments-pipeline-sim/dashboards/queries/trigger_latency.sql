SELECT
  mr.moment_type,
  AVG(TIMESTAMPDIFF(MICROSECOND, mr.event_time, at.triggered_at)) / 1000 AS avg_latency_ms,
  MAX(TIMESTAMPDIFF(MICROSECOND, mr.event_time, at.triggered_at)) / 1000 AS max_latency_ms
FROM moments_raw mr
JOIN ad_triggers at ON at.event_id = mr.event_id
GROUP BY mr.moment_type
ORDER BY avg_latency_ms DESC;
