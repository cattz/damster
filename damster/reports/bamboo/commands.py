"""Bamboo reports commands"""
from damster.reports.bamboo import BambooDeploymentsReport, BambooBuildsReport, BambooDBDeploymentPermissions
from damster.utils import previous_month_range
import click
import logging


log = logging.getLogger(__name__)


@click.command('deployments', short_help='generate deployments report')
@click.argument('from-date', required=False)
@click.argument('to-date', required=False)
@click.option('--use-cache/--no-use-cache', default=False)
@click.pass_context
def bamboo_deployments(ctx, from_date, to_date, use_cache):
    """Generate a deployments report"""

    if from_date is None:
        from_date, to_date = previous_month_range()

    log.info('Getting Bamboo deployments between {} and {}'.format(from_date, to_date))
    report = BambooDeploymentsReport(
        ctx.obj,
        from_date=from_date,
        to_date=to_date
    )
    report.run_report(use_cache=use_cache)


@click.command('builds', short_help='generate build report')
@click.argument('from-date', required=False)
@click.argument('to-date', required=False)
@click.option('--use-cache/--no-use-cache', default=False)
@click.pass_context
def bamboo_builds(ctx, from_date, to_date, use_cache):
    """Generate a builds report"""

    if from_date is None:
        from_date, to_date = previous_month_range()

    log.info('Getting Bamboo builds between {} and {}'.format(from_date, to_date))
    report = BambooBuildsReport(
        ctx.obj,
        from_date=from_date,
        to_date=to_date
    )
    report.run_report(use_cache=use_cache)


@click.command('deployment-permissions', short_help='generate deployment permissions report')
@click.option('--use-ssh-tunnel/--no-use-ssh-tunnel', '-S', default=False)
@click.pass_context
def bamboo_deployment_permissions(ctx, use_ssh_tunnel):
    """Deployment projects and environments permissions"""

    bamboo_report = BambooDBDeploymentPermissions(ctx.obj, use_ssh_tunnel=use_ssh_tunnel)
    bamboo_report.save_to_csv()
    bamboo_report.save_to_json()
    bamboo_report.save_to_html(title='Bamboo Reports: Deployment Permissions')
