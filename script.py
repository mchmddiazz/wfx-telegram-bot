#!/usr/bin/env python3
"""
Telegram Bot Control Panel untuk WFX Tele Session Manager
Lengkap dengan Menu Settings, Kustom API per User, & Manajemen Whitelist
"""
import asyncio
import os
import re
import json
import zipfile
import shutil
from aiogram.types import FSInputFile
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

# Path Konfigurasi
ENV_PATH = Path(__file__).resolve().parent / ".env"
WHITELIST_PATH = Path(__file__).resolve().parent / "whitelist.json"
SESSION_DIR = Path("/home/flowyourcode/wfx-tele")

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Masukkan Telegram User ID Admin utama di .env

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher(storage=MemoryStorage())


# ---------------------------------------------------------------- FSM STATES GROUP
class SettingsStates(StatesGroup):
    waiting_for_bot_token = State()
    waiting_for_api_id = State()
    waiting_for_api_hash = State()


class OTPStates(StatesGroup):
    waiting_for_session_choice = State()


class UserApiSettingsStates(StatesGroup):
    waiting_for_api_id = State()
    waiting_for_api_hash = State()


class AdminUserStates(StatesGroup):
    waiting_for_add_id = State()
    waiting_for_remove_id = State()


# ---------------------------------------------------------------- GET API CREDENTIALS (PER USER)
def get_user_api_credentials(user_id: int):
    """
    Mengambil API ID & API Hash milik user tertentu.
    Jika tidak diset, akan fallback ke kredensial default dari .env
    """
    default_api_id = os.getenv("TG_API_ID")
    default_api_hash = os.getenv("TG_API_HASH")

    if user_id == ADMIN_ID:
        return default_api_id, default_api_hash

    if WHITELIST_PATH.exists():
        try:
            with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                users = data.get("allowed_users", {})
                
                if isinstance(users, dict) and str(user_id) in users:
                    u_data = users[str(user_id)]
                    if isinstance(u_data, dict):
                        u_api_id = u_data.get("api_id")
                        u_api_hash = u_data.get("api_hash")
                        if u_api_id and u_api_hash:
                            return u_api_id, u_api_hash
        except Exception:
            pass

    return default_api_id, default_api_hash


# ---------------------------------------------------------------- UTILS WHITELIST
def load_allowed_users() -> list:
    """Memuat daftar User ID Telegram yang diizinkan."""
    users = []
    if ADMIN_ID != 0:
        users.append(ADMIN_ID)

    if WHITELIST_PATH.exists():
        try:
            with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                allowed_data = data.get("allowed_users", [])
                if isinstance(allowed_data, list):
                    users.extend(allowed_data)
                elif isinstance(allowed_data, dict):
                    users.extend([int(k) for k in allowed_data.keys()])
        except Exception:
            pass
    return list(set(users))


def save_allowed_users(users: list):
    """Menyimpan daftar User ID ke file whitelist.json dengan mempertahankan struktur dict."""
    whitelist_data = {"allowed_users": {}}
    if WHITELIST_PATH.exists():
        try:
            with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
                whitelist_data = json.load(f)
        except Exception:
            pass

    current_allowed = whitelist_data.get("allowed_users", {})
    if isinstance(current_allowed, list):
        current_allowed = {str(uid): {"role": "admin" if uid == ADMIN_ID else "member"} for uid in current_allowed}

    new_allowed = {}
    for uid in users:
        uid_str = str(uid)
        if uid_str in current_allowed:
            new_allowed[uid_str] = current_allowed[uid_str]
        else:
            new_allowed[uid_str] = {"role": "admin" if uid == ADMIN_ID else "member"}

    whitelist_data["allowed_users"] = new_allowed
    with open(WHITELIST_PATH, "w", encoding="utf-8") as f:
        json.dump(whitelist_data, f, indent=4)


def is_user_allowed(user_id: int) -> bool:
    allowed = load_allowed_users()
    return user_id in allowed


# ---------------------------------------------------------------- MIDDLEWARE OTORISASI
@dp.message.outer_middleware()
@dp.callback_query.outer_middleware()
async def auth_middleware(handler, event, data):
    user = data.get("event_from_user")
    if user:
        if not is_user_allowed(user.id):
            block_msg = (
                "⛔ **Akses Ditolak / Unauthorized**\n\n"
                f"ID Telegram Anda (`{user.id}`) belum terdaftar untuk menggunakan sistem ini.\n\n"
                "Silakan hubungi admin di **@flowyourc0de** untuk meminta/membuat akses."
            )
            
            kb = types.InlineKeyboardMarkup(
                inline_keyboard=[[
                    types.InlineKeyboardButton(text="💬 Hubungi @flowyourc0de", url="https://t.me/flowyourc0de")
                ]]
            )

            if isinstance(event, types.Message):
                await event.answer(block_msg, reply_markup=kb, parse_mode="Markdown")
            elif isinstance(event, types.CallbackQuery):
                await event.message.answer(block_msg, reply_markup=kb, parse_mode="Markdown")
                await event.answer("Akses Ditolak", show_alert=True)
            return

    return await handler(event, data)


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
    set_key(str(ENV_PATH), key, value)
    os.environ[key] = value


def get_main_keyboard(user_id: int):
    kb = [
        [
            types.InlineKeyboardButton(text="📁 Daftar Session", callback_data="menu_list"),
            types.InlineKeyboardButton(text="🔍 Cek Semua Session", callback_data="menu_check_all"),
        ],
        [
            types.InlineKeyboardButton(text="🔑 Baca OTP", callback_data="menu_otp"),
            types.InlineKeyboardButton(text="📂 Sortir Region & Status", callback_data="menu_rename"),
        ],
        [
            types.InlineKeyboardButton(text="📤 Export Data", callback_data="menu_export"),
            types.InlineKeyboardButton(text="⚙️ Settings API", callback_data="menu_settings"),
        ],
    ]
    
    if user_id == ADMIN_ID:
        kb.append([types.InlineKeyboardButton(text="👥 Kelola Akses User (Admin)", callback_data="menu_admin_users")])

    return types.InlineKeyboardMarkup(inline_keyboard=kb)


def back_keyboard(user_id: int):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="« Kembali ke Menu Utama", callback_data="menu_back")]]
    )


# ---------------------------------------------------------------- HANDLER COMMAND & START
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 **WFX Session Control Panel**\n\nSilakan pilih menu di bawah ini untuk mengelola akun Telegram Anda:",
        reply_markup=get_main_keyboard(message.from_user.id),
        parse_mode="Markdown",
    )


@dp.callback_query(F.data == "menu_back")
async def cb_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("👋 **WFX Session Control Panel**\nPilih menu manajemen akun:", reply_markup=get_main_keyboard(callback.from_user.id), parse_mode="Markdown")


# ---------------------------------------------------------------- USER SETTINGS (CUSTOM API ID & HASH)
@dp.callback_query(F.data == "menu_user_settings")
async def cb_user_settings(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    curr_id, curr_hash = get_user_api_credentials(user_id)
    
    masked_hash = f"{curr_hash[:5]}..." if curr_hash else "❌ Belum diset"
    text = (
        "⚙️ **Pengaturan API Telegram Anda**\n\n"
        f"• **API ID:** `{curr_id}`\n"
        f"• **API Hash:** `{masked_hash}`\n\n"
        "Silakan pilih opsi di bawah untuk memperbarui API Credential pribadi Anda:"
    )
    
    kb = [
        [types.InlineKeyboardButton(text="✏️ Ubah API ID & Hash Pribadi", callback_data="set_my_api")],
        [types.InlineKeyboardButton(text="« Kembali ke Menu Utama", callback_data="menu_back")]
    ]
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


@dp.callback_query(F.data == "set_my_api")
async def cb_set_my_api(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserApiSettingsStates.waiting_for_api_id)
    await callback.message.edit_text(
        "🔑 **Setup API ID**\n\nSilakan kirimkan **API ID** Anda (berupa angka dari my.telegram.org):\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown"
    )


@dp.message(UserApiSettingsStates.waiting_for_api_id)
async def process_user_api_id(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    api_id_input = message.text.strip()
    if not api_id_input.isdigit():
        await message.answer("❌ API ID harus berupa angka!")
        return

    await state.update_data(new_api_id=api_id_input)
    await state.set_state(UserApiSettingsStates.waiting_for_api_hash)
    await message.answer("🔑 Bagus! Sekarang silakan kirimkan **API Hash** Anda:")


@dp.message(UserApiSettingsStates.waiting_for_api_hash)
async def process_user_api_hash(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    api_hash_input = message.text.strip()
    data = await state.get_data()
    new_api_id = data.get("new_api_id")
    user_id = str(message.from_user.id)

    whitelist_data = {"allowed_users": {}}
    if WHITELIST_PATH.exists():
        try:
            with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
                whitelist_data = json.load(f)
        except Exception:
            pass

    if "allowed_users" not in whitelist_data:
        whitelist_data["allowed_users"] = {}

    if isinstance(whitelist_data["allowed_users"], list):
        old_list = whitelist_data["allowed_users"]
        whitelist_data["allowed_users"] = {str(uid): {"role": "admin" if uid == ADMIN_ID else "member"} for uid in old_list}

    if user_id not in whitelist_data["allowed_users"]:
        whitelist_data["allowed_users"][user_id] = {"role": "member"}

    whitelist_data["allowed_users"][user_id]["api_id"] = new_api_id
    whitelist_data["allowed_users"][user_id]["api_hash"] = api_hash_input

    with open(WHITELIST_PATH, "w", encoding="utf-8") as f:
        json.dump(whitelist_data, f, indent=4)

    await state.clear()
    await message.answer("✅ **Berhasil!** API ID dan API Hash pribadi Anda telah disimpan.", parse_mode="Markdown", reply_markup=get_main_keyboard(message.from_user.id))


# ---------------------------------------------------------------- FITUR KELOLA USER (KHUSUS ADMIN)
@dp.callback_query(F.data == "menu_admin_users")
async def cb_admin_users(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Khusus Admin!", show_alert=True)
        return

    users = load_allowed_users()
    text = "👥 **Daftar User Terdaftar (Allowed Users):**\n\n"
    for u in users:
        role = "👑 Admin" if u == ADMIN_ID else "👤 Member"
        text += f"• `{u}` ({role})\n"

    kb = [
        [types.InlineKeyboardButton(text="➕ Tambah ID User", callback_data="admin_add_user")],
        [types.InlineKeyboardButton(text="➖ Hapus ID User", callback_data="admin_remove_user")],
        [types.InlineKeyboardButton(text="« Kembali ke Menu Utama", callback_data="menu_back")]
    ]
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


@dp.callback_query(F.data == "admin_add_user")
async def cb_add_user_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminUserStates.waiting_for_add_id)
    await callback.message.edit_text(
        "➕ **Tambah User ID**\n\nSilakan kirimkan Telegram User ID (angka) yang ingin diberi akses:\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown"
    )


@dp.message(AdminUserStates.waiting_for_add_id)
async def process_add_user(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    new_id_str = message.text.strip()
    if not new_id_str.isdigit():
        await message.answer("❌ User ID harus berupa angka!")
        return

    new_id = int(new_id_str)
    users = load_allowed_users()
    
    if new_id in users:
        await message.answer("⚠️ User ID tersebut sudah terdaftar sebelumnya.")
    else:
        users.append(new_id)
        save_allowed_users(users)
        await message.answer(f"✅ User ID `{new_id}` berhasil ditambahkan ke akses bot!", parse_mode="Markdown", reply_markup=get_main_keyboard(message.from_user.id))

    await state.clear()


@dp.callback_query(F.data == "admin_remove_user")
async def cb_remove_user_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminUserStates.waiting_for_remove_id)
    await callback.message.edit_text(
        "➖ **Hapus User ID**\n\nSilakan kirimkan Telegram User ID yang ingin dihapus aksesnya:\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown"
    )


@dp.message(AdminUserStates.waiting_for_remove_id)
async def process_remove_user(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    rem_id_str = message.text.strip()
    if not rem_id_str.isdigit():
        await message.answer("❌ User ID harus berupa angka!")
        return

    rem_id = int(rem_id_str)
    if rem_id == ADMIN_ID:
        await message.answer("❌ ID Admin utama tidak dapat dihapus!")
        return

    users = load_allowed_users()
    if rem_id in users:
        users.remove(rem_id)
        save_allowed_users(users)
        await message.answer(f"✅ User ID `{rem_id}` berhasil dihapus dari akses bot!", parse_mode="Markdown", reply_markup=get_main_keyboard(message.from_user.id))
    else:
        await message.answer("⚠️ User ID tersebut tidak ditemukan dalam daftar.")

    await state.clear()


# ---------------------------------------------------------------- MENU SETTINGS ADMIN (GLOBAL .ENV)
@dp.callback_query(F.data == "menu_settings")
async def cb_menu_settings(callback: types.CallbackQuery):
    token_status = "✅ Terisi" if os.getenv("TELEGRAM_BOT_TOKEN") else "❌ Belum diset"
    api_id_status = os.getenv("TG_API_ID") or "❌ Belum diset"
    api_hash_status = "✅ Terisi" if os.getenv("TG_API_HASH") else "❌ Belum diset"

    text = (
        "⚙️ **Pengaturan Global Bot & Admin**\n\n"
        f"• **Bot Token**: {token_status}\n"
        f"• **TG API ID (Default)**: `{api_id_status}`\n"
        f"• **TG API Hash (Default)**: {api_hash_status}\n\n"
        "Pilih parameter yang ingin Anda ubah:"
    )

    kb = [
        [types.InlineKeyboardButton(text="🤖 Set Bot Token", callback_data="set_bot_token")],
        [types.InlineKeyboardButton(text="🆔 Set Default API ID", callback_data="set_api_id")],
        [types.InlineKeyboardButton(text="🔑 Set Default API Hash", callback_data="set_api_hash")],
        [types.InlineKeyboardButton(text="« Kembali ke Menu Utama", callback_data="menu_back")],
    ]
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


@dp.callback_query(F.data == "set_bot_token")
async def cb_set_bot_token(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_bot_token)
    await callback.message.edit_text(
        "🤖 **Input Telegram Bot Token**\n\nSilakan kirimkan Bot Token baru dari @BotFather:\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown",
    )


@dp.message(SettingsStates.waiting_for_bot_token)
async def process_bot_token(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    new_token = message.text.strip()
    update_env_file("TELEGRAM_BOT_TOKEN", new_token)
    await state.clear()
    await message.answer("✅ **Bot Token berhasil disimpan!** Silakan restart bot.", parse_mode="Markdown", reply_markup=get_main_keyboard(message.from_user.id))


@dp.callback_query(F.data == "set_api_id")
async def cb_set_api_id(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_api_id)
    await callback.message.edit_text(
        "🆔 **Input Default TG API ID**\n\nSilakan masukkan API ID utama:\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown",
    )


@dp.message(SettingsStates.waiting_for_api_id)
async def process_api_id(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    new_api_id = message.text.strip()
    if not new_api_id.isdigit():
        await message.answer("❌ API ID harus berupa angka!")
        return

    update_env_file("TG_API_ID", new_api_id)
    await state.clear()
    await message.answer("✅ **Default TG API ID berhasil disimpan!**", parse_mode="Markdown", reply_markup=get_main_keyboard(message.from_user.id))


@dp.callback_query(F.data == "set_api_hash")
async def cb_set_api_hash(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.waiting_for_api_hash)
    await callback.message.edit_text(
        "🔑 **Input Default TG API Hash**\n\nSilakan masukkan API Hash utama:\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown",
    )


@dp.message(SettingsStates.waiting_for_api_hash)
async def process_api_hash(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    new_api_hash = message.text.strip()
    update_env_file("TG_API_HASH", new_api_hash)
    await state.clear()
    await message.answer("✅ **Default TG API Hash berhasil disimpan!**", parse_mode="Markdown", reply_markup=get_main_keyboard(message.from_user.id))


# ---------------------------------------------------------------- LIST SESSION
@dp.callback_query(F.data == "menu_list")
async def cb_list_sessions(callback: types.CallbackQuery):
    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session di direktori.", reply_markup=back_keyboard(callback.from_user.id))
        return

    text = f"📁 **Daftar Session ({len(files)} ditemukan):**\n\n"
    for i, f in enumerate(files, 1):
        rel_path = f.relative_to(SESSION_DIR).with_suffix("")
        text += f"{i}. `{rel_path}`\n"

    await callback.message.edit_text(text, reply_markup=back_keyboard(callback.from_user.id), parse_mode="Markdown")


# ---------------------------------------------------------------- CEK SEMUA SESSION
@dp.callback_query(F.data == "menu_check_all")
async def cb_check_all(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    api_id, api_hash = get_user_api_credentials(user_id)

    if not api_id or not api_hash:
        await callback.message.edit_text("❌ TG_API_ID / TG_API_HASH belum diset. Silakan isi di menu Settings terlebih dahulu.", reply_markup=back_keyboard(user_id))
        return

    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session.", reply_markup=back_keyboard(user_id))
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
    await callback.message.edit_text(report, reply_markup=back_keyboard(user_id), parse_mode="Markdown")


# ---------------------------------------------------------------- BACA OTP
@dp.callback_query(F.data == "menu_otp")
async def cb_menu_otp(callback: types.CallbackQuery):
    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session.", reply_markup=back_keyboard(callback.from_user.id))
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
    user_id = callback.from_user.id
    api_id, api_hash = get_user_api_credentials(user_id)

    if not api_id or not api_hash:
        await callback.message.edit_text("❌ TG_API_ID / TG_API_HASH belum diset.", reply_markup=back_keyboard(user_id))
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

    await callback.message.edit_text(result_text, reply_markup=back_keyboard(user_id), parse_mode="Markdown")


# ---------------------------------------------------------------- SORTIR REGION & STATUS KESEHATAN
@dp.callback_query(F.data == "menu_rename")
async def cb_rename_sessions(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    api_id, api_hash = get_user_api_credentials(user_id)

    if not api_id or not api_hash:
        await callback.message.edit_text("❌ TG_API_ID / TG_API_HASH belum diset.", reply_markup=back_keyboard(user_id))
        return

    files = list(SESSION_DIR.rglob("*.session"))
    if not files:
        await callback.message.edit_text("❌ Belum ada file session.", reply_markup=back_keyboard(user_id))
        return

    await callback.message.edit_text("⏳ Sedang memeriksa akun, menyortir kode negara, dan mengelompokkan berdasarkan status...")

    country_prefixes = ["62", "1", "44", "60", "65", "81", "84", "91"]
    stats = {"active": 0, "spam": 0, "frozen": 0, "invalid": 0, "error": 0}

    for f in files:
        client = TelegramClient(str(f.with_suffix("")), int(api_id), api_hash)
        status_folder = "invalid"
        clean_phone = ""
        country_code = "OTHER"

        try:
            await client.connect()
            me = await client.get_me()
            
            if me and me.phone:
                clean_phone = str(me.phone).strip().replace("+", "")
                for p in sorted(country_prefixes, key=len, reverse=True):
                    if clean_phone.startswith(p):
                        country_code = p
                        break
                
                if getattr(me, "restricted", False):
                    status_folder = "spam"
                else:
                    status_folder = "active"
            else:
                status_folder = "invalid"
                clean_phone = f.stem
            await client.disconnect()
        except UserDeactivatedBanError:
            status_folder = "frozen"
            clean_phone = f.stem
        except Exception:
            status_folder = "invalid"
            clean_phone = f.stem
        finally:
            try:
                await client.disconnect()
            except:
                pass

        if not clean_phone:
            clean_phone = f.stem

        target_dir = SESSION_DIR / country_code / status_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        new_path = target_dir / f"{clean_phone}.session"
        try:
            if f.resolve() != new_path.resolve():
                if new_path.exists():
                    new_path.unlink()
                f.rename(new_path)
            stats[status_folder] += 1
        except Exception as e:
            stats["error"] += 1

    report = (
        "✅ **Penyortiran & Pengecekan Status Selesai!**\n\n"
        f"• 🟢 **Active**: {stats['active']}\n"
        f"• 🟡 **Spam / Restricted**: {stats['spam']}\n"
        f"• 🔴 **Frozen / Banned**: {stats['frozen']}\n"
        f"• ❌ **Invalid / Error**: {stats['invalid']}\n\n"
        "File session telah dipindahkan ke subfolder masing-masing."
    )
    await callback.message.edit_text(report, reply_markup=back_keyboard(user_id), parse_mode="Markdown")


# ---------------------------------------------------------------- EXPORT SESSIONS
async def create_export_zip(export_type: str = "session") -> Path:
    export_dir = SESSION_DIR / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = export_dir / f"wfx_export_{export_type}.zip"
    files = list(SESSION_DIR.rglob("*.session"))
    
    if not files:
        return None

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in files:
            if "exports" in f.parts:
                continue
            rel_path = f.relative_to(SESSION_DIR)
            
            if export_type == "session":
                zipf.write(f, arcname=str(rel_path))
            elif export_type == "json":
                country_code = rel_path.parts[0] if len(rel_path.parts) > 1 else "Unknown"
                status_cat = rel_path.parts[1] if len(rel_path.parts) > 2 else "Unknown"
                meta_data = {
                    "session_name": f.stem,
                    "phone": f.stem,
                    "country_code": country_code,
                    "status": status_cat,
                    "relative_path": str(rel_path)
                }
                json_bytes = json.dumps(meta_data, indent=4).encode("utf-8")
                zipf.writestr(str(rel_path.with_suffix(".json")), json_bytes)
            elif export_type == "tdata":
                tdata_path = rel_path.parent / f"tdata_{f.stem}" / "tdata"
                zipf.write(f, arcname=str(tdata_path / f"{f.stem}.session"))

    return zip_path


@dp.callback_query(F.data == "menu_export")
async def cb_menu_export(callback: types.CallbackQuery):
    kb = [
        [types.InlineKeyboardButton(text="📦 Export Paket Session (.session)", callback_data="export_type_session")],
        [types.InlineKeyboardButton(text="📄 Export Metadata (.json)", callback_data="export_type_json")],
        [types.InlineKeyboardButton(text="📁 Export Format TData (Folder)", callback_data="export_type_tdata")],
        [types.InlineKeyboardButton(text="« Kembali ke Menu Utama", callback_data="menu_back")]
    ]
    await callback.message.edit_text(
        "📤 **Menu Export Session & Data**\n\nPilih format export yang Anda inginkan:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("export_type_"))
async def cb_process_export(callback: types.CallbackQuery):
    export_type = callback.data.replace("export_type_", "")
    await callback.message.edit_text(f"⏳ Sedang memproses file ke format **{export_type.upper()}**...")

    zip_file = await create_export_zip(export_type)
    user_id = callback.from_user.id
    
    if not zip_file or not zip_file.exists():
        await callback.message.edit_text("❌ Tidak ada file session yang dapat diexport.", reply_markup=back_keyboard(user_id))
        return

    document = FSInputFile(str(zip_file), filename=zip_file.name)
    await callback.message.answer_document(
        document=document,
        caption=f"✅ **Export Berhasil!**\nFormat: `{export_type.upper()}`",
        parse_mode="Markdown"
    )
    await callback.message.edit_text("Kembali ke menu utama:", reply_markup=get_main_keyboard(user_id))

# ---------------------------------------------------------------- COMMAND ADMIN & START

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Validasi apakah user yang mengetik adalah Admin utama
    if user_id != ADMIN_ID:
        await message.answer("⛔ **Akses Ditolak!** Perintah ini khusus untuk Admin.")
        return

    await state.clear()
    
    # Tampilan Dashboard khusus Admin
    admin_dashboard_text = (
        "👑 **WFX Admin Dashboard**\n\n"
        "Selamat datang kembali, Admin! Di sini Anda memiliki akses penuh untuk mengelola sistem dan whitelist pengguna.\n\n"
        "Silakan pilih menu di bawah ini:"
    )
    
    kb = [
        [types.InlineKeyboardButton(text="👥 Kelola Akses User (Whitelist)", callback_data="menu_admin_users")],
        [types.InlineKeyboardButton(text="⚙️ Pengaturan Global (.env)", callback_data="menu_settings")],
        [types.InlineKeyboardButton(text="📁 Daftar Session", callback_data="menu_list")],
        [types.InlineKeyboardButton(text="« Menu Utama", callback_data="menu_back")]
    ]
    
    await message.answer(
        admin_dashboard_text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Tampilan Default Menu untuk user umum / member
    default_menu_text = (
        "👋 **WFX Session Control Panel**\n\n"
        "Silakan pilih menu di bawah ini untuk mengelola akun Telegram Anda:"
    )
    
    await message.answer(
        default_menu_text,
        reply_markup=get_main_keyboard(message.from_user.id),
        parse_mode="Markdown",
    )
    
    kb = [
        [types.InlineKeyboardButton(text="👥 Kelola Akses User (Whitelist)", callback_data="menu_admin_users")],
        [types.InlineKeyboardButton(text="⚙️ Pengaturan Global (.env)", callback_data="menu_settings")],
        [types.InlineKeyboardButton(text="📁 Daftar Session", callback_data="menu_list")],
        [types.InlineKeyboardButton(text="« Menu Utama", callback_data="menu_back")]
    ]
    
    await message.answer(
        admin_dashboard_text,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    # Tampilan Default Menu untuk user umum / member
    default_menu_text = (
        "👋 **WFX Session Control Panel**\n\n"
        "Silakan pilih menu di bawah ini untuk mengelola akun Telegram Anda:"
    )
    
    await message.answer(
        default_menu_text,
        reply_markup=get_main_keyboard(message.from_user.id),
        parse_mode="Markdown",
    )

# ---------------------------------------------------------------- MAIN APP
async def main():
    if not bot:
        print("❌ TELEGRAM_BOT_TOKEN belum ada di file .env!")
        return

    print("Bot Telegram berjalan dengan sistem Multi-API User & Whitelist...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot dihentikan.")