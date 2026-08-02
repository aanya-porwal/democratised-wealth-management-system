"""Background task modules run by the APScheduler.

Each module wraps one of the ``app.services.background`` functions so
the scheduler in ``app.main`` can import them cleanly without circular
dependencies.

These modules are deliberately thin — the actual logic lives in
``app.services.background`` so it can be called from both the scheduler
and the test suite.
"""
