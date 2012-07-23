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
    "Force report into the current month."
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

    def test_category_single_month(self):
        "Simplified test for category reporting. All reports in current month."
        reports = map(make_current_month, generate_pbf_data())
        self.load_report_mock.return_value = reports
        stats = utils.pbf.main_dashboard_stats()[0]['by_category']
        for category, value in stats.iteritems():
            manual_count = len(filter(lambda x: x[category], reports))
            self.assertEqual(value, manual_count)

    def test_category_multi_month(self):
        "Category reporting with multiple months of data."
        reports = generate_pbf_data(20)
        self.load_report_mock.return_value = reports
        stats = utils.pbf.main_dashboard_stats()
        for month in stats:
            for category, value in month['by_category'].iteritems():
                manual_count = len(filter(lambda x: x[category] and x['month'] == month['month'], reports))
                self.assertEqual(value, manual_count)

    def test_by_clinic_single_month(self):
        "Count reports by clinic. Single month only."
        reports = map(make_current_month, generate_pbf_data())
        self.load_report_mock.return_value = reports
        stats = utils.pbf.main_dashboard_stats()[0]['by_clinic']
        for clinic, value in stats:
            manual_count = len(filter(lambda x: x['facility'] == clinic['id'], reports))
            self.assertEqual(value, manual_count)

    def test_by_clinic_multi_month(self):
        "Count reports by clinic."
        reports = generate_pbf_data(20)
        self.load_report_mock.return_value = reports
        stats = utils.pbf.main_dashboard_stats()
        for month in stats:
            for clinic, value in month['by_clinic']:
                manual_count = len(filter(lambda x: x['facility'] == clinic['id'] and x['month'] == month['month'], reports))
                self.assertEqual(value, manual_count)


class PBFDetailStatsTestCase(TestCase):
    "Detailed info on a given PBF facility."

    def setUp(self):
        self.load_report_patch = patch('aremind.apps.dashboard.utils.pbf.load_reports')
        self.load_report_mock = self.load_report_patch.start()

    def tearDown(self):
        self.load_report_patch.stop()

    def test_basic_totals(self):
        "Monthly totals for message for a given facility."
        reports = generate_pbf_data(20)
        self.load_report_mock.return_value = reports
        stats = utils.pbf.detail_stats(1)
        for month in stats:
            manual_count = len(filter(lambda x: x['facility'] == 1 and x['month'] == month['month'], reports))
            self.assertEqual(month['total'], manual_count)

    def test_category_totals(self):
        "Monthly category totals for message for a given facility."
        reports = generate_pbf_data(20)
        self.load_report_mock.return_value = reports
        stats = utils.pbf.detail_stats(1)
        categories = ('satisfied', 'staff_friendliness', 'price_display',
                      'drug_availability', 'cleanliness', )
        for month in stats:
            for category in categories:
                manual_postivite_count = len(filter(lambda x: x[category] and x['facility'] == 1 and x['month'] == month['month'], reports))
                manual_negative_count = len(filter(lambda x: not x[category] and x['facility'] == 1 and x['month'] == month['month'], reports))
                self.assertEqual(month['stats'][category][True], manual_postivite_count)
                self.assertEqual(month['stats'][category][False], manual_negative_count)

    def test_wait_time_totals(self):
        "Wait bucket totals for a given facility."
        reports = generate_pbf_data(20)
        self.load_report_mock.return_value = reports
        stats = utils.pbf.detail_stats(1)
        for month in stats:
            for threshold, label in utils.pbf.WAIT_BUCKETS:
                manual_count = len(filter(lambda x: x['wait_bucket'] == label and x['facility'] == 1 and x['month'] == month['month'], reports))
                self.assertEqual(month['stats']['wait_bucket'][label], manual_count)

    def test_unfiltered_stats(self):
        "Passing None for the facility will return unfiltered stats."
        reports = generate_pbf_data(20)
        self.load_report_mock.return_value = reports
        stats = utils.pbf.detail_stats(None)
        for month in stats:
            manual_count = len(filter(lambda x: x['month'] == month['month'], reports))
            self.assertEqual(month['total'], manual_count)
