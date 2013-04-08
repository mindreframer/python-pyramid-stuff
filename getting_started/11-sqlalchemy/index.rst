==============================
11: Databases Using SQLAlchemy
==============================

Our Pyramid-based wiki application now needs database-backed storage of
pages. This frequently means a SQL database. The Pyramid community
strongly supports the SQLAlchemy object-relational mapper (ORM) as a
convenient, Pythonic way to interface to databases.

In this step we hook up SQLAlchemy to a SQLite database table.

Objectives
==========

- Store pages in SQLite by using SQLAlchemy models

- Use SQLAlchemy queries to list/add/view/edit/delete pages

- Provide a database-initialize command by writing a Pyramid *console
  script* which can be run from the command line

.. note::

    The ``alchemy`` scaffold is really helpful for getting a
    SQLAlchemy project going, including generation of the console
    script. Since we want to see all the decisions,
    we will forgo convenience in this tutorial and wire it up ourselves.

Steps To Initialize Database
============================

.. warning::

    To make sure that your Python can reach your SQLite library
    correctly, please make sure the following succeeds:

    .. code-block:: bash

        $ python3.3
        Python 3.3.0 (default, Mar  8 2013, 15:50:47)
        [GCC 4.2.1 Compatible Apple Clang 4.0 ((tags/Apple/clang-421.0.60))] on darwin
        Type "help", "copyright", "credits" or "license" for more information.
        >>> from sqlite3 import *
        >>>

#. As before, let's use the previous package as a starting point for
   a new distribution. Also, let's install the dependencies required
   for a SQLAlchemy-oriented Pyramid application and make a directory
   for the console script:

   .. code-block:: bash

    (env33)$ cd ..; cp -r step10 step11; cd step11
    (env33)$ easy_install-3.3 sqlalchemy pyramid_tm zope.sqlalchemy

   .. note::

     We aren't yet doing ``python3.3 setup.py develop`` as we
     are changing it later.

#. Our configuration file at ``development.ini`` wires together some
   new pieces:

   .. literalinclude:: development.ini
    :language: ini

#. This engine configuration now needs to be read into the application
   through changes in ``tutorial/__init__.py``:

   .. literalinclude:: tutorial/__init__.py
    :linenos:

#. We need a command-line script for initializing the database. Enter
   the following to initialize ``tutorial/scripts/__init__.py``:

   .. literalinclude:: tutorial/scripts/__init__.py

#. Now enter our console script at
   ``tutorial/scripts/initializedb.py``:

   .. literalinclude:: tutorial/scripts/initializedb.py

#. To wire up this new console script, our ``setup.py`` needs an entry
   point:

   .. literalinclude:: setup.py

#. Since ``setup.py`` changed, we now run it:

   .. code-block:: bash

    (env33)$ python3.3 setup.py develop

#. The script references some models in ``tutorial/models.py``:

   .. literalinclude:: tutorial/models.py
    :linenos:

#. Let's run this console script, thus producing our database and table:

   .. code-block:: bash

    (env33)$ initialize_tutorial_db development.ini
    2013-03-12 10:13:56,972 INFO  [sqlalchemy.engine.base.Engine][MainThread] PRAGMA table_info("wikipages")
    2013-03-12 10:13:56,972 INFO  [sqlalchemy.engine.base.Engine][MainThread] ()
    2013-03-12 10:13:56,974 INFO  [sqlalchemy.engine.base.Engine][MainThread]
    CREATE TABLE wikipages (
        id INTEGER NOT NULL,
        title TEXT,
        body TEXT,
        PRIMARY KEY (id),
        UNIQUE (title)
    )


    2013-03-12 10:13:56,974 INFO  [sqlalchemy.engine.base.Engine][MainThread] ()
    2013-03-12 10:13:56,977 INFO  [sqlalchemy.engine.base.Engine][MainThread] COMMIT
    2013-03-12 10:13:56,981 INFO  [sqlalchemy.engine.base.Engine][MainThread] BEGIN (implicit)
    2013-03-12 10:13:56,983 INFO  [sqlalchemy.engine.base.Engine][MainThread] INSERT INTO wikipages (title, body) VALUES (?, ?)
    2013-03-12 10:13:56,983 INFO  [sqlalchemy.engine.base.Engine][MainThread] ('Root', '<p>Root</p>')
    2013-03-12 10:13:56,985 INFO  [sqlalchemy.engine.base.Engine][MainThread] COMMIT

Application Steps
=================

#. With our data now driven by SQLAlchemy queries,
   we need to update our ``tutorial/views.py``:

   .. literalinclude:: tutorial/views.py

#. The introduction of a relational database means significant changes
   in our ``tutorial/tests.py``:

   .. literalinclude:: tutorial/tests.py

#. Run the tests in your package using ``nose``:

   .. code-block:: bash

    (env33)$ nosetests .
    ..
    -----------------------------------------------------------------
    Ran 2 tests in 1.971s

    OK

#. Run the WSGI application:

   .. code-block:: bash

    (env33)$ pserve development.ini --reload

#. Open ``http://127.0.0.1:6547/`` in your browser.

Analysis
========

Let's start with the dependencies. We made the decision to use
``SQLAlchemy`` to talk to our database. We also, though, installed
``pyramid_tm`` and ``zope.sqlalchemy``. Why?

Pyramid has a strong orientation towards support for ``transactions``.
Specifically, you can install a transaction manager into your app
application, either as middleware or a Pyramid "tween". Then,
just before you return the response, all transaction-aware parts of
your application are executed.

This means Pyramid view code usually doesn't manage transactions. If
your view code or a template generates an error, the transaction manager
aborts the transaction. This is a very liberating way to write code.

The ``pyramid_tm`` package provides a "tween" that is configured in the
``development.ini`` configuration file. That installs it. We then need
a package that makes SQLAlchemy and thus the RDBMS transaction manager
integrate with the Pyramid transaction manager. That's what
``zope.sqlalchemy`` does.

Where do we point at the location on disk for the SQLite file? In the
configuration file. This lets consumers of our package change the
location in a safe (non-code) way. That is, in configuration. This
configuration-oriented approach isn't required in Pyramid; you can
still make such statements in your ``__init__.py`` or some companion
module.

The ``initializedb`` is a nice example of framework support. You point
your setup at the location of some ``[console_scripts]`` and these get
generated into your virtualenv's ``bin`` directory. Our console script
follows the pattern of being fed a configuration file with all the
bootstrapping. It then opens SQLAlchemy and creates the root of the
wiki, which also makes the SQLite file. Note the
``with transaction.manager`` part that puts the work in the scope of a
transaction (as we aren't inside a web request where this is done
automatically.)

The ``models.py`` does a little bit extra work to hook up SQLAlchemy
into the Pyramid transaction manager. It then declares the model for a
``Page``.

Our views have changes primarily around replacing our dummy
dictionary-of-dictionaries data with proper database support: list the
rows, add a row, edit a row, and delete a row.

Extra Credit
============

#. Why all this code? Why can't I just type 2 lines have magic ensue?