from django import forms

from aremind.apps.dashboard import models


class ReportCommentForm(forms.ModelForm):
    class Meta:
        model = models.ReportComment
