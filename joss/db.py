"""Database schema and migration helpers for the JOSS SQLite store."""

# Copyright (c) 2025 Nicholas M. Synovic

from logging import Logger
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    Engine,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    text,
)

from joss.logger import JOSSLogger


class DB:
    """Manage database engine creation, schema creation, and safe migrations."""

    def __init__(self, joss_logger: JOSSLogger, db_path: Path) -> None:
        """
        Initialize database engine, metadata, and schema.

        Args:
            joss_logger: Logger wrapper used for schema migration messages.
            db_path: Path to the SQLite database file.

        """
        self._path: Path = db_path.absolute()

        self.engine: Engine = create_engine(url=f"sqlite:///{self._path}")
        self.logger: Logger = joss_logger.get_logger()
        self.metadata: MetaData = MetaData()

        self._create_tables()

    def _create_tables(self) -> None:
        """Create all known tables if they do not already exist."""
        _: Table = Table(
            "_joss_github_issues",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("is_pull_request", Boolean),
            Column("body", String),
            Column("creator", String),
            Column("state", String),
            Column("labels", String),
            Column("json_str", String),
        )

        _: Table = Table(
            "_joss_paper_project_issues",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column(
                "joss_github_issue_id",
                Integer,
                ForeignKey("_joss_github_issues.id"),
            ),
            Column("github_repo_url", String),
            Column("repo_host", String),
            Column("joss_url", String),
            Column("joss_resolved_url", String),
            Column("is_accepted", Boolean),
            Column("journal", String),
        )

        self.metadata.create_all(bind=self.engine, checkfirst=True)
        self._migrate_tables()

    def _migrate_tables(self) -> None:
        """Apply safe, additive migrations for existing SQLite tables."""
        self._ensure_column_exists(
            table_name="_joss_paper_project_issues",
            column_name="is_accepted",
            sql_type="BOOLEAN",
        )
        self._ensure_column_exists(
            table_name="_joss_paper_project_issues",
            column_name="repo_host",
            sql_type="TEXT",
        )

    def _ensure_column_exists(
        self, table_name: str, column_name: str, sql_type: str
    ) -> None:
        """
        Add a missing column using ALTER TABLE when the table already exists.

        Args:
            table_name: Name of table to inspect.
            column_name: Column to add if not present.
            sql_type: SQLite column type declaration.

        """
        with self.engine.begin() as conn:
            rows = conn.execute(text(f"PRAGMA table_info({table_name})"))
            existing_columns = {row[1] for row in rows}
            if column_name in existing_columns:
                return

            conn.execute(
                text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {sql_type}")
            )
            self.logger.info(
                "Added missing column `%s` to `%s`",
                column_name,
                table_name,
            )
