from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooDeploymentsReport, BambooBuildsReport, BambooDBDeploymentPermissions
import click

log = initialize_logger(__name__)

cfg = get_config()


@click.group()
@click.version_option()
def cli():
    """Damster-Reports.
    """


@cli.group()
def bamboo():
    """Bamboo reports."""


@bamboo.command('deployments')
@click.argument('from-date')
@click.argument('to-date', required=False)
@click.option('--use-cache/--no-use-cache', default=False)
def bamboo_deployments(from_date, to_date, use_cache):
    """Generate a deployments report"""

    click.echo('Getting Bamboo deployments between {} and {}'.format(from_date, to_date))
    report = BambooDeploymentsReport(
        cfg,
        from_date=from_date,
        to_date=to_date
    )
    report.run_report(use_cache=use_cache)


@bamboo.command('builds')
@click.argument('from-date')
@click.argument('to-date', required=False)
@click.option('--use-cache/--no-use-cache', default=False)
def bamboo_builds(from_date, to_date, use_cache):
    """Generate a builds report"""

    click.echo('Getting Bamboo builds between {} and {}'.format(from_date, to_date))
    report = BambooBuildsReport(
        cfg,
        from_date=from_date,
        to_date=to_date
    )
    report.run_report(use_cache=use_cache)


@bamboo.command('deployment-permissions')
@click.option('--use-ssh-tunnel/--no-use-ssh-tunnel', default=False)
def bamboo_deployment_permissions(use_ssh_tunnel):
    """Deployment projects and environments permissions"""

    bamboo_report = BambooDBDeploymentPermissions(cfg, use_ssh_tunnel=use_ssh_tunnel)
    bamboo_report.save_to_csv()
    bamboo_report.save_to_json()
    bamboo_report.save_to_html(title='Bamboo Reports: Deployment Permissions')