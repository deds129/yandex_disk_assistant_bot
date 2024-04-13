import io

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.api.yandex_disk_service import login_via_code, login_via_token, create_default_dir, client, DEFAULT_DIR_NAME
from bot.keyboards import inline, reply
from bot.misc import IntegrationsAccessProvider
from bot.misc.states import BotStates

bot = Bot(token=IntegrationsAccessProvider.TG_BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot=bot, storage=MemoryStorage())

buf = io.BytesIO()

@dp.message(CommandStart())
async def start(message: Message, ) -> None:
    await message.answer(f'Привет!👋🏻\n'
                         f'Я бот-помощник для работы с Яндекс.Диск\n'
                         f'Я сохраню на Диск все, что ты мне пришлешь. \n\n'
                         f'Для того, чтобы начать работу с ботом необходимо пройти Аутентификацию\n'
                         f'После аутентификации ты получишь код,'
                         f'который мне необходимо ввести, вызвав команду "Ввести код"'
                         , parse_mode='HTML', reply_markup=inline.main_login_inline_keyboard)


@dp.callback_query(F.data == 'request_code')
async def request_code(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите код:")
    await state.set_state(BotStates.input_code)


@dp.message(BotStates.input_code)
async def get_code(message: Message, state: FSMContext) -> None:
    args_data = message.text
    if args_data:
        code = args_data.strip()
        if code.isdigit():
            await code_login(code, message, state)
        else:
            await token_login(code, message, state)
    else:
        await state.clear()
        await message.answer("Данные не были введены!")


@dp.message(BotStates.ready_to_work, F.photo)
async def download_photo(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.ready_to_work)
    download_photo_msg = await message.answer("Скачиваю фото...")
    file_name = f"{message.chat.username}_{message.date}".replace(' ', '_')
    file = await bot.download(
        message.photo[-1],
        destination=buf
    )
    await client.upload(file, f"{DEFAULT_DIR_NAME}/{file_name}")

    await download_photo_msg.edit_text("Фото успешно загружено на Диск!")


@dp.message(BotStates.ready_to_work)
async def default_message(message: Message, state: FSMContext) -> None:
    await message.answer("Не могу обработать твое сообщение :(")


@dp.message()
async def default_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Чтобы начать со мной работу, нужно пройти аутентификацию",
                         reply_markup=inline.main_login_inline_keyboard)


async def token_login(code, message, state):
    try:
        is_success_login = await login_via_token(code=code)
        if is_success_login:
            await state.set_state(BotStates.ready_to_work)
            await message.answer('Аутентификация прошла успешно!\n'
                                 'Все готово к работе!\n'
                                 'Я буду сохранять все, что ты мне отправишь в папку '
                                 '<a href="https://disk.yandex.ru/client/disk/from_bot">from_bot</a>'
                                 ' на твоем диске',
                                 parse_mode='HTML')
            await create_default_dir()
        else:
            await state.clear()
            await message.answer("Аутентификация не увенчалась успехом, попробуйте снова!",
                                 reply_markup=inline.try_again_input_code)
    except:
        await state.clear()
        await message.answer("Непредвиденная ошибка, попробуйте снова!",
                             reply_markup=inline.try_again_input_code)


async def code_login(code, message, state):
    try:
        is_success_login = await login_via_code(code=code)
        if is_success_login:
            await state.set_state(BotStates.ready_to_work)
            await message.answer("Аутентификация прошла успешно!"
                                 "Я создам папку на твоем ")
        else:
            await state.clear()
            await message.answer("Аутентификация не увенчалась успехом, попробуйте снова!",
                                 reply_markup=inline.try_again_input_code)
    except:
        await state.clear()
        await message.answer("Непредвиденная ошибка, попробуйте снова!",
                             reply_markup=inline.try_again_input_code)


async def start_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
