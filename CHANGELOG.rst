=========
Changelog
=========

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog`_, adapted to reStructuredText, and this project adheres to `Semantic Versioning`.

.. _Keep a Changelog: https://keepachangelog.com/en/1.1.0/
.. _Semantic Versioning: https://semver.org/spec/v2.0.0.html

Unreleased
==========

Added
-----

- Add ``/mods`` command that displays information about mods on the server.
- Add Bot presence activity status.
- Add emoji to buttons.

- Add `pm2`_ ecosystem file for launching bot using `pm2`_.

Changed
-------

- Renamed ``/embed`` command to ``/controls`` to make the command more descriptive.
- Switch from `shutil.which` to `os.access` to determine if server `./run.sh` is executable.
- Switch dependency management to use `Poetry`_.
- Use controller to handle communication between server manager and view object.
- Clean up ``/controls`` embed so that there is only one embed per server by storing previous messages in a database.

Removed
-------

- In-memory store of messages for updating messages.

0.1.0 - 2024-07-14
==================

Added
-----

- ``/embed`` command for bringing up a Discord embed and buttons for managing server.
- Server manager using ``libtmux`` for handling starting and stopping the Minecraft Server.
- View for controls which contain start and stop buttons and server status information in a Discord embed.

.. _Poetry: https://python-poetry.org/
.. _pm2: https://pm2.keymetrics.io/
