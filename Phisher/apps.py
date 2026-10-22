from django.apps import AppConfig
from django.db.backends.signals import connection_created


def _sqlite_pragmas(sender, connection, **kwargs):
    """Make SQLite safe for two containers at once.

    The page and the console are separate processes sharing one file. In
    the default journal mode a writer blocks every reader, so while forty
    students are clicking, opening the console can fail outright with
    "database is locked".

    WAL lets readers carry on while a write is in progress, and
    busy_timeout makes the rare collision wait instead of raising.
    """
    if connection.vendor != 'sqlite':
        return
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA busy_timeout=5000;')


class PhisherConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Phisher'

    def ready(self):
        # Defined at module level and connected with weak=False on purpose.
        # Django signals keep handlers by weak reference, so a function
        # defined inside ready() is garbage-collected the moment ready()
        # returns - it connects, and then silently never fires.
        connection_created.connect(
            _sqlite_pragmas, weak=False, dispatch_uid='phisher_sqlite_pragmas')
