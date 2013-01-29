WBNigeria
=========

The RapidSMS WBNigeria project...


Developer Setup
===============

**Prerequisites:**

* A Linux-based development environment including Python 2.6.  Ubuntu 10.04 or
  later is recommended.  At present, Windows-based environments are not
  actively supported.

* PostgreSQL and the appropriate Python bindings (``psycopg2``).  In
  Debian-based distributions, you can install these using ``apt-get``, e.g.::

    sudo apt-get install postgresql libpq-dev

* The following additional build dependencies::

    sudo apt-get install libxslt1-dev libxml2-dev mercurial

* CouchDB is required for logging and audit tracking purposes. See
  http://wiki.apache.org/couchdb/Installing_on_Ubuntu for more information about CouchDB::

    sudo apt-get install couchdb

* Jython is required for the Touchforms player::

    wget http://sourceforge.net/projects/jython/files/jython/2.5.2/jython_installer-2.5.2.jar
    sudo java -jar jython_installer-2.5.2.jar
    # Default answers. Target directory /usr/local/lib/jython
    sudo ln -s /usr/local/lib/jython/bin/jython /usr/local/bin/

* Install pip and virtualenv, and make sure virtualenv is up to date, e.g.::

    easy_install pip
    pip install -U virtualenv
    pip install -U virtualenvwrapper


**To setup a local development environment, follow these steps:**

#. Clone the code from Github:

    git clone git@github.com:dimagi/WBNigeria.git

#. Create a Python virtual environment for this project::

    mkvirtualenv --distribute wbnigeria
    workon wbnigeria

#. Install the project dependencies into the virtual environment::

    ./bootstrap.py

#. Create local settings file and initialize a development database::

    cp localsettings.py.example localsettings.py
    createdb wbnigeria
    ./manage.py syncdb

#. Update the submodules::

    git submodule init
    git submodule update

#. In a terminal, start the Django development server::

    ./manage.py runserver

#. In another terminal, start the XForms player::

    cd submodules/touchforms/touchforms/backend/
    jython xformserver.py 4444

#. Open http://localhost:8000 in your web browser and you should see an
   **Installation Successful!** screen.

Bootstrapping Data
==================

.. code-block::

    python manage.py loaddata locations_data.json
    python manage.py loaddata sites_data.json
    python manage.py loaddata flat_forms.json
    upload xforms in forms/ in 'Decision Tree XForms' tab
    python manage.py populate_sites
    python manage.py import_users apps/web_users/fixtures/user_import.sample.csv
    python manage.py loaddata flatpages.json

Generating Report Data
======================

For testing purposes you can generate random data for the report dashboards::

    python manage.py generate_fake_reports --all

This will generated 1000 reports per dashboard as defined by the ``DASHBOARD_SAMPLE_DATA``
setting. See `python manage.py help generate_fake_reports` for additional options.

