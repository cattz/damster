from damster.utils import initialize_logger
import arrow
from distutils.dir_util import mkpath
import os
import json

log = initialize_logger(__name__)


class BaseReport(object):

    def __init__(self, cfg, from_date, to_date=None, name='base_report'):

        self.name = name
        self.cfg = cfg
        self.time_zone = cfg['Common']['time_zone']
        self.from_date = arrow.get(from_date).replace(tzinfo=self.time_zone)
        self.to_date = arrow.get(to_date).replace(tzinfo=self.time_zone) \
            if to_date else arrow.utcnow().to(self.time_zone)
        self._report = None
        # self.bamboo = Bamboo(**cfg['Bamboo'])

    @property
    def output_folder(self):
        return os.path.join(
            self.cfg['Reports']['destination_folder'],
            self.name,
            '{}__{}'.format(self.from_date.format('YYYY-MM-DD'), self.to_date.format('YYYY-MM-DD'))
        )

    @property
    def report(self):
        if not self._report:
            self._report = self.generate_report()
        return self._report

    def output_file(self, ext='json'):
        return os.path.join(
            self.output_folder,
            '{}.{}'.format(self.name, ext)
        )

    def save_to_json(self):
        out_json = self.output_file()
        log.info('Saving to JSON: {}'.format(out_json))
        mkpath(self.output_folder)
        with open(out_json, 'w', encoding='utf8') as outfile:
            json.dump(self.report, outfile)

    def generate_report(self):
        return self._report  # This will be overridden

    def run_report(self, use_cache=True):
        if not (os.path.isfile(self.output_file()) and use_cache):
            self.generate_report()
            self.save_to_json()
        else:
            self._report = json.load(open(self.output_file()))

    def _long_time_to_epoch(self, tm):
        """
        Converts long epoch (from Bamboo deployments timestamps) into 'normal' epoch
        and sets to current time zone
        :param tm: long
        :return: arrow time object
        """
        return arrow.get(tm / 1000).to(self.time_zone)

    def _time_to_string(self, tm, fmt='YYYY-MM-DD HH:mm:ss'):
        """
        Converts arrow time to string
        :param tm: arrow time object
        :param fmt: format string
        :return: string with formatted time
        """
        if tm:
            return tm.to(self.time_zone).format(fmt)
        return tm
