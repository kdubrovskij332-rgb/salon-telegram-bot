import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

BOT_TOKEN = os.getenv("BOT_TOKEN", "9043205849:AAEDqmIJVkY8CvhonTjP-T-vwYDOIgRxB-8")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1029773942"))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


class BookingState(StatesGroup):
  waiting_for_service = State()
  waiting_for_name = State()
  waiting_for_phone = State()


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


def get_main_menu():
  return InlineKeyboardMarkup(
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


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
  text = "Йоу! 🎧\nДобро пожаловать в SaloDlaMuzikow в Кракове.\nВыбери раздел:"
  await message.answer(text, reply_markup=get_main_menu())


@dp.callback_query(F.data == "services")
async def show_services(callback: types.CallbackQuery):
  text = "📋 Наши услуги:\n\n"
  for key, data in SERVICES.items():
    text += f"• {data['name']}\n  💵 {data['price']} | ⏱ {data['time']}\n\n"

  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="📅 Забронировать", callback_data="book")],
          [InlineKeyboardButton(text="◀️ Назад", callback_data="back_home")],
      ]
  )
  await callback.message.edit_text(text, reply_markup=kb)
  await callback.answer()


@dp.callback_query(F.data == "location")
async def show_location(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="◀️ Назад", callback_data="back_home")]
      ]
  )
  text = "📍 Краков, ul. Zabłocie 20\nУютная студия для музыкантов. 🎸"
  await callback.message.edit_text(text, reply_markup=kb)
  await callback.answer()


@dp.callback_query(F.data == "contact")
async def show_contact(callback: types.CallbackQuery):
  kb = InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text="◀️ Назад", callback_data="back_home")]
      ]
  )
  text = "📞 Связь с нами:\nТел: +48 123 456 789\nИли пиши сюда!"
  await callback.message.edit_text(text, reply_markup=kb)
  await callback.answer()


@dp.callback_query(F.data == "back_home")
async def back_home(callback: types.CallbackQuery):
  await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu())
  await callback.answer()


@dp.callback_query(F.data == "book")
async def start_booking(callback: types.CallbackQuery, state: FSMContext):
  buttons = []
  for key, data in SERVICES.items():
    buttons.append(
        [InlineKeyboardButton(text=data["name"], callback_data=f"srv_{key}")]
    )
  buttons.append([InlineKeyboardButton(text="◀️ Отмена", callback_data="back_home")])

  kb = InlineKeyboardMarkup(inline_keyboard=buttons)
  await callback.message.edit_text("Выбери услугу:", reply_markup=kb)
  await state.set_state(BookingState.waiting_for_service)
  await callback.answer()


@dp.callback_query(BookingState.waiting_for_service, F.data.startswith("srv_"))
async def process_service(callback: types.CallbackQuery, state: FSMContext):
  service_key = callback.data.split("_")[1]
  await state.update_data(chosen_service=SERVICES[service_key]["name"])
  await callback.message.edit_text("Напиши свое имя или псевдоним:")
  await state.set_state(BookingState.waiting_for_name)
  await callback.answer()


@dp.message(BookingState.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
  await state.update_data(client_name=message.text)
  await message.answer("Отправь номер телефона или контакт для связи:")
  await state.set_state(BookingState.waiting_for_phone)


@dp.message(BookingState.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
  data = await state.get_data()
  phone = message.text
  name = data.get("client_name")
  service = data.get("chosen_service")

  await message.answer(
      "🔥 Заявка принята!\nСкоро с тобой свяжемся.", reply_markup=get_main_menu()
  )

  if message.from_user.username:
    user_link = f"@{message.from_user.username}"
  else:
    user_link = f"ID: {message.from_user.id}"

  admin_text = (
      "🚨 НОВАЯ БРОНЬ!\n\nУслуга: "
      + str(service)
      + "\nКлиент: "
      + str(name)
      + "\nТелефон: "
      + str(phone)
      + "\nПрофиль: "
      + str(user_link)
  )

  try:
    await bot.send_message(ADMIN_ID, admin_text)
  except Exception as e:
    logging.error(f"Ошибка отправки админу: {e}")

  await state.clear()


async def main():
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())
