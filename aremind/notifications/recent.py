from alerts import Alert

from aremind.apps.dashboard.models import FadamaReportVisibility, PBFReportVisibility


class RecentActivity(object):
    """
    Generates a program-specific alert summarizing how many new reports have
    been received.
    """

    def __init__(self, slug, visibility, *args, **kwargs):
        super(RecentActivity, self).__init__(*args, **kwargs)
        self.slug = slug  # 'pbf' or 'fadama'
        self.visibility = visibility  # Visibility object to query

    def __call__(self, request, context, *args, **kwargs):
        """Generates an alert if there are any unviewed reports."""
        if context['program'] == self.slug:
            unviewed = self.visibility.objects.filter(user=request.user).count()
            if unviewed:
                verb = 'has' if unviewed == 1 else 'have'
                noun = 'report' if unviewed == 1 else 'reports'
                msg = 'There {0} been {1} new {2} since you last viewed '\
                      'the report log.'.format(verb, unviewed, noun)
                yield Alert(msg)


recent_fadama_activity = RecentActivity('fadama', FadamaReportVisibility)

recent_pbf_activity = RecentActivity('pbf', PBFReportVisibility)
