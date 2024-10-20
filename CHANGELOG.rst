=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_, adapted to reStructuredText and using `PEP 440`_ instead of `Semantic Versioning`_ while still keeping the core major, minor, patch semantics.

.. _Keep a Changelog: https://keepachangelog.com/en/1.1.0/
.. _PEP 440: https://peps.python.org/pep-0440/
.. _Semantic Versioning: https://semver.org/spec/v2.0.0.html

Unreleased
==========

Added
-----

- Added ``/mods`` command that displays information about mods on the server.
- Added player count and player list to ``/controls`` (formerly ``/embed``) embed.
- Added restart button to server controls.
- Added contextual disabling of server control buttons depending on server status and player count.
- Added Bot presence activity status.
- Added emoji to buttons.
- Added ``MAX_WAIT_FOR_ONLINE`` configuration option, for servers that take a long time to start.

- Added event-based system for sending updates in server state from server manager to controller.
- Added controller to handle communication between server manager and view object.

- Added `pm2`_ ecosystem file for launching bot using `pm2`_.

Changed
-------

- Renamed ``/embed`` command to ``/controls`` to make the command more descriptive.
- Switched dependency management to use `Poetry`_.
- Switched from ``shutil.which`` to ``os.access`` to determine if server ``./run.sh`` is executable.
- Cleaned up ``/controls`` embed so that there is only one embed per server by storing previous messages in a database.

Fixed
-----

- ``tmux`` sessions not having the correct permissions to call ``systemd-inhibit`` if used to stop a machine from sleeping while the Minecraft server is running, if the session is created while the Python virtualenv is activated.

Removed
-------

- Removed in-memory store of messages for updating messages.

0.1.0 - 2024-07-14
==================

Added
-----

- ``/embed`` command for bringing up a Discord embed and buttons for managing server.
- Server manager using ``libtmux`` for handling starting and stopping the Minecraft Server.
- View for controls which contain start and stop buttons and server status information in a Discord embed.

.. _Poetry: https://python-poetry.org/
.. _pm2: https://pm2.keymetrics.io/
