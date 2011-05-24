from django.conf.urls.defaults import *


urlpatterns = patterns('aremind.apps.wisepill.views',
  url(r'^/$', 'index', name='wisepill-index'),
  url(r'^list_messages/(?P<patient_id>\d+)/$', 'list_messages_for_patient', name='wisepill-list-messages-for-patient'),
  url(r'^fake_messages/(?P<patient_id>\d+)/$', 'make_fake_message', name='wisepill-fake-message'),
)
