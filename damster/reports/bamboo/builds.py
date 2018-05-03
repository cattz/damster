from damster.utils import initialize_logger, quoted, time_to_excel, replace_non_ascii
from damster.reports.bamboo.utils import TriggerReason
from damster.reports.base_report import BaseReport
from atlassian import Bamboo
import arrow
import jinja2
from distutils.dir_util import mkpath
from six.moves.urllib.parse import unquote


log = initialize_logger(__name__)


def prettify_date_time(dt):
    if len(dt) == 24:
        return dt[:-5].replace('T', ' ')
    return dt


class BambooBuildsReport(BaseReport):

    def __init__(self, cfg, from_date, to_date=None, name='bamboo_builds_report'):

        super(BambooBuildsReport, self).__init__(cfg, from_date, to_date, name)
        self.bamboo = Bamboo(**cfg['Bamboo'])

    # TODO: Needs refactoring
    def generate_report(self):
        if self._report is None:
            log.info('Starting report generation for build results between {} and {}'.format(
                self._time_to_string(self.from_date), self._time_to_string(self.to_date)
            ))
            report = list()
            for project in self.bamboo.projects():
                log.info('Retrieving plans for project "{}:{}"'.format(project['key'], project['name']))
                project_description = project['description'] if 'description' in project else ''
                project_dict = dict(
                    key=project['key'],
                    name=project['name'],
                    description=project_description,
                    plans=list()
                )
                for plan in self.bamboo.project_plans(project_key=project['key']):
                    log.info('Retrieving branches for plan "{}:{}"'.format(plan['key'], plan['shortName']))
                    plan_dict = dict(
                        short_name=plan['shortName'],
                        short_key=plan['shortKey'],
                        enabled=plan['enabled'],
                        type=plan['type'],
                        key=plan['key'],
                        name=plan['name'],
                        branches=list()
                    )
                    log.debug(plan_dict)
                    for branch in self.bamboo.search_branches(plan['key']):
                        log.info('Retrieving results for branch "{}"'.format(branch['searchEntity']['branchName']))
                        branch_dict = dict(
                            key=branch['id'],
                            type=branch['type'],
                            name=branch['searchEntity']['branchName'],
                            results=list()
                        )
                        for result in self.bamboo.results(project_key=branch['id'], expand='results'):
                            log.debug('Build result: {}'.format(result))
                            result_dict = dict(
                                number=result['number'],
                                state=result['state'],
                                key=result['key'],
                                lifecycle_state=result['lifeCycleState'],
                            )
                            result_details = self.bamboo.build_result(build_key=result['buildResultKey'])
                            # WTF Atlassian! buildStartedTime is not always stored
                            started_time_string = result_details.get('buildStartedTime',
                                                                     result_details.get('buildCompletedTime'))
                            started_time = arrow.get(started_time_string).replace(tzinfo=self.time_zone)
                            if started_time > self.from_date:
                                if started_time < self.to_date:
                                    log.debug('Result details: {}'.format(result_details))
                                    result_dict['started'] = prettify_date_time(started_time_string)
                                    result_dict['finished'] = prettify_date_time(
                                        result_details.get('buildCompletedTime', ''))
                                    result_dict['duration'] = result_details.get('buildDuration', 0)
                                    trigger, user_name, user_id, build_id = TriggerReason(
                                        result_details['reasonSummary']).tuple
                                    result_dict['trigger_raw'] = unquote(result_details['reasonSummary'])
                                    result_dict['trigger_type'] = trigger
                                    result_dict['trigger_user'] = user_name
                                    result_dict['trigger_user_id'] = user_id
                                    result_dict['trigger_build'] = build_id
                                    result_dict['number_stages'] = result_details['stages']['size']
                                    result_dict['number_issues'] = result_details['jiraIssues']['size']
                                    result_dict['number_artifacts'] = result_details['artifacts']['size']
                                    branch_dict['results'].append(result_dict)
                            else:
                                break
                            branch_dict['successful'] = len(
                                [r for r in branch_dict['results'] if r['state'] == 'Successful'])
                            branch_dict['failed'] = len(
                                [r for r in branch_dict['results'] if r['state'] == 'Failed'])
                            branch_dict['unknown'] = (len(branch_dict['results']) -
                                                      branch_dict['failed'] - branch_dict['successful'])
                        if branch_dict['results']:
                            plan_dict['branches'].append(branch_dict)
                    if plan_dict['branches']:
                        plan_dict['successful'] = sum([b['successful'] for b in plan_dict['branches']])
                        plan_dict['failed'] = sum([b['failed'] for b in plan_dict['branches']])
                        plan_dict['unknown'] = sum([b['unknown'] for b in plan_dict['branches']])
                        project_dict['plans'].append(plan_dict)
                if project_dict['plans']:
                    project_dict['successful'] = sum([b['successful'] for b in project_dict['plans']])
                    project_dict['failed'] = sum([b['failed'] for b in project_dict['plans']])
                    project_dict['unknown'] = sum([b['unknown'] for b in project_dict['plans']])
                    report.append(project_dict)
            self._report = report
        return self._report

    def save_to_html(self, template_name=None, **args):
        out_html = self.output_file(ext='html')
        log.info('Saving to HTML: {}'.format(out_html))
        template_name = template_name or self.name + '.html'
        jinja_env = jinja2.Environment(loader=jinja2.PackageLoader('damster', 'templates'))
        template = jinja_env.get_template(template_name)

        summary = dict(
            projects=len(self.report),
            successful=sum([pr['successful'] for pr in self.report]),
            failed=sum([pr['failed'] for pr in self.report]),
            unknown=sum([pr['unknown'] for pr in self.report]),
            from_date=self._time_to_string(self.from_date, fmt='YYYY/MM/DD'),
            to_date=self._time_to_string(self.to_date, fmt='YYYY/MM/DD'),
            bamboo_url=self.bamboo.url
        )

        html = template.render(
            report=self.report,
            summary=summary,
            **args
        )
        mkpath(self.output_folder)
        with open(out_html, 'w', encoding='utf8') as outfile:
            outfile.write(html)

    def save_to_csv(self):
        out_csv = self.output_file(ext='csv')
        log.info('Saving to CSV file {}'.format(out_csv))
        lines = list()
        header = ','.join([
            'project_key',
            'project_name',
            'plan_key',
            'plan_name',
            'branch_name',
            'branch_type',
            'build_key',
            'status',
            'started',
            'finished',
            'duration',
            'trigger',
            'trigger_type',
            'trigger_user',
            'trigger_user_id',
            'trigger_build',
            'trigger_raw',
            'stages',
            'artifacts',
            'jira_issues'
        ])
        lines.append(header)
        for project in self.report:
            for plan in project['plans']:
                for branch in plan['branches']:
                    for result in branch['results']:
                        try:
                            line = ','.join([
                                project['key'],
                                quoted(project['name']),
                                plan['short_key'],
                                quoted(plan['name']),
                                quoted(branch['name']),
                                branch['type'],
                                result['key'],
                                result['state'],
                                time_to_excel(result['started']),
                                time_to_excel(result['finished']),
                                str(result['duration']),
                                result['trigger_type'],
                                result['trigger_type'],
                                result['trigger_user'],
                                result['trigger_user_id'],
                                result['trigger_build'],
                                result['trigger_raw'].replace('\n', ' - '),
                                str(result['number_stages']),
                                str(result['number_artifacts']),
                                str(result['number_issues'])
                            ])
                            lines.append(line)
                        except TypeError as e:
                            log.error(e)
                            log.error(result)
        mkpath(self.output_folder)
        with open(out_csv, 'w', encoding='ascii') as outfile:
            outfile.write(replace_non_ascii('\n'.join(lines), '_'))

    def run_report(self, use_cache=True):
        super(BambooBuildsReport, self).run_report(use_cache=use_cache)
        self.save_to_csv()
        self.save_to_html(title='Bamboo Reports: Builds')
