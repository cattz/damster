#!/bin/env python
from damster.utils import initialize_logger, get_config
from damster.metrics.bamboo import BambooBuildAgentsMetrics
from atlassian import Bamboo
from influxdb import InfluxDBClient

import schedule
import time

log = initialize_logger(__name__)


cfg = get_config()


def main():
    log.setLevel(int(cfg['Common']['loglevel']))

    bamboo = Bamboo(**cfg['Bamboo'])
    influxdb = InfluxDBClient(**cfg['InfluxDB'])

    bamboo_metrics = BambooBuildAgentsMetrics(bamboo, influxdb)

    log.debug('Scheduling jobs...')
    schedule.every(1).minutes.do(
        bamboo_metrics.agent_status, metric_name='wst_swf_bamboo_agent_status')
    schedule.every(1).minutes.do(
        bamboo_metrics.activity, metric_name='wst_swf_bamboo_activity')

    while True:
        schedule.run_pending()
        time.sleep(1)


def deployment_report():
    bamboo = Bamboo(**cfg['Bamboo'])
    report = BambooDeploymentsReport(bamboo, '2018-01-18 00:00:00')
    report.run_report()


if __name__ == "__main__":
    main()
