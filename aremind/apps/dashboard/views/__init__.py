import os
import json

from django.http import HttpResponse

from pbf import *
from fadama import *


def load_test_data(request):
    filename = request.GET.get('filename', None)

    if filename and month:
        testfile = os.path.abspath(
            os.path.join(os.path.dirname(__file__), 'data', '%s' % filename)
        )

        with open(testfile, 'r') as f:
            data = f.read()
            return HttpResponse(json.dumps(data),
                content_type='application/json')

    return HttpResponse(json.dumps('{}'), content_type='application/json')
