"""initial schema for the wealth management backend

Revision ID: 0001_initial
Revises:
Create Date: 2025-01-01 00:00:00.000000

Creates every table that backs the ORM models in ``app.models``:

* identity & auth: users, refresh_tokens, password_reset_tokens,
  email_verification_tokens
* profiles: user_profiles, financial_profiles, behavioral_profiles
* planning: goals, goal_progress
* portfolio: portfolios, portfolio_holdings, portfolio_snapshots
* intelligence: recommendations, financial_health_scores,
  simulation_results, scenario_analyses
* system: system_settings, market_data_cache, chat_sessions
* audit: audit_logs
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the initial schema."""
    # gen_random_uuid() ships in PostgreSQL 13+ core; pgcrypto is a
    # no-op on newer versions and required on older ones.
    # PostgreSQL-only: SQLite (used for local/migration smoke checks) has
    # no CREATE EXTENSION and rejects the statement outright.
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── users ──────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.String(length=16),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_phone"), "users", ["phone"], unique=True)
    op.create_index(op.f("ix_users_role"), "users", ["role"])
    op.create_index(op.f("ix_users_deleted_at"), "users", ["deleted_at"])

    # ── refresh_tokens ─────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_tokens_jti"), "refresh_tokens", ["jti"], unique=True)
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"])

    # ── password_reset_tokens ──────────────────────────────────────
    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_password_reset_tokens_user_id"), "password_reset_tokens", ["user_id"]
    )

    # ── email_verification_tokens ──────────────────────────────────
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_verification_tokens_user_id"), "email_verification_tokens", ["user_id"]
    )

    # ── user_profiles ──────────────────────────────────────────────
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("dependents", sa.Integer(), nullable=False),
        sa.Column("life_stage", sa.String(length=32), nullable=True),
        sa.Column("marital_status", sa.String(length=32), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("occupation", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_user_profiles_user_id"), "user_profiles", ["user_id"], unique=True)
    op.create_index(op.f("ix_user_profiles_deleted_at"), "user_profiles", ["deleted_at"])

    # ── financial_profiles ─────────────────────────────────────────
    op.create_table(
        "financial_profiles",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("monthly_income", sa.Float(), nullable=False),
        sa.Column("employment_type", sa.String(length=32), nullable=False),
        sa.Column("income_stability", sa.Float(), nullable=False),
        sa.Column("secondary_income", sa.Boolean(), nullable=False),
        sa.Column("secondary_monthly_income", sa.Float(), nullable=False),
        sa.Column("monthly_fixed_expenses", sa.Float(), nullable=False),
        sa.Column("monthly_variable_expenses", sa.Float(), nullable=False),
        sa.Column("emergency_fund_months", sa.Float(), nullable=False),
        sa.Column("existing_investments", sa.Float(), nullable=False),
        sa.Column("provident_fund_balance", sa.Float(), nullable=False),
        sa.Column("real_estate_value", sa.Float(), nullable=False),
        sa.Column("gold_value", sa.Float(), nullable=False),
        sa.Column("total_debt", sa.Float(), nullable=False),
        sa.Column("monthly_emi_total", sa.Float(), nullable=False),
        sa.Column("tax_bracket_percent", sa.Float(), nullable=False),
        sa.Column("has_term_life_insurance", sa.Boolean(), nullable=False),
        sa.Column("has_health_insurance", sa.Boolean(), nullable=False),
        sa.Column("existing_monthly_sip", sa.Float(), nullable=False),
        sa.Column("extra", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_financial_profiles_user_id"), "financial_profiles", ["user_id"], unique=True
    )
    op.create_index(op.f("ix_financial_profiles_deleted_at"), "financial_profiles", ["deleted_at"])

    # ── behavioral_profiles ────────────────────────────────────────
    op.create_table(
        "behavioral_profiles",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("risk_tolerance", sa.String(length=64), nullable=False),
        sa.Column("drawdown_reaction_score", sa.Integer(), nullable=False),
        sa.Column("has_invested_before", sa.Boolean(), nullable=False),
        sa.Column("has_experienced_market_crash", sa.Boolean(), nullable=False),
        sa.Column("financial_literacy_score", sa.Integer(), nullable=False),
        sa.Column("loss_aversion_score", sa.Integer(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("risk_category", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_behavioral_profiles_user_id"), "behavioral_profiles", ["user_id"], unique=True
    )
    op.create_index(op.f("ix_behavioral_profiles_deleted_at"), "behavioral_profiles", ["deleted_at"])

    # ── goals ──────────────────────────────────────────────────────
    op.create_table(
        "goals",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("goal_type", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("target_amount", sa.Float(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("current_savings_for_goal", sa.Float(), nullable=False),
        sa.Column("current_monthly_contribution", sa.Float(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_goals_user_id"), "goals", ["user_id"])
    op.create_index(op.f("ix_goals_goal_type"), "goals", ["goal_type"])
    op.create_index(op.f("ix_goals_priority"), "goals", ["priority"])
    op.create_index(op.f("ix_goals_deleted_at"), "goals", ["deleted_at"])

    # ── goal_progress ──────────────────────────────────────────────
    op.create_table(
        "goal_progress",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("goal_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_savings", sa.Float(), nullable=False),
        sa.Column("progress_percent", sa.Float(), nullable=False),
        sa.Column("probability_of_success", sa.Float(), nullable=True),
        sa.Column("required_sip", sa.Float(), nullable=True),
        sa.Column("remaining_gap", sa.Float(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_goal_progress_goal_id"), "goal_progress", ["goal_id"])
    op.create_index(op.f("ix_goal_progress_user_id"), "goal_progress", ["user_id"])
    op.create_index(op.f("ix_goal_progress_recorded_at"), "goal_progress", ["recorded_at"])
    op.create_index(op.f("ix_goal_progress_deleted_at"), "goal_progress", ["deleted_at"])

    # ── portfolios ─────────────────────────────────────────────────
    op.create_table(
        "portfolios",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_value", sa.Float(), nullable=False),
        sa.Column("target_allocation", sa.JSON(), nullable=True),
        sa.Column("is_primary", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_portfolios_user_id"), "portfolios", ["user_id"])
    op.create_index(op.f("ix_portfolios_deleted_at"), "portfolios", ["deleted_at"])

    # ── portfolio_holdings ─────────────────────────────────────────
    op.create_table(
        "portfolio_holdings",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("portfolio_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("asset_class", sa.String(length=64), nullable=False),
        sa.Column("bucket", sa.String(length=32), nullable=True),
        sa.Column("market_value", sa.Float(), nullable=False),
        sa.Column("cost_basis", sa.Float(), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_portfolio_holdings_portfolio_id"), "portfolio_holdings", ["portfolio_id"]
    )
    op.create_index(op.f("ix_portfolio_holdings_user_id"), "portfolio_holdings", ["user_id"])
    op.create_index(
        op.f("ix_portfolio_holdings_asset_class"), "portfolio_holdings", ["asset_class"]
    )
    op.create_index(op.f("ix_portfolio_holdings_deleted_at"), "portfolio_holdings", ["deleted_at"])

    # ── portfolio_snapshots ────────────────────────────────────────
    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("portfolio_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_value", sa.Float(), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=True),
        sa.Column("cash_flow", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_portfolio_snapshots_portfolio_id"), "portfolio_snapshots", ["portfolio_id"]
    )
    op.create_index(op.f("ix_portfolio_snapshots_user_id"), "portfolio_snapshots", ["user_id"])
    op.create_index(
        op.f("ix_portfolio_snapshots_captured_at"), "portfolio_snapshots", ["captured_at"]
    )
    op.create_index(
        op.f("ix_portfolio_snapshots_deleted_at"), "portfolio_snapshots", ["deleted_at"]
    )

    # ── recommendations ────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("recommendation_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=True),
        sa.Column("impact", sa.String(length=255), nullable=True),
        sa.Column("priority", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recommendations_user_id"), "recommendations", ["user_id"])
    op.create_index(
        op.f("ix_recommendations_recommendation_type"), "recommendations", ["recommendation_type"]
    )
    op.create_index(op.f("ix_recommendations_status"), "recommendations", ["status"])
    op.create_index(op.f("ix_recommendations_valid_until"), "recommendations", ["valid_until"])
    op.create_index(op.f("ix_recommendations_deleted_at"), "recommendations", ["deleted_at"])

    # ── financial_health_scores ────────────────────────────────────
    op.create_table(
        "financial_health_scores",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("grade", sa.String(length=16), nullable=False),
        sa.Column("factors", sa.JSON(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("weaknesses", sa.JSON(), nullable=True),
        sa.Column("suggestions", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_financial_health_scores_user_id"), "financial_health_scores", ["user_id"]
    )
    op.create_index(
        op.f("ix_financial_health_scores_scored_at"), "financial_health_scores", ["scored_at"]
    )
    op.create_index(
        op.f("ix_financial_health_scores_deleted_at"), "financial_health_scores", ["deleted_at"]
    )

    # ── simulation_results ─────────────────────────────────────────
    op.create_table(
        "simulation_results",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("goal_id", sa.UUID(), nullable=True),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("simulation_type", sa.String(length=32), nullable=False),
        sa.Column("simulations", sa.Float(), nullable=False),
        sa.Column("horizon_years", sa.Float(), nullable=False),
        sa.Column("expected_return", sa.Float(), nullable=False),
        sa.Column("volatility", sa.Float(), nullable=False),
        sa.Column("inflation", sa.Float(), nullable=False),
        sa.Column("monthly_investment", sa.Float(), nullable=False),
        sa.Column("initial_corpus", sa.Float(), nullable=False),
        sa.Column("target_amount", sa.Float(), nullable=True),
        sa.Column("median", sa.Float(), nullable=True),
        sa.Column("percentile_5", sa.Float(), nullable=True),
        sa.Column("percentile_25", sa.Float(), nullable=True),
        sa.Column("percentile_75", sa.Float(), nullable=True),
        sa.Column("percentile_95", sa.Float(), nullable=True),
        sa.Column("worst_case", sa.Float(), nullable=True),
        sa.Column("best_case", sa.Float(), nullable=True),
        sa.Column("mean", sa.Float(), nullable=True),
        sa.Column("std_dev", sa.Float(), nullable=True),
        sa.Column("probability_of_success", sa.Float(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("statistics", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["goal_id"], ["goals.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_simulation_results_user_id"), "simulation_results", ["user_id"])
    op.create_index(op.f("ix_simulation_results_goal_id"), "simulation_results", ["goal_id"])
    op.create_index(op.f("ix_simulation_results_run_at"), "simulation_results", ["run_at"])
    op.create_index(
        op.f("ix_simulation_results_simulation_type"), "simulation_results", ["simulation_type"]
    )
    op.create_index(op.f("ix_simulation_results_deleted_at"), "simulation_results", ["deleted_at"])

    # ── scenario_analyses ──────────────────────────────────────────
    op.create_table(
        "scenario_analyses",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scenario_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=512), nullable=True),
        sa.Column("adjustments", sa.JSON(), nullable=True),
        sa.Column("goal_probabilities", sa.JSON(), nullable=True),
        sa.Column("total_required_sip", sa.Float(), nullable=True),
        sa.Column("net_worth", sa.Float(), nullable=True),
        sa.Column("allocation", sa.JSON(), nullable=True),
        sa.Column("summary", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scenario_analyses_user_id"), "scenario_analyses", ["user_id"])
    op.create_index(op.f("ix_scenario_analyses_run_at"), "scenario_analyses", ["run_at"])
    op.create_index(
        op.f("ix_scenario_analyses_scenario_type"), "scenario_analyses", ["scenario_type"]
    )
    op.create_index(op.f("ix_scenario_analyses_deleted_at"), "scenario_analyses", ["deleted_at"])

    # ── system_settings ────────────────────────────────────────────
    op.create_table(
        "system_settings",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_system_settings_key"), "system_settings", ["key"], unique=True)

    # ── market_data_cache ──────────────────────────────────────────
    op.create_table(
        "market_data_cache",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("symbol", sa.String(length=64), nullable=False),
        sa.Column("asset_class", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_market_data_cache_symbol"), "market_data_cache", ["symbol"])
    op.create_index(op.f("ix_market_data_cache_deleted_at"), "market_data_cache", ["deleted_at"])

    # ── chat_sessions ──────────────────────────────────────────────
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("context", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("messages", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_sessions_user_id"), "chat_sessions", ["user_id"])
    op.create_index(op.f("ix_chat_sessions_status"), "chat_sessions", ["status"])
    op.create_index(op.f("ix_chat_sessions_deleted_at"), "chat_sessions", ["deleted_at"])

    # ── audit_logs ─────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("request_id", sa.String(length=36), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_user_id"), "audit_logs", ["user_id"])
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"])
    op.create_index(op.f("ix_audit_logs_resource_id"), "audit_logs", ["resource_id"])
    op.create_index(op.f("ix_audit_logs_status"), "audit_logs", ["status"])


def downgrade() -> None:
    """Drop every table in reverse dependency order."""
    op.drop_table("audit_logs")
    op.drop_table("chat_sessions")
    op.drop_table("market_data_cache")
    op.drop_table("system_settings")
    op.drop_table("scenario_analyses")
    op.drop_table("simulation_results")
    op.drop_table("financial_health_scores")
    op.drop_table("recommendations")
    op.drop_table("portfolio_snapshots")
    op.drop_table("portfolio_holdings")
    op.drop_table("portfolios")
    op.drop_table("goal_progress")
    op.drop_table("goals")
    op.drop_table("behavioral_profiles")
    op.drop_table("financial_profiles")
    op.drop_table("user_profiles")
    op.drop_table("email_verification_tokens")
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
