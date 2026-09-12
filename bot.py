import os
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

CARD_NUMBER = "9860 1666 5457 6569"
CARD_OWNER = "Yunusov Ilhom"

# Monetka paketlari
PACKAGES = {
    "100":  {"name": "100 monetka",  "price": 5000},
    "500":  {"name": "500 monetka",  "price": 20000},
    "1000": {"name": "1000 monetka", "price": 35000},
    "5000": {"name": "5000 monetka", "price": 150000},
}

db = sqlite3.connect("bot.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    package TEXT,
    amount INTEGER,
    status TEXT DEFAULT 'pending'
)
""")

db.commit()

bot = Bot(TOKEN)
dp = Dispatcher()


def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🪙 Monetka sotib olish", callback_data="buy")
    kb.button(text="💳 To‘lov qilish", callback_data="payment")
    kb.button(text="📋 Buyurtmalarim", callback_data="orders")
    kb.button(text="💰 Balans", callback_data="balance")
    kb.adjust(1)
    return kb.as_markup()


@dp.message(CommandStart())
async def start(message: Message):
    cur.execute(
        "INSERT OR IGNORE INTO users(user_id) VALUES (?)",
        (message.from_user.id,)
    )
    db.commit()

    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "🪙 TikTok Monetka Savdo botiga xush kelibsiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "buy")
async def buy(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()

    for key, package in PACKAGES.items():
        kb.button(
            text=f"🪙 {package['name']} — {package['price']:,} so‘m",
            callback_data=f"package:{key}"
        )

    kb.button(text="🔙 Orqaga", callback_data="back")
    kb.adjust(1)

    await callback.message.edit_text(
        "🪙 Monetka paketini tanlang:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("package:"))
async def package_selected(callback: CallbackQuery):
    key = callback.data.split(":")[1]
    package = PACKAGES[key]

    cur.execute(
        "INSERT INTO orders(user_id, package, amount) VALUES (?, ?, ?)",
        (callback.from_user.id, package["name"], package["price"])
    )
    order_id = cur.lastrowid
    db.commit()

    await callback.message.edit_text(
        f"🪙 {package['name']}\n"
        f"💵 Narxi: {package['price']:,} so‘m\n\n"
        f"🆔 Buyurtma: #{order_id}\n\n"
        f"💳 Karta:\n"
        f"`{CARD_NUMBER}`\n"
        f"👤 {CARD_OWNER}\n\n"
        "To‘lovni amalga oshirgach, admin tasdiqlaydi.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

    if ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 Yangi buyurtma!\n\n"
            f"🆔 #{order_id}\n"
            f"👤 ID: {callback.from_user.id}\n"
            f"🪙 {package['name']}\n"
            f"💵 {package['price']:,} so‘m"
        )

    await callback.answer()


@dp.callback_query(F.data == "payment")
async def payment(callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 To‘lov uchun karta:\n\n"
        f"`{CARD_NUMBER}`\n"
        f"👤 {CARD_OWNER}\n\n"
        "To‘lov qilganingizdan keyin buyurtma raqamingizni saqlang.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "balance")
async def balance(callback: CallbackQuery):
    cur.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (callback.from_user.id,)
    )
    row = cur.fetchone()
    balance = row[0] if row else 0

    await callback.message.edit_text(
        f"💰 Sizning balansingiz:\n\n"
        f"🪙 {balance} monetka",
        reply_markup=main_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery):
    cur.execute(
        "SELECT id, package, amount, status "
        "FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10",
        (callback.from_user.id,)
    )
    rows = cur.fetchall()

    if not rows:
        text = "📋 Sizda hali buyurtmalar yo‘q."
    else:
        text = "📋 Buyurtmalarim:\n\n"

        for order_id, package, amount, status in rows:
            text += (
                f"🆔 #{order_id}\n"
                f"🪙 {package}\n"
                f"💵 {amount:,} so‘m\n"
                f"📌 {status}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 Bosh menyu:",
        reply_markup=main_menu()
    )
    await callback.answer()


async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
