from damster.utils import initialize_logger
from sshtunnel import SSHTunnelForwarder
from getpass import getuser
import psycopg2
import jinja2
import os
import json
from distutils.dir_util import mkpath

log = initialize_logger(__name__)


class GenericDB(object):
    """
    Generic DB query object
    """
    table_columns = ()

    query = ''

    def __init__(self, cfg, db_settings_section='Common', name='generic_db_query', use_ssh_tunnel=False):
        self.name = name
        self.cfg = cfg
        self.db_settings = self.cfg[db_settings_section]
        self.ssh_tunnel = self.start_ssh_tunnel() if use_ssh_tunnel else None
        self.db = self.connect()
        self.cur = self.db.cursor()
        self._report = None

    def start_ssh_tunnel(self):
        ssh_settings = self.cfg['SSH']
        host = self.db_settings['host']
        port = ssh_settings.get('port', 22)
        remote_bind_address = ('localhost', int(self.db_settings.get('port', 5432)))
        local_bind_address = ('localhost', int(ssh_settings.get('local_bind_port', 6543)))
        tunnel = SSHTunnelForwarder(
            (host, port),
            ssh_username=ssh_settings.get('ssh_username', getuser()),
            ssh_private_key=os.path.expanduser(
                ssh_settings.get('ssh_private_key', '~/.ssh/id_rsa')),
            remote_bind_address=remote_bind_address,
            local_bind_address=local_bind_address
        )
        tunnel.start()
        return tunnel

    def connect(self):
        if self.ssh_tunnel:
            db_settings = dict(self.db_settings)
            db_settings['host'] = 'localhost'
            db_settings['port'] = self.ssh_tunnel.local_bind_port
            return self._connect(**db_settings)
        else:
            return self._connect(**self.db_settings)

    def _connect(self, dbname, dbuser, host, password, port):
        cons = "dbname='{dbname}' user='{dbuser}' host='{host}' " \
               "password='{password}' port='{port}'".format(**locals())
        log.info('Connecting to db {dbname} at {host}:{port}'.format(**locals()))
        return psycopg2.connect(cons)

    @property
    def output_folder(self):
        return os.path.join(
            self.cfg['Reports']['destination_folder'],
            self.name)

    def exec_query(self, query):
        self.cur.execute(query)
        return self.cur.fetchall()

    def generate_report(self):
        self.cur.execute(self.query)
        results = list()
        for row in self.cur.fetchall():
            results.append(dict(zip(self.table_columns, row)))
        return results

    @property
    def report(self):
        if not self._report:
            self._report = self.generate_report()
        return self._report

    def output_file(self, ext='json'):
        return os.path.join(
            self.output_folder,
            '{}.{}'.format(self.name, ext)
        )

    def save_to_csv(self, output_file=None):
        csv_query = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(self.query)
        csv_file = output_file or self.output_file('csv')
        log.info('Saving query results to CSV file: {}'.format(csv_file))
        mkpath(os.path.dirname(csv_file))
        with open(csv_file, 'w') as f:
            self.cur.copy_expert(csv_query, f)

    def save_to_json(self):
        out_json = self.output_file()
        log.info('Saving to JSON: {}'.format(out_json))
        mkpath(self.output_folder)
        with open(out_json, 'w') as outfile:
            json.dump(self.report, outfile)

    def save_to_html(self, template_name=None, **args):
        out_html = self.output_file(ext='html')
        log.info('Saving to HTML: {}'.format(out_html))
        template_name = template_name or self.name + '.html'
        jinja_env = jinja2.Environment(loader=jinja2.PackageLoader('damster', 'templates'))
        template = jinja_env.get_template(template_name)

        html = template.render(deployments=self.report, **args)
        mkpath(self.output_folder)
        with open(out_html, 'w') as outfile:
            outfile.write(html)

    def __del__(self):
        self.cur.close()
        self.db.close()
        if self.ssh_tunnel:
            self.ssh_tunnel.stop()