import importlib
import logging


log = logging.getLogger(__name__)

_BASE_MODULENAME = 'ddtrace.contrib'

# Default set of modules to automatically patch or not
DEFAULT_INTEGRATIONS = {
    'aiobotocore': True,
    'aiohttp': True,  # requires asyncio (Python 3.4+)
    'aiopg': True,
    'asyncio': False,
    'boto': True,
    'botocore': True,
    'bottle': True,
    'cassandra': True,
    'celery': True,
    'django': True,
    'elasticsearch': True,
    'falcon': True,
    'futures': False,
    'grpc': True,
    'httplib': True,
    'jinja2': True,
    'mongoengine': True,
    'mysql': True,
    'mysqldb': True,
    'pymysql': True,
    'psycopg': True,
    'pylibmc': True,
    'pylons': True,
    'pymemcache': True,
    'pymongo': True,
    'pyramid': True,
    'redis': True,
    'requests': True,
    'sqlalchemy': True,
    'sqlite3': True,
    'vertica': True,

    # Ignore some web framework integrations that might be configured explicitly in code
    "flask": False,
}

class InstallException(Exception):
    pass


def integration_modname(intname, basemodname=None):
    basemodname = basemodname or _BASE_MODULENAME
    return '{}.{}'.format(basemodname, intname)


def install_all(overrides={}, raise_errors=False):
    """
    Installs all default enabled integrations allowing the defaults to be
    overridden.

    :param overrides: particular integrations to override
    :type overrides: dict
    :param raise_errors: whether or not to raise errors when they occur
    :type raise_errors: bool
    """
    integrations_to_install = DEFAULT_INTEGRATIONS.copy()
    integrations_to_install.update(overrides)

    for integration, enabled in integrations_to_install.items():
        if not enabled:
            log.info(
                'install: skipping disabled integration {}'.format(integration)
            )
            continue
        install(integration, raise_errors)


def install(integration, raise_errors=False):
    """Installs an integration using its ``patch()`` function.

    :param integration: the integration to install
    :type integration: str
    :param raise_errors: whether or not to raise errors if they occur
    :type raise_errors: bool
    """
    intmodname = integration_modname(integration)

    try:
        intmod = importlib.import_module(intmodname)
    except ImportError:
        log_msg = 'install: integration {} not found'.format(integration)
        if raise_errors:
            raise InstallException(log_msg)
        else:
            log.error(log_msg)
            return

    if not hasattr(intmod, 'patch'):
        log.error(
            'install: integration {} does not have patch '
            'attribute'.format(integration))
        return

    intmod.patch()


def patch_all(**integrations):
    """Patch all default enabled integrations.

    :param **integrations: override default enabled integrations.
    :type integrations: dict

    To patch all the default enabled integrations::

        patch_all()

    To patch all the default enabled integrations, but override specific ones::

        patch_all(redis=False, futures=True)
    """
    install_all(overrides=integrations, raise_errors=False)


def patch(raise_errors=True, **integrations):
    """Patch specified integrations.

    :param raise_errors: whether or not to raise errors if they occur
    :type raise_errors: bool

    :param **integrations: integrations to patch.
    :type integrations: dict

    To patch a particular integration::

        patch(celery=True)
    """
    integrations_to_install = [i for i, enabled in integrations.items() if enabled]
    for integration in integrations_to_install:
        install(integration, raise_errors=raise_errors)