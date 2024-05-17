import io
import tempfile

import yadisk
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.api.yandex_disk_service import login_via_code, login_via_token, create_save_dir, client, DEFAULT_DIR_NAME
from bot.keyboards import inline
from bot.misc import IntegrationsAccessProvider
from bot.misc.states import BotStates

bot = Bot(token=IntegrationsAccessProvider.TG_BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot=bot, storage=MemoryStorage())
save_dir = DEFAULT_DIR_NAME

buf = io.BytesIO()

@dp.message(CommandStart())
async def start(message: Message, ) -> None:
    await message.answer(f'Привет!👋🏻\n'
                         f'Я бот-помощник для работы с Яндекс.Диск\n'
                         f'Я сохраню на Диск все, что ты мне пришлешь. \n\n',
                         parse_mode="HTML")
    await message.answer(f'Для того чтобы начать работу с ботом необходимо пройти аутентификацию',
                         parse_mode='HTML',
                         reply_markup=inline.main_login_inline_keyboard)


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


@dp.callback_query(F.data == 'change_save_path')
async def change_save_path(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("Введите путь для сохранения файлов:")
    await state.set_state(BotStates.change_save_dir)


@dp.message(BotStates.change_save_dir)
async def change_save_dir(message: Message, state: FSMContext) -> None:
    args_data = message.text.strip()
    global save_dir
    try:
        await create_save_dir(save_path=args_data)
        await message.answer("Файлы будут сохрняться в следующей папке:\n"
                             f"<a href='https://disk.yandex.ru/client/disk/{args_data}'>{args_data}</a>",
                             parse_mode="HTML")
        save_dir = args_data
    except yadisk.exceptions.YaDiskError:
        await message.answer("Не удалось найти/создать папку для сохранения!",
                             reply_markup=inline.edit_save_path)
    await state.set_state(BotStates.ready_to_work)


@dp.message(BotStates.ready_to_work, F.photo)
async def download_photo(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.ready_to_work)
    download_photo_msg = await message.answer("Скачиваю фото...")
    msg_datetime = message.date.strftime('%m-%d-%y %H:%M:%S')
    file_name = f"picture_{message.chat.username}_{msg_datetime}".replace(' ', '_')
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            await bot.download(
                message.photo[-1],
                destination=temp_file.name,
                timeout=120
            )
            temp_file.flush()

            await client.upload(temp_file.name, f"{save_dir}/{file_name}.jpg")
            await download_photo_msg.edit_text("Фото успешно загружено на Диск!")
        except yadisk.exceptions.YaDiskError as e:
            await download_photo_msg.edit_text(
                "Пока что не удалось сохранить файл на диск! Возможно он будет загружен позже\n"
                f"{str(e)}")
        except Exception as e:
            await download_photo_msg.edit_text(f"Ошибка при скачивании фото: {str(e)}")
        finally:
            temp_file.close()


@dp.message(BotStates.ready_to_work, F.video)
async def download_video(message: Message, state: FSMContext) -> None:
    await state.set_state(BotStates.ready_to_work)
    download_video_msg = await message.answer("Скачиваю видео...")
    msg_datetime = message.date.strftime('%m-%d-%y %H:%M:%S')
    file_name = f"video_{message.chat.username}_{msg_datetime}".replace(' ', '_')
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            # Скачиваем видео во временный файл
            await bot.download(
                file=message.video,
                destination=temp_file.name,
                timeout=600
            )
            temp_file.flush()  # Обязательно сбросить буфер на диск

            # Загружаем файл на Яндекс.Диск
            await client.upload(temp_file.name, f"{save_dir}/{file_name}.mp4")
            await download_video_msg.edit_text("Видео успешно загружено на Диск!")
        except yadisk.exceptions.YaDiskError as e:
            await download_video_msg.edit_text("Пока что не удалось сохранить файл на диск! Возможно он будет загружен позже\n"
                                               f"{str(e)}")
        except Exception as e:
            await download_video_msg.edit_text(f"Ошибка при скачивании видео: {str(e)}")
        finally:
            temp_file.close()

@dp.message(BotStates.ready_to_work)
async def default_message(message: Message, state: FSMContext) -> None:
    await message.answer("Пока что я не умею обрабатывать такие сообщения :(")


@dp.message()
async def default_message(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Чтобы начать со мной, нужно пройти аутентификацию",
                         reply_markup=inline.main_login_inline_keyboard)


async def token_login(code, message, state):
    try:
        is_success_login = await login_via_token(code=code)
        if is_success_login:
            await state.set_state(BotStates.ready_to_work)
            await create_save_dir(save_path=DEFAULT_DIR_NAME)
            await message.answer('Аутентификация прошла успешно!\n'
                                 'Все готово к работе!\n'
                                 ' По умолчанию, я сохраняю все, что ты мне отправишь в папку '
                                 '<a href="https://disk.yandex.ru/client/disk/from_bot">from_bot</a>'
                                 ' на твоем диске.',
                                 reply_markup=inline.edit_save_path,
                                 parse_mode='HTML')
        else:
            await state.clear()
            await message.answer("Аутентификация не увенчалась успехом, попробуйте снова!",
                                 reply_markup=inline.try_again_input_code)
    except yadisk.exceptions.YaDiskError as e:
        await state.clear()
        await message.answer(f"Ошибка при аутентификации, попробуйте снова!\n",
                             e.error_type,
                             reply_markup=inline.try_again_input_code)
    except Exception as e:
        await state.clear()
        await message.answer(f"Непредвиденная ошибка: {str(e)}")


async def code_login(code, message, state):
    try:
        is_success_login = await login_via_code(code=code)
        if is_success_login:
            await state.set_state(BotStates.ready_to_work)
            await message.answer('Аутентификация прошла успешно!\n'
                                 'Все готово к работе!\n'
                                 ' По умолчанию, я сохраняю все, что ты мне отправишь в папку '
                                 '<a href="https://disk.yandex.ru/client/disk/from_bot">from_bot</a>'
                                 ' на твоем диске.',
                                 reply_markup=inline.change_save_path,
                                 parse_mode='HTML')
        else:
            await state.clear()
            await message.answer("Аутентификация не увенчалась успехом, попробуйте снова!",
                                 reply_markup=inline.try_again_input_code)
    except yadisk.exceptions.YaDiskError as e:
        await state.clear()
        await message.answer(f"Ошибка при аутентификации, попробуйте снова!\n",
                             e.error_type,
                             reply_markup=inline.try_again_input_code)
    except Exception as e:
        await state.clear()
        await message.answer(f"Непредвиденная ошибка: {str(e)}")


async def start_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
