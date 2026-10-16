from controllers.applications import ALLOWED_TRANSITIONS

def test_valid_application_transitions_exist():
    assert "under_review" in ALLOWED_TRANSITIONS["submitted"]
    assert "interview" in ALLOWED_TRANSITIONS["shortlisted"]
    assert "hired" in ALLOWED_TRANSITIONS["offered"]

def test_terminal_states_do_not_allow_arbitrary_transitions():
    assert "submitted" not in ALLOWED_TRANSITIONS.get("rejected", set())
    assert "submitted" not in ALLOWED_TRANSITIONS.get("withdrawn", set())
