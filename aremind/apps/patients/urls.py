from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.patients.views',
    url(r'post$', 'receive_patient_record', name='patient-import'),
    url(r'^create/$', 'create_edit_patient', name='patient-create'),    
    url(r'^(?P<patient_id>\d+)/$', 'create_edit_patient', name='patient-detail'),
    url(r'^onetime/(?P<patient_id>\d+)/$', 'patient_onetime_message', name='patient-onetime-message'),
    url(r'^starttree/(?P<patient_id>\d+)/$', 'patient_start_adherence_tree', name='patient-start-adherence-tree'),
    url(r'^startivr/(?P<patient_id>\d+)/$', 'patient_start_ivr', name='patient-start-ivr'),
    url(r'^$', 'list_patients', name='patient-list'),
)
