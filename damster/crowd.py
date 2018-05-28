"""Memoize version of the Crowd user API"""
from atlassian import Crowd as CrowdNotMemoized
try:
    from functools import lru_cache
except ImportError:
    from backports.functools_lru_cache import lru_cache


class Crowd(CrowdNotMemoized):
    def __init__(self, url, username, password, timeout=60, api_root='rest', api_version='latest'):
        super(Crowd, self).__init__(url, username, password, timeout, api_root, api_version)

    @lru_cache(maxsize=500)
    def user(self, user_id):
        return super(Crowd, self).user(username=user_id)
