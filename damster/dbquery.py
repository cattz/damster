#!/bin/env python
from damster.utils import initialize_logger, get_config
from damster.reports.bamboo import BambooDB

log = initialize_logger(__name__)


cfg = get_config()


def main():

    bamboodb = BambooDB(cfg)
    query = """
    SELECT NAME as DeploymentProject,
          AE.sid,
        (CASE
          WHEN AE.type = 'PRINCIPAL'
               THEN 'USER'
          WHEN AE.type = 'GROUP_PRINCIPAL'
               THEN 'GROUP'
        END) as user_or_group,
        (CASE
           WHEN mask = 1
                THEN 'VIEW'
           WHEN mask = 2
                THEN 'EDIT'
           WHEN mask = 16
                THEN 'ADMIN'
           WHEN mask = 64
                THEN 'BUILD'
           WHEN mask = 128
                THEN 'CLONE'
         END) as permission_type,
         mask
   FROM ACL_ENTRY AS AE
   JOIN ACL_OBJECT_IDENTITY AS AOI
         ON AE.acl_object_identity = AOI.id
  JOIN DEPLOYMENT_PROJECT ON deployment_project_id = object_id_identity
 ORDER BY
  NAME, AE.sid, permission_type
  """
    bamboodb.query(query)
    bamboodb.save_to_csv(query)


if __name__ == "__main__":
    main()
