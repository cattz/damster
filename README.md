
# Damster

Scripts to collect metrics and reports from Atlassian tools.
This is a WIP, starting with some reports on Bamboo deployments


    _*Damster*	Builder of dams for logging purposes_


## Database configuration

In order to use any of the queries that access directly to the database, you will need to provide a database
configuration section.

### Direct connection

Use this settings if you can connect directly to the DB port

    [Confluence DB]
    dbname=confluence
    dbuser=confluence
    password=password1
    host=dbhost.example.com
    port=5432


### Use SSH tunnel

Use this configuration when you can not access the DB directly. For example, if your DB is an RDS instance in AWS:


    ----------------------------------------------------------------------

                              |
    -------------+            |    +---------+              +--------+
        LOCAL    |            |    |  APP    |              |  RDS   |
        CLIENT   | <== SSH ======> | SERVER  | <== Sec  ==> | SERVER |
    -------------+            |    +---------+    Group     +--------+
                              |
                          AWS (only access to port 22 on app.server)

    ----------------------------------------------------------------------

Example configuration for the above case:

    [Confluence DB]
    dbname=confluence
    dbuser=confluence
    password=password1
    ssh_gateway=app.server
    host=rds.server
    port=5432

Additionally, you may also need an SSH section, if the defaults do not work for your case:

    [SSH]
    ; All below values are optional. Examples are the default values
    ;ssh_username: current_user
    ;ssh_private_key: ~/.ssh/id_rsa
    ;port: 22
    ;local_bind_port: 6543