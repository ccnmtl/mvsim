This is the Millennium Village Simulation project, or MVSim, a
teaching tool to help students appreciate the complexity of meeting
the [Millennium Development
Goals](http://mvsim.wikischolars.columbia.edu/Millennium+Development+Goals)
in a rural African setting, and to experience the interdisciplinary
nature of sustainable development.  The web-based game has been
developed and hosted by Columbia University's [Center for New Media
Teaching and Learning](http://ccnmtl.columbia.edu) and can be accessed
at
[http://mvsim.ccnmtl.columbia.edu](http://mvsim.ccnmtl.columbia.edu).

Installation
============

The source code ships with bundled versions of all its Python module
dependencies, and a bootstrap script that installs all of the
dependencies in a virtualenv.  Installation is simple:

$ git clone git://github.com/ccnmtl/mvsim.git
$ cd mvsim
$ ./bootstrap.py

Note that Python 2.6 is currently required.

Edit the `settings_shared.py` file to suit your needs (don't forget to
create a database, or change the settings to use SQLite) and then
sync the database schema and necessary initial content:

$ ./manage.py syncdb

You're now ready to run the server.  Sample Apache/mod_wsgi
configuration files are available in the `apache` subdirectory of the
source code.

If you're running this outside of Columbia University, you'll want to
remove `djangowind` (which connects the Django auth to Columbia's central
identify/sign-in mechanism) and modify the
`COURSEAFFILS_COURSESTRING_MAPPER` setting; the default setting
creates course groupings, and associates users with courses, based on
Columbia course-strings and affiliations.
