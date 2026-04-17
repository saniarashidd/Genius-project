SELECT
  mr.moment_type,
  COUNT(*) AS trigger_count,
  AVG(CASE WHEN at.triggered THEN 1 ELSE 0 END) AS trigger_rate
FROM moments_raw mr
JOIN ad_triggers at ON at.event_id = mr.event_id
GROUP BY mr.moment_type
ORDER BY trigger_count DESC;
