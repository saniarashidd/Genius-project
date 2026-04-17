use std::collections::HashSet;

pub struct DedupeCache {
    seen: HashSet<String>,
}

impl DedupeCache {
    pub fn new() -> Self {
        Self {
            seen: HashSet::new(),
        }
    }

    pub fn has_seen(&self, event_id: &str) -> bool {
        self.seen.contains(event_id)
    }

    pub fn mark_seen(&mut self, event_id: &str) {
        self.seen.insert(event_id.to_string());
    }
}
