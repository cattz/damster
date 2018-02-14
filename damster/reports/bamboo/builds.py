from damster.utils import initialize_logger
from damster.reports.bamboo.utils import TriggerReason
from damster.reports.base_report import BaseReport
from atlassian import Bamboo
import arrow

log = initialize_logger(__name__)


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
            build_projects = self.bamboo.projects()
            for project in build_projects['projects']['project']:
                project_dict = dict(
                    key=project['key'],
                    name=project['name'],
                    #  description=project['description'],
                    plans=list()
                )
                build_plans = self.bamboo.projects(project_key=project['key'], expand='plans')
                for plan in build_plans['plans']['plan']:
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
                    branches = self.bamboo.search_branches(plan['key'])
                    for branch in branches['searchResults']:
                        branch_dict = dict(
                            key=branch['id'],
                            type=branch['type'],
                            name=branch['searchEntity']['branchName'],
                            results=list()
                        )
                        build_results = self.bamboo.results(project_key=branch['id'], expand='results')
                        for result in build_results['results']['result']:
                            log.debug(result)
                            result_dict = dict(
                                number=result['number'],
                                state=result['state'],
                                key=result['key'],
                                lifecycle_state=result['lifeCycleState'],
                            )
                            result_details = self.bamboo.results(project_key=result['buildResultKey'])
                            # WTF Atlassian! buildStartedTime is not sorted for first builds of a plan
                            started_time_string = result_details.get('buildStartedTime',
                                                                     result_details.get('buildCompletedTime'))
                            started_time = arrow.get(started_time_string).replace(tzinfo=self.time_zone)
                            if started_time > self.from_date:
                                if started_time < self.to_date:
                                    log.debug(result_details)
                                    result_dict['started'] = started_time_string
                                    result_dict['finished'] = result_details.get('buildCompletedTime', '')
                                    result_dict['duration'] = result_details.get('buildDuration', 0)
                                    trigger, user_name, user_id, build_id = TriggerReason(result_details['reasonSummary']).tuple
                                    result_dict['trigger_raw'] = result_details['reasonSummary']
                                    result_dict['trigger_type'] = trigger
                                    result_dict['trigger_user'] = user_name
                                    result_dict['trigger_user_id'] = user_id
                                    result_dict['trigger_build'] = build_id
                                    result_dict['stage_number'] = result_details['stages']['size']
                                    result_dict['issue_number'] = result_details['jiraIssues']['size']
                                    result_dict['artifact_number'] = result_details['artifacts']['size']
                                    branch_dict['results'].append(result_dict)

                            else:
                                break
                        if branch_dict['results']:
                            plan_dict['branches'].append(branch_dict)
                    if plan_dict['branches']:
                        project_dict['plans'].append(plan_dict)
                if project_dict['plans']:
                    report.append(project_dict)
            self._report = report
        return self._report
