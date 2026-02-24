"""Loading stage for writing transformed JOSS data into SQLite tables."""

# Copyright (c) 2025 Nicholas M. Synovic

from logging import Logger

from pandas import DataFrame
from progress.bar import Bar

from joss.db import DB
from joss.interfaces import LoadInterface
from joss.logger import JOSSLogger


class JOSSLoad(LoadInterface):
    """Persist transformed table rows into the configured SQLite database."""

    def __init__(self, joss_logger: JOSSLogger, db: DB) -> None:
        """
        Initialize loader dependencies.

        Args:
            joss_logger: Logger wrapper for write progress messages.
            db: Database wrapper with engine and metadata.

        """
        self.db: DB = db
        self.logger: Logger = joss_logger.get_logger()

    def load_data(self, data: dict[str, list]) -> bool:
        """
        Write transformed rows to each destination table.

        Args:
            data: Mapping from table name to list of row dictionaries.

        Returns:
            ``True`` when all tables are written successfully.

        """
        table_names: list[str] = list(data.keys())

        self.logger.info("Writing data to `%s`", self.db._path)
        with Bar(
            f"Writing data to `{self.db._path}`... ",
            max=len(table_names),
        ) as bar:
            table: str
            for table in table_names:
                content: DataFrame = DataFrame(data=data[table])
                content.to_sql(
                    name=table,
                    con=self.db.engine,
                    if_exists="delete_rows",
                    index=False,
                    index_label="_id",
                )
                self.logger.info("Wrote data to `%s`", table)
                bar.next()

        return True
