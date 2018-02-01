from damster.utils import initialize_logger
from atlassian import Bamboo
import json
import os
import jinja2
import arrow
import re

log = initialize_logger(__name__)


class BambooDeploymentsReport(object):

    re_MANUAL = re.compile(r'Manual run by <a href="http[s]?:\/\/[^"]*\/(.*)">(.*)<\/a>')
    re_CHILD = re.compile(r'Child of <a href="http[s]?:\/\/[^"]*">(.*)<\/a>')

    def __init__(self, cfg, from_date, to_date=None, output_file='deployment_report'):
        self.cfg = cfg
        self.time_zone = cfg['Common']['time_zone']
        self.from_date = arrow.get(from_date).replace(tzinfo=self.time_zone)
        self.to_date = arrow.get(to_date).replace(tzinfo=self.time_zone) \
            if to_date else arrow.utcnow().to(self.time_zone)
        self.output_file = output_file
        self.json_file = '{}.json'.format(self.output_file)
        self.csv_file = '{}.csv'.format(self.output_file)
        self.html_file = '{}.html'.format(self.output_file)
        self.report_dict = None
        self.bamboo = Bamboo(**cfg['Bamboo'])

    def _time_to_epoch(self, tm):
        return arrow.get(tm / 1000).to(self.time_zone)

    def _string_to_time(self, tm, fmt='YYYY-MM-DD HH:mm:ss'):
        return tm.to(self.time_zone).format(fmt)

    def parse_trigger_info(self, msg):
        find = re.search(self.re_MANUAL, msg)
        if msg.startswith('Scheduled'):
            return 'Scheduled', '', '', ''
        if find:
            full_name = find.group(2)
            if ',' in full_name:
                last, first = full_name.split(', ')
                full_name = '{} {}'.format(first, last)
            return 'Manual', find.group(1), full_name, ''
        find = re.search(self.re_CHILD, msg)
        if find:
            return 'Child', '', '', find.group(1)
        raise ValueError('No regex for: {}'.format(msg))

    def generate_report(self):
        log.info('Starting report generation for deployment results between {} and {}'.format(
            self._string_to_time(self.from_date), self._string_to_time(self.to_date)
        ))
        report = list()
        deploy_projects = self.bamboo.deployment_project()

        for project in deploy_projects:
            plan_key = project['planKey'] if 'planKey' in project else ''
            project_dict = dict(
                prj_id=project['id'],
                prj_name=project['name'],
                prj_plan=plan_key,
                prj_environments=list()
            )
            log.debug(project_dict)
            for env in project['environments']:
                env_dict = dict(
                    env_id=env['id'],
                    env_name=env['name'],
                    env_results=list()
                )
                log.debug('\t{}'.format(env_dict))
                deploy_results = self.bamboo.deployment_environment_results(env['id'], 'results')
                if 'results' in deploy_results:
                    for result in deploy_results['results']:
                        started_time = self._time_to_epoch(result['startedDate'])
                        if started_time > self.from_date:
                            if started_time < self.to_date:
                                finished_time = self._time_to_epoch(result['finishedDate']) \
                                    if 'finishedDate' in result else ''
                                queued_time = self._time_to_epoch(result['queuedDate']) \
                                    if 'queuedDate' in result else ''
                                executed_time = self._time_to_epoch(result['executedDate']) \
                                    if 'executedDate' in result else ''
                                trigger, user_id, user_name, build_id = self.parse_trigger_info(result['reasonSummary'])
                                result_dict = dict(
                                    started=self._string_to_time(started_time),
                                    finished=self._string_to_time(finished_time),
                                    queued=self._string_to_time(queued_time),
                                    executed=self._string_to_time(executed_time),
                                    state=result['deploymentState'],
                                    version_name=result['deploymentVersionName'],
                                    deployment_type=trigger,
                                    deployment_type_raw=result['reasonSummary'],
                                    deployment_trigger_user_id=user_id,
                                    deployment_trigger_user=user_name,
                                    deployment_trigger_build=build_id
                                )
                                log.debug('\t\t{}'.format(result_dict))
                                env_dict['env_results'].append(result_dict)
                        else:
                            break  # Since results are ordered from newest, exit as soon as we find an older result
                env_summary = dict(
                    successful=len([r for r in env_dict['env_results'] if r['state'] == 'SUCCESS']),
                    failed=len([r for r in env_dict['env_results'] if r['state'] == 'FAILED']),
                    in_progress=len([r for r in env_dict['env_results'] if r['state'] == 'UNKNOWN']),
                )
                env_dict['summary'] = env_summary
                project_dict['prj_environments'].append(env_dict)
            project_dict['summary'] = dict(
                successful=sum([e['summary']['successful'] for e in project_dict['prj_environments']]),
                failed=sum([e['summary']['failed'] for e in project_dict['prj_environments']]),
                in_progress=sum([e['summary']['in_progress'] for e in project_dict['prj_environments']])
            )
            report.append(project_dict)
        return report

    def save_to_csv(self, csv_file=None):
        log.info('Saving to CSV')
        out_csv = csv_file or self.csv_file
        lines = list()
        header = ','.join([
            'prj_id',
            'prj_name',
            'prj_plan_key',
            'env_name',
            'started',
            'finished',
            'queued',
            'executed',
            'version_name',
            'deployment_type',
            'deployment_trigger_user_name',
            'deployment_trigger_user_id',
            'deployment_trigger_build',
            'deployment_type_raw'
        ])
        lines.append(header)
        for project in self.report_dict:
            for environment in project['prj_environments']:
                for result in environment['env_results']:
                    line = ','.join([
                        str(project['prj_id']),
                        project['prj_name'],
                        project['prj_plan']['key'],
                        environment['env_name'],
                        result['started'],
                        result['finished'],
                        result['queued'],
                        result['executed'],
                        result['version_name'],
                        result['deployment_type'],
                        result['deployment_trigger_user'],
                        result['deployment_trigger_user_id'],
                        result['deployment_trigger_build'],
                        result['deployment_type_raw'].replace(', ', '; ').replace('\n', ' - ')
                    ])
                    lines.append(line)
        with open(out_csv, 'w') as outfile:
            outfile.write('\n'.join(lines))

    def filter_projects_with_no_deployments(self):
        return [prj for prj in self.report_dict if sum(
            [prj['summary']['successful'], prj['summary']['failed'], prj['summary']['in_progress']]) > 0]

    def save_to_json(self, json_file=None, filter_empty=False):
        log.info('Saving to JSON')
        out_json = json_file or self.json_file
        report = self.filter_projects_with_no_deployments() if filter_empty else self.report_dict
        with open(out_json, 'w') as outfile:
            json.dump(report, outfile)

    def save_to_html(self, template_name, html_file=None, filter_empty=True):
        out_html = html_file or self.html_file
        log.info('Saving to HTML: {}'.format(out_html))

        jinja_env = jinja2.Environment(loader=jinja2.PackageLoader('damster', 'templates'))
        template = jinja_env.get_template(template_name)
        report = self.filter_projects_with_no_deployments() if filter_empty else self.report_dict
        html = template.render(deployments=report)
        with open(out_html, 'w') as outfile:
            outfile.write(html)

    def run_report(self, use_cache=True):
        if not self.report_dict:
            if not (os.path.isfile(self.json_file) and use_cache):
                self.report_dict = self.generate_report()
                self.save_to_json()
            else:
                self.report_dict = json.load(open(self.json_file))

        self.save_to_csv()

        self.save_to_html('deployments_report.html')
