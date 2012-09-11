import json

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from apps.dashboard.utils import shared as u

class LoginMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginMixin, self).dispatch(request, *args, **kwargs)


class ReportMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ReportMixin, self).get_context_data(**kwargs)
        context['default_site'] = kwargs.get('site')
        context['default_metric'] = kwargs.get('metric')
        return context


class APIMixin(object):
    def get_user_state(self):
        """return state for logged-in user, None for national user (or mis-configured)"""
        return u.get_user_state(self.request.user)

    def get(self, request, *args, **kwargs):
        _site = request.GET.get('site')
        site = int(_site) if _site else None
        user = request.user

        payload = self.get_payload(site=site, user=user)
        return HttpResponse(json.dumps(payload), mimetype='application/json')
