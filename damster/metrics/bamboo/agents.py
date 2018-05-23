from damster.utils import initialize_logger
import re
try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse
from pprint import pformat


log = initialize_logger(__name__)


def _sanitize_url(url):
    u = urlparse(url)
    return u.netloc.split(':')[0].replace('.', '_')


class BambooBuildAgentsMetrics(object):

    AGENTS_BUILDING = re.compile(r'(?P<online>\d+)(?: of (?P<busy>\d+))? online agents(?: building)?')

    def __init__(self, bamboo_client, influx_client):
        self.cli = bamboo_client
        self.influx = influx_client

    def agent_status(self, metric_name):
        try:
            agents = self.cli.agent_status()
            log.debug('Agent Status:\n{}'.format(pformat(agents)))
            metrics = list()
            for agent in agents:
                metrics.append(dict(
                    measurement=metric_name,
                    tags=dict(
                        agent_name=agent['name'].replace(' ', '_'),
                        type=agent['type'],
                        busy=agent['busy'],
                        enabled=agent['enabled'],
                        active=agent['active'],
                    ),
                    fields=dict(
                        value=1
                    )
                ))
            self.influx.write_points(metrics)
        except ValueError as e:
            log.error('Agent Status threw a ValueError: {}'.format(e))
        except Exception as e:
            log.error('Agent Status threw an Exception: {}'.format(e))

    def activity(self, metric_name, tags=None):
        try:
            activity = self.cli.activity()
            log.debug('Build Activity:\n{}'.format(pformat(activity)))

            building = [b for b in activity['builds'] if b['status'] == 'BUILDING']
            queued = [b for b in activity['builds'] if b['status'] == 'QUEUED']
            total_building = len(building)
            local_building = len([b for b in building if b['agent']['type'] == 'LOCAL'])
            remote_building = len([b for b in building if b['agent']['type'] == 'REMOTE'])
            total_queued = len(queued)
            try:
                search = re.search(self.AGENTS_BUILDING, activity['agentSummary'])
                agents_building = int(search.groupdict('0')['busy'])
                agents_online = int(search.groupdict('0')['online'])
            except AttributeError:
                log.error('Error parsing agentSummary')
                agents_building = 0
                agents_online = 0

            metric = dict(
                    measurement=metric_name,
                    tags=dict(
                        host=_sanitize_url(self.cli.url)
                    ),
                    fields=dict(
                        total_building=total_building,
                        local_building=local_building,
                        remote_building=remote_building,
                        queued=total_queued,
                        agents_building=agents_building,
                        agents_online=agents_online
                    )
                )
            if tags:
                metric['tags'].update(tags)
            log.debug('Metric:\n{}'.format(pformat(metric)))
            self.influx.write_points([metric])
        except Exception as e:
            log.error('Bamboo Activity threw an Exception: {}'.format(e))
