#!/bin/env python
from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooBuildsReport

log = initialize_logger(__name__)


cfg = get_config()


def main():

    report = BambooBuildsReport(
        cfg,
        from_date='2018-01-01',
        to_date='2018-02-28'
    )
    report.run_report(use_cache=False)


if __name__ == "__main__":
    main()
