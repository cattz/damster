
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
                          AWS (only port 22 is open)

    ----------------------------------------------------------------------

Example configuration for the above case:

    [Confluence DB]
    dbname=confluence
    dbuser=confluence
    password=password1
    ssh_gateway=app.server
    host=rds.server
    port=5432