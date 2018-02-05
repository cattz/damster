import re


class TriggerReason(object):
    """
    Parses Bamboo trigger reason strings
    Examples of possible buildReason string:
    Child of <a href="https://.../FHS-FHSADP-55">FHS-FHSADP-55</a>
    Manual run by <a href="https://...">Davila Freire, Xabier</a>
    Manual run by someuser
    Code has changed
    Scheduled
    """

    manual = re.compile(
        r'Manual run by (?:<a href="http[s]?:\/\/[^"]*\/(?P<user_id>.*)">)?(?P<user_name>[^<]*)(?:<\/a>)?')
    child = re.compile(
        r'Child\s+of\s+<a href="http[s]?:\/\/[^"]*">(?P<parent_plan>.*)<\/a>')
    source = re.compile(
        r'Changes\s+by\s+(?:<a href="http[s]?:\/\/[^=]*=(?P<user_id>.*)">)?(?P<user_name>[^<]*)(?:<\/a>)?'
    )
    rebuilt = re.compile(
        r'Rebuilt\s+by\s+(?:<a href="http[s]?:\/\/[^"]*\/(?P<user_id>.*)">)?(?P<user_name>[^<]*)(?:<\/a>)?'
    )

    def __init__(self, msg):

        self.msg = msg
        self.trigger_type, self.user_id, self.user_name, self.build_key = self.parse()

    def parse(self):
        if self.msg.startswith('Code has changed'):
            return 'Commit', '', '', ''

        if self.msg.startswith('Scheduled'):
            return 'Scheduled', '', '', ''

        found = re.search(self.manual, self.msg)
        if found:
            user_id = found.group('user_id') or found.group('user_name')
            return 'Manual', user_id, found.group('user_name'), ''

        found = re.search(self.child, self.msg)
        if found:
            return 'Child', '', '', found.group('parent_plan')

        found = re.search(self.source, self.msg)
        if found:
            user_id = found.group('user_id') or found.group('user_name')
            return 'Commit', user_id,  found.group('user_name'), ''

        found = re.search(self.rebuilt, self.msg)
        if found:
            user_id = found.group('user_id') or found.group('user_name')
            return 'Rebuilt', user_id,  found.group('user_name'), ''

        else:
            raise ValueError('No regex matching: {}'.format(self.msg))

    @property
    def tuple(self):
        return self.trigger_type, self.user_name, self.user_id, self.build_key

    @property
    def dict(self):
        return dict(
            type=self.trigger_type,
            user_name=self.user_name,
            user_id=self.user_id,
            build=self.build_key
        )
