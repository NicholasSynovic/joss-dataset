from joss.joss.extract import JOSSExtract
from joss.logger import JOSSLogger


class JOSSRunner:
    def __init__(self, joss_logger: JOSSLogger) -> None:
        self.extract: JOSSExtract = JOSSExtract(joss_logger=joss_logger)

    def run(self) -> None:
        data: list[dict] = self.extract.download_data()
