"""Financial health score engine.

Produces a 0-100 financial health score across nine factors — emergency
fund, debt, savings rate, insurance, investment rate, diversification,
goal progress, tax efficiency, and return — with strengths, weaknesses
and actionable suggestions for every user.
"""

from wealth_management_system.score.engine import HealthScoreEngine

__all__ = ["HealthScoreEngine"]

