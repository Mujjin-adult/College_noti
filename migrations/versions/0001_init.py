"""
Alembic migration: initial schema for crawler system
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "crawl_job",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("priority", sa.String(4), nullable=False),
        sa.Column("schedule_cron", sa.String(64)),
        sa.Column(
            "seed_type",
            sa.Enum("URL_LIST", "SITEMAP", "DOMAIN", "SEARCH", name="seedtype"),
            nullable=False,
        ),
        sa.Column("seed_payload", sa.JSON, nullable=False),
        sa.Column(
            "render_mode",
            sa.Enum("STATIC", "HEADLESS", "AUTO", name="rendermode"),
            nullable=False,
        ),
        sa.Column("rate_limit_per_host", sa.Float),
        sa.Column("max_depth", sa.Integer),
        sa.Column(
            "robots_policy",
            sa.Enum("OBEY", "IGNORE_WHITELIST", name="robotspolicy"),
            nullable=False,
        ),
        sa.Column("status", sa.String(16)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    op.create_table(
        "crawl_task",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("crawl_job.id")),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("status", sa.String(16)),
        sa.Column("retries", sa.Integer, default=0),
        sa.Column("last_error", sa.Text),
        sa.Column("started_at", sa.DateTime),
        sa.Column("finished_at", sa.DateTime),
        sa.Column("http_status", sa.Integer),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("blocked_flag", sa.Boolean, default=False),
        sa.Column("cost_ms_browser", sa.Integer),
        sa.Column("attempt_strategy", sa.JSON),
    )

    op.create_table(
        "extracted_doc",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("crawl_job.id")),
        sa.Column("url", sa.Text, nullable=False),
        sa.Column("extracted", sa.JSON),
        sa.Column("raw", sa.Text),
        sa.Column("snapshot_version", sa.String(32)),
        sa.Column("fingerprint", sa.String(64)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "host_budget",
        sa.Column("host", sa.String(128), primary_key=True),
        sa.Column("qps_limit", sa.Float),
        sa.Column("concurrency_limit", sa.Integer),
        sa.Column("daily_budget_sec_browser", sa.Integer),
        sa.Column("used_today_sec", sa.Integer),
    )

    op.create_table(
        "webhook",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("crawl_job.id")),
        sa.Column("target_url", sa.Text, nullable=False),
        sa.Column(
            "event",
            sa.Enum("JOB_DONE", "DOC_READY", "ERROR", name="webhookevent"),
            nullable=False,
        ),
        sa.Column("secret", sa.String(128)),
    )


def downgrade():
    op.drop_table("webhook")
    op.drop_table("host_budget")
    op.drop_table("extracted_doc")
    op.drop_table("crawl_task")
    op.drop_table("crawl_job")
