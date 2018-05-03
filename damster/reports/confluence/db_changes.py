from damster.utils import initialize_logger, time_to_excel, quoted
from damster.reports.db_query import GenericDB
from atlassian import Crowd
from functools import lru_cache
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
               c.prevver,
               um.username,
               sp.spacekey,
               sp.spacename
        FROM   PUBLIC.content c
        JOIN   PUBLIC.user_mapping um
        ON     c.lastmodifier = um.user_key
        LEFT JOIN   PUBLIC.spaces sp
        ON     c.spaceid = sp.spaceid
        WHERE  c.contenttype ='PAGE'
        /*AND    c.content_status = 'current'*/
        {time_constraint}
        ORDER BY sp.spacename, c.title, c.lastmoddate
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
        'c_prevver',
        'um_username',
        'sp_spacekey',
        'sp_spacename'
        ]
    additional_fields = [
        'version_diff',
        'excel_created',
        'excel_modified',
        'user_name'
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

    @lru_cache(maxsize=50)
    def _get_space_info_for_draft(self, prevver):
        query = """
        SELECT sp.spacekey,
               sp.spacename,
               sp.spaceid
        FROM   PUBLIC.spaces sp
               JOIN PUBLIC.content c
                 ON c.spaceid = sp.spaceid
        WHERE  c.contentid = {prevver}
        """.format(prevver=prevver)
        if prevver:
            return self.exec_query(query=query)[0]
        return None, None, None

    def _get_display_name(self, user_id):
        try:
            user_details = self.crowd.user(user_id)
            return user_details['display-name']
        except Exception:
            return user_id

    def __version_change_diff(self, content):
        base_url = self.cfg['Confluence'].get('url', 'http://localhost:8090')
        if content['c_version'] == '1':
            url = '{base_url}/pages/?pageId={page_id}'
        else:
            url = "{base_url}/pages/diffpagesbyversion.action?" \
                  "pageId={page_id}&" \
                  "selectedPageVersions={version_number_1}&selectedPageVersions={version_number_2}"
        return url.format(
            base_url=base_url,
            page_id=content['c_contentid'],
            version_number_1=content['c_version'],
            version_number_2=str(int(content['c_version'])-1)
        )

    def generate_report(self):
        time_constraint = "AND c.lastmoddate > CURRENT_DATE - interval '1 months'"
        if self.from_date:
            time_constraint = " AND c.lastmoddate > {}".format(self.from_date)
        if self.to_date:
            time_constraint = time_constraint + " AND c.lastmoddate > {}".format(self.to_date)

        query = self.query_changes.format(time_constraint=time_constraint)
        confluence_changes = self.exec_query(query=query)

        report = list()
        for row in confluence_changes:
            zp = list(zip(self.db_fields, row))
            report_row = {k: str(v) for k, v in zp}
            report_row['version_diff'] = self.__version_change_diff(report_row)
            report_row['excel_created'] = time_to_excel(report_row['c_creationdate'])
            report_row['excel_modified'] = time_to_excel(report_row['c_lastmoddate'])
            report_row['user_name'] = self._get_display_name(report_row['um_username'])
            log.debug(report_row)
            if report_row['sp_spacekey'] == 'None':
                space_key, space_name, space_id = self._get_space_info_for_draft(report_row['c_prevver'])
                report_row['sp_spacekey'] = space_key
                report_row['sp_spacename'] = space_name
                report_row['c_spaceid'] = space_id
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
