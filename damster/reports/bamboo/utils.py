from damster.utils import initialize_logger
try:
    from urllib import unquote  # Python 2.X
except ImportError:
    from urllib.parse import unquote  # Python 3+
import re

log = initialize_logger(__name__)


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
        r'Manual run (?:.+?(?=by))?by\s*(?:<a href="http[s]?:\/\/[^"]*\/(?P<user_id>.*)">)?'
        r'(?P<user_name>[^<]*)(?:<\/a>)?$')
    child = re.compile(
        r'(?:Child\s+of\s+|Triggered\s+by\s+)<a href="http[s]?:\/\/[^"]*">(?P<parent_plan>.*)<\/a>')
    source = re.compile(
        r'Changes\s+by\s+(?:<a href="http[s]?:\/\/[^=]*=(?P<user_id>.*)">)?(?P<user_name>[^<]*)(?:<\/a>)?'
    )
    rebuilt = re.compile(
        r'Rebuilt\s+by\s+(?:<a href="http[s]?:\/\/[^"]*\/(?P<user_id>.*)">)?(?P<user_name>[^<]*)(?:<\/a>)?'
    )
    custom_build = re.compile(
        r'^Custom build by (?P<user_id>[^&]+).*$'
    )

    def __init__(self, msg):

        self.msg = unquote(msg)
        self.trigger_type, self.user_id, self.user_name, self.build_key = self.parse()

    def parse(self):
        if self.msg.startswith('Code has changed') or self.msg.startswith('Code changes detected'):
            return 'Commit', '', '', ''

        if self.msg.startswith('Scheduled'):
            return 'Scheduled', '', '', ''

        if self.msg.startswith('First build for this plan'):
            return 'First build', '', '', ''

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

        found = re.search(self.custom_build, self.msg)
        if found:
            user_id = found.group('user_id')
            return 'Manual', user_id, user_id, ''

        else:
            log.error('No regex matching: {}'.format(self.msg))
            # raise ValueError('No regex matching: {}'.format(self.msg))
            return '', '', '', ''

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
