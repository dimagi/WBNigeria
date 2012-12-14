import json

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required

from aremind.apps.dashboard.models import ReportComment
from aremind.apps.dashboard.utils import shared as u


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


class AuditMixin(object):

    @method_decorator(permission_required('auth.supervisor'))
    def dispatch(self, request, *args, **kwargs):
        return super(AuditMixin, self).dispatch(request, *args, **kwargs)

    def get_observed_users(self):
        "Return users overseen in the region/state."
        supervisor = self.request.user
        try:
            contact = supervisor.contact_set.all()[0]
        except IndexError:
            return []
        # Check for dashboard view permission?
        users = User.objects.all()
        if contact.location_id and contact.location.type.slug == 'state':
            users = users.filter(contact__location=contact.location).distinct()
        return users

    def get_user_actions(self, **kwargs):
        "Get actions taken by observed users."
        users = self.get_observed_users()
        comments = ReportComment.objects.filter(author_user__in=users).order_by('-date')
        return {'users': users, 'comments': comments}
