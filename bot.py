import os
import sqlite3
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =====================
# SOZLAMALAR
# =====================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8483198773

CARD_NUMBER = os.getenv("CARD_NUMBER", "9860 1666 5457 6569")
CARD_OWNER = "Yunusov Ilhomjon"
HELP = "@yunusovv_777"

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")


# =====================
# NARXLAR
# =====================

COINS = {
    "20": ("20 monetka", "$0.50"),
    "40": ("40 monetka", "$0.85"),
    "50": ("50 monetka", "$0.95"),
    "70": ("70 monetka", "$1.35"),
    "139": ("139 monetka", "$2.42"),
    "210": ("210 monetka", "$3.55"),
    "280": ("280 monetka", "$4.63"),
    "350": ("350 monetka", "$5.80"),
}

PREMIUM = {
    "1": ("Premium 1 oy", "50 000 so‘m"),
    "3": ("Premium 3 oy", "180 000 so‘m"),
    "6": ("Premium 6 oy", "230 000 so‘m"),
    "12": ("Premium 12 oy", "300 000 so‘m"),
}


# =====================
# DATABASE
# =====================

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
    product TEXT,
    price TEXT,
    status TEXT DEFAULT 'Kutilmoqda'
)
""")

db.commit()


bot = Bot(TOKEN)
dp = Dispatcher()


# =====================
# ASOSIY MENYU
# =====================

def main_menu(user_id):
    kb = InlineKeyboardBuilder()

    kb.button(text="🪙 Monetka sotib olish", callback_data="coins")
    kb.button(text="⭐ Telegram Premium", callback_data="premium")
    kb.button(text="💳 To‘lov qilish", callback_data="payment")
    kb.button(text="📋 Buyurtmalarim", callback_data="orders")
    kb.button(text="💰 Balans", callback_data="balance")
    kb.button(text="📞 Yordam", callback_data="help")

    if user_id == ADMIN_ID:
        kb.button(text="👨‍💼 Admin panel", callback_data="admin")

    kb.adjust(1)
    return kb.as_markup()


# =====================
# START
# =====================

@dp.message(CommandStart())
async def start(message: Message):
    cur.execute(
        "INSERT OR IGNORE INTO users(user_id) VALUES (?)",
        (message.from_user.id,)
    )
    db.commit()

    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "🛍 Savdo botiga xush kelibsiz!\n\n"
        "Kerakli bo‘limni tanlang:",
        reply_markup=main_menu(message.from_user.id)
    )


# =====================
# MONETKA
# =====================

@dp.callback_query(F.data == "coins")
async def coins(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()

    for key, (name, price) in COINS.items():
        kb.button(
            text=f"🪙 {name} — {price}",
            callback_data=f"coin:{key}"
        )

    kb.button(text="🔙 Orqaga", callback_data="back")
    kb.adjust(1)

    await callback.message.edit_text(
        "🪙 Monetka paketini tanlang:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# =====================
# PREMIUM
# =====================

@dp.callback_query(F.data == "premium")
async def premium(callback: CallbackQuery):
    kb = InlineKeyboardBuilder()

    for key, (name, price) in PREMIUM.items():
        kb.button(
            text=f"⭐ {name} — {price}",
            callback_data=f"prem:{key}"
        )

    kb.button(text="🔙 Orqaga", callback_data="back")
    kb.adjust(1)

    await callback.message.edit_text(
        "⭐ Telegram Premium muddatini tanlang:",
        reply_markup=kb.as_markup()
    )
    await callback.answer()


# =====================
# BUYURTMA YARATISH
# =====================

async def create_order(callback, product, price):
    cur.execute(
        "INSERT INTO orders(user_id, product, price) VALUES (?, ?, ?)",
        (callback.from_user.id, product, price)
    )

    order_id = cur.lastrowid
    db.commit()

    await callback.message.edit_text(
        f"🛒 BUYURTMA #{order_id}\n\n"
        f"📦 {product}\n"
        f"💰 Narxi: {price}\n\n"
        f"💳 Karta:\n"
        f"`{CARD_NUMBER}`\n"
        f"👤 {CARD_OWNER}\n\n"
        "To‘lovni amalga oshirgach, shu chatga "
        "📸 chek/rasm yuboring.\n\n"
        "⏳ Admin to‘lovni tekshiradi.",
        parse_mode="Markdown",
        reply_markup=main_menu(callback.from_user.id)
    )

    await bot.send_message(
        ADMIN_ID,
        f"🔔 YANGI BUYURTMA\n\n"
        f"🆔 #{order_id}\n"
        f"👤 User ID: {callback.from_user.id}\n"
        f"📦 {product}\n"
        f"💰 {price}"
    )


@dp.callback_query(F.data.startswith("coin:"))
async def coin_selected(callback: CallbackQuery):
    key = callback.data.split(":")[1]
    name, price = COINS[key]

    await create_order(callback, name, price)
    await callback.answer()


@dp.callback_query(F.data.startswith("prem:"))
async def premium_selected(callback: CallbackQuery):
    key = callback.data.split(":")[1]
    name, price = PREMIUM[key]

    await create_order(callback, name, price)
    await callback.answer()


# =====================
# TO‘LOV
# =====================

@dp.callback_query(F.data == "payment")
async def payment(callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 TO‘LOV\n\n"
        f"Karta: `{CARD_NUMBER}`\n"
        f"👤 {CARD_OWNER}\n\n"
        "To‘lov qilgandan keyin shu yerga "
        "📸 chek rasmini yuboring.",
        parse_mode="Markdown",
        reply_markup=main_menu(callback.from_user.id)
    )
    await callback.answer()


# =====================
# CHEK QABUL QILISH
# =====================

@dp.message(F.photo)
async def receipt(message: Message):
    user_id = message.from_user.id

    cur.execute("""
        SELECT id, product, price
        FROM orders
        WHERE user_id = ? AND status = 'Kutilmoqda'
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))

    order = cur.fetchone()

    if not order:
        await message.answer(
            "❗ Kutilayotgan buyurtma topilmadi.\n"
            "Avval mahsulot tanlang."
        )
        return

    order_id, product, price = order

    kb = InlineKeyboardBuilder()
    kb.button(
        text="✅ Tasdiqlash",
        callback_data=f"approve:{order_id}"
    )
    kb.button(
        text="❌ Rad etish",
        callback_data=f"reject:{order_id}"
    )
    kb.adjust(2)

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=(
            "🔔 YANGI CHEK!\n\n"
            f"🆔 Buyurtma: #{order_id}\n"
            f"👤 User ID: {user_id}\n"
            f"📦 {product}\n"
            f"💰 {price}"
        ),
        reply_markup=kb.as_markup()
    )

    await message.answer(
        f"✅ Chek qabul qilindi!\n\n"
        f"🆔 Buyurtma: #{order_id}\n"
        "⏳ Admin tekshiruvini kuting."
    )


# =====================
# TASDIQLASH
# =====================

@dp.callback_query(F.data.startswith("approve:"))
async def approve(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo‘q!", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])

    cur.execute(
        "SELECT user_id FROM orders WHERE id=?",
        (order_id,)
    )
    row = cur.fetchone()

    if not row:
        await callback.answer("Buyurtma topilmadi.", show_alert=True)
        return

    user_id = row[0]

    cur.execute(
        "UPDATE orders SET status='Tasdiqlandi' WHERE id=?",
        (order_id,)
    )
    db.commit()

    await bot.send_message(
        user_id,
        f"✅ To‘lovingiz tasdiqlandi!\n\n"
        f"🆔 Buyurtma: #{order_id}\n"
        "📦 Buyurtmangiz qayta ishlanmoqda."
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("✅ Tasdiqlandi!")


# =====================
# RAD ETISH
# =====================

@dp.callback_query(F.data.startswith("reject:"))
async def reject(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo‘q!", show_alert=True)
        return

    order_id = int(callback.data.split(":")[1])

    cur.execute(
        "SELECT user_id FROM orders WHERE id=?",
        (order_id,)
    )
    row = cur.fetchone()

    if not row:
        await callback.answer("Buyurtma topilmadi.", show_alert=True)
        return

    user_id = row[0]

    cur.execute(
        "UPDATE orders SET status='Rad etildi' WHERE id=?",
        (order_id,)
    )
    db.commit()

    await bot.send_message(
        user_id,
        f"❌ To‘lovingiz rad etildi.\n\n"
        f"🆔 Buyurtma: #{order_id}\n"
        f"📞 Yordam: {HELP}"
    )

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("❌ Rad etildi!")


# =====================
# BUYURTMALAR
# =====================

@dp.callback_query(F.data == "orders")
async def orders(callback: CallbackQuery):
    cur.execute("""
        SELECT id, product, price, status
        FROM orders
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (callback.from_user.id,))

    rows = cur.fetchall()

    if not rows:
        text = "📋 Hali buyurtmalar yo‘q."
    else:
        text = "📋 BUYURTMALARIM\n\n"

        for order_id, product, price, status in rows:
            text += (
                f"🆔 #{order_id}\n"
                f"📦 {product}\n"
                f"💰 {price}\n"
                f"📌 {status}\n\n"
            )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu(callback.from_user.id)
    )
    await callback.answer()


# =====================
# BALANS
# =====================

@dp.callback_query(F.data == "balance")
async def balance(callback: CallbackQuery):
    cur.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (callback.from_user.id,)
    )
    row = cur.fetchone()

    bal = row[0] if row else 0

    await callback.message.edit_text(
        f"💰 BALANS\n\n"
        f"🪙 {bal} monetka",
        reply_markup=main_menu(callback.from_user.id)
    )
    await callback.answer()


# =====================
# YORDAM
# =====================

@dp.callback_query(F.data == "help")
async def help_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        f"📞 YORDAM\n\n"
        f"Admin: {HELP}",
        reply_markup=main_menu(callback.from_user.id)
    )
    await callback.answer()


# =====================
# ADMIN PANEL
# =====================

@dp.callback_query(F.data == "admin")
async def admin(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Ruxsat yo‘q!", show_alert=True)
        return

    cur.execute("SELECT COUNT(*) FROM orders")
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM orders WHERE status='Kutilmoqda'"
    )
    pending = cur.fetchone()[0]

    await callback.message.edit_text(
        "👨‍💼 ADMIN PANEL\n\n"
        f"📋 Jami buyurtmalar: {total}\n"
        f"⏳ Kutilayotganlar: {pending}\n\n"
        "🔔 Yangi chek kelganda shu bot orqali "
        "tasdiqlash/rad etish tugmalari chiqadi.",
        reply_markup=main_menu(callback.from_user.id)
    )
    await callback.answer()


# =====================
# ORQAGA
# =====================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 Bosh menyu:",
        reply_markup=main_menu(callback.from_user.id)
    )
    await callback.answer()


# =====================
# ISHGA TUSHIRISH
# =====================

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
