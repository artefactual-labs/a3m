Settings
========

Users can provide settings via the ``/etc/a3m/a3m.conf`` configuration file,
e.g.::

    [a3m]
    debug = False

Environment strings are also supported and they are evaluated last, e.g.::

    env A3M_DEBUG=yes

The full list of environment strings can be found in the
``a3m.settings.common`` module. This module can be customized as needed.

.. literalinclude:: ../a3m/settings/common.py
