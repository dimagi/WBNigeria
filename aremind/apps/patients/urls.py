from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.patients.views',
    url(r'post$', 'receive_patient_record', name='patient-import'),
    url(r'^create/$', 'create_edit_patient', name='patient-create'),    
    url(r'^(?P<patient_id>\d+)/$', 'create_edit_patient', name='patient-detail'),
    url(r'^onetime/(?P<patient_id>\d+)/$', 'patient_onetime_message', name='patient-onetime-message'),
    url(r'^$', 'list_patients', name='patient-list'),
)
