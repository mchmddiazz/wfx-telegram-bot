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
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher(storage=MemoryStorage())


# Mapping nama negara & bendera lengkap seluruh dunia
COUNTRY_NAMES = {
    "1": "🇺🇸/🇨🇦 US/Canada",
    "7": "🇷🇺 Russia/Kazakhstan",
    "20": "🇪🇬 Egypt",
    "27": "🇿🇦 South Africa",
    "30": "🇬🇷 Greece",
    "31": "🇳🇱 Netherlands",
    "32": "🇧🇪 Belgium",
    "33": "🇫🇷 France",
    "34": "🇪🇸 Spain",
    "36": "🇭🇺 Hungary",
    "39": "🇮🇹 Italy",
    "40": "🇦🇹 Austria",
    "41": "🇨🇭 Switzerland",
    "43": "🇦🇺 Australia",
    "44": "🇬🇧 United Kingdom",
    "45": "🇩🇰 Denmark",
    "46": "🇸🇪 Sweden",
    "47": "🇳🇴 Norway",
    "48": "🇵🇱 Poland",
    "49": "🇩🇪 Germany",
    "51": "🇵🇪 Peru",
    "52": "🇲🇽 Mexico",
    "53": "🇨🇺 Cuba",
    "54": "🇦🇷 Argentina",
    "55": "🇧🇷 Brazil",
    "56": "🇨🇱 Chile",
    "57": "🇨🇴 Colombia",
    "58": "🇻🇪 Venezuela",
    "60": "🇲🇾 Malaysia",
    "61": "🇦🇺 Australia",
    "62": "🇮🇩 Indonesia",
    "63": "🇵🇭 Philippines",
    "64": "🇳🇿 New Zealand",
    "65": "🇸🇬 Singapore",
    "66": "🇹🇭 Thailand",
    "81": "🇯🇵 Japan",
    "82": "🇰🇷 South Korea",
    "84": "🇻🇳 Vietnam",
    "86": "🇨🇳 China",
    "90": "🇹🇷 Turkey",
    "91": "🇮🇳 India",
    "92": "🇵🇰 Pakistan",
    "93": "🇦🇫 Afghanistan",
    "94": "🇱🇰 Sri Lanka",
    "95": "🇲🇲 Myanmar",
    "98": "🇮🇷 Iran",
    "211": "🇸🇸 South Sudan",
    "212": "🇲🇦 Morocco",
    "213": "🇩🇿 Algeria",
    "216": "🇹🇳 Tunisia",
    "218": "🇱🇾 Libya",
    "220": "🇬🇲 Gambia",
    "221": "🇸🇳 Senegal",
    "222": "🇲🇷 Mauritania",
    "223": "🇲🇱 Mali",
    "224": "🇬🇳 Guinea",
    "225": "🇨🇮 Ivory Coast",
    "226": "🇧🇫 Burkina Faso",
    "227": "🇳🇪 Niger",
    "228": "🇹🇬 Togo",
    "229": "🇧🇯 Benin",
    "230": "🇲🇺 Mauritius",
    "231": "🇱🇷 Liberia",
    "232": "🇸🇱 Sierra Leone",
    "233": "🇬🇭 Ghana",
    "234": "🇳🇬 Nigeria",
    "235": "🇹🇩 Chad",
    "236": "🇨🇫 Central African Republic",
    "237": "🇨🇲 Cameroon",
    "238": "🇨🇻 Cape Verde",
    "239": "🇸🇹 Sao Tome and Principe",
    "240": "🇬🇶 Equatorial Guinea",
    "241": "🇬🇦 Gabon",
    "242": "🇨🇬 Republic of the Congo",
    "243": "🇨🇩 DR Congo",
    "244": "🇦🇴 Angola",
    "245": "🇬🇼 Guinea-Bissau",
    "246": "🇩🇮 Diego Garcia",
    "248": "🇸🇨 Seychelles",
    "249": "🇸🇩 Sudan",
    "250": "🇷🇼 Rwanda",
    "251": "🇪🇹 Ethiopia",
    "252": "🇸🇴 Somalia",
    "253": "🇩🇯 Djibouti",
    "254": "🇰🇪 Kenya",
    "255": "🇹🇿 Tanzania",
    "256": "🇺🇬 Uganda",
    "257": "🇧🇮 Burundi",
    "258": "🇲🇿 Mozambique",
    "260": "🇿🇲 Zambia",
    "261": "🇲🇬 Madagascar",
    "262": "🇷🇪 Réunion",
    "263": "🇿🇼 Zimbabwe",
    "264": "🇳🇦 Namibia",
    "265": "🇲🇼 Malawi",
    "266": "🇱🇸 Lesotho",
    "267": "🇧🇼 Botswana",
    "268": "🇸🇿 Eswatini",
    "269": "🇰🇲 Comoros",
    "290": "🇸🇭 Saint Helena",
    "291": "🇪🇷 Eritrea",
    "297": "🇦🇼 Aruba",
    "298": "🇫🇴 Faroe Islands",
    "299": "🇬🇱 Greenland",
    "350": "🇬🇮 Gibraltar",
    "351": "🇵🇹 Portugal",
    "352": "🇱🇺 Luxembourg",
    "353": "🇮🇪 Ireland",
    "354": "🇮🇸 Iceland",
    "355": "🇦🇱 Albania",
    "356": "🇲🇹 Malta",
    "357": "🇨🇾 Cyprus",
    "358": "🇫🇮 Finland",
    "359": "🇧🇬 Bulgaria",
    "364": "🇭🇺 Hungary",
    "370": "🇱🇹 Lithuania",
    "371": "🇱🇻 Latvia",
    "372": "🇪🇪 Estonia",
    "373": "🇲🇩 Moldova",
    "374": "🇦🇲 Armenia",
    "375": "🇧🇾 Belarus",
    "376": "🇦🇩 Andorra",
    "377": "🇲🇨 Monaco",
    "378": "🇸🇲 San Marino",
    "379": "🇻🇦 Vatican City",
    "380": "🇺🇦 Ukraine",
    "381": "🇷🇸 Serbia",
    "382": "🇲🇪 Montenegro",
    "383": "🇽🇰 Kosovo",
    "385": "🇭🇷 Croatia",
    "386": "🇸🇮 Slovenia",
    "387": "🇧🇦 Bosnia and Herzegovina",
    "389": "🇲🇰 North Macedonia",
    "420": "🇨🇿 Czech Republic",
    "421": "🇸🇰 Slovakia",
    "423": "🇱🇮 Liechtenstein",
    "500": "🇫🇰 Falkland Islands",
    "501": "🇧🇿 Belize",
    "502": "🇬🇹 Guatemala",
    "503": "🇸🇻 El Salvador",
    "504": "🇭🇳 Honduras",
    "505": "🇳🇮 Nicaragua",
    "506": "🇨🇷 Costa Rica",
    "507": "🇵🇦 Panama",
    "508": "🇵🇲 Saint Pierre and Miquelon",
    "509": "🇭🇹 Haiti",
    "590": "🇬🇵 Guadeloupe",
    "591": "🇧🇴 Bolivia",
    "592": "🇬🇾 Guyana",
    "593": "🇪🇨 Ecuador",
    "594": "🇬🇫 French Guiana",
    "595": "🇵🇾 Paraguay",
    "596": "🇲🇶 Martinique",
    "597": "🇸🇷 Suriname",
    "598": "🇺🇾 Uruguay",
    "599": "🇨🇼 Curaçao",
    "670": "🇹🇱 Timor-Leste",
    "672": "🇳🇫 Norfolk Island",
    "673": "🇧🇳 Brunei",
    "674": "🇳🇷 Nauru",
    "675": "🇵🇬 Papua New Guinea",
    "676": "🇹🇴 Tonga",
    "677": "🇸🇧 Solomon Islands",
    "678": "🇻🇺 Vanuatu",
    "679": "🇫🇯 Fiji",
    "680": "🇵🇼 Palau",
    "681": "🇼🇫 Wallis and Futuna",
    "682": "🇨🇰 Cook Islands",
    "683": "🇳🇺 Niue",
    "685": "🇼🇸 Samoa",
    "686": "🇰🇮 Kiribati",
    "687": "🇳🇨 New Caledonia",
    "688": "🇹🇻 Tuvalu",
    "689": "🇵🇫 French Polynesia",
    "690": "🇹🇰 Tokelau",
    "691": "🇫🇲 Micronesia",
    "692": "🇲🇭 Marshall Islands",
    "850": "🇰🇵 North Korea",
    "852": "🇭🇰 Hong Kong",
    "853": "🇲🇴 Macau",
    "855": "🇰🇭 Cambodia",
    "856": "🇱🇦 Laos",
    "880": "🇧🇩 Bangladesh",
    "886": "🇹🇼 Taiwan",
    "960": "🇲🇻 Maldives",
    "961": "🇱🇧 Lebanon",
    "962": "🇯🇴 Jordan",
    "963": "🇸🇾 Syria",
    "964": "🇮🇶 Iraq",
    "965": "🇰🇼 Kuwait",
    "966": "🇸🇦 Saudi Arabia",
    "967": "🇾🇪 Yemen",
    "968": "🇴🇲 Oman",
    "970": "🇵🇸 Palestine",
    "971": "🇦🇪 United Arab Emirates",
    "972": "🇮🇱 Israel",
    "973": "🇧🇭 Bahrain",
    "974": "🇶🇦 Qatar",
    "975": "🇧🇹 Bhutan",
    "976": "🇲🇳 Mongolia",
    "977": "🇳🇵 Nepal",
    "992": "🇹🇯 Tajikistan",
    "993": "🇹🇲 Turkmenistan",
    "994": "🇦🇿 Azerbaijan",
    "995": "🇬🇪 Georgia",
    "996": "🇰🇬 Kyrgyzstan",
    "998": "🇺🇿 Uzbekistan",
    "OTHER": "🌐 Lainnya"
}

# ---------------------------------------------------------------- FSM STATES GROUP
class ExportStates(StatesGroup):
    waiting_for_custom_amount = State()


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


# ---------------------------------------------------------------- GET API CREDENTIALS
def get_user_api_credentials(user_id: int):
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


# ---------------------------------------------------------------- UTILS SESSION & KEYBOARD
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
            types.InlineKeyboardButton(text="📂 Sortir Region & Status", callback_data="menu_rename"),
            types.InlineKeyboardButton(text="🔑 Baca OTP", callback_data="menu_otp"),
        ],
        [
            types.InlineKeyboardButton(text="⚙️ Settings", callback_data="menu_settings"),
        ],
        [
            types.InlineKeyboardButton(text="⚠️ Under Development", callback_data="under_development"),
        ],
        # Baris 1: Check Live & Daftar Session
        [
            types.InlineKeyboardButton(text="✅ Check Live", callback_data="menu_check_live"),
            types.InlineKeyboardButton(text="📁 File Manager", callback_data="menu_file_manager"),
        ],
        # Baris 2: Check ID & Change Mail
        [
            types.InlineKeyboardButton(text="🆔 Check ID", callback_data="menu_check_id"),
            types.InlineKeyboardButton(text="📧 Change Mail", callback_data="menu_change_mail"),
        ],
        # Baris 3: Check Health & Check Spam
        [
            types.InlineKeyboardButton(text="💚 Check Health", callback_data="menu_check_health"),
            types.InlineKeyboardButton(text="🚫 Check Spam", callback_data="menu_check_spam"),
        ],
        # Baris 4: Remove 2FA & Change 2FA
        [
            types.InlineKeyboardButton(text="🔓 Remove 2FA", callback_data="menu_remove_2fa"),
            types.InlineKeyboardButton(text="🔄 Change 2FA", callback_data="menu_change_2fa"),
        ],
        # Baris 5: Enable 2FA
        [
            types.InlineKeyboardButton(text="🔐 Enable 2FA", callback_data="menu_enable_2fa"),
        ],
        # Baris 6: Clean Profile & Clean Message
        [
            types.InlineKeyboardButton(text="🧹 Clean Profile", callback_data="menu_clean_profile"),
            types.InlineKeyboardButton(text="💬 Clean Message", callback_data="menu_clean_message"),
        ],
        # Baris 7: Fitur Utama Anda (Sortir Region & Settings API)
    ]
    
    if user_id == ADMIN_ID:
        kb.append([types.InlineKeyboardButton(text="👥 Kelola Akses User (Admin)", callback_data="menu_admin_users")])

    return types.InlineKeyboardMarkup(inline_keyboard=kb)

# ---------------------------------------------------------------- PLACEHOLDER HANDLER MENU BARU
@dp.callback_query(F.data.startswith("menu_"))
async def cb_feature_placeholders(callback: types.CallbackQuery):
    # Biarkan menu yang sudah ada tetap berjalan tanpa tertimpa
    handled_callbacks = [
        "menu_list", "menu_check_all", "menu_otp", "menu_rename", 
        "menu_settings", "menu_back", "menu_user_settings", "menu_admin_users"
    ]
    if callback.data in handled_callbacks:
        return

    menu_title = callback.data.replace("menu_", "").replace("_", " ").title()
    await callback.answer(f"⚠️ Fitur {menu_title} dalam tahap pengembangan.", show_alert=True)


def back_keyboard(user_id: int):
    return types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text="« Kembali ke Menu Utama", callback_data="menu_back")]]
    )


# ---------------------------------------------------------------- HELPER SPAMBOT CHECK
async def check_spambot_status(client: TelegramClient) -> str:
    """
    Mengirimkan pesan /start ke @SpamBot dan menganalisis kriteria alasannya.
    """
    try:
        await client.send_message("SpamBot", "/start")
        await asyncio.sleep(2.5)

        messages = await client.get_messages("SpamBot", limit=1)
        if not messages or not messages[0].text:
            return "invalid"

        reply_text = messages[0].text.lower()

        if "your account was blocked for violations of the telegram terms of service based on user reports confirmed by our moderators" in reply_text:
            return "frozen"
        elif "good news" in reply_text or "no limits" in reply_text:
            return "free_spam"
        elif "unfortunately" in reply_text:
            return "new_register"
        elif "limited" in reply_text:
            return "spam_limit"
        else:
            return "free_spam"

    except UserDeactivatedBanError:
        return "frozen"
    except FloodWaitError:
        return "spam_limit"
    except Exception:
        return "invalid"


# ---------------------------------------------------------------- HANDLER COMMAND & START
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 **WFX Session Control Panel**\n\nSilakan pilih menu di bawah ini untuk mengelola akun Telegram Anda:",
        reply_markup=get_main_keyboard(message.from_user.id),
        parse_mode="Markdown",
    )


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id != ADMIN_ID:
        await message.answer("⛔ **Akses Ditolak!** Perintah ini khusus untuk Admin.")
        return

    await state.clear()
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


@dp.callback_query(F.data == "menu_back")
async def cb_back(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("👋 **WFX Session Control Panel**\nPilih menu manajemen akun:", reply_markup=get_main_keyboard(callback.from_user.id), parse_mode="Markdown")


# ---------------------------------------------------------------- MENU UTAMA FILE MANAGER (DAFTAR SESSION)
@dp.callback_query(F.data == "menu_list")
async def cb_list_sessions(callback: types.CallbackQuery):
    files = list_sessions()
    if not files:
        await callback.message.edit_text("❌ Belum ada file session di direktori.", reply_markup=back_keyboard(callback.from_user.id))
        return

    country_counts = {}
    total_accounts = 0

    for f in files:
        if "exports" in f.parts:
            continue
        rel_path = f.relative_to(SESSION_DIR)
        parts = rel_path.parts
        
        if len(parts) >= 2:
            country_code = parts[0]
        else:
            country_code = "OTHER"

        country_counts[country_code] = country_counts.get(country_code, 0) + 1
        total_accounts += 1

    text = f"📂 **File Manager**\n\n"
    text += f"📊 **Accounts : {total_accounts}**"

    kb = []
    for c_code, count in country_counts.items():
        c_name = COUNTRY_NAMES.get(c_code, f"🏳️ {c_code}")
        kb.append([types.InlineKeyboardButton(text=f"{c_name} - {count}", callback_data=f"select_country_{c_code}")])

    kb.append([
        types.InlineKeyboardButton(text="« Back", callback_data="menu_back"),
        types.InlineKeyboardButton(text="🏠 Home", callback_data="menu_back")
    ])

    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


# ---------------------------------------------------------------- SUBMENU NEGARA
@dp.callback_query(F.data.startswith("select_country_"))
async def cb_select_country(callback: types.CallbackQuery):
    country_code = callback.data.replace("select_country_", "")
    files = list_sessions()

    stats = {
        "new_register": 0,
        "free_spam": 0,
        "spam_limit": 0,
        "frozen": 0,
        "invalid": 0
    }

    for f in files:
        if "exports" in f.parts:
            continue
        rel_path = f.relative_to(SESSION_DIR)
        parts = rel_path.parts
        
        c_code = parts[0] if len(parts) >= 2 else "OTHER"
        status = parts[1] if len(parts) >= 3 else "new_register"

        if c_code == country_code:
            if status in ["active"]:
                status = "free_spam"
            elif status in ["limit"]:
                status = "spam_limit"

            if status in stats:
                stats[status] += 1
            else:
                stats["invalid"] += 1

    c_name = COUNTRY_NAMES.get(country_code, country_code)
    
    text = f"📂 **File Manager**\n\n"
    text += f"{c_name}\n\n"
    text += f"🟢 New Register : {stats['new_register']}\n"
    text += f"🟡 Free Spam    : {stats['free_spam']}\n"
    text += f"🔵 Spam Limit   : {stats['spam_limit']}\n"
    text += f"🔴 Frozen       : {stats['frozen']}\n"
    text += f"⚪ Invalid      : {stats['invalid']}\n"

    kb = [
        [types.InlineKeyboardButton(text=f"🟢 New Register - {stats['new_register']}", callback_data=f"show_sess_{country_code}_new_register")],
        [types.InlineKeyboardButton(text=f"🟡 Free Spam - {stats['free_spam']}", callback_data=f"show_sess_{country_code}_free_spam")],
        [types.InlineKeyboardButton(text=f"🔵 Spam Limit - {stats['spam_limit']}", callback_data=f"show_sess_{country_code}_spam_limit")],
        [types.InlineKeyboardButton(text=f"🔴 Frozen - {stats['frozen']}", callback_data=f"show_sess_{country_code}_frozen")],
        [types.InlineKeyboardButton(text=f"⚪ Invalid - {stats['invalid']}", callback_data=f"show_sess_{country_code}_invalid")],
        [
            types.InlineKeyboardButton(text="« Back", callback_data="menu_list"),
            types.InlineKeyboardButton(text="🏠 Home", callback_data="menu_back")
        ]
    ]

    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


# ---------------------------------------------------------------- SUBMENU KATEGORI & OPSI EXPORT
@dp.callback_query(F.data.startswith("show_sess_"))
async def cb_show_specific_sessions(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    parts = callback.data.split("_", 3)
    if len(parts) < 4:
        await callback.answer("Callback data tidak valid.", show_alert=True)
        return
        
    c_code = parts[2]
    status = parts[3]
    
    target_dir = SESSION_DIR / c_code / status
    if target_dir.exists():
        files = sorted(list(target_dir.glob("*.session")))
    else:
        files = [
            f for f in list_sessions() 
            if len(f.relative_to(SESSION_DIR).parts) >= 3
            and f.relative_to(SESSION_DIR).parts[0] == c_code 
            and f.relative_to(SESSION_DIR).parts[1] == status
        ]

    if not files:
        await callback.answer("Tidak ada session dalam kategori ini.", show_alert=True)
        return

    c_name = COUNTRY_NAMES.get(c_code, c_code)
    
    text = (
        f"📱 **Daftar Session ({c_name} - {status.replace('_', ' ').upper()}):**\n\n"
        f"📦 **Total Terdeteksi:** `{len(files)}` file session\n\n"
        f"Silakan pilih format export di bawah ini:"
    )
    
    kb = [
        [types.InlineKeyboardButton(text="📦 Export Session (.session)", callback_data=f"expfmt_session_{c_code}_{status}")],
        [types.InlineKeyboardButton(text="📁 Export TData (Folder)", callback_data=f"expfmt_tdata_{c_code}_{status}")],
        [types.InlineKeyboardButton(text="📄 Export JSON (.json)", callback_data=f"expfmt_json_{c_code}_{status}")],
        [types.InlineKeyboardButton(text="« Kembali", callback_data=f"select_country_{c_code}")]
    ]
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("expfmt_"))
async def cb_choose_export_amount(callback: types.CallbackQuery):
    parts = callback.data.split("_", 3)
    exp_fmt = parts[1]
    c_code = parts[2]
    status = parts[3]
    
    kb = [
        [types.InlineKeyboardButton(text="📦 Export Semua File", callback_data=f"doexp_{exp_fmt}_{c_code}_{status}")],
        [types.InlineKeyboardButton(text="✏️ Input Jumlah (Custom)", callback_data=f"askcount_{exp_fmt}_{c_code}_{status}")],
        [types.InlineKeyboardButton(text="« Kembali", callback_data=f"show_sess_{c_code}_{status}")]
    ]
    
    await callback.message.edit_text(
        f"📤 **Metode Export ({exp_fmt.upper()})**\n\nPilih opsi pengunduhan file:",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data.startswith("askcount_"))
async def cb_ask_export_count(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 3)
    exp_fmt = parts[1]
    c_code = parts[2]
    status = parts[3]
    
    await state.set_state(ExportStates.waiting_for_custom_amount)
    await state.update_data(exp_fmt=exp_fmt, c_code=c_code, status=status)
    
    await callback.message.edit_text(
        f"✏️ **Input Jumlah Session**\n\nKirimkan angka/jumlah file session yang ingin diexport format **{exp_fmt.upper()}**:\n\n*(Ketik /cancel untuk membatalkan)*",
        parse_mode="Markdown"
    )


@dp.message(ExportStates.waiting_for_custom_amount)
async def process_custom_export_amount(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Dibatalkan.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    amount_str = message.text.strip()
    if not amount_str.isdigit() or int(amount_str) <= 0:
        await message.answer("❌ Harap masukkan angka yang valid!")
        return

    data = await state.get_data()
    await state.clear()
    
    exp_fmt = data.get("exp_fmt")
    c_code = data.get("c_code")
    status = data.get("status")
    count = int(amount_str)

    await message.answer(f"⏳ Memproses export **{count}** file ke format **{exp_fmt.upper()}**...")
    zip_path = await generate_category_export(c_code, status, exp_fmt, count)
    
    if not zip_path or not zip_path.exists():
        await message.answer("❌ Gagal membuat zip atau file tidak ditemukan.", reply_markup=get_main_keyboard(message.from_user.id))
        return

    doc = FSInputFile(str(zip_path), filename=zip_path.name)
    await message.answer_document(doc, caption=f"✅ **Export Berhasil!**\nFormat: `{exp_fmt.upper()}` | Jumlah: `{count}` file", parse_mode="Markdown")


@dp.callback_query(F.data.startswith("doexp_"))
async def cb_do_export_all(callback: types.CallbackQuery):
    parts = callback.data.split("_", 3)
    if len(parts) < 4:
        await callback.answer("Callback data tidak valid.", show_alert=True)
        return

    exp_fmt = parts[1]
    c_code = parts[2]
    status = parts[3]
    
    await callback.message.edit_text(f"⏳ Sedang memproses **semua file** ke format **{exp_fmt.upper()}**...")
    zip_path = await generate_category_export(c_code, status, exp_fmt, count=None)
    
    if not zip_path or not zip_path.exists():
        await callback.message.edit_text("❌ Gagal membuat file export. Tidak ada file session yang ditemukan.", reply_markup=back_keyboard(callback.from_user.id))
        return

    doc = FSInputFile(str(zip_path), filename=zip_path.name)
    await callback.message.answer_document(doc, caption=f"✅ **Export Berhasil!**\nFormat: `{exp_fmt.upper()}` | Opsi: Semua file", parse_mode="Markdown")


# ---------------------------------------------------------------- FUNCTION GENERATOR EXPORT ZIP
async def generate_category_export(c_code: str, status: str, exp_type: str, count: int = None) -> Path:
    export_dir = SESSION_DIR / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    
    target_dir = SESSION_DIR / c_code / status
    
    if target_dir.exists():
        files = sorted(list(target_dir.glob("*.session")))
    else:
        files = [
            f for f in list_sessions() 
            if len(f.relative_to(SESSION_DIR).parts) >= 3
            and f.relative_to(SESSION_DIR).parts[0] == c_code 
            and f.relative_to(SESSION_DIR).parts[1] == status
        ]

    if not files:
        return None

    if count is not None and count > 0:
        files = files[:count]

    zip_path = export_dir / f"export_{c_code}_{status}_{exp_type}.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for f in files:
            rel_path = f.name
            
            if exp_type == "session":
                zipf.write(f, arcname=rel_path)
            elif exp_type == "json":
                meta_data = {
                    "session_name": f.stem,
                    "phone": f.stem,
                    "country_code": c_code,
                    "status": status,
                }
                json_bytes = json.dumps(meta_data, indent=4).encode("utf-8")
                zipf.writestr(f"{f.stem}.json", json_bytes)
            elif exp_type == "tdata":
                tdata_inner = f"tdata_{f.stem}/tdata/{f.stem}.session"
                zipf.write(f, arcname=tdata_inner)

    return zip_path


# ---------------------------------------------------------------- CEK SEMUA SESSION (VIA SPAMBOT)
@dp.callback_query(F.data == "menu_check_all")
async def cb_check_all(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    api_id, api_hash = get_user_api_credentials(user_id)

    if not api_id or not api_hash:
        await callback.message.edit_text("❌ TG_API_ID / TG_API_HASH belum diset. Silakan isi di menu Settings terlebih dahulu.", reply_markup=back_keyboard(user_id))
        return

    files = [f for f in list_sessions() if "exports" not in f.parts]
    if not files:
        await callback.message.edit_text("❌ Belum ada file session.", reply_markup=back_keyboard(user_id))
        return

    await callback.message.edit_text(f"⏳ Sedang memeriksa {len(files)} akun via @SpamBot, mohon tunggu...")

    report = "📊 **Ringkasan Kesehatan Akun (via @SpamBot):**\n\n"
    stats_count = {
        "free_spam": 0,
        "new_register": 0,
        "spam_limit": 0,
        "frozen": 0,
        "invalid": 0
    }

    for f in files:
        rel_name = str(f.relative_to(SESSION_DIR).with_suffix(""))
        path = session_path(rel_name)
        client = TelegramClient(path, int(api_id), api_hash)
        
        status_category = "invalid"
        try:
            await client.connect()
            status_category = await check_spambot_status(client)
        except UserDeactivatedBanError:
            status_category = "frozen"
        except Exception:
            status_category = "invalid"
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass

        stats_count[status_category] += 1

        status_display = {
            "free_spam": "🟡 FREE SPAM",
            "new_register": "🟢 NEW REGISTER",
            "spam_limit": "🔵 SPAM LIMIT",
            "frozen": "🔴 FROZEN / BANNED",
            "invalid": "⚪ INVALID / ERROR"
        }.get(status_category, "⚪ INVALID")

        report += f"• `{rel_name}` : **{status_display}**\n"

    report += (
        f"\nTotal: {len(files)} | "
        f"🟢 New Reg: {stats_count['new_register']} | "
        f"🟡 Free Spam: {stats_count['free_spam']} | "
        f"🔵 Limit: {stats_count['spam_limit']} | "
        f"🔴 Frozen: {stats_count['frozen']} | "
        f"⚪ Invalid: {stats_count['invalid']}"
    )
    await callback.message.edit_text(report, reply_markup=back_keyboard(user_id), parse_mode="Markdown")


# ---------------------------------------------------------------- BACA OTP
@dp.callback_query(F.data == "menu_otp")
async def cb_menu_otp(callback: types.CallbackQuery):
    files = [f for f in list_sessions() if "exports" not in f.parts]
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


# ---------------------------------------------------------------- SORTIR REGION & STATUS KESEHATAN (VIA SPAMBOT)
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

    await callback.message.edit_text("⏳ Sedang memeriksa akun via @SpamBot, menyortir kode negara, dan mengelompokkan...")

    country_prefixes = sorted(list(COUNTRY_NAMES.keys()), key=len, reverse=True)
    stats = {
        "new_register": 0,
        "free_spam": 0,
        "spam_limit": 0,
        "frozen": 0,
        "invalid": 0,
        "error": 0
    }

    for f in files:
        if "exports" in f.parts:
            continue

        client = TelegramClient(str(f.with_suffix("")), int(api_id), api_hash)
        clean_phone = ""
        country_code = "OTHER"
        status_folder = "invalid"

        try:
            await client.connect()
            me = await client.get_me()
            
            if me and me.phone:
                clean_phone = str(me.phone).strip().replace("+", "")
                for p in country_prefixes:
                    if clean_phone.startswith(p):
                        country_code = p
                        break
                
                status_folder = await check_spambot_status(client)
            else:
                status_folder = "invalid"
                clean_phone = f.stem

        except UserDeactivatedBanError:
            status_folder = "frozen"
            clean_phone = f.stem
        except FloodWaitError:
            status_folder = "spam_limit"
            clean_phone = f.stem
        except Exception:
            status_folder = "invalid"
            clean_phone = f.stem
        finally:
            try:
                await client.disconnect()
            except Exception:
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
        except Exception:
            stats["error"] += 1

    report = (
        "✅ **Penyortiran & Pengecekan Status via @SpamBot Selesai!**\n\n"
        f"• 🟢 **New Register**: {stats['new_register']}\n"
        f"• 🟡 **Free Spam**: {stats['free_spam']}\n"
        f"• 🔵 **Spam Limit**: {stats['spam_limit']}\n"
        f"• 🔴 **Frozen**: {stats['frozen']}\n"
        f"• ⚪ **Invalid**: {stats['invalid']}\n\n"
        "File session telah dipindahkan ke subfolder masing-masing."
    )
    await callback.message.edit_text(report, reply_markup=back_keyboard(user_id), parse_mode="Markdown")


# ---------------------------------------------------------------- USER SETTINGS
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


# ---------------------------------------------------------------- KELOLA USER (ADMIN)
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


# ---------------------------------------------------------------- MENU SETTINGS ADMIN
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