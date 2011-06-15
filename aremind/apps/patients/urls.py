from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.patients.views',
    url(r'post$', 'receive_patient_record', name='patient-import'),
    url(r'^create/$', 'create_edit_patient', name='patient-create'),    
    url(r'^(?P<patient_id>\d+)/$', 'create_edit_patient', name='patient-detail'),
    url(r'^(?P<patient_id>\d+)/report/$', 'patient_pill_report', name='patient-report'),
    url(r'^(?P<patient_id>\d+)/report/add/$', 'create_edit_pill_history', name='patient-add-pill-history'),
    url(r'^(?P<patient_id>\d+)/report/edit/(?P<pill_id>\d+)/$', 'create_edit_pill_history', name='patient-edit-pill-history'),
    url(r'^onetime/(?P<patient_id>\d+)/$', 'patient_onetime_message', name='patient-onetime-message'),
    url(r'^starttree/(?P<patient_id>\d+)/$', 'patient_start_adherence_tree', name='patient-start-adherence-tree'),
    url(r'^startivr/(?P<patient_id>\d+)/$', 'patient_start_ivr', name='patient-start-ivr'),
    url(r'^ivrcallback/(?P<patient_id>\d+)/$', 'patient_ivr_callback', name='patient-ivr-callback'),
    url(r'^ivrcomplete/(?P<patient_id>\d+)$', 'patient_ivr_complete', name='patient-ivr-complete'),
    url(r'^$', 'list_patients', name='patient-list'),
)
