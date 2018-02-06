from damster.utils import initialize_logger
from damster.reports.db_query import GenericDB

import psycopg2
import os
from distutils.dir_util import mkpath

log = initialize_logger(__name__)


class BambooDBDeploymentPermissions(GenericDB):

    query = """
              SELECT
                Name as deployment_project,
                AE.sid,
                (CASE
                  WHEN AE.type = 'PRINCIPAL'
                    THEN 'USER'
                  WHEN AE.type = 'GROUP_PRINCIPAL'
                    THEN 'GROUP'
                  ELSE
                     'ROLE'
                END) as user_or_group,
                sum(mask) as mask
              FROM ACL_ENTRY AS AE
                JOIN ACL_OBJECT_IDENTITY AS AOI
                  ON AE.acl_object_identity = AOI.id
                JOIN DEPLOYMENT_PROJECT ON deployment_project_id = object_id_identity
              GROUP BY
                deployment_project, AE.sid, user_or_group
              ORDER BY
                deployment_project
    """
    table_columns = (
        'deployment_project', 'user_or_group', 'permission_type', 'mask'
    )

    permissions = [
        ('view', 1),
        ('edit', 2),
        ('admin', 16),
        ('deploy', 64),
        # No clone for deployments('clone', 128)
    ]

    def __init__(self, cfg, db_settings_section='Bamboo DB',
                 name='deployment_permissions',
                 use_ssh_tunnel=False):
        super(BambooDBDeploymentPermissions, self).__init__(cfg, db_settings_section, name,
                                                            use_ssh_tunnel=use_ssh_tunnel)

    def generate_report(self):
        super(BambooDBDeploymentPermissions, self).generate_report()

        for row in self.report:
            for perm, mask in self.permissions:
                row[perm] = mask & int(row['mask']) > 0

    def save_to_csv(self, output_file=None):
        out_csv = self.output_file(ext='csv')
        log.info('Saving to CSV file {}'.format(out_csv))
        lines = [','.join(self.report[0].keys())]
        for row in self.report:
            lines.append(','.join([str(v) for v in row.values()]))

        mkpath(self.output_folder)
        with open(out_csv, 'w') as outfile:
            outfile.write('\n'.join(lines))
