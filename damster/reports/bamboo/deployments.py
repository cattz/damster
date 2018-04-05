from damster.utils import initialize_logger, time_to_excel, time_delta, quoted, replace_non_ascii
from damster.reports.bamboo.utils import TriggerReason
from damster.reports.base_report import BaseReport
from atlassian import Bamboo
import jinja2
from distutils.dir_util import mkpath
import os
import json

log = initialize_logger(__name__)


class BambooDeploymentsReport(BaseReport):

    def __init__(self, cfg, from_date, to_date=None, name='bamboo_deployments_report'):
        super(BambooDeploymentsReport, self).__init__(cfg, from_date, to_date, name)
        self.bamboo = Bamboo(**cfg['Bamboo'])

    # TODO: Needs refactoring
    def generate_report(self):
        log.info('Starting report generation for deployment results between {} and {}'.format(
            self._time_to_string(self.from_date), self._time_to_string(self.to_date)
        ))
        report = list()
        for project in self.bamboo.deployment_projects():
            log.debug('Searching deployments for project "{}"'.format(project['name']))
            plan_key = project['planKey']['key'] if 'planKey' in project else ''
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
                log.debug('Getting deployments to environment "{}"'.format(env['name']))
                for result in self.bamboo.deployment_environment_results(env['id'], expand='results', max_results=25):
                    started_time = self._long_time_to_epoch(result['startedDate'])
                    if started_time > self.from_date:
                        if started_time < self.to_date:
                            env_dict['env_results'].append(self.get_deploy_result_details(result))
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
                in_progress=sum([e['summary']['in_progress'] for e in project_dict['prj_environments']]),
            )
            report.append(project_dict)
        return report

    def get_deploy_result_details(self, result):
        finished_time = self._long_time_to_epoch(result['finishedDate']) \
            if 'finishedDate' in result else ''
        queued_time = self._long_time_to_epoch(result['queuedDate']) \
            if 'queuedDate' in result else ''
        executed_time = self._long_time_to_epoch(result['executedDate']) \
            if 'executedDate' in result else ''
        trigger, user_name, user_id, build_id = TriggerReason(result['reasonSummary']).tuple
        result_dict = dict(
            id=result['id'],
            started=self._time_to_string(self._long_time_to_epoch(result['startedDate'])),
            finished=self._time_to_string(finished_time),
            queued=self._time_to_string(queued_time),
            executed=self._time_to_string(executed_time),
            state=result['deploymentState'],
            version_name=result['deploymentVersionName'],
            deployment_type=trigger,
            deployment_type_raw=result['reasonSummary'],
            deployment_trigger_user_id=user_id,
            deployment_trigger_user=user_name,
            deployment_trigger_build=build_id,
            details=self.get_build_details_from_result(result)
        )
        log.debug('Processing result {}'.format(result_dict))
        return result_dict

    def get_build_details_from_result(self, result):
        details = list()
        if not('deploymentVersion' in result and 'items' in result['deploymentVersion']):
            log.error('No version details available for {}'.format(result))
            return details
        try:
            for artifact in result['deploymentVersion']['items']:
                log.debug('Getting info for plan: {}'.format(artifact))
                build_key = artifact['planResultKey']['key']
                if not build_key.startswith('DELETED_'):
                    build = self.bamboo.build_result(build_key)
                    trigger, user_name, user_id, trigger_plan_key = TriggerReason(build['buildReason']).tuple
                    build_reason = build['buildReason']
                else:
                    trigger, user_name, user_id, trigger_plan_key = '', '', '', build_key
                    build_reason = 'N/A'
                details.append(
                    dict(
                        plan_key=build_key,
                        trigger=trigger,
                        user_id=user_id,
                        user_name=user_name,
                        trigger_plan_key=trigger_plan_key,
                        build_reason=build_reason
                    )
                )
        except Exception as e:
            log.error(e)
        return details

    def save_to_csv(self):
        out_csv = self.output_file(ext='csv')
        log.info('Saving to CSV file {}'.format(out_csv))
        lines = list()
        header = ','.join([
            'prj_id',
            'prj_name',
            'prj_plan_key',
            'env_name',
            'status',
            'started',
            'finished',
            'queued',
            'executed',
            'total_time',
            'time_in_queue',
            'time_deploying',
            'version_name',
            'deployment_type',
            'deployment_trigger_user_name',
            'deployment_trigger_user_id',
            'deployment_trigger_build',
            'deployment_type_raw'
        ])
        lines.append(header)
        for project in self.report:
            for environment in project['prj_environments']:
                for result in environment['env_results']:
                    try:
                        line = ','.join([
                            str(project['prj_id']),
                            quoted(project['prj_name']),
                            project['prj_plan'],
                            quoted(environment['env_name']),
                            result['state'],
                            time_to_excel(result['started']),
                            time_to_excel(result['finished']),
                            time_to_excel(result['queued']),
                            time_to_excel(result['executed']),
                            time_delta(result['started'], result['finished']),
                            time_delta(result['queued'], result['executed']),
                            time_delta(result['executed'], result['finished']),
                            result['version_name'],
                            result['deployment_type'],
                            quoted(result['deployment_trigger_user']),
                            quoted(result['deployment_trigger_user_id']),
                            result['deployment_trigger_build'],
                            result['deployment_type_raw'].replace(', ', '; ').replace('\n', ' - ')
                        ])
                        lines.append(line)
                    except TypeError as e:
                        log.error(e)
                        log.error(result)

        mkpath(self.output_folder)
        with open(out_csv, 'w', encoding='ascii') as outfile:
            outfile.write(replace_non_ascii('\n'.join(lines), '_'))

    def filter_projects_with_no_deployments(self):
        return [prj for prj in self.report if sum(
            [prj['summary']['successful'], prj['summary']['failed'], prj['summary']['in_progress']]) > 0]

    def save_to_html(self, template_name=None, filter_empty=True, **args):
        out_html = self.output_file(ext='html')
        log.info('Saving to HTML: {}'.format(out_html))
        template_name = template_name or self.name + '.html'
        jinja_env = jinja2.Environment(loader=jinja2.PackageLoader('damster', 'templates'))
        template = jinja_env.get_template(template_name)
        report = self.filter_projects_with_no_deployments() if filter_empty else self.report

        summary = dict(
            projects=len(report),
            successful=sum([pr['summary']['successful'] for pr in report]),
            failed=sum([pr['summary']['failed'] for pr in report]),
            in_progress=sum([pr['summary']['in_progress'] for pr in report]),
            from_date=self._time_to_string(self.from_date, fmt='YYYY/MM/DD'),
            to_date=self._time_to_string(self.to_date, fmt='YYYY/MM/DD'),
            bamboo_url=self.bamboo.url
        )

        html = template.render(
            deployments=report,
            summary=summary,
            **args
        )
        mkpath(self.output_folder)
        with open(out_html, 'w', encoding='utf8') as outfile:
            outfile.write(html)

    def run_report(self, use_cache=True):
        if not (os.path.isfile(self.output_file()) and use_cache):
            self._report = self.generate_report()
            self.save_to_json()
        else:
            self._report = json.load(open(self.output_file()))

        self.save_to_csv()

        self.save_to_html(title='Bamboo Reports: Deployments')
