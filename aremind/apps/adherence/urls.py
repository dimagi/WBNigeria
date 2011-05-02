from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.adherence.views',
    url(r'^$', 'dashboard', name='adherence-dashboard'),
)
