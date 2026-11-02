import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Вставь свой токен сюда или настрой через Environment Variables на Render
BOT_TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН_ОТ_BOTFATHER")
# ID администратора (куда будут приходить заявки на запись). Узнай свой ID через @userinfobot
ADMIN_ID = int(os.getenv("ADMIN_ID", "ТВОЙ_TELEGRAM_ID"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# Состояния для машины состояний (FSM) при записи
class BookingState(StatesGroup):
  waiting_for_service = State()
  waiting_for_name = State()
  waiting_for_phone = State()


# Услуги салона
SERVICES = {
    "haircut": {"name": "✂️ Мужская стрижка", "price": "70 PLN", "time": "45 мин"},
    "beard": {"name": "🧔 Оформление бороды", "price": "50 PLN", "time": "30 мин"},
    (
        "complex"
    ): {"name": "🔥 Комплекс (Стрижка + Борода)", "price": "110 PLN", "time": "1 ч 15 мин"},
    "styling": {"name": "💈 Укладка и уход", "price": "40 PLN", "time": "20 мин"},
}


# Главное меню (инлайн-кнопки)
def get_main_menu():
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="📋 Услуги и цены", callback_data="services")],
          [InlineKeyboardButton(text="📅 Записаться онлайн", callback_data="book")],
          [
              InlineKeyboardButton(
                  text="📍 Как нас найти (Kraków)", callback_data="location"
              )
          ],
          [InlineKeyboardButton(text="📞 Связаться с нами", callback_data="contact")],
      ]
  )
  return keyboard


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  await message.answer(
      f"Привет, {message.from_user.first_name}! 👋\n\n"
      "Добро пожаловать в наш барбершоп/салон в Кракове.\n"
      "Выберите интересующий вас раздел в меню ниже:",
      reply_markup=get_main_menu(),
  )


# Кнопка: Услуги и цены
@dp.callback_query(F.data == "services")
async def show_services(callback: types.CallbackQuery):
  text = "📋 **Наши услуги и стоимость:**\n\n"
  for key, data in SERVICES.items():
    text += f"• **{data['name']}**\n  💵 Цена: {data['price']} | ⏱ Длительность: {data['time']}\n\n"

  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="📅 Записаться", callback_data="book")],
          [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_home")],
      ]
  )
  await callback.message.edit_text(
      text, reply_markup=keyboard, parse_mode="Markdown"
  )
  await callback.answer()


# Кнопка: Локация
@dp.callback_query(F.data == "location")
async def show_location(callback: types.CallbackQuery):
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_home")]
      ]
  )
  await callback.message.edit_text(
      "📍 **Мы находимся в Кракове:**\n"
      "ul. Floriańska 15, Kraków\n\n"
      "Работаем ежедневно с 9:00 до 20:00.\n"
      "Ждем вас в гости! ☕️",
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await callback.answer()


# Кнопка: Контакты
@dp.callback_query(F.data == "contact")
async def show_contact(callback: types.CallbackQuery):
  keyboard = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="back_home")]
      ]
  )
  await callback.message.edit_text(
      "📞 **Связаться с администратором:**\n\n"
      "Телефон: +48 123 456 789\n"
      "Telegram: @admin_salon\n"
      "Или просто напишите в этот чат!",
      reply_markup=keyboard,
      parse_mode="Markdown",
  )
  await callback.answer()


# Кнопка: Назад в главное меню
@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
  await callback.message.edit_text(
      "Главное меню:", reply_markup=get_main_menu()
  )
  await callback.answer()


# --- ПРОЦЕСС ЗАПИСИ (FSM) ---
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
  await callback.message.edit_text(
      "Выберите услугу для записи:", reply_markup=keyboard
  )
  await state.set_state(BookingState.waiting_for_service)
  await callback.answer()


@dp.callback_query(
    BookingState.waiting_for_service, F.data.startswith("srv_")
)
async def process_service(callback: types.CallbackQuery, state: FSMContext):
  service_key = callback.data.split("_")[1]
  await state.update_data(chosen_service=SERVICES[service_key]["name"])

  await callback.message.edit_text(
      "Отличный выбор! ✨\n\nТеперь введите **ваше имя и фамилию**:"
  )
  await state.set_state(BookingState.waiting_for_name)
  await callback.answer()


@dp.message(BookingState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
  await state.update_data(client_name=message.text)
  await message.answer(
      "Принято! 📱\n\nТеперь отправьте **ваш номер телефона** для связи:"
  )
  await state.set_state(BookingState.waiting_for_phone)


@dp.message(BookingState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
  user_data = await state.get_data()
  client_phone = message.text
  client_name = user_data.get("client_name")
  chosen_service = user_data.get("chosen_service")

  # Текст клиенту
  await message.answer(
      "🎉 **Спасибо за запись!**\n\n"
      f"Услуга: {chosen_service}\n"
      f"Имя: {client_name}\n"
      f"Телефон: {client_phone}\n\n"
      "Администратор свяжется с вами в ближайшее время для подтверждения времени! 🕒",
      reply_markup=get_main_menu(),
      parse_mode="Markdown",
  )

  # Отправка уведомления администратору
  admin_text = (
      "🚨 **НОВАЯ ЗАЯВКА НА ЗАПИСЬ!** 🚨\n\n"
      f"📌 Услуга: {chosen_service}\n"
      f"👤 Клиент: {client_name}\n"
      f"📞 Телефон: {client_phone}\n"
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
