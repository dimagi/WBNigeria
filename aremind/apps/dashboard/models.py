from django.db import models


class ReportComment(models.Model):
    INQUIRY_TYPE = 'inquiry'
    NOTE_TYPE = 'note'
    REPLY_TYPE = 'response'

    COMMENT_TYPES = (
        (INQUIRY_TYPE, INQUIRY_TYPE),
        (NOTE_TYPE, NOTE_TYPE),
        (REPLY_TYPE, REPLY_TYPE),
    )

    report_id = models.IntegerField()
    comment_type = models.CharField(max_length=50, choices=COMMENT_TYPES)
    author = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    text = models.TextField()

    def json(self):
        return {
            'text': self.text,
            'date_fmt': self.date.strftime('%d/%m/%Y %H:%M'),
            'author': self.author,
            'report_id': self.report_id,
            'type': self.comment_type,
        }

