# 🚀 Telegram Session Manager & Bot Control Panel

A comprehensive Python toolkit for managing multiple Telethon `.session` files. It features automated session health checks, interactive CLI management, real-time OTP retrieval, country code auto-sorting, and a full Telegram Bot control panel with dynamic `.env` configuration.

---

## 📋 Features

- **Session Health Check**: Scan and classify session statuses (`AKTIF`, `BANNED`, `FROZEN`, `DEACTIVATED`, or `FLOODWAIT`).
- **OTP Reader**:
  - **History Mode**: Search recent messages across all chats for 4-6 digit OTP codes.
  - **Live Listener**: Real-time event listener waiting for incoming OTP messages.
- **Auto-Sort & Rename**: Automatically rename `.session` files to their phone numbers and organize them into subfolders based on country phone codes (e.g., `/62/`, `/1/`, `/44/`).
- **Interactive Telegram Bot**:
  - Remotely manage sessions via inline menu buttons.
  - Interactive **Settings Menu** to update `BOT_TOKEN`, `TG_API_ID`, and `TG_API_HASH` directly inside Telegram (saves to `.env`).
- **Backup Utility**: Compress all session files into `.zip` archives.

---

## 📁 Project Structure

```text
.
├── session_manager.py    # Main CLI tool for managing session files
├── bot_manager.py        # Telegram Bot Control Panel (aiogram 3)
├── .env                  # Environment configuration file (git-ignored)
├── .env.example          # Template for environment variables
├── .gitignore            # Git exclusion settings
└── README.md             # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone & Install Dependencies

```bash
git clone <your-repository-url>
cd <your-repository-folder>
pip install telethon aiogram python-dotenv
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TG_API_ID=12345678
TG_API_HASH=your_api_hash_here
```

---

## 🚀 Usage

### Option 1: Interactive CLI (`session_manager.py`)

Run the script to launch the interactive menu:

```bash
python session_manager.py
```

**Available CLI Menu Commands:**
1. **Lihat daftar session**: Lists all session files (including subfolders).
2. **Cek semua session**: Recursively inspects and checks all session statuses.
3. **Cek satu session**: Deep check for a single specified session.
4. **Tambah session baru**: Log in a new account and create a `.session` file.
5. **Buat ZIP semua session**: Backup session files into a timestamped `.zip` archive.
6. **Baca OTP session**: Choose between checking message history or waiting live for an incoming OTP.
7. **Rename & Sortir Region**: Sorts all sessions into country code folders based on phone numbers.

**CLI Flags:**

```bash
python session_manager.py --list                 # List all session files
python session_manager.py --check                # Check status of all sessions
python session_manager.py --otp session_name     # Read OTP for a session
python session_manager.py --rename-all           # Sort sessions by country code
python session_manager.py --zip                  # Backup sessions to zip
```

---

### Option 2: Telegram Bot Control Panel (`bot_manager.py`)

Start the bot service:

```bash
python bot_manager.py
```

Open your Telegram bot and type `/start`. You can:
- View all active sessions.
- Run health checks on all sessions.
- Extract OTPs directly from chat dialogs.
- Organize sessions into region subfolders.
- Access **⚙️ Settings** to update your API ID, API Hash, or Bot Token on the fly.

---

## 🔒 Security Note

- **Never commit `.env` or `.session` files to Git!**
- Ensure your `.gitignore` contains the following lines:

```gitignore
.env
*.session
backup/
```

---

## ⚠️ Disclaimer

> This project is for **educational purposes only**, not for malicious use or unauthorized trading. 
>  
> *If you want to use for buy and sell sessions, please contact https://t.me/flowyourc0de*
> 
> **免责声明：**
> *如果您想将此工具用于买卖会话（Session），请联系：https://t.me/flowyourc0de*