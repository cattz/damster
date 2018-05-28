from damster.reports.bamboo.utils import TriggerReason
from damster.utils import previous_month_range
from datetime import date


class TestParseTriggerReason(object):

    reasons = [
        ('Child of <a href="https://host/path/to/XX-YY-55">XX-YY-55</a>', ('Child', '', '', 'XX-YY-55')),
        ('Manual run by <a href="https://host/path/to/userid">User Name</a>', ('Manual', 'User Name', 'userid', '')),
        ('Manual run by someuser', ('Manual', 'someuser', 'someuser', '')),
        ('Code has changed', ('Commit', '', '', '')),
        ('Scheduled', ('Scheduled', '', '', '')),
        ('Changes by <a href="http://url/viewUserSummary.action?currentUserName=usid">Last, First</a>',
         ('Commit', 'Last, First', 'usid', '')),
        ('Rebuilt by <a href="https://foo.bar.com/bamboo/browse/user/jsnow">John Snow</a>',
         ('Rebuilt', 'John Snow', 'jsnow', '')),
        ('Rebuilt      by <a href="https://foo.bar.com/bamboo/browse/user/mward">M Ward</a>',
         ('Rebuilt', 'M Ward', 'mward', '')),
        ('Code changes detected', ('Commit', '', '', '')),
        ('First build for this plan', ('First build', '', '', '')),
        ('Triggered by <a href="https://foobar.com/bamboo/deploy/viewDeploymentResult.action?'
         'deploymentResultId=1122334455">Some Deployment Project &rsaquo; Test</a>',
         ('Child', '', '', 'Some Deployment Project &rsaquo; Test')),
        ('Custom build by SOUSERID&nbsp;with revision '
         '<a href="https://foobar.com/bamboo/browse/PPP-LLL-777#changesSummary">1234abc</a>',
         ('Manual', 'SOUSERID', 'SOUSERID', '')),
        ('Manual run from the stage: <b>Deploy</b> by <a href="https://swfactory.aegon.com/bamboo/browse/user/UUID">'
         'User Name</a>', ('Manual', 'User Name', 'UUID', '')),
        ('Manual run from the stage: <b>Artifactory</b> by L4IJUM', ('Manual', 'L4IJUM', 'L4IJUM', ''))
    ]

    def test_dummy(self):
        for reason, result in self.reasons:
            assert result == TriggerReason(reason).tuple


class TestPreviousMonthRange(object):
    cases = [
        (date(2018, 1, 1), ('2017-12-01', '2018-01-01')),
        (date(2018, 1, 31), ('2017-12-01', '2018-01-01')),
        (date(2018, 5, 25), ('2018-04-01', '2018-05-01')),
        (date(2018, 12, 31), ('2018-11-01', '2018-12-01')),
    ]

    def test_previous_month(self):
        for date_, result in self.cases:
            assert previous_month_range(date_) == result
