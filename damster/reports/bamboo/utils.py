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
        r'Child of <a href="http[s]?:\/\/[^"]*">(?P<parent_plan>.*)<\/a>')

    def __init__(self, msg):

        self.msg = msg
        self.trigger_type = None  # Commit, Scheduled, Manual, Child
        self.user_id = None
        self.user_name = None
        self.build_key = None

        self.parse()

    def parse(self):
        if self.msg.startswith('Code has changed'):
            self.trigger_type = 'Commit'
            self.user_id = self.user_name = self.build_key = ''
        elif self.msg.startswith('Scheduled'):
            self.trigger_type = 'Scheduled'
            self.user_id = self.user_name = self.build_key = ''
        else:
            found = re.search(self.manual, self.msg)
            if found:
                self.trigger_type = 'Manual'
                self.user_name = found.group('user_name')
                self.user_id = found.group('user_id') or self.user_name
                self.build_key = ''
            else:
                found = re.search(self.child, self.msg)
                if found:
                    self.trigger_type = 'Child'
                    self.user_id = self.user_name = ''
                    self.build_key = found.group('parent_plan')
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
