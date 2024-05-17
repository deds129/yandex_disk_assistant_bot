import yadisk

from bot.misc import IntegrationsAccessProvider

DEFAULT_DIR_NAME = "/from_bot"

client = yadisk.AsyncClient(secret=IntegrationsAccessProvider.YA_DISK_CLIENT_SECRET,
                            id=IntegrationsAccessProvider.YA_DISK_CLIENT_ID)


async def login_via_token(*, code: str) -> bool:
    client.token = code
    return await client.check_token()


async def login_via_code(*, code: str) -> bool:
    try:
        response = await client.get_token(code)
        if response is None:
            return False
    except yadisk.exceptions.BadRequestError:
        return False
    client.token = response.access_token
    return await client.check_token()


async def create_save_dir(*, save_path: str):
    if not await client.exists(save_path):
        await client.mkdir(save_path)
