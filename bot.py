import asyncio
import os
import csv
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ---------- СОСТОЯНИЯ ----------
class Form(StatesGroup):
    service = State()
    name = State()
    phone = State()
    comment = State()

# ---------- CSV ----------
def save_lead(data):
    file_exists = os.path.isfile("leads.csv")
    with open("leads.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Дата", "Услуга", "Имя", "Телефон", "Комментарий"])
        writer.writerow([
            datetime.now().strftime("%d.%m.%Y %H:%M"),
            data["service"],
            data["name"],
            data["phone"],
            data["comment"]
        ])

# ---------- СТАРТ ----------
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Записаться")],
            [KeyboardButton(text="💰 Узнать цену")],
            [KeyboardButton(text="❓ Консультация")]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Здравствуйте 👋\n"
        "Я помогу вам быстро оставить заявку.\n\n"
        "Выберите, что вас интересует:",
        reply_markup=kb
    )
    await state.set_state(Form.service)

# ---------- УСЛУГА ----------
@dp.message(Form.service)
async def service_step(message: types.Message, state: FSMContext):
    await state.update_data(service=message.text)
    await message.answer("Как вас зовут?")
    await state.set_state(Form.name)

# ---------- ИМЯ ----------
@dp.message(Form.name)
async def name_step(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "Нажмите кнопку, чтобы отправить номер телефона:",
        reply_markup=kb
    )
    await state.set_state(Form.phone)

# ---------- ТЕЛЕФОН ----------
@dp.message(Form.phone, F.contact)
async def phone_step(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Комментарий или удобное время для звонка?")
    await state.set_state(Form.comment)

# ---------- КОММЕНТАРИЙ ----------
@dp.message(Form.comment)
async def comment_step(message: types.Message, state: FSMContext):
    data = await state.get_data()
    data["comment"] = message.text

    save_lead(data)

    admin_text = (
        "🔥 Новая заявка\n\n"
        f"📌 Услуга: {data['service']}\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"💬 Комментарий: {data['comment']}"
    )

    await bot.send_message(ADMIN_ID, admin_text)

    await message.answer(
        "✅ Заявка принята!\n"
        "Мы свяжемся с вами в ближайшее время.\n\n"
        "Хорошего дня!"
    )

    await state.clear()

# ---------- ЗАПУСК ----------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
