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

    pub fn is_duplicate(&mut self, event_id: &str) -> bool {
        if self.seen.contains(event_id) {
            true
        } else {
            self.seen.insert(event_id.to_string());
            false
        }
    }
}
