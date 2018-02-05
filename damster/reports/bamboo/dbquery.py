from damster.utils import initialize_logger
import psycopg2

log = initialize_logger(__name__)


class BambooDB(object):

    def __init__(self, cfg, name='bamboo_dbquery_report'):
        self.name = name
        self.cfg = cfg
        self.db = self._connect()
        self.cur = self.db.cursor()

    def _connect(self):
        cons = "dbname='{dbname}' user='{dbuser}' host='{host}' " \
               "password='{password}' port='{port}'".format(**self.cfg['Bamboo DB'])
        log.info('Connecting to db {dbname} at {host}:{port}'.format(**self.cfg['Bamboo DB']))
        return psycopg2.connect(cons)

    def query(self, query):
        self.cur.execute(query)
        return self.cur

    def save_to_csv(self, query):
        log.info('Saving query results to csv')
        csv_query = "COPY ({0}) TO STDOUT WITH CSV HEADER".format(query)
        with open('resultsfile.csv', 'w') as f:
            self.cur.copy_expert(csv_query, f)

    def __del__(self):
        self.cur.close()
        self.db.close()
