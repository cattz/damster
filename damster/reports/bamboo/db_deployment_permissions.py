from damster.utils import initialize_logger
from damster.reports.db_query import GenericDB
from atlassian import Crowd


from distutils.dir_util import mkpath

log = initialize_logger(__name__)


class BambooDBDeploymentPermissions(GenericDB):

    query_project = """
              SELECT
                DP.name as deployment_project,
                DP.deployment_project_id as deployment_project_id,
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
                JOIN DEPLOYMENT_PROJECT DP ON deployment_project_id = object_id_identity
              GROUP BY
                deployment_project, deployment_project_id, entity_name, entity_type
              ORDER BY
                deployment_project
    """
    query_environment = """
            SELECT
                DP.name as deployment_project,
                DP.deployment_project_id as deployment_project_id,
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
                deployment_project, deployment_project_id, deployment_environment, entity_type, entity_name
            ORDER BY
                deployment_project
            """
    name = 'deployment_permissions'

    def __init__(self, cfg, db_settings_section='Bamboo DB',
                 name='deployment_permissions',
                 use_ssh_tunnel=False):
        super(BambooDBDeploymentPermissions, self).__init__(cfg, db_settings_section, name,
                                                            use_ssh_tunnel=use_ssh_tunnel)
        self.crowd = Crowd(**cfg['Crowd'])

    @staticmethod
    def _mask_to_dict(mask):
        permissions = [
            ('view', 1),
            ('edit', 2),
            ('deploy', 64),
            # No clone or admin for deployments(
            # ('admin', 16),
            # ('clone', 128)
        ]
        perms = dict()
        for perm, int_mask in permissions:
            perms[perm] = int_mask & int(mask) > 0
        return perms

    def _get_display_name(self, user_id):
        try:
            user_details = self.crowd.user(user_id)
            return user_details['display-name']
        except Exception:
            return user_id

    def generate_report(self):
        report = dict()

        # First get the project permissions
        dep_projects_perms = self.exec_query(query=self.query_project)
        for deployment_project, id, entity_name,  entity_type, mask in dep_projects_perms:
            if deployment_project not in report:
                report[deployment_project] = dict(
                    id=id,
                    permissions=list(),
                    environments=dict()
                )
            permission = self._mask_to_dict(mask)
            permission['entity_name'] = entity_name
            permission['entity_type'] = entity_type
            permission['display_name'] = self._get_display_name(entity_name) if entity_type == 'USER' else entity_name
            report[deployment_project]['permissions'].append(permission)

        # Second, get the environment permissions
        dep_environments_perms = self.exec_query(self.query_environment)
        for deployment_project, id, deployment_environment, entity_name, entity_type, mask in dep_environments_perms:
            if deployment_project not in report:
                report[deployment_project] = dict(
                    id=id,
                    prj_permissions=list(),
                    environments=dict()
                )
            if deployment_environment not in report[deployment_project]['environments']:
                report[deployment_project]['environments'][deployment_environment] = list()
            permission = self._mask_to_dict(mask)
            permission['entity_name'] = entity_name
            permission['entity_type'] = entity_type
            permission['display_name'] = self._get_display_name(entity_name) if entity_type == 'USER' else entity_name
            report[deployment_project]['environments'][deployment_environment].append(permission)

        return report

    def save_to_csv(self, output_file=None):
        out_csv = output_file or self.output_file(ext='csv')
        log.info('Saving to CSV file {}'.format(out_csv))
        lines = ['deployment_project,environment_name,entity_name,entity_type,view,edit,deploy']
        for deployment_project in self.report:
            line = '{},{},_PROJECT_,'.format(self.report[deployment_project]['id'], deployment_project)
            for project_permission in self.report[deployment_project]['permissions']:
                lines.append(
                    line + '"{entity_name}","{display_name}",{entity_type},{view},{edit},{deploy}'.format(
                        **project_permission))
            for environment in self.report[deployment_project]['environments']:
                line = '{},{},{},'.format(self.report[deployment_project]['id'], deployment_project, environment)
                for env_permission in self.report[deployment_project]['environments'][environment]:
                    lines.append(
                        line + '"{entity_name}","{display_name}",{entity_type},{view},{edit},{deploy}'.format(
                            **env_permission))

        mkpath(self.output_folder)
        with open(out_csv, 'w', encoding='utf8') as outfile:
            outfile.write('\n'.join(lines))
