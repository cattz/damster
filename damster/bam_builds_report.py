#!/bin/env python
from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooBuildsReport

log = initialize_logger(__name__)


cfg = get_config()

YEAR = '2017'


def monthly():

    for month in range(1, 11):
        report = BambooBuildsReport(
            cfg,
            from_date='{}-{:02}-01'.format(YEAR, month),
            to_date='{}-{:02}-01'.format(YEAR, month+1)
        )
        report.run_report(use_cache=True)


def main():

    report = BambooBuildsReport(
        cfg,
        from_date='2018-02-01',
        # to_date='2018-03-01'
    )
    report.run_report(use_cache=False)


if __name__ == "__main__":
    main()
