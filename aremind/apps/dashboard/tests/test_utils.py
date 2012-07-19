from datetime import datetime

from django.test import TestCase

from mock import patch

from aremind.apps.dashboard import utils
from aremind.apps.dashboard.management.commands.generate_fake_reports import Command


def generate_pbf_data(count=10):
    "Generate random data for PBF dashboard."
    command = Command()
    reports = map(command.generate_pbf_report, xrange(1, count + 1))
    return map(utils.pbf.process_raw_report, reports)


def make_current_month(report):
    "Forcre report into the current month."
    now = datetime.now()
    report['timestamp'] = now.strftime('%Y-%m-%dT%H:%M:%S')
    report['month'] = now.strftime('%b %Y')
    report['_month'] = now.strftime('%Y-%m')
    return report


class PBFDashboardStatsTestCase(TestCase):
    "Main PBF dashboard stat generation."

    def setUp(self):
        self.load_report_patch = patch('aremind.apps.dashboard.utils.pbf.load_reports')
        self.load_report_mock = self.load_report_patch.start()
        self.load_report_mock.side_effect = generate_pbf_data

    def tearDown(self):
        self.load_report_patch.stop()

    def test_single_month_report(self):
        "Examine output for a single month."
        reports = map(make_current_month, generate_pbf_data())
        self.load_report_mock.side_effect = None
        self.load_report_mock.return_value = reports
        data = utils.pbf.main_dashboard_stats()
        self.assertEqual(len(data), 1)
        stats = data[0]
        self.assertEqual(stats['total'], len(reports))
