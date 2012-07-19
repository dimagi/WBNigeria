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

    def tearDown(self):
        self.load_report_patch.stop()

    def test_single_month_report(self):
        "Examine output for a single month."
        reports = map(make_current_month, generate_pbf_data())
        self.load_report_mock.return_value = reports
        data = utils.pbf.main_dashboard_stats()
        self.assertEqual(len(data), 1)
        stats = data[0]
        self.assertEqual(stats['total'], len(reports))

    def test_multi_month_report(self):
        "All reports should be accounted for in one of the months."
        reports = generate_pbf_data(20)
        self.load_report_mock.return_value = reports
        data = utils.pbf.main_dashboard_stats()
        self.assertEqual(sum(map(lambda s: s['total'], data)), 20)

    def test_satifaction_single_month(self):
        "Simplified test for satification reporting. All reports in current month."
        reports = map(make_current_month, generate_pbf_data())
        self.load_report_mock.return_value = reports
        stats = utils.pbf.main_dashboard_stats()[0]
        manual_count_satified = len(filter(lambda x: x['satisfied'], reports))
        manual_count_not_satified = len(filter(lambda x: not x['satisfied'], reports))
        self.assertEqual(stats['satisfaction'][True], manual_count_satified)
        self.assertEqual(stats['satisfaction'][False], manual_count_not_satified)

    def test_satifaction_multi_month(self):
        "More complex test for satification reporting."
        reports = generate_pbf_data(20)
        self.load_report_mock.return_value = reports
        stats = utils.pbf.main_dashboard_stats()
        for month in stats:
            # Check manual count vs reported count
            manual_count_satified = len(filter(lambda x: x['satisfied'] and x['month'] == month['month'], reports))
            manual_count_not_satified = len(filter(lambda x: not x['satisfied'] and x['month'] == month['month'], reports))
            satified = month['satisfaction'][True]
            not_satified = month['satisfaction'][False]
            self.assertEqual(satified, manual_count_satified)
            self.assertEqual(not_satified, manual_count_not_satified)
            self.assertEqual(month['total'], not_satified + satified)

