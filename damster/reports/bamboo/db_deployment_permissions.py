from damster.utils import initialize_logger
from damster.reports.db_query import GenericDB

import psycopg2
import os
from distutils.dir_util import mkpath

log = initialize_logger(__name__)


class BambooDBDeploymentPermissions(GenericDB):

    query_project = """
              SELECT
                Name as deployment_project,
                AE.sid  as entity_name,
                (CASE
                  WHEN AE.type = 'PRINCIPAL'
                    THEN 'USER'
                  WHEN AE.type = 'GROUP_PRINCIPAL'
                    THEN 'GROUP'
                  ELSE
                     'ROLE'
                END) as entity_type,
                sum(mask) as mask
              FROM ACL_ENTRY AS AE
                JOIN ACL_OBJECT_IDENTITY AS AOI
                  ON AE.acl_object_identity = AOI.id
                JOIN DEPLOYMENT_PROJECT ON deployment_project_id = object_id_identity
              GROUP BY
                deployment_project, entity_name, entity_type
              ORDER BY
                deployment_project
    """
    query_environment = """
            SELECT 
                DP.name as deployment_project, 
                DE.name as deployment_environment,
                AE.sid as entity_name,         
                (CASE
                    WHEN AE.type = 'PRINCIPAL'
                       THEN 'USER'
                    WHEN AE.type = 'GROUP_PRINCIPAL'
                       THEN 'GROUP'
                    ELSE
                       'ROLE'
                END) as entity_type,
                sum(mask) as mask
            FROM ACL_ENTRY AS AE
            JOIN ACL_OBJECT_IDENTITY AS AOI
                ON AE.acl_object_identity = AOI.id
            JOIN DEPLOYMENT_ENVIRONMENT DE 
                ON DE.environment_id = object_id_identity
            JOIN DEPLOYMENT_PROJECT DP 
                ON DE.package_definition_id = DP. deployment_project_id
            GROUP BY 
                deployment_project, deployment_environment, entity_type, entity_name
            ORDER BY
                deployment_project
            """
    name = 'deployment_permissions'

    def __init__(self, cfg, db_settings_section='Bamboo DB',
                 name='deployment_permissions',
                 use_ssh_tunnel=False):
        super(BambooDBDeploymentPermissions, self).__init__(cfg, db_settings_section, name,
                                                            use_ssh_tunnel=use_ssh_tunnel)

    def _mask_to_dict(self, mask):
        permissions = [
            ('view', 1),
            ('edit', 2),
            ('admin', 16),
            ('deploy', 64),
            # No clone for deployments('clone', 128)
        ]
        perms = dict()
        for perm, int_mask in permissions:
            perms[perm] = int_mask & int(mask) > 0
        return perms

    def generate_report(self):
        report = dict()

        # First get the project permissions
        dep_projects_perms = self.exec_query(query=self.query_project)
        for deployment_project, entity_name,  entity_type, mask in dep_projects_perms:
            if deployment_project not in report:
                report[deployment_project] = dict(
                    permissions=list(),
                    environments=dict()
                )
            permission = self._mask_to_dict(mask)
            permission['entity_name'] = entity_name
            permission['entity_type'] = entity_type
            report[deployment_project]['permissions'].append(permission)

        # Second, get the environment permissions
        dep_environments_perms = self.exec_query(self.query_environment)
        for deployment_project, deployment_environment, entity_name, entity_type, mask in dep_environments_perms:
            if deployment_project not in report:
                report[deployment_project] = dict(
                    prj_permissions=list(),
                    environments=dict()
                )
            if deployment_environment not in report[deployment_project]['environments']:
                report[deployment_project]['environments'][deployment_environment] = list()
            permission = self._mask_to_dict(mask)
            permission['entity_name'] = entity_name
            permission['entity_type'] = entity_type
            report[deployment_project]['environments'][deployment_environment].append(permission)

        return report

    def save_to_csv(self, output_file=None):
        out_csv = output_file or self.output_file(ext='csv')
        log.info('Saving to CSV file {}'.format(out_csv))
        lines = ['deployment_project,environment_name,entity_name,entity_type,view,edit,deploy,admin']
        for deployment_project in self.report:
            line = '{},_PROJECT_,'.format(deployment_project)
            for project_permission in self.report[deployment_project]['permissions']:
                lines.append(
                    line + '{entity_name},{entity_type},{view},{edit},{deploy},{admin}'.format(**project_permission))
            for environment in self.report[deployment_project]['environments']:
                line = '{},{},'.format(deployment_project, environment)
                for env_permission in self.report[deployment_project]['environments'][environment]:
                    lines.append(
                        line + '{entity_name},{entity_type},{view},{edit},{deploy},{admin}'.format(**env_permission))

        mkpath(self.output_folder)
        with open(out_csv, 'w') as outfile:
            outfile.write('\n'.join(lines))
