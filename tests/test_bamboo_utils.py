from damster.reports.bamboo.utils import TriggerReason


class TestParseTriggerReason(object):

    reasons = [
        ('Child of <a href="https://host/path/to/XX-YY-55">XX-YY-55</a>', ('Child', '', '', 'XX-YY-55')),
        ('Manual run by <a href="https://host/path/to/userid">User Name</a>', ('Manual', 'User Name', 'userid', '')),
        ('Manual run by someuser', ('Manual', 'someuser', 'someuser', '')),
        ('Code has changed', ('Commit', '', '', '')),
        ('Scheduled', ('Scheduled', '', '', ''))
    ]

    def test_dummy(self):
        for reason, result in self.reasons:
            assert TriggerReason(reason).tuple == result
