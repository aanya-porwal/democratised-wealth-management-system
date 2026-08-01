"""tests for the end-to-end planner."""

from wealth_management_system.planner import build_plan
from wealth_management_system.sample_users import build_all_sample_users


def test_plan_builds_for_all_users():
    """the planner must produce a plan for every archetype."""
    for user in build_all_sample_users():
        plan = build_plan(user)
        assert plan.user_name == user.name
        assert plan.summary
        assert plan.health.score >= 0
        assert plan.risk.final_score_100 >= 0


def test_every_action_has_a_reason():
    """no unexplained recommendations — that is the core promise."""
    for user in build_all_sample_users():
        plan = build_plan(user)
        for a in plan.actions:
            assert a.action
            assert a.reason
            assert a.priority in ("now", "next", "later")


def test_foundations_come_first_for_ravi():
    """ravi's thin emergency fund must be the top priority."""
    plan = build_plan([u for u in build_all_sample_users() if u.name == "Ravi Shankar"][0])
    now_actions = [a for a in plan.actions if a.priority == "now"]
    assert now_actions, "ravi should have immediate actions"
    # at least one 'now' action must mention the emergency fund
    assert any("emergency fund" in a.action.lower() for a in now_actions)


def test_student_is_told_not_to_invest():
    """a student spending more than they earn should never be told to invest."""
    student = [u for u in build_all_sample_users() if u.name == "Aarav Student"][0]
    plan = build_plan(student)
    now_actions = " ".join(a.action.lower() for a in plan.actions if a.priority == "now")
    assert "cut expenses" in now_actions or "raise income" in now_actions


def test_actions_ordered_now_before_next():
    """now-actions must come before next-actions."""
    for user in build_all_sample_users():
        plan = build_plan(user)
        priorities = [a.priority for a in plan.actions]
        # 'now' must not appear after 'next'
        seen_next = False
        for p in priorities:
            if p == "next":
                seen_next = True
            if seen_next:
                assert p != "now", "now-action must not come after a next-action"

