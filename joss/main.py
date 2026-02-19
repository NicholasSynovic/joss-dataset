"""Entry point for the unified ``joss`` command-line application."""

# Copyright (c) 2025 Nicholas M. Synovic

import sys

from joss import APPLICATION_NAME
from joss.cli import CLI
from joss.db import DB
from joss.joss.runner import JOSSRunner
from joss.logger import JOSSLogger


def main() -> int:
    """
    Entry point for the JOSS CLI application.

    Raises:
        RuntimeError: If input file does not exist or has invalid format.

    """
    args = CLI().run()

    if args.dataset is None:
        sys.exit(1)

    logger: JOSSLogger = JOSSLogger(name=__name__)
    logger.setup_file_logging(prefix=APPLICATION_NAME)

    if args.dataset == "joss":
        db: DB = DB(joss_logger=logger, db_path=args.out_file)
        JOSSRunner(joss_logger=logger, db=db).run()

    else:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
