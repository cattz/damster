"""Confluence reports commands"""
import click
from damster.reports.confluence import ConfluenceChanges
from damster.utils import previous_month_range
import logging


log = logging.getLogger(__name__)


@click.command('changes', short_help='generate changes report')
@click.argument('from-date', required=False)
@click.argument('to-date', required=False)
@click.option('--use-ssh-tunnel/--no-use-ssh-tunnel', '-S', default=False)
@click.pass_context
def confluence_changes(ctx, from_date, to_date, use_ssh_tunnel):
    """Confluence content changes"""

    if from_date is None:
        from_date, to_date = previous_month_range()

    log.info('Getting Confluence changes between {} and {}'.format(from_date, to_date))
    confluence_report = ConfluenceChanges(ctx.obj, from_date, to_date, use_ssh_tunnel=use_ssh_tunnel)
    confluence_report.save_to_csv()
    confluence_report.save_to_json()

    # For some reason, this class destructor doesn't always run, so adding this here to make sure
    # The scripts actually ends
    if confluence_report.ssh_tunnel:
        confluence_report.ssh_tunnel.close()
