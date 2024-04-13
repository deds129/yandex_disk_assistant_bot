from os import environ
from typing import Final


class IntegrationsAccessProvider:
    TG_BOT_TOKEN: Final = environ.get('TG_BOT_TOKEN', 'define me!')
    YA_DISK_CLIENT_TOKEN: Final = environ.get('YA_DISK_CLIENT_TOKEN', 'define me!')
    YA_DISK_CLIENT_ID: Final = environ.get('YA_DISK_CLIENT_ID', 'define me!')
    YA_DISK_CLIENT_SECRET: Final = environ.get('YA_DISK_CLIENT_SECRET', 'define me!')
