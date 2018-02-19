#!/bin/env python
from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooBuildsReport

log = initialize_logger(__name__)


cfg = get_config()

YEAR = '2017'


def main():

    for month in range(1, 11):
        report = BambooBuildsReport(
            cfg,
            from_date='{}-{:02}-01'.format(YEAR, month),
            to_date='{}-{:02}-01'.format(YEAR, month+1)
        )
        report.run_report(use_cache=True)


if __name__ == "__main__":
    main()
