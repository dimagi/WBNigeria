from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.patients.views',
    url(r'post$', 'receive_patient_record', name='patient-import'),
    url(r'^(?P<patient_id>\d+)/$', 'view_patient', name='patient-detail'),
    url(r'^$', 'list_patients', name='patient-list'),
)
