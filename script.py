#!/usr/bin/env python3
"""
Telegram Bot Control Panel untuk WFX Tele Session Manager
Lengkap dengan Menu Settings (Set Bot Token, API ID, API Hash)
"""
import asyncio
import os
import re
from pathlib import Path
from dotenv import load_dotenv, set_key

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    UserDeactivatedBanError,
)
from telethon.tl.functions.users import GetUsersRequest
from telethon.tl.types import InputUserSelf

# Path File Environment (.env)
ENV_PATH = Path(__file__).resolve().parent / ".env"
SESSION_DIR = Path("/home/flowyourcode/wfx-tele")

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    ENV_PATH.touch()  # Buat file .env baru jika belum ada

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API_ID = os.getenv("TG_API_ID", "")
TG_API_HASH = os.getenv("TG_API_HASH", "")

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher(storage=MemoryStorage())


# State FSM untuk Settings
class SettingsStates(StatesGroup):
    waiting_for_bot_token = State()
    waiting_for_api_id = State()
    waiting_for_api_hash = State()


# State FSM untuk OTP
class OTPStates(StatesGroup):
    waiting_for_session_choice = State()


# ---------------------------------------------------------------- UTILS SESSION
def list_sessions():
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(SESSION_DIR.rglob("*.session"))


def session_path(name: str) -> str:
    name = name.strip()
    if name.endswith(".session"):
        name = name[: -len(".session")]
    matches = list(SESSION_DIR.rglob(f"{name}.session"))
    if matches:
        return str(matches[0].with_suffix(""))
    return str(SESSION_DIR / name)


def update_env_file(key: str, value: str):
    """Memperbarui atau menambah nilai variabel pada file .env"""
    set_key(str(ENV_PATH), key, value)
    os.environ[key] = value


def get_main_keyboard():
    kb = [
        [
            types.InlineKeyboardButton(text="📁 Daftar Session", callback_data="menu_list"),
            types.InlineKeyboardButton(text="🔍 Cek Semua Session", callback_data="menu_check_all"),
        ],
        [
            types.InlineKeyboardButton(text="🔑 Baca OTP", callback_data="menu_otp"),
            types.InlineKeyboardButton(text="📂 Sortir Region", callback_data="menu_rename"),
        ],
        [types.InlineKeyboardButton(text="⚙️ Settings (API / Token)", callback_data="menu_settings")],
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=kb)


# ---------------------------------------------------------------- MENU UTAMA
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 **WFX Session Control Panel**\n\nSilakan pilih menu di bawah ini untuk mengelola akun Telegram Anda:",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown",
    )


# ---------------------------------------------------------------- MENU SETTINGS
@dp.callback_query(F.data == "menu_settings")
async def cb_menu_settings(callback: types.CallbackQuery):
    token_status = "✅ Terisi" if os.getenv("TELEGRAM_BOT_TOKEN") else "❌ Belum diset"
    api_id_status = os.getenv("TG_API_ID") or "❌ Belum diset"
    api_hash_status = "✅ Terisi" if os.getenv("TG_API_HASH") else "❌ Belum diset"

    text = (
        "⚙️ **Pengaturan API & Token**\n\n"
        f"• **Bot Token**: {token_status}\n"
        f"• **TG API ID**: `{api_id_status}`\n"
        f"• **TG API Hash**: {api_hash_status}\n\n"
        "Pilih parameter yang ingin Anda ubah/input:"
    )

    kb = [
        [types.InlineKeyboardButton(text="🤖 Set Bot Token", callback_data="set_bot_token")],
        [types.InlineKeyboardButton(text="🆔 Set TG API ID", callback_data="set_api_id")],
        [types.InlineKeyboardButton(text="🔑 Set TG API Hash", callback_data="set_api_hash")],
        [types.InlineKeyboardButton(text="« Kembali ke Menu Utama", callback_data="menu_back")],
    ]
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


# --- Handler Input Bot Token
@dp.callback_query(F.data == "set_bot_token")
async def cb_set_bot_token(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_bot_token)
    await callback.message.edit_text(
        "🤖 **Input Telegram Bot Token**\n\nSilakan kirimkan Bot Token baru dari @BotFather ke chat ini:\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown",
    )


@dp.message(SettingsStates.waiting_for_bot_token)
async def process_bot_token(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard())
        return

    new_token = message.text.strip()
    update_env_file("TELEGRAM_BOT_TOKEN", new_token)
    await state.clear()
    await message.answer("✅ **Bot Token berhasil disimpan ke file .env!**\n\n*Catatan: Jika mengganti Token Bot, Anda perlu me-restart script bot agar token baru aktif.*", parse_mode="Markdown", reply_markup=get_main_keyboard())


# --- Handler Input API ID
@dp.callback_query(F.data == "set_api_id")
async def cb_set_api_id(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_api_id)
    await callback.message.edit_text(
        "🆔 **Input TG API ID**\n\nSilakan masukkan Telegram API ID (angka) dari https://my.telegram.org:\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown",
    )


@dp.message(SettingsStates.waiting_for_api_id)
async def process_api_id(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard())
        return

    new_api_id = message.text.strip()
    if not new_api_id.isdigit():
        await message.answer("❌ API ID harus berupa angka! Silakan masukkan lagi:")
        return

    update_env_file("TG_API_ID", new_api_id)
    await state.clear()
    await message.answer("✅ **TG API ID berhasil disimpan ke file .env!**", parse_mode="Markdown", reply_markup=get_main_keyboard())


# --- Handler Input API Hash
@dp.callback_query(F.data == "set_api_hash")
async def cb_set_api_hash(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_api_hash)
    await callback.message.edit_text(
        "🔑 **Input TG API Hash**\n\nSilakan masukkan Telegram API Hash dari https://my.telegram.org:\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown",
    )


@dp.message(SettingsStates.waiting_for_api_hash)
async def process_api_hash(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard())
        return

    new_api_hash = message.text.strip()
    update_env_file("TG_API_HASH", new_api_hash)
    await state.clear()
    await message.answer("✅ **TG API Hash berhasil disimpan ke file .env!**", parse_mode="Markdown", reply_markup=get_main_keyboard())


# ---------------------------------------------------------------- LIST SESSION
@dp.callback_query(F.data == "menu_list")
async def cb_list_sessions(callback: types.CallbackQuery):
    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session di direktori.", reply_markup=back_keyboard())
        return

    text = f"📁 **Daftar Session ({len(files)} ditemukan):**\n\n"
    for i, f in enumerate(files, 1):
        rel_path = f.relative_to(SESSION_DIR).with_suffix("")
        text += f"{i}. `{rel_path}`\n"

    await callback.message.edit_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")


# ---------------------------------------------------------------- CEK SEMUA SESSION
@dp.callback_query(F.data == "menu_check_all")
async def cb_check_all(callback: types.CallbackQuery):
    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")

    if not api_id or not api_hash:
        await callback.message.edit_text("❌ TG_API_ID / TG_API_HASH belum diset. Silakan isi di menu Settings terlebih dahulu.", reply_markup=back_keyboard())
        return

    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session.", reply_markup=back_keyboard())
        return

    await callback.message.edit_text(f"⏳ Sedang memeriksa {len(files)} akun, mohon tunggu...")

    report = "📊 **Ringkasan Kesehatan Akun:**\n\n"
    active_count, banned_count, error_count = 0, 0, 0

    for f in files:
        rel_name = str(f.relative_to(SESSION_DIR).with_suffix(""))
        path = session_path(rel_name)
        client = TelegramClient(path, int(api_id), api_hash)
        status = "AKTIF"
        try:
            await client.connect()
            me = (await client(GetUsersRequest([InputUserSelf()])))[0]
            if getattr(me, "restricted", False):
                status = "TERBATAS"
            active_count += 1
        except UserDeactivatedBanError:
            status = "BANNED"
            banned_count += 1
        except Exception:
            status = "MATI/ERROR"
            error_count += 1
        finally:
            await client.disconnect()

        report += f"• `{rel_name}` : **{status}**\n"

    report += f"\nTotal: {len(files)} | Aktif: {active_count} | Banned: {banned_count} | Error: {error_count}"
    await callback.message.edit_text(report, reply_markup=back_keyboard(), parse_mode="Markdown")


# ---------------------------------------------------------------- BACA OTP
@dp.callback_query(F.data == "menu_otp")
async def cb_menu_otp(callback: types.CallbackQuery):
    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session.", reply_markup=back_keyboard())
        return

    kb = []
    for f in files:
        rel_name = str(f.relative_to(SESSION_DIR).with_suffix(""))
        kb.append([types.InlineKeyboardButton(text=f"📱 {rel_name}", callback_data=f"otp_sel_{rel_name}")])

    kb.append([types.InlineKeyboardButton(text="« Kembali", callback_data="menu_back")])
    await callback.message.edit_text("Pilih akun session yang ingin dicek OTP-nya:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb))


@dp.callback_query(F.data.startswith("otp_sel_"))
async def cb_otp_selected(callback: types.CallbackQuery, state: FSMContext):
    session_name = callback.data.replace("otp_sel_", "")
    await state.update_data(target_session=session_name)

    kb = [
        [types.InlineKeyboardButton(text="📜 Cek Riwayat Terakhir (15 pesan)", callback_data="otp_mode_history")],
        [types.InlineKeyboardButton(text="« Kembali", callback_data="menu_otp")],
    ]
    await callback.message.edit_text(f"Session dipilih: `{session_name}`\nPilih mode baca OTP:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


@dp.callback_query(F.data == "otp_mode_history")
async def cb_otp_history(callback: types.CallbackQuery, state: FSMContext):
    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")

    if not api_id or not api_hash:
        await callback.message.edit_text("❌ TG_API_ID / TG_API_HASH belum diset. Silakan isi di menu Settings terlebih dahulu.", reply_markup=back_keyboard())
        return

    data = await state.get_data()
    session_name = data.get("target_session")
    path = session_path(session_name)

    await callback.message.edit_text(f"⏳ Mengambil riwayat pesan untuk `{session_name}`...", parse_mode="Markdown")

    client = TelegramClient(path, int(api_id), api_hash)
    otp_pattern = r"\b\d{4,6}\b"
    result_text = f"🔑 **Hasil OTP untuk `{session_name}`:**\n\n"

    try:
        await client.connect()
        messages = await client.get_messages(None, limit=15)
        found = False
        for msg in messages:
            if not msg.text:
                continue
            match = re.search(otp_pattern, msg.text)
            if match:
                found = True
                code = match.group(0)
                try:
                    sender = await msg.get_sender()
                    s_name = getattr(sender, "title", None) or getattr(sender, "first_name", "Unknown")
                except Exception:
                    s_name = "Unknown"

                result_text += f"• **Waktu**: {msg.date.astimezone():%H:%M:%S}\n"
                result_text += f"  **Pengirim**: {s_name}\n"
                result_text += f"  **Kode OTP**: `{code}`\n"
                result_text += f"  -------------------\n"

        if not found:
            result_text += "Tidak ditemukan kode OTP dalam 15 pesan terakhir."
    except Exception as e:
        result_text += f"❌ Error: {type(e).__name__}"
    finally:
        await client.disconnect()

    await callback.message.edit_text(result_text, reply_markup=back_keyboard(), parse_mode="Markdown")


# ---------------------------------------------------------------- RENAME & SORTIR REGION
@dp.callback_query(F.data == "menu_rename")
async def cb_rename_sessions(callback: types.CallbackQuery):
    api_id = os.getenv("TG_API_ID")
    api_hash = os.getenv("TG_API_HASH")

    if not api_id or not api_hash:
        await callback.message.edit_text("❌ TG_API_ID / TG_API_HASH belum diset. Silakan isi di menu Settings terlebih dahulu.", reply_markup=back_keyboard())
        return

    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session.", reply_markup=back_keyboard())
        return

    await callback.message.edit_text("⏳ Sedang menyortir dan me-rename session berdasarkan nomor HP...")

    country_prefixes = ["62", "1", "44", "60", "65", "81", "84", "91"]
    success = 0

    for f in files:
        client = TelegramClient(str(f.with_suffix("")), int(api_id), api_hash)
        try:
            await client.connect()
            me = await client.get_me()
            if me and me.phone:
                clean_phone = str(me.phone).strip().replace("+", "")
                code = "OTHER"
                for p in sorted(country_prefixes, key=len, reverse=True):
                    if clean_phone.startswith(p):
                        code = p
                        break

                target_dir = SESSION_DIR / code
                target_dir.mkdir(parents=True, exist_ok=True)
                new_path = target_dir / f"{clean_phone}.session"

                await client.disconnect()
                if f.resolve() != new_path.resolve() and not new_path.exists():
                    f.rename(new_path)
                    success += 1
            else:
                await client.disconnect()
        except Exception:
            try:
                await client.disconnect()
            except Exception:
                pass

    await callback.message.edit_text(f"✅ Berhasil menyortir & me-rename {success} file session ke folder region masing-masing!", reply_markup=back_keyboard())


# ---------------------------------------------------------------- NAVIGASI & MAIN
def back_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="« Kembali ke Menu Utama", callback_data="menu_back")]]
    )


@dp.callback_query(F.data == "menu_back")
async def cb_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("👋 **WFX Session Control Panel**\nPilih menu manajemen akun:", reply_markup=get_main_keyboard(), parse_mode="Markdown")


async def main():
    if not bot:
        print("❌ TELEGRAM_BOT_TOKEN belum ada di file .env!")
        print("   Silakan buka file .env dan isi TELEGRAM_BOT_TOKEN terlebih dahulu untuk menjalankan bot.")
        return

    print("Bot Telegram berjalan...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot dihentikan.")