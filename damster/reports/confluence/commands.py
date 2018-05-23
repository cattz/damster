"""Confluence reports commands"""
import click
from damster.reports.confluence import ConfluenceChanges


@click.command('changes', short_help='generate changes report')
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
