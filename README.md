
# Damster

> _Damster_	Builder of dams for logging purposes

Damster is a collection of scripts to collect metrics and reports from Atlassian tools.

The scripts are wrapped by the `damster` command line tool. The tool has 3 top-level subcommands,
for generating reports, publishing metrics and (for conveninece) a quick way to publish an attachment to
a Confluence page.

## Reports

At the moment, these are the reports available:

* Bamboo
  * **builds:** All builds for a specific time period
  * **deployments:** All deployments for a specific time period
  * **deployment-permissions:** Permissions per deployment project and environment
* Confluence
  * **changes**: changes in Confluence content in the specific period

Most of this reports will produce 3 files:
* `.json` contains the raw data used for the report.
* `.csv` contains the above data 'flattened' as csv
* `.html` is a more visual representation of the report

The output location for this files can be defined in the configuration:

```ini
[Reports]
destination_folder=C:\work\damster\globalitconfluence
```

## Metrics

All metrics commands collect a specific set of metrics and publish them to InfluxDB.

Available metrics:

* Bamboo
  * **agent-status** Collects the following data from bamboo agents: name, busy, enabled, type
  * **activity** Collects data from the build activity page: number of agents online, agents building
    (split in local and remote) and queued jobs.

Note: You will note that the information from the above metrics is very similar, but not exactly the same.
`agent-status` provides more granularity, giving specific status for each agent, instead of just totals.
On the other side, `activity` provides the queue size, which is a very important metric.

The InfluxDB settings can be provided in the configuration:

```ini
[InfluxDB]
host=influx.example.com
port=8086
username=root
password=root
database=my-db
```

# Usage

Create a virtualenv and install `damster`, either from source or from PyPi/Artifactory:

```bash
$ virtualenv .env
$ source .env/bin/activate
(.env) $ pip install damster                # Install from PyPi
(.env) $ pip install -e ./path/to/damster   # Install from source after clone
(.env) $ damster
Usage: damster [OPTIONS] COMMAND [ARGS]...

  Damster: Reports and metrics from Atlassian tools.

Options:
  --version          Show the version and exit.
  -c, --config TEXT  configuration file to use
  --help             Show this message and exit.

Commands:
  metrics                Collect metrics and store them in InfluxDB.
  publish-to-confluence  Publish file to Confluence
  reports                Generate reports.

```

For specific instructions on how to use a report, you can request help form the cli:

```bash
(.env) $ damster reports bamboo builds --help
Usage: damster reports bamboo builds [OPTIONS] FROM_DATE [TO_DATE]

  Generate a builds report

Options:
  --use-cache / --no-use-cache
  --help                        Show this message and exit.
```

# Configuration

There are 3 levels of configuration files that can override settings from the previous level:

1. Package defaults, stored in `damster/defaults.cfg`. This file contains the whole set of available
settings and is a good default for your development install.
2. User settings, from `~/.config/damster.cfg` can be used to store user specific settings, like secrets, etc
3. Per-use settings, passes as an argument to damster in each call to the command line:

```bash
(.env) $ damster -c path/to/bamboo-prod.cfg bamboo builds
```

Some of the reports use the REST API for retrieving data, while others will try to connect directly to the
database. For the REST API reports you will need to provide a user credentials with sufficient permissions,
while for the database reports you will need the credentials of a user with, at least, `SELECT` privileges
on the corresponding database.

## Database configuration

In order to use any of the queries that access directly to the database, you will need to provide a database
configuration section.

### Direct connection

Use this settings if you can connect directly to the DB port

```ini
[Confluence DB]
dbname=confluence
dbuser=confluence
password=password1
host=dbhost.example.com
port=5432
```

### Use SSH tunnel

Use this configuration when you can not access the DB directly, for example, if your DB is an
RDS instance in AWS:

```

----------------------------------------------------------------------

                          |
-------------+            |    +---------+              +--------+
    LOCAL    |            |    |  APP    |              |  RDS   |
    CLIENT   | <== SSH ======> | SERVER  | <== Sec  ==> | SERVER |
-------------+            |    +---------+    Group     +--------+
                          |
                      AWS (only access to port 22 on app.server)

----------------------------------------------------------------------
```

Example configuration for the above case:

```ini
[Confluence DB]
dbname=confluence
dbuser=confluence
password=password1
ssh_gateway=app.server
host=rds.server
port=5432
```

Another use case for the SSH tunnel would be having your DB server only listening in localhost

------------------------------------------------------------

                          |
-------------+            |    +-----------+
    LOCAL    |            |    |  DB SRV.  |
    CLIENT   | <== SSH ======> | port 5432 |
-------------+            |    +-----------+
                          |
                      Port 5432 only listening for localhost

--------------------------------------------------------------

```ini
[Bamboo DB]
dbname=bamboo
dbuser=bamboo
password=password1
ssh_gateway=db_server
host=localhost
port=5432
```

Additionally, when using the ssh tunel, you will need an SSH section if the defaults (below) do not work for your case:

```ini
[SSH]
; All below values are optional. Examples are the default values
;ssh_username: current_user
;ssh_private_key: id_rsa
;port: 22
;local_bind_port: 6543
```

Don't forget to instruct `damster` to use the ssh gateway by adding the `-S` or `--use-ssh-tunnel` flag:

```bash
(.env) $ damster -c myconfig.cfg confluence changes -S
```

# Debugging

Debug logging can be enabled via environment variable. Default is INFO

```
DAMSTER_LOGLEVEL=DEBUG