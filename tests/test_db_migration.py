"""Tests for DB schema migration behavior."""

# Copyright (c) 2025 Nicholas M. Synovic

import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import text

from joss.db import DB
from joss.logger import JOSSLogger


def test_db_adds_mapping_columns_for_existing_table(tmp_path: Path) -> None:
    """Ensure additive migration adds new mapping columns to legacy table."""
    db_path = tmp_path / "legacy.db"

    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE _joss_github_issues (
                id INTEGER PRIMARY KEY,
                is_pull_request BOOLEAN,
                body TEXT,
                creator TEXT,
                state TEXT,
                labels TEXT,
                json_str TEXT
            );
            CREATE TABLE _joss_paper_project_issues (
                id INTEGER PRIMARY KEY,
                joss_github_issue_id INTEGER,
                github_repo_url TEXT,
                joss_url TEXT,
                joss_resolved_url TEXT,
                journal TEXT,
                FOREIGN KEY(joss_github_issue_id) REFERENCES _joss_github_issues(id)
            );
            """
        )
        connection.commit()

    db = DB(
        joss_logger=JOSSLogger(name="test-db-migration"),
        db_path=db_path,
    )

    with db.engine.begin() as conn:
        rows = conn.execute(text("PRAGMA table_info(_joss_paper_project_issues)"))
        column_names = {row[1] for row in rows}

    if "is_accepted" not in column_names:
        pytest.fail("is_accepted column missing after migration")
    if "repo_host" not in column_names:
        pytest.fail("repo_host column missing after migration")
