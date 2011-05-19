from django.contrib import admin

from aremind.apps.wisepill import models as wisepill

admin.site.register(wisepill.WisepillMessage)
