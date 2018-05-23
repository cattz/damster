from damster.utils import initialize_logger, get_config
from damster.reports.bamboo.commands import bamboo_builds, bamboo_deployment_permissions, bamboo_deployments
from damster.reports.confluence.commands import confluence_changes
from damster.metrics.bamboo.commands import agent_status, build_activity

from atlassian import Confluence

import click

log = initialize_logger(__name__)


@click.group()
@click.version_option()
@click.option('--config', '-c', required=False, help='configuration file to use')
@click.pass_context
def damster(ctx, config):
    """Damster: Reports and metrics from Atlassian tools.
    """
    ctx.obj = get_config(config)


@damster.group()
def reports():
    """Generate reports."""
    pass


@reports.group('bamboo')
def reports_bamboo():
    """Bamboo reports."""
    pass


@reports.group('confluence')
def reports_confluence():
    """Confluence reports."""
    pass


@damster.group()
def metrics():
    """Collect metrics and store them in InfluxDB."""
    pass


@metrics.group('bamboo')
def metrics_bamboo():
    """Collect Bamboo metrics."""
    pass


@damster.command('publish-to-confluence')
@click.argument('filename', required=True)
@click.argument('page_id', required=True)
@click.pass_context
def publish_to_confluence(ctx, filename, page_id):
    """Publish file to Confluence"""
    cfg = ctx.obj
    confluence = Confluence(**cfg['Confluence'])
    confluence.attach_file(filename=filename, page_id=page_id)


reports_bamboo.add_command(bamboo_builds)
reports_bamboo.add_command(bamboo_deployments)
reports_bamboo.add_command(bamboo_deployment_permissions)

reports_confluence.add_command(confluence_changes)

metrics_bamboo.add_command(agent_status)
metrics_bamboo.add_command(build_activity)
