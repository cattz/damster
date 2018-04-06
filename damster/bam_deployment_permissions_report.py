#!/bin/env python
from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooDBDeploymentPermissions

log = initialize_logger(__name__)


cfg = get_config()


def main():

    bamboo_report = BambooDBDeploymentPermissions(cfg, use_ssh_tunnel=False)
    bamboo_report.save_to_csv()
    bamboo_report.save_to_json()
    bamboo_report.save_to_html(title='Bamboo Reports: Deployment Permissions')


if __name__ == "__main__":
    main()
