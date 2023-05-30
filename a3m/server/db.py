"""
Database related functionality.

This module implements an `auto_close_old_connections` decorator/context manager.
In order to be able to re-use database connections in the Django ORM outside of
the typical request/response cycle, we have to wrap database usage in order to
make sure anything older than CONN_MAX_AGE is cleared.

This is done via the function decorator `auto_close_old_connections()` in most
cases. For some cases (e.g. generator functions) it may be preferable to use it
as a context manager. Note that because of multiple entry points we sometimes
end up entering multiple times; that causes a slight increase in overhead, but
it is much preferred to having an unwrapped function, which may cause errors.

To debug connection timeouts, turn DEBUG on in Django settings, which will log
all SQL queries and allow us to check that all logged queries occur within the
wrapper. Note though, this will result in _very_ verbose logs.
"""
import logging
import threading
import traceback
from contextlib import ContextDecorator
from importlib import import_module
from typing import Any

from django.apps import apps
from django.conf import settings
from django.core.management.sql import emit_post_migrate_signal
from django.core.management.sql import emit_pre_migrate_signal
from django.db import close_old_connections
from django.db import connections
from django.db import DEFAULT_DB_ALIAS
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.state import ModelState
from django.utils.module_loading import module_has_submodule


logger = logging.getLogger(__name__)
thread_locals = threading.local()


class AutoCloseOldConnections(ContextDecorator):
    """
    Decorator to ensure that db connections older than CONN_MAX_AGE are
    closed before execution. Normally, one would close connections after
    execution, but we have some jobs that could run for hours out of
    process, then trigger db access.
    """

    def __enter__(self):
        close_old_connections()
        return self

    def __exit__(self, *exc):
        return False


class DebugAutoCloseOldConnections(AutoCloseOldConnections):
    """
    Debug version of AutoCloseOldConnections; logs warnings with stack traces
    to identify functions that should be wrapped.
    """

    def __enter__(self):
        if not hasattr(thread_locals, "auto_close_connections_depth"):
            thread_locals.auto_close_connections_depth = 0
        thread_locals.auto_close_connections_depth += 1
        logger.debug(
            "Entered auto close connections (depth %s)",
            thread_locals.auto_close_connections_depth,
        )
        return super().__enter__()

    def __exit__(self, *exc):
        thread_locals.auto_close_connections_depth -= 1
        logger.debug(
            "Exited auto close connections (depth %s)",
            thread_locals.auto_close_connections_depth,
        )
        return False


class CheckCloseConnectionsHandler(logging.Handler):
    """A logger that issues warnings when the database is accessed outside
    of an auto_close_old_connections wrapper.
    """

    def emit(self, record):
        if "Entered auto close connections" not in record.getMessage():
            return
        depth = getattr(thread_locals, "auto_close_connections_depth", 0)
        if depth <= 0:
            logging.getLogger("a3m.server").warning(
                "Database access occurred outside of an "
                "auto_close_old_connections context. Depth %d. Traceback %s",
                depth,
                "\n".join(traceback.format_stack()),
            )


def migration_progress_callback(action, migration=None, fake=False):
    if action == "apply_start":
        logger.info("Applying migration %s...", migration)
    elif action == "unapply_start":
        logger.info("Unapplying %s...", migration)
    elif action == "render_start":
        logger.info("Rendering model states...")


def migrate():
    """Migrate the database.

    This is a simplified version of Django's ``migrate`` management command
    that does not require ``management.call_command`` which is not functional
    in the native binary environment.
    """
    # Import the 'management' module within each installed app, to register
    # dispatcher events.
    verbosity = int(settings.DEBUG)
    interactive = False
    for app_config in apps.get_app_configs():
        if module_has_submodule(app_config.module, "management"):
            import_module(".management", app_config.name)

    connection = connections[DEFAULT_DB_ALIAS]
    connection.prepare_database()
    executor = MigrationExecutor(connection, migration_progress_callback)
    executor.loader.check_consistent_history(connection)
    conflicts = executor.loader.detect_conflicts()
    if conflicts:
        raise Exception("Conflicting mgirations detected.")
    targets = executor.loader.graph.leaf_nodes()
    plan = executor.migration_plan(targets)
    pre_migrate_state = executor._create_project_state(with_applied_migrations=True)
    pre_migrate_apps = pre_migrate_state.apps
    emit_pre_migrate_signal(
        verbosity,
        False,
        connection.alias,
        apps=pre_migrate_apps,
        plan=plan,
    )
    post_migrate_state = executor.migrate(
        targets,
        plan=plan,
        state=pre_migrate_state.clone(),
        fake=False,
        fake_initial=False,
    )
    post_migrate_state.clear_delayed_apps_cache()
    post_migrate_apps = post_migrate_state.apps
    with post_migrate_apps.bulk_update():
        model_keys = []
        for model_state in post_migrate_apps.real_models:
            model_key = model_state.app_label, model_state.name_lower
            model_keys.append(model_key)
            post_migrate_apps.unregister_model(*model_key)
    post_migrate_apps.render_multiple(
        [ModelState.from_model(apps.get_model(*model)) for model in model_keys]
    )
    emit_post_migrate_signal(
        verbosity,
        interactive,
        connection.alias,
        apps=post_migrate_apps,
        plan=plan,
    )
    logger.info("Database configured.")


auto_close_old_connections: type[Any]
if settings.DEBUG:
    logger.debug("Using DEBUG auto_close_old_connections")
    auto_close_old_connections = DebugAutoCloseOldConnections

    # Queries are only logged if DEBUG is on.
    db_logger = logging.getLogger(__name__)
    db_logger.setLevel(logging.DEBUG)
    handler = CheckCloseConnectionsHandler(level=logging.DEBUG)
    db_logger.addHandler(handler)
else:
    auto_close_old_connections = AutoCloseOldConnections


__all__ = ("auto_close_old_connections",)
