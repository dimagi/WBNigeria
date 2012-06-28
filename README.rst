WBNigeria
=======

The RapidSMS WBNigeria project...


Developer Setup
===============

**Prerequisites:**

* A Linux-based development environment including Python 2.6.  Ubuntu 10.04 or
  later is recommended.  At present, Windows-based environments are not
  actively supported.

* PostgreSQL and the appropriate Python bindings (``psycopg2``).  In
  Debian-based distributions, you can install these using ``apt-get``, e.g.::

    sudo apt-get install postgresql python-psycopg2 libpq-dev

* The following additional build dependencies::

    sudo apt-get install libxslt1-dev libxml2-dev mercurial

* CouchDB is required for logging and audit tracking purposes::

    sudo apt-get install couchdb

See
  http://wiki.apache.org/couchdb/Installing_on_Ubuntu
for more information about couch.


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

#. Open http://localhost:8000 in your web browser and you should see an
   **Installation Successful!** screen.

