"""Metrics commands"""
from damster.metrics.bamboo import BambooBuildAgentsMetrics
from atlassian import Bamboo
from influxdb import InfluxDBClient
import click


@click.command('agent-status')
@click.argument('metric-prefix')
@click.pass_context
def agent_status(ctx, metric_prefix):
    cfg = ctx.obj
    bamboo = Bamboo(**cfg['Bamboo'])
    influxdb = InfluxDBClient(**cfg['InfluxDB'])

    bamboo_metrics = BambooBuildAgentsMetrics(bamboo, influxdb)
    bamboo_metrics.agent_status(metric_name='_'.join([metric_prefix, 'bamboo_agent_status']))


@click.command('activity')
@click.argument('metric-prefix')
@click.pass_context
def build_activity(ctx, metric_prefix):
    cfg = ctx.obj
    bamboo = Bamboo(**cfg['Bamboo'])
    influxdb = InfluxDBClient(**cfg['InfluxDB'])

    bamboo_metrics = BambooBuildAgentsMetrics(bamboo, influxdb)
    bamboo_metrics.activity(metric_name='_'.join([metric_prefix, 'bamboo_activity']))
