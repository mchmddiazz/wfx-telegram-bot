#!/usr/bin/env python3
"""
Telegram Bot Control Panel untuk WFX Tele Session Manager
"""
import asyncio
import os
import re
from pathlib import Path
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from telethon import TelegramClient
from telethon.errors import (
    AuthKeyUnregisteredError,
    FloodWaitError,
    RPCError,
    UserDeactivatedBanError,
    UserDeactivatedError,
)
from telethon.tl.functions.account import GetAuthorizationsRequest
from telethon.tl.functions.help import GetConfigRequest
from telethon.tl.functions.users import GetUsersRequest
from telethon.tl.types import InputUserSelf

# Muat environment variabel
ENV_PATH = Path(__file__).resolve().parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API_ID = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH = os.getenv("TG_API_HASH", "")
SESSION_DIR = Path("/home/flowyourcode/wfx-tele")

if not BOT_TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN belum diset di environment / file .env")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# State untuk FSM (Conversational Flow)
class BotStates(StatesGroup):
    waiting_for_session_choice = State()
    waiting_for_otp_limit = State()


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


# ---------------------------------------------------------------- MENU UTAMA
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.InlineKeyboardButton(text="📁 Daftar Session", callback_data="menu_list"),
         types.InlineKeyboardButton(text="🔍 Cek Semua Session", callback_data="menu_check_all")],
        [types.InlineKeyboardButton(text="🔑 Baca OTP (History/Live)", callback_data="menu_otp"),
         types.InlineKeyboardButton(text="📂 Sortir & Rename Region", callback_data="menu_rename")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer(
        "👋 **WFX Session Control Panel**\n\nSilakan pilih menu di bawah ini untuk mengelola akun Telegram Anda:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ---------------------------------------------------------------- 1. LIST SESSION
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


# ---------------------------------------------------------------- 2. CEK SEMUA SESSION
@dp.callback_query(F.data == "menu_check_all")
async def cb_check_all(callback: types.CallbackQuery):
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
        client = TelegramClient(path, TG_API_ID, TG_API_HASH)
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


# ---------------------------------------------------------------- 3. BACA OTP
@dp.callback_query(F.data == "menu_otp")
async def cb_menu_otp(callback: types.CallbackQuery, state: FSMContext):
    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session.", reply_markup=back_keyboard())
        return

    kb = []
    for f in files:
        rel_name = str(f.relative_to(SESSION_DIR).with_suffix(""))
        kb.append([types.InlineKeyboardButton(text=f"📱 {rel_name}", callback_data=f"otp_sel_{rel_name}")])
    
    kb.append([types.InlineKeyboardButton(text="« Kembali", callback_data="menu_back")])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    await callback.message.edit_text("Pilih akun session yang ingin dicek OTP-nya:", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("otp_sel_"))
async def cb_otp_selected(callback: types.CallbackQuery, state: FSMContext):
    session_name = callback.data.replace("otp_sel_", "")
    await state.update_data(target_session=session_name)

    kb = [
        [types.InlineKeyboardButton(text="📜 Cek Riwayat Terakhir (15 pesan)", callback_data="otp_mode_history")],
        [types.InlineKeyboardButton(text="« Kembali", callback_data="menu_otp")]
    ]
    await callback.message.edit_text(f"Session dipilih: `{session_name}`\nPilih mode baca OTP:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


@dp.callback_query(F.data == "otp_mode_history")
async def cb_otp_history(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session_name = data.get("target_session")
    path = session_path(session_name)

    await callback.message.edit_text(f"⏳ Mengambil riwayat pesan untuk `{session_name}`...", parse_mode="Markdown")

    client = TelegramClient(path, TG_API_ID, TG_API_HASH)
    otp_pattern = r'\b\d{4,6}\b'
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
                    s_name = getattr(sender, 'title', None) or getattr(sender, 'first_name', 'Unknown')
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


# ---------------------------------------------------------------- 4. RENAME & SORTIR REGION
@dp.callback_query(F.data == "menu_rename")
async def cb_rename_sessions(callback: types.CallbackQuery):
    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session.", reply_markup=back_keyboard())
        return

    await callback.message.edit_text("⏳ Sedang menyortir dan me-rename session berdasarkan nomor HP...")
    
    country_prefixes = ["62", "1", "44", "60", "65", "81", "84", "91"]
    success = 0

    for f in files:
        old_stem = f.stem
        client = TelegramClient(str(f.with_suffix("")), TG_API_ID, TG_API_HASH)
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
            except:
                pass

    await callback.message.edit_text(f"✅ Berhasil menyortir & me-rename {success} file session ke folder region masing-masing!", reply_markup=back_keyboard())


# ---------------------------------------------------------------- HELPER NAVIGASI
def back_keyboard():
    return types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="« Kembali ke Menu Utama", callback_data="menu_back")]]
    )

@dp.callback_query(F.data == "menu_back")
async def cb_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    kb = [
        [types.InlineKeyboardButton(text="📁 Daftar Session", callback_data="menu_list"),
         types.InlineKeyboardButton(text="🔍 Cek Semua Session", callback_data="menu_check_all")],
        [types.InlineKeyboardButton(text="🔑 Baca OTP (History/Live)", callback_data="menu_otp"),
         types.InlineKeyboardButton(text="📂 Sortir & Rename Region", callback_data="menu_rename")],
    ]
    await callback.message.edit_text("👋 **WFX Session Control Panel**\nPilih menu manajemen akun:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


# ---------------------------------------------------------------- MAIN RUNNER
async def main():
    print("Bot Telegram berjalan...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot dihentikan.")