from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required


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
