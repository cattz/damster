from damster.utils import initialize_logger, time_to_excel, quoted
from damster.reports.db_query import GenericDB
from atlassian import Crowd

from distutils.dir_util import mkpath

log = initialize_logger(__name__)


class ConfluenceChanges(GenericDB):
    query_changes = """
    SELECT c.contentid,
           c.contenttype,
           c.title,
           c.version,
           c.creationdate,
           c.lastmoddate,
           c.content_status,
           c.spaceid,
           um.username,
           um.lower_username,
           sp.spacekey,
           sp.spacename
    FROM   PUBLIC.content c
    JOIN   PUBLIC.user_mapping um
    ON     c.lastmodifier = um.user_key
    JOIN   PUBLIC.spaces sp
    ON     c.spaceid = sp.spaceid
    WHERE  c.contenttype='PAGE'
    AND    c.content_status = 'current'
        """

    name = 'confluence_changes'

    db_fields = [
        'c_contentid',
        'c_contenttype',
        'c_title',
        'c_version',
        'c_creationdate',
        'c_lastmoddate',
        'c_content_status',
        'c_spaceid',
        'um_username',
        'um_lower_username',
        'sp_spacekey',
        'sp_spancename'
        ]
    additional_fields = [
        'version_diff',
        'excel_created',
        'excel_modified'
    ]

    def __init__(self, cfg, from_date, to_date,
                 db_settings_section='Confluence DB',
                 name='confluence_changes',
                 use_ssh_tunnel=False):
        super(ConfluenceChanges, self).__init__(
            cfg, db_settings_section, name, use_ssh_tunnel=use_ssh_tunnel)
        self.from_date = from_date
        self.to_date = to_date
        self.crowd = Crowd(**cfg['Crowd'])

    def _get_display_name(self, user_id):
        try:
            user_details = self.crowd.user(user_id)
            return user_details['display-name']
        except Exception:
            return user_id

    def __version_change_diff(self, content):
        if content['c_version'] == '1':
            return ''
        url = "{base_url}/pages/diffpagesbyversion.action?" \
              "pageId={page_id}&" \
              "selectedPageVersions={version_number_1}&selectedPageVersions={version_number_2}"

        base_url = self.cfg['Confluence'].get('url', 'http://localhost:8090')
        return url.format(
            base_url=base_url,
            page_id=content['c_contentid'],
            version_number_1=content['c_version'],
            version_number_2=str(int(content['c_version'])-1)
        )

    def generate_report(self):
        time_constraint = "AND c.lastmoddate > CURRENT_DATE - interval '1 days';"
        if self.from_date:
            time_constraint = " AND c.lastmoddate > {}".format(self.from_date)
        if self.to_date:
            time_constraint = time_constraint + " AND c.lastmoddate > {}".format(self.to_date)

        query = self.query_changes + time_constraint
        confluence_changes = self.exec_query(query=query)

        report = list()
        for row in confluence_changes:
            zp = list(zip(self.db_fields, row))
            report_row = {k: str(v) for k, v in zp}
            report_row['version_diff'] = self.__version_change_diff(report_row)
            report_row['excel_created'] = time_to_excel(report_row['c_creationdate'])
            report_row['excel_modified'] = time_to_excel(report_row['c_lastmoddate'])
            report.append(report_row)
        return report

    def save_to_csv(self, output_file=None):
        out_csv = output_file or self.output_file(ext='csv')
        log.info('Saving to CSV file {}'.format(out_csv))
        lines = [','.join(self.db_fields + self.additional_fields)]
        for line in self.report:
            lines.append(','.join([quoted(f) for f in line.values()]))

        mkpath(self.output_folder)
        with open(out_csv, 'w', encoding='utf8') as outfile:
            outfile.write('\n'.join(lines))
