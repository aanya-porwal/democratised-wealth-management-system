"""orchestration entry point — run the full planning pipeline.

this is the public face of the system. it takes a user, runs the
planner (cashflow -> health -> goals -> risk -> portfolio ->
probability -> explained actions) and prints the result in plain
language. all heavy lifting lives in the engines; this file only
wires them together and prints.
"""

from wealth_management_system.planner import build_plan
from wealth_management_system.sample_users import build_all_sample_users
from wealth_management_system.utils import ensure_utf8_console


def _print_plan(user) -> None:
    """print one user's full explained plan."""
    plan = build_plan(user)

    print("=" * 72)
    print(f"FINANCIAL PLAN — {plan.user_name}")
    print("=" * 72)
    print(plan.summary)
    print()

    print(f"Health: {plan.health.grade} ({plan.health.score}/100)")
    print(f"Risk capacity: {plan.risk.risk_category} ({plan.risk.final_score_100}/100)")

    print("\nPortfolio allocation (strategic target):")
    for s in plan.portfolio.slices:
        names = ", ".join(i.value.replace("_", " ") for i in s.instruments)
        print(f"  {s.bucket:<8} {s.weight:>5.1%}  →  {names}")

    print("\nRecommended actions:")
    for a in plan.actions:
        print(f"  [{a.priority:<4}] {a.action}")
        print(f"        ↳ {a.reason}")

    print("\nGoal outlook:")
    for p in plan.probabilities:
        print(
            f"  {p.goal_type.replace('_', ' '):<20} "
            f"{p.probability:>5.0%}  median ₹{p.median_outcome:>12,.0f} "
            f"({p.verdict})"
        )
    print()


def main() -> None:
    """run the planning pipeline for every sample user."""
    ensure_utf8_console()
    for user in build_all_sample_users():
        _print_plan(user)


if __name__ == "__main__":
    main()

