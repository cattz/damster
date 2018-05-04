from damster.utils import initialize_logger
from sshtunnel import SSHTunnelForwarder
from getpass import getuser
import psycopg2
import jinja2
import os
import json
from distutils.dir_util import mkpath
import sys

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
        self.ssh_tunnel = None
        self.db_settings = self.cfg[db_settings_section]

        if use_ssh_tunnel:
            self.ssh_tunnel = self.start_ssh_tunnel()
        self.db = self.connect()
        self.cur = self.db.cursor()
        self._report = None

    def start_ssh_tunnel(self):
        ssh_settings = self.cfg['SSH']
        host = self.db_settings['ssh_gateway']
        port = ssh_settings.get('port', 22)
        remote_bind_address = (self.db_settings.get('host'), int(self.db_settings.get('port', 5432)))
        local_bind_address = ('localhost', int(ssh_settings.get('local_bind_port', 6543)))
        tunnel = SSHTunnelForwarder(
            (host, port),
            ssh_username=ssh_settings.get('ssh_username', getuser()),
            ssh_private_key=os.path.expanduser('~/.ssh/{}'.format(
                ssh_settings.get('ssh_private_key', 'id_rsa'))),
            remote_bind_address=remote_bind_address,
            local_bind_address=local_bind_address
        )
        try:
            tunnel.start()
            return tunnel
        except Exception as e:
            log.error('Error starting SSH tunnel to {}: {}'.format(host, e))
            log.error('SSH settings: {}'.format(dict(ssh_settings)))
            sys.exit(-1)

    def connect(self):
        if self.ssh_tunnel:
            db_settings = dict(self.db_settings)
            db_settings['host'] = 'localhost'
            db_settings['port'] = self.ssh_tunnel.local_bind_port
            return self._connect(**db_settings)
        else:
            return self._connect(**self.db_settings)

    def _connect(self, dbname, dbuser, host, password, port, ssh_gateway=None):
        cons = "dbname='{dbname}' user='{dbuser}' host='{host}' " \
               "password='{password}' port='{port}'".format(**locals())
        if ssh_gateway:
            log.info('Connecting to db {dbname} at {host}:{port} through gateway {gateway}'.format(
                host=self.db_settings.get('host'),
                port=self.db_settings.get('port'),
                dbname=dbname,
                gateway=ssh_gateway
                )
            )
        else:
            log.info('Connecting to db {dbname} at {host}:{port}'.format(**locals()))
        try:
            return psycopg2.connect(cons)
        except psycopg2.OperationalError as e:
            log.error('Error connecting to database: {}'.format(e))
            sys.exit(-1)

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
        with open(csv_file, 'w', encoding='ascii') as f:
            self.cur.copy_expert(csv_query, f)

    def save_to_json(self):
        out_json = self.output_file()
        log.info('Saving to JSON: {}'.format(out_json))
        mkpath(self.output_folder)
        with open(out_json, 'w', encoding='utf8') as outfile:
            json.dump(self.report, outfile)

    def save_to_html(self, template_name=None, **args):
        out_html = self.output_file(ext='html')
        log.info('Saving to HTML: {}'.format(out_html))
        template_name = template_name or self.name + '.html'
        jinja_env = jinja2.Environment(loader=jinja2.PackageLoader('damster', 'templates'))
        template = jinja_env.get_template(template_name)

        log.debug('Using template {}'.format(template))

        html = template.render(report=self.report, **args)
        mkpath(self.output_folder)
        with open(out_html, 'w', encoding='utf8') as outfile:
            outfile.write(html)

    def __del__(self):
        if 'cur' in self.__dict__:
            self.cur.close()
            self.db.close()
        if self.ssh_tunnel:
            self.ssh_tunnel.stop()
