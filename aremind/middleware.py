from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.conf import settings

ADMIN_ONLY_APPS = ('smscouchforms', 'xforms', 'smsforms')

# don't use this code as a role model

class AccessControlMiddleware:
    def process_request(self, request):
        url = request.path_info.lstrip('/')
        user = request.user
        if not user.is_superuser and any(url.startswith(prefix + '/') for prefix in ADMIN_ONLY_APPS):
            return self.access_denied()
        if url.startswith('dashboard/pbf') and not user.has_perm('dashboard.pbf_view'):
            return self.access_denied()
        if url.startswith('dashboard/fadama') and not user.has_perm('dashboard.fadama_view'):
            return self.access_denied()

    def access_denied(self):
        return HttpResponseRedirect('/')
