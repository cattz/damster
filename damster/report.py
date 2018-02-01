#!/bin/env python
from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooDeploymentsReport

log = initialize_logger(__name__)


cfg = get_config()


def main():

    report = BambooDeploymentsReport(
        cfg,
        from_date='2018-01-18 00:00:00',
        to_date='2018-02-01 14:06:31'
    )
    report.run_report()


if __name__ == "__main__":
    main()
