|pypi| |license| |pyvers| |tests| |coverage|

What is a3m?
------------

*a3m* is a lightweight version of Archivematica focused on AIP creation. It has
neither external dependencies, integration with access sytems, search
capabilities nor a graphical interface.

All functionality is made available as a `gRPC <https://grpc.io/docs/>`_ service
with a minimal set of methods and strongly typed messages. a3m can be executed
as a standalone process or be embedded as part of your application.

For more documentation, please see https://a3m.readthedocs.io.

----------

**a3m is a proof of concept. Please send us your feedback!**

.. |pypi| image:: https://img.shields.io/pypi/v/a3m.svg
   :target: https://pypi.python.org/pypi/a3m

.. |license| image:: https://img.shields.io/pypi/l/a3m.svg
   :target: https://github.com/artefactual-labs/a3m

.. |pyvers| image:: https://img.shields.io/pypi/pyversions/a3m.svg
   :target: https://pypi.python.org/pypi/a3m

.. |tests| image:: https://github.com/artefactual-labs/a3m/workflows/Tests/badge.svg
   :target: https://github.com/artefactual-labs/a3m/actions?query=workflow%3ATests

.. |coverage| image:: https://img.shields.io/codecov/c/github/artefactual-labs/a3m
   :target:  https://codecov.io/gh/artefactual-labs/a3m
