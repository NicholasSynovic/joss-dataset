"""Orchestrator for JOSS extract-transform-load execution."""

# Copyright (c) 2025 Nicholas M. Synovic

from joss.db import DB
from joss.joss.extract import JOSSExtract
from joss.joss.load import JOSSLoad
from joss.joss.transform import JOSSTransform
from joss.logger import JOSSLogger


class JOSSRunner:
    """Run the full ETL flow for the JOSS dataset pipeline."""

    def __init__(self, joss_logger: JOSSLogger, db: DB) -> None:
        """
        Initialize ETL stage components.

        Args:
            joss_logger: Logger wrapper used by all pipeline stages.
            db: Database object used by the load stage.

        """
        self.extract: JOSSExtract = JOSSExtract(joss_logger=joss_logger)
        self.transform: JOSSTransform = JOSSTransform(joss_logger=joss_logger)
        self.load: JOSSLoad = JOSSLoad(joss_logger=joss_logger, db=db)

    def run(self) -> None:
        """Execute extraction, transformation, and loading in order."""
        data: list[dict] = self.extract.download_data()
        normalized_data: dict[str, list] = self.transform.transform_data(
            data=data,
        )
        self.load.load_data(data=normalized_data)
