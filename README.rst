minecraft-server-bot
=======================

A Discord bot for remotely managing a Minecraft server.

Setup
-----

#. This bot uses `tmux`_ to run your server in the background, and `PostgreSQL`_ to record messages sent by the bot so that information can be persisted between bot restarts, so make sure these are installed first.
#. Python packages are managed by `poetry`_, and you're highly encouraged to use `venv`_ or `virtualenv`_ when you install packages for this project. 

   Install the packages using::

    poetry install

#. Copy ``.env_template`` to ``.env`` to set configuration options::

    cp .env{_template,}

   The following configuration options are **required**:

   - ``BOT_TOKEN`` is the token for your bot on Discord. Refer to the `Discord documentation`_ for more information.

   The following configuration options are **optional**:

   - ``SERVER_PATH`` is the directory where the server will be run from. By default this is ``~/minecraft_server``.
   - ``EXECUTABLE_FILE`` is the name of the script that will be executed to run your server, relative to ```SERVER_PATH``. The simplest form is to just run the server by calling ``java``::

         java -Xmx2G -jar server.jar nogui

     Make sure that the server command line can be accessed while this script is running. By default, this is ``./run.sh``

   - ``SESSION_NAME`` is the name of the ``tmux``` session that the bot will use to manage the session. If the name is blank, or not set then the default is ``minecraft_server``.
   - ``DATABASE_NAME`` is the name of the database on will be used by the bot. By default this is ``minecraft_server_bot``.

#. Create the database with the name under the ``DATABASE_NAME`` key in your configuration.


Usage
-----

First, run the migrations to update your database schema::

    aerich upgrade

Then you can run the bot by executing ``main.py``::

    ./main.py

Changelog
---------

See `CHANGELOG.rst`.

Licence
-------

Refer to `LICENSE`_ for the full licence text.

.. _tmux: https://github.com/tmux/tmux
.. _PostgreSQL: https://www.postgresql.org/
.. _poetry: https://python-poetry.org
.. _venv: https://docs.python.org/3/library/venv.html
.. _virtualenv: https://virtualenv.pypa.io/en/latest/
.. _Discord documentation: https://discord.com/developers/
.. _LICENSE: LICENSE
.. _CHANGELOG.rst: CHANGELOG.rst
