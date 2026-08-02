"""Backend test suite.

Tests cover:
* Authentication (register, login, refresh, logout, password reset)
* User management (CRUD, roles)
* Profile management (demographic, financial, behavioural)
* Goal CRUD and engine analysis
* Portfolio CRUD, holdings, snapshots
* Strategic allocation engine
* Rebalancing engine
* Recommendation engine
* Monte Carlo simulation engine
* Financial health score engine
* Planner (full pipeline)
* Repositories (unit, mocked session)
* Services (integration via engine adapter)

Run with::

    cd capstone/wealth-management-system
    python -m pytest app/tests -v --tb=short
"""
