# Signal weights for sales outreach decisions
# Higher weights = more influence on final score

SIGNAL_WEIGHTS = {
    "recent_engagement": 0.20,      # Did they open/click recently?
    "reply_signal": 0.15,           # Did they reply before?
    "cooldown_respected": 0.15,     # Enough time since last contact?
    "business_hours": 0.15,         # Is it a good time of day?
    "day_score": 0.10,              # Is it a good day of week?
    "hiring_signal": 0.08,          # Company actively hiring?
    "growth_signal": 0.07,          # Company growing?
    "tech_match": 0.05,             # Do they use similar tech?
    "urgency_score": 0.05           # How urgent is this lead?
}
