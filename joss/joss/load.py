from logging import Logger

from pandas import DataFrame
from progress.bar import Bar

from joss.db import DB
from joss.interfaces import LoadInterface
from joss.logger import JOSSLogger


class JOSSLoad(LoadInterface):
    def __init__(self, joss_logger: JOSSLogger, db: DB) -> None:
        self.db: DB = db
        self.logger: Logger = joss_logger.get_logger()

    def load_data(self, data: dict[str, list]) -> bool:
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
