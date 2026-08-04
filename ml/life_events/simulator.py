"""Probabilistic life-event simulation engine (PART 3).

This module walks a synthetic person (or Digital Twin) forward through
time, throwing life events with probabilities read from config. Each
event is emitted as a :class:`FinancialEvent` with a payload describing
the change. The events are *not* applied to the twin here — the caller
decides whether to append them to a twin's timeline (the Digital Twin
service does that). The simulator is purely generative.

All probabilities are loadable from ``ml/config/config.yaml`` under the
``life_events`` section, so the simulation is fully configurable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from ml.config import MLConfig, get_config
from ml.digital_twin.events.event import EventType, FinancialEvent
from ml.models import FinancialTwinProfile, Occupation
from ml.utils.logging import get_logger
from ml.utils.seeding import get_rng

logger = get_logger(__name__)


@dataclass
class LifeEventSimulator:
    """Simulates life events for a person over a horizon.

    Parameters
    ----------
    config:
        Optional :class:`~ml.config.MLConfig`. Defaults to the process
        cached config.
    """

    config: Optional[MLConfig] = None

    def __post_init__(self) -> None:
        self._cfg = self.config or get_config()
        self._events = self._cfg.life_events

    # ── per-year event sampling ────────────────────────────────────
    def _draw_events_for_year(
        self,
        profile: FinancialTwinProfile,
        age: int,
        rng,
    ) -> List[FinancialEvent]:
        """Return the events a person experiences during one year of life."""
        twin_id = profile.person_id
        events: List[FinancialEvent] = []
        ev = self._events

        # Promotion / salary growth (if working)
        if profile.occupation in (Occupation.STUDENT, Occupation.RETIRED, Occupation.HOMEMAKER):
            pass
        elif rng.random() < ev.promotion_probability:
            growth = profile.salary_growth_rate * (1.0 + rng.uniform(-0.2, 0.4))
            new_income = profile.monthly_income * (1.0 + growth)
            events.append(
                FinancialEvent.create(
                    twin_id,
                    EventType.PROMOTION,
                    {
                        "monthly_income": new_income,
                        "salary_growth_rate": growth,
                        "old_income": profile.monthly_income,
                    },
                )
            )
        else:
            # Routine salary growth
            growth = profile.salary_growth_rate * rng.uniform(0.5, 1.2)
            new_income = profile.monthly_income * (1.0 + growth)
            events.append(
                FinancialEvent.create(
                    twin_id,
                    EventType.SALARY_CHANGE,
                    {"monthly_income": new_income, "salary_growth_rate": growth},
                )
            )

        # Marriage (only if single and above a threshold age)
        if (
            profile.marital_status.value == "single"
            and age >= 22
            and rng.random() < ev.marriage_probability
        ):
            events.append(
                FinancialEvent.create(
                    twin_id, EventType.MARRIAGE, {"marital_status": "married"}
                )
            )

        # Childbirth (if married, under 45)
        if (
            profile.marital_status.value == "married"
            and age < 45
            and rng.random() < ev.childbirth_probability
        ):
            events.append(
                FinancialEvent.create(twin_id, EventType.CHILD_BIRTH, {"dependents": profile.dependents + 1})
            )

        # House purchase
        if rng.random() < ev.house_purchase_probability:
            estimated_value = profile.monthly_income * 60 * rng.uniform(0.8, 1.5)
            debt = estimated_value * 0.8
            emi = debt * 0.0075  # ~7.5% annual equivalent monthly repayment
            events.append(
                FinancialEvent.create(
                    twin_id,
                    EventType.HOUSE_PURCHASE,
                    {"value": estimated_value, "debt": debt, "emi": emi},
                )
            )

        # Vehicle purchase
        if rng.random() < ev.vehicle_purchase_probability:
            value = profile.monthly_income * 6 * rng.uniform(0.8, 1.4)
            debt = value * 0.6
            emi = debt * 0.01
            events.append(
                FinancialEvent.create(
                    twin_id,
                    EventType.VEHICLE_PURCHASE,
                    {"value": value, "debt": debt, "emi": emi},
                )
            )

        # Inheritance
        if rng.random() < ev.inheritance_probability:
            amount = profile.monthly_income * 24 * rng.uniform(1.0, 5.0)
            events.append(FinancialEvent.create(twin_id, EventType.INHERITANCE, {"amount": amount}))

        # Medical emergency
        if rng.random() < ev.medical_emergency_probability:
            cost = profile.monthly_income * rng.uniform(2.0, 12.0)
            events.append(FinancialEvent.create(twin_id, EventType.MEDICAL_EMERGENCY, {"cost": cost}))

        # Job loss
        if profile.occupation not in (Occupation.STUDENT, Occupation.RETIRED, Occupation.HOMEMAKER):
            if rng.random() < ev.job_loss_probability:
                events.append(FinancialEvent.create(twin_id, EventType.JOB_LOSS, {"reason": "layoff"}))

        # Career switch
        if (
            profile.occupation not in (Occupation.STUDENT, Occupation.RETIRED)
            and rng.random() < ev.career_switch_probability
        ):
            events.append(
                FinancialEvent.create(
                    twin_id,
                    EventType.CAREER_SWITCH,
                    {"occupation": profile.occupation, "monthly_income": profile.monthly_income},
                )
            )

        # Business success / failure (business owners)
        if profile.occupation in (Occupation.BUSINESS_OWNER, Occupation.STARTUP_FOUNDER, Occupation.RETAIL_OWNER):
            if rng.random() < ev.business_success_probability:
                bonus = profile.monthly_income * rng.uniform(2.0, 10.0)
                events.append(
                    FinancialEvent.create(
                        twin_id, EventType.BUSINESS_SUCCESS, {"amount": bonus, "monthly_income": profile.monthly_income * (1 + rng.uniform(0.1, 0.5))}
                    )
                )
            elif rng.random() < ev.business_failure_probability:
                loss = profile.monthly_income * rng.uniform(3.0, 12.0)
                events.append(
                    FinancialEvent.create(twin_id, EventType.BUSINESS_FAILURE, {"amount": loss})
                )

        return events

    def simulate_year(
        self, profile: FinancialTwinProfile, year: int, start_age: int
    ) -> List[FinancialEvent]:
        """Simulate one year of a person's life.

        Parameters
        ----------
        profile:
            The person's current profile.
        year:
            Absolute calendar year (used only for timestamps).
        start_age:
            The person's age at the start of this year.

        Returns
        -------
        List[FinancialEvent]
            The events that occurred during this year.
        """
        rng = get_rng()
        events = self._draw_events_for_year(profile, start_age, rng)
        # Stamp a timestamp for this year
        now = datetime.now(timezone.utc)
        for e in events:
            e = FinancialEvent(
                event_id=e.event_id,
                twin_id=e.twin_id,
                event_type=e.event_type,
                timestamp=now.replace(year=year),
                payload=e.payload,
            )
        return events

    def simulate_lifetime(
        self,
        profile: FinancialTwinProfile,
        n_years: Optional[int] = None,
        start_year: int = 2024,
    ) -> List[FinancialEvent]:
        """Simulate a full lifetime of events for a person.

        Parameters
        ----------
        profile:
            The starting profile.
        n_years:
            Number of years to simulate. Defaults to the person's
            remaining working years until retirement_age.
        start_year:
            The absolute year to start from.

        Returns
        -------
        List[FinancialEvent]
            The ordered list of life events.
        """
        rng = get_rng()
        if n_years is None:
            n_years = max(1, profile.retirement_age - profile.age)
        events: List[FinancialEvent] = []
        age = profile.age
        for i in range(n_years):
            year_events = self._draw_events_for_year(profile, age, rng)
            now = datetime.now(timezone.utc)
            for e in year_events:
                e = FinancialEvent(
                    event_id=e.event_id,
                    twin_id=e.twin_id,
                    event_type=e.event_type,
                    timestamp=now.replace(year=start_year + i),
                    payload=e.payload,
                )
                events.append(e)
            age += 1
            # death check
            if rng.random() < self._cfg.life_events.mortality_base * (age / 60.0):
                events.append(
                    FinancialEvent.create(
                        profile.person_id, EventType.DEATH, {"age": age}
                    )
                )
                break
        return events


def simulate_life_timeline(
    profile: FinancialTwinProfile,
    n_years: Optional[int] = None,
    config: Optional[MLConfig] = None,
) -> List[FinancialEvent]:
    """Convenience wrapper to simulate a full life timeline.

    Parameters
    ----------
    profile:
        The starting profile.
    n_years:
        Number of years to simulate.
    config:
        Optional config.

    Returns
    -------
    List[FinancialEvent]
        The ordered list of life events.
    """
    sim = LifeEventSimulator(config=config)
    return sim.simulate_lifetime(profile, n_years=n_years)
