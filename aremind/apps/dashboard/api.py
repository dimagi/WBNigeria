from tastypie.resources import ModelResource
from tastypie.authentication import BasicAuthentication
from .models import PBFReport, ReportComment

class JsonDefaultModelResource(ModelResource):
    def determine_format(self, request):
        return 'application/json'

class PBFReportResource(JsonDefaultModelResource):
    class Meta:
        allowed_methods = ['get']
        authentication = BasicAuthentication()
        queryset = PBFReport.objects.all()
        resource_name = 'pbfreport'

class ReportCommentResource(JsonDefaultModelResource):
    class Meta:
        allowed_methods = ['get']
        authentication = BasicAuthentication()
        queryset = ReportComment.objects.all()
        resource_name = 'reportcomment'
