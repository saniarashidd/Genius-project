CREATE INDEX idx_moments_raw_game_time ON moments_raw (game_id, event_time);
CREATE INDEX idx_moments_raw_type_time ON moments_raw (moment_type, event_time);
CREATE INDEX idx_ad_triggers_campaign_time ON ad_triggers (campaign_id, triggered_at);
CREATE INDEX idx_consumer_errors_time ON consumer_errors (occurred_at);
