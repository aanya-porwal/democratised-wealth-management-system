"""Production backend package for the wealth management system.

This package is the FastAPI + PostgreSQL + Redis backend. It is
deliberately decoupled from the financial engine
(``wealth_management_system``): the only bridge between the two is
:mod:`app.services.engine_adapter`, which maps database records to the
engine's pure dataclasses and converts engine outputs back into API DTOs.

The engine itself is never modified.
"""

__version__ = "1.0.0"

