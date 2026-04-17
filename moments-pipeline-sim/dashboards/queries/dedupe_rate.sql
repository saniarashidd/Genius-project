SELECT
  DATE(created_at) AS day,
  COUNT(*) AS unique_events
FROM moments_raw
GROUP BY DATE(created_at)
ORDER BY day DESC;
