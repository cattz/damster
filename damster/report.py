#!/bin/env python
from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooDeploymentsReport
from atlassian import Bamboo


log = initialize_logger(__name__)


cfg = get_config()


def main():
    bamboo = Bamboo(**cfg['Bamboo'])
    report = BambooDeploymentsReport(bamboo, '2018-01-18 00:00:00')
    report.run_report()


if __name__ == "__main__":
    main()
