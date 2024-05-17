from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from bot.api.yandex_disk_service import client

code_url = client.get_auth_url("code")
auth_url = client.get_auth_url("token")

main_login_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Войти используя код", url=f"{code_url}"),
        ],
        [
            InlineKeyboardButton(text="Войти используя токен", url=f"{auth_url}")
        ],
        [
            InlineKeyboardButton(text="Ввести код", callback_data="request_code")
        ]
    ]
)

try_again_input_code = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Ввести код", callback_data="request_code")
        ]
    ]
)

to_start_need_to_auth = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Войти используя код", url=f"{code_url}"),
            InlineKeyboardButton(text="Войти используя токен", url=f"{auth_url}")
        ]
    ]
)

edit_save_path = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Изменить место сохранения", callback_data="change_save_path")
        ]
    ]
)
