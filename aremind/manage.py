#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import sys, os
from os.path import exists, join
from django.core.management import execute_manager


# use a default settings module if none was specified on the command line
DEFAULT_SETTINGS = 'aremind.localsettings'
DEFAULT_TEST_SETTINGS = 'aremind.test_localsettings'
settings_specified = any([arg.startswith('--settings=') for arg in sys.argv])
if not settings_specified and len(sys.argv) >= 2:
    if sys.argv[1] == 'test':
        settings = DEFAULT_TEST_SETTINGS
    else:
        settings = DEFAULT_SETTINGS
    if 'RAPIDSMS_SETTINGS' in os.environ:
        settings = os.environ['RAPIDSMS_SETTINGS']
    sys.argv.append('--settings=%s' % settings)
    print "NOTICE: using default settings module '%s'" % settings    

if __name__ == "__main__":
    # all imports should begin with the full Python package ('aremind.'):
    project_root = os.path.abspath(os.path.dirname(__file__))
    # TODO: rename all apps.* imports to aremind.apps.*
    # if project_root in sys.path:
    #     sys.path.remove(project_root)
    sys.path.insert(0, os.path.dirname(project_root))
    sys.path.append(os.path.abspath(os.path.join(project_root,'..','submodules','rapidsms','lib')))

    from aremind import settings
    execute_manager(settings)

