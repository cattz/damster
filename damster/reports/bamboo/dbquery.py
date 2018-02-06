from damster.utils import initialize_logger
from damster.reports.dbquery import GenericDB

import psycopg2
import os
from distutils.dir_util import mkpath

log = initialize_logger(__name__)


class BambooDB(GenericDB):

    def __init__(self, cfg, db_settings_section='Bamboo DB',
                 name='bamboo_dbquery_report',
                 use_ssh_tunnel=False):
        super(BambooDB, self).__init__(cfg, db_settings_section, name, use_ssh_tunnel=use_ssh_tunnel)

