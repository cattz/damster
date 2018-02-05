from damster.reports.bamboo.utils import TriggerReason


class TestParseTriggerReason(object):

    reasons = [
        ('Child of <a href="https://host/path/to/XX-YY-55">XX-YY-55</a>', ('Child', '', '', 'XX-YY-55')),
        ('Manual run by <a href="https://host/path/to/userid">User Name</a>', ('Manual', 'User Name', 'userid', '')),
        ('Manual run by someuser', ('Manual', 'someuser', 'someuser', '')),
        ('Code has changed', ('Commit', '', '', '')),
        ('Scheduled', ('Scheduled', '', '', '')),
        ('Changes by <a href="http://url/viewUserSummary.action?currentUserName=usid">Last, Fisrt</a>',
         ('Commit', 'Last, Fisrt', 'usid', '')),
        ('Rebuilt by <a href="https://foo.bar.com/bamboo/browse/user/jsnow">John Snow</a>',
         ('Rebuilt', 'John Snow', 'jsnow', '')),
        ('Rebuilt      by <a href="https://foo.bar.com/bamboo/browse/user/mward">M Ward</a>',
         ('Rebuilt', 'M Ward', 'mward', '')),
        ('Code changes detected', ('Commit', '', '', ''))
    ]

    def test_dummy(self):
        for reason, result in self.reasons:
            assert TriggerReason(reason).tuple == result
