"""Event types and the immutable event model for the Digital Twin.

Every change to a twin's financial life is an event. Events are
immutable once created — they carry a timestamp, an event type, the
twin id and a payload describing the change. Because events are never
mutated or deleted, the twin's complete history is preserved and can be
replayed.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class EventType(str, Enum):
    """The universe of financial life events a twin can experience."""

    # Demographic / identity
    PROFILE_CREATED = "profile_created"
    MARRIAGE = "marriage"
    DIVORCE = "divorce"
    CHILD_BIRTH = "child_birth"
    DEPENDENT_CHANGE = "dependent_change"

    # Income / career
    SALARY_CHANGE = "salary_change"
    PROMOTION = "promotion"
    JOB_LOSS = "job_loss"
    CAREER_SWITCH = "career_switch"
    RETIREMENT = "retirement"
    BUSINESS_SUCCESS = "business_success"
    BUSINESS_FAILURE = "business_failure"
    INHERITANCE = "inheritance"

    # Expenses / liabilities
    HOUSE_PURCHASE = "house_purchase"
    VEHICLE_PURCHASE = "vehicle_purchase"
    LOAN_TAKEN = "loan_taken"
    LOAN_REPAID = "loan_repaid"
    MEDICAL_EMERGENCY = "medical_emergency"

    # Portfolio / market
    PORTFOLIO_CHANGE = "portfolio_change"
    MARKET_MOVEMENT = "market_movement"
    INVESTMENT_ADDED = "investment_added"
    INVESTMENT_WITHDRAWN = "investment_withdrawn"

    # Insurance / tax
    INSURANCE_ADDED = "insurance_added"
    TAX_STATUS_CHANGE = "tax_status_change"

    # Behaviour
    BEHAVIOUR_CHANGE = "behaviour_change"
    RISK_PROFILE_CHANGE = "risk_profile_change"

    # Recommendations
    RECOMMENDATION_GENERATED = "recommendation_generated"
    RECOMMENDATION_ACCEPTED = "recommendation_accepted"
    RECOMMENDATION_REJECTED = "recommendation_rejected"
    RECOMMENDATION_IGNORED = "recommendation_ignored"
    RECOMMENDATION_MODIFIED = "recommendation_modified"

    # Lifecycle
    DEATH = "death"
    SNAPSHOT = "snapshot"


@dataclass(frozen=True)
class FinancialEvent:
    """An immutable, timestamped change to a twin's financial life.

    Attributes
    ----------
    event_id:
        Unique identifier for this event.
    twin_id:
        The twin this event belongs to.
    event_type:
        The category of event.
    timestamp:
        When the event occurred (UTC).
    payload:
        Arbitrary structured data describing the change.
    """

    event_id: str
    twin_id: str
    event_type: EventType
    timestamp: datetime
    payload: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        twin_id: str,
        event_type: EventType,
        payload: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> "FinancialEvent":
        """Create a new immutable event with a generated id."""
        return cls(
            event_id=str(uuid.uuid4()),
            twin_id=twin_id,
            event_type=event_type,
            timestamp=timestamp or datetime.utcnow(),
            payload=payload or {},
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "twin_id": self.twin_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancialEvent":
        return cls(
            event_id=data["event_id"],
            twin_id=data["twin_id"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload=data.get("payload", {}),
        )


# ImmutableFinancialEvent is an alias for clarity — the core type is
# already a frozen dataclass, so it is immutable by construction.
ImmutableFinancialEvent = FinancialEvent
