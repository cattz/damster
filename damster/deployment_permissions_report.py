#!/bin/env python
from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooDBDeploymentPermissions

log = initialize_logger(__name__)


cfg = get_config()


def main():

    bamboodb = BambooDBDeploymentPermissions(cfg, use_ssh_tunnel=False)
    bamboodb.generate_report()
    bamboodb.save_to_csv()


if __name__ == "__main__":
    main()
