Settings
========

Users can provide service settings via the ``/etc/a3m/a3m.conf`` configuration
file, e.g.::

    [a3m]
    debug = False

Environment strings are also supported and they are evaluated last, e.g.::

    env A3M_DEBUG=yes a3m ...

Configuration settings are not properly described yet, but here's the list:

* ``debug`` (boolean)
* ``batch_size`` (int)
* ``concurrent_packages`` (int)
* ``rpc_threads`` (int)
* ``worker_threads`` (int)
* ``shared_directory`` (string)
* ``temp_directory`` (string)
* ``processing_directory`` (string)
* ``rejected_directory`` (string)
* ``capture_client_script_output`` (boolean)
* ``removable_files`` (string)
* ``secret_key`` (string)
* ``prometheus_bind_address`` (string)
* ``prometheus_bind_port`` (string)
* ``time_zone`` (string)
* ``clamav_server`` (string)
* ``clamav_pass_by_stream`` (boolean)
* ``clamav_client_timeout`` (float)
* ``clamav_client_backend`` (string)
* ``clamav_client_max_file_size`` (float)
* ``clamav_client_max_scan_size`` (float)
* ``virus_scanning_enabled`` (boolean)
* ``db_engine`` (string)
* ``db_name`` (string)
* ``db_user`` (string)
* ``db_password`` (string)
* ``db_host`` (string)
* ``db_port`` (string)
* ``rpc_bind_address`` (string)
* ``s3_enabled`` (boolean)
* ``s3_endpoint_url`` (string)
* ``s3_region_name`` (string)
* ``s3_access_key_id`` (string)
* ``s3_secret_access_key`` (string)
* ``s3_use_ssl`` (boolean)
* ``s3_addressing_style`` (string)
* ``s3_signature_version`` (string)
* ``s3_bucket`` (string)

For greater flexibility, it is also possible to alter the applicatin settings
module manually. This is how our :mod:`a3m.settings.common` module looks like:

.. literalinclude:: ../a3m/settings/common.py
