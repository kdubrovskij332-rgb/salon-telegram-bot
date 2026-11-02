import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Твой токен бота (уже вставлен!)
BOT_TOKEN = os.getenv("BOT_TOKEN", "9043205849:AAEDqmIJVkY8CvhonTjP-T-vwYDOIgRxB-8")
# Твой ID администратора (сюда будут падать заявки на запись/аренду). Если захочешь, потом поменяешь.
ADMIN_ID = int(os.getenv("ADMIN_ID", "707572793")) # можешь заменить на свой числовой ID из @userinfobot

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# Состояния для записи
class BookingState(StatesGroup):
  waiting_for_service = State()
  waiting_for_name = State()
  waiting_for_phone = State()


# Услуги / Направления студии
SERVICES = {
    "recording": {"name": "🎙 Запись вокала / инструментов", "price": "80 PLN / час", "time": "1 час"},
    "mixing": {"name": "🎛 Сведение и мастеринг", "price": "200 PLN", "time": "за трек"},
    "rehearsal": {"name": "🎸 Репетиционная точка", "price": "50 PLN / час", "time": "1 час"},
    "beatmaking": {"name": "🎹 Создание бита / аранжировка", "price": "от 300 PLN", "time": "индивидуально"},
}


# Главное меню
def get_main_menu():
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="📋 Услуги и цены", callback_data="services")],
          [InlineKeyboardButton(text="📅 Забронировать время", callback_data="book")],
          [InlineKeyboardButton(text="📍 Где мы находимся (Kraków)", callback_data="location")],
          [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="contact")],
      ]
  )
  return keyboard


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  await message.answer(
      f"Йоу, {message.from_user.first_name}! 🎧\n\n"
      "Добро пожаловать в **SaloDlaMuzikow** — творческое пространство в Кракове.\n"
      "Выбери нужный раздел в меню ниже:",
      reply_markup=get_main_menu(),
      parse_mode="Markdown"
  )


# Услуги и цены
@dp.callback_query(F.data == "services")
async def show_services(callback: types.CallbackQuery):
  text = "📋 **Наши услуги и прайс:**\n\n"
  for key, data in SERVICES.items():
    text += f"• **{data['name']}**\n  💵 {data['price']} | ⏱ {data['time']}\n\n"

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="📅 Забронировать", callback_data="book")],
          [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_home")],
      ]
  )
  await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
  await callback.answer()


# Локация
@dp.callback_query(F.data == "location")
async def show_location(callback: types.CallbackQuery):
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_home")]
      ]
  )
  await callback.message.edit_text(
      "📍 **Наша точка в Кракове:**\n"
      "ul. Zabłocie 20, Kraków\n\n"
      "Уютная студия, качественный звук, чай/кофе и хорошая атмосфера для музыкантов. 🎸",
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await callback.answer()


# Контакты
@dp.callback_query(F.data == "contact")
async def show_contact(callback: types.CallbackQuery):
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_home")]
      ]
  )
  await callback.message.edit_text(
      "📞 **Связь с администратором:**\n\n"
      "Телефон / WhatsApp: +48 123 456 789\n"
      "Telegram: @salodlamuzikow_admin\n"
      "Или пиши прямо сюда!",
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await callback.answer()


# Возврат в меню
@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
  await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu())
  await callback.answer()


# --- ПРОЦЕСС БРОНИРОВАНИЯ ---
@dp.callback_query(F.data == "book")
async def start_booking(callback: types.CallbackQuery, state: FSMContext):
  keyboard_buttons = []
  for key, data in SERVICES.items():
    keyboard_buttons.append(
        [InlineKeyboardButton(text=data["name"], callback_data=f"srv_{key}")]
    )
  keyboard_buttons.append(
      [InlineKeyboardButton(text="◀️ Отмена", callback_data="back_home")]
  )

  keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
  await callback.message.edit_text("Выбери услугу для бронирования:", reply_markup=keyboard)
  await state.set_state(BookingState.waiting_for_service)
  await callback.answer()


@dp.callback_query(BookingState.waiting_for_service, F.data.startswith("srv_"))
async def process_service(callback: types.CallbackQuery, state: FSMContext):
  service_key = callback.data.split("_")[1]
  await state.update_data(chosen_service=SERVICES[service_key]["name"])

  await callback.message.edit_text(
      "Отличный выбор! 🎵\n\nТеперь напиши **свое имя или псевдоним**:"
  )
  await state.set_state(BookingState.waiting_for_name)
  await callback.answer()


@dp.message(BookingState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
  await state.update_data(client_name=message.text)
  await message.answer(
      "Принято! 📱\n\nТеперь отправь **номер телефона** (или удобный способ связи):"
  )
  await state.set_state(BookingState.waiting_for_phone)


@dp.message(BookingState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  client_phone = message.text
  client_name = user_data.get("client_name")
  chosen_service = user_data.get("chosen_service")

  # Подтверждение клиенту
  await message.answer(
      "🔥 **Заявка принята!**\n\n"
      f"Услуга: {chosen_service}\n"
      f"Имя/Ник: {client_name}\n"
      f"Контакт: {client_phone}\n\n"
      "Администратор скоро свяжется с тобой для подтверждения времени и деталей! 🕒",
      reply_markup=get_main_menu(),
      parse_mode="Markdown",
  )

  # Уведомление админу
  admin_text = (
      "🚨 **НОВАЯ БРОНЬ В СТУДИИ!** 🚨\n\n"
      f"📌 Услуга: {chosen_service}\n"
      f"👤 Клиент: {client_name}\n"
      f"📞 Связь: {client_phone}\n"
      f"💬 Юзернейм: @{message.from_user.username if message.from_user.username else 'нет'}"
  )
  try:
    await bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
  except Exception as e:
    logging.error(f"Не удалось отправить уведомление админу: {e}")

  await state.clear()


async def main():
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
