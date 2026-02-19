from joss.joss.extract import JOSSExtract
from joss.joss.transform import JOSSTransform
from joss.logger import JOSSLogger


class JOSSRunner:
    def __init__(self, joss_logger: JOSSLogger) -> None:
        self.extract: JOSSExtract = JOSSExtract(joss_logger=joss_logger)
        self.transform: JOSSTransform = JOSSTransform(joss_logger=joss_logger)

    def run(self) -> None:
        data: list[dict] = self.extract.download_data()
        normalized_data: dict[str, list] = self.transform.transform_data(
            data=data,
        )
