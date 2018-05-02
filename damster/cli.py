from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooDeploymentsReport, BambooBuildsReport, BambooDBDeploymentPermissions
from damster.reports.confluence import ConfluenceChanges
import click

log = initialize_logger(__name__)


@click.group()
@click.version_option()
# @click.option('--debug/--no-debug', default=False)
@click.option('--config', '-c', required=False, help='configuration file to use')
@click.pass_context
def cli(ctx, config):
    """Damster: Reports from Atlassian tools.
    """
    ctx.obj = get_config(config)


@cli.group()
def bamboo():
    """Bamboo reports."""
    pass


@bamboo.command('deployments', short_help='generate deployments report')
@click.argument('from-date')
@click.argument('to-date', required=False)
@click.option('--use-cache/--no-use-cache', default=False)
@click.pass_context
def bamboo_deployments(ctx, from_date, to_date, use_cache):
    """Generate a deployments report"""

    click.echo('Getting Bamboo deployments between {} and {}'.format(from_date, to_date))
    report = BambooDeploymentsReport(
        ctx.obj,
        from_date=from_date,
        to_date=to_date
    )
    report.run_report(use_cache=use_cache)


@bamboo.command('builds', short_help='generate build report')
@click.argument('from-date')
@click.argument('to-date', required=False)
@click.option('--use-cache/--no-use-cache', default=False)
@click.pass_context
def bamboo_builds(ctx, from_date, to_date, use_cache):
    """Generate a builds report"""

    click.echo('Getting Bamboo builds between {} and {}'.format(from_date, to_date))
    report = BambooBuildsReport(
        ctx.obj,
        from_date=from_date,
        to_date=to_date
    )
    report.run_report(use_cache=use_cache)


@bamboo.command('deployment-permissions', short_help='generate deployment permissions report')
@click.option('--use-ssh-tunnel/--no-use-ssh-tunnel', '-S', default=False)
@click.pass_context
def bamboo_deployment_permissions(ctx, use_ssh_tunnel):
    """Deployment projects and environments permissions"""

    bamboo_report = BambooDBDeploymentPermissions(ctx.obj, use_ssh_tunnel=use_ssh_tunnel)
    bamboo_report.save_to_csv()
    bamboo_report.save_to_json()
    bamboo_report.save_to_html(title='Bamboo Reports: Deployment Permissions')


@cli.group()
def confluence():
    """Confluence reports."""
    pass


@confluence.command('changes', short_help='generate changes report')
@click.argument('from-date', required=False)
@click.argument('to-date', required=False)
@click.option('--use-ssh-tunnel/--no-use-ssh-tunnel', '-S', default=False)
@click.pass_context
def confluence_changes(ctx, from_date, to_date, use_ssh_tunnel):
    """Confluence content changes"""

    confluence_report = ConfluenceChanges(ctx.obj, from_date, to_date, use_ssh_tunnel=use_ssh_tunnel)
    confluence_report.save_to_csv()
    confluence_report.save_to_json()
    # confluence_report.save_to_html(title='Confluence Reports: Changes')
