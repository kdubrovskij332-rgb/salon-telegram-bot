import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Токен твоего бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "9043205849:AAEDqmIJVkY8CvhonTjP-T-vwYDOIgRxB-8")

# Твой личный Telegram ID (уведомления о бронях будут прилетать прямо тебе!)
ADMIN_ID = int(os.getenv("ADMIN_ID", "1029773942"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# Состояния для пошаговой записи (FSM)
class BookingState(StatesGroup):
  waiting_for_service = State()
  waiting_for_name = State()
  waiting_for_phone = State()


# Список услуг и прайс-лист студии
SERVICES = {
    "recording": {
        "name": "🎙 Запись вокала / инструментов",
        "price": "80 PLN / час",
        "time": "1 час",
    },
    "mixing": {
        "name": "🎛 Сведение и мастеринг",
        "price": "200 PLN",
        "time": "за трек",
    },
    "rehearsal": {
        "name": "🎸 Репетиционная точка",
        "price": "50 PLN / час",
        "time": "1 час",
    },
    "beatmaking": {
        "name": "🎹 Создание бита / аранжировка",
        "price": "от 300 PLN",
        "time": "индивидуально",
    },
}


# Главное меню бота (кнопки)
def get_main_menu():
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="📋 Услуги и цены", callback_data="services")],
          [
              InlineKeyboardButton(
                  text="📅 Забронировать время", callback_data="book"
              )
          ],
          [
              InlineKeyboardButton(
                  text="📍 Где мы находимся (Kraków)", callback_data="location"
              )
          ],
          [
              InlineKeyboardButton(
                  text="📞 Связаться с нами", callback_data="contact"
              )
          ],
      ]
  )
  return keyboard


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  await message.answer(
      f"Йоу, {message.from_user.first_name}! 🎧\n\n"
      "Добро пожаловать в **SaloDlaM
