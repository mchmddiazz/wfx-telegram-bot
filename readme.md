# 🚀 Telegram Session Manager & Bot Control Panel

A comprehensive Python toolkit for managing multiple Telethon `.session` files. It features automated session health checks, interactive management, real-time OTP retrieval, country code auto-sorting, and a full Telegram Bot control panel supporting a user whitelist system, per-user custom API configurations, and dynamic `.env` management.

[English](#english) | [中文 (Chinese)](#中文-chinese)

![Alt Text](https://prod-tamdev.vercel.app/assets/wfx-tele-Dlk_aRT6.webp)

---

<a name="english"></a>
## 🇬🇧 English Documentation

## 📋 Features

- **Session Health Check**: Scan and classify session statuses (`ACTIVE`, `BANNED`, `FROZEN`, `DEACTIVATED`, or `FLOODWAIT`).
- **OTP Reader**:
  - **History Mode**: Search recent messages across all chats for 4-6 digit OTP codes.
  - **Live Listener**: Real-time event listener waiting for incoming OTP messages.
- **Auto-Sort & Rename**: Automatically rename `.session` files to their phone numbers and organize them into subfolders based on country phone codes (e.g., `/62/`, `/1/`, `/44/`).
- **Interactive Telegram Bot & Multi-API Support**:
  - Remotely manage sessions via inline menu buttons.
  - **Settings Menu** to update `BOT_TOKEN`, `TG_API_ID`, and `TG_API_HASH` directly inside Telegram.
  - **Whitelist System & Admin Dashboard**: Strict access control via the `/admin` command for administrators and per-user custom API setups.
- **Backup Utility**: Compress all session files into `.zip` archives (supporting `.session`, `.json`, and `TData` structures).

---

### ✨ Newly Added Features

1. **Automated Health Checking via Official `@SpamBot`**
   - Interacts with `@SpamBot` (`/start`) to accurately determine the limitation status of each session.
   - Intelligent response classification:
     - **`free_spam`**: Balances containing `"good news"` or `"no limits"`.
     - **`new_register`**: Balances containing `"unfortunately"`.
     - **`spam_limit`**: Balances containing `"limited"`.
     - **`frozen`**: Accounts receiving explicit block notices or raising `UserDeactivatedBanError`.
     - **`invalid`**: Broken, unreadable, or unhandled session errors.

2. **Automated Folder Classification & Region Sorting**
   - Dynamically sorts session files into structured subdirectories:
     `SESSION_DIR / <country_code> / <status_folder>`
   - Supported status folders: `new_register`, `free_spam`, `spam_limit`, `frozen`, and `invalid`.
   - Backward compatibility for legacy folder names (e.g., migrating `active` to `free_spam`).

3. **In-Menu Category Export System**
   - Direct export functionality integrated into sub-menus based on country and status.
   - **Supported Export Formats:**
     - `.session` (Standard Telethon/Pyrogram session file)
     - `.tdata` (Telegram Desktop data structure)
     - `.json` (Structured metadata representation)
   - **Export Quantity Modes:**
     - **Export All Files**: Downloads all session files in the selected category.
     - **Custom Quantity**: Interactive FSM prompt allowing users to specify exact file counts.

4. **Multi-User Access & Security**
   - Access restricted via `whitelist.json` with user role management.
   - Individual API ID and API Hash settings per user.

---

### 🚧 Features Under Development

The following utility tools have UI buttons integrated into the control panel with placeholder feedback while their core logic is being built:

- 🟢 **Check Live** – Real-time session active status check.
- 🆔 **Check ID** – User ID & Telegram account identity inspector.
- 📧 **Change Mail** – Automated 2FA/login email modification.
- 💚 **Check Health** – Comprehensive account integrity report.
- 🚫 **Check Spam** – Standalone spam status checker.
- 🔓 **Remove 2FA** – Remove Two-Step Verification passwords.
- 🔄 **Change 2FA** – Update current Two-Step Verification password.
- 🔐 **Enable 2FA** – Set up new Two-Step Verification password.
- 🧹 **Clean Profile** – Reset bio, profile photos, and names.
- 💬 **Clean Message** – Delete history and dialogs across accounts.
- ✂️ **Split Files** – Batch split session folders into smaller batches.
- 🔗 **Merge Files** – Combine multiple session directory outputs.

---

## 📁 Project Structure

```text
.
├── script.py             # Main Telegram Bot script (aiogram 3 & Telethon)
├── .env                  # Environment configuration file (git-ignored)[cite: 2]
├── .env.example          # Template for environment variables[cite: 2]
├── whitelist.json        # User ID access list & per-user custom APIs
├── .gitignore            # Git exclusion settings[cite: 2]
└── README.md             # Project documentation[cite: 2]
```

---

## ⚙️ Installation & Setup

### 1. Clone & Install Dependencies

```bash
git clone [https://github.com/mchmddiazz/wfx-telegram-bot](https://github.com/mchmddiazz/wfx-telegram-bot)
cd wfx-telegram-bot
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TG_API_ID=12345678
TG_API_HASH=your_api_hash_here
ADMIN_ID=your_telegram_user_id
```

---

## 🚀 Usage

### Option 1: Interactive CLI (`session_manager.py`)

Run the script to launch the interactive menu:

```bash
python session_manager.py
```

**Available CLI Menu Commands:**
1. **See all sessions**: Lists all session files (including subfolders).
2. **Check all sessions**: Recursively inspects and checks all session statuses.
3. **Check one session**: Deep check for a single specified session.
4. **Add new session**: Log in a new account and create a `.session` file.
5. **Create ZIP all sessions**: Backup session files into a timestamped `.zip` archive.
6. **Read sessions OTP**: Choose between checking message history or waiting live for an incoming OTP.
7. **Rename & Sort Region**: Sorts all sessions into country code folders based on phone numbers.

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

- **Never commit `.env`, `whitelist.json` or `.session` files to Git!**
- Ensure your `.gitignore` contains the following lines:

```gitignore
.env
*.session
backup/
whitelist.json
```

---

<a name="chinese"></a>
## 🇨🇳 中文文档

# 🚀 Telegram 会话管理器与机器人控制面板 (Telegram Session Manager & Bot Control Panel)

一个全面的 Python 工具包，用于管理多个 Telethon `.session` 文件。它具有自动会话健康检查、实时验证码 (OTP) 获取、区号自动分类，以及一个功能完整的 Telegram 机器人控制面板，支持白名单系统、用户自定义 API 配置以及动态 `.env` 管理。

![Alt Text](https://prod-tamdev.vercel.app/assets/wfx-tele-Dlk_aRT6.webp)

---

## 📋 主要功能 (Features)

- **会话健康检查 (Session Health Check)**：扫描并分类会话状态（`ACTIVE`、`BANNED`、`FROZEN`、`DEACTIVATED` 或 `FLOODWAIT`）[cite: 2]。
- **验证码读取器 (OTP Reader)**：
  - **历史模式 (History Mode)**：在所有聊天记录中搜索最近的 4-6 位数 OTP 验证码[cite: 2]。
  - **实时监听 (Live Listener)**：实时监听并等待传入的 OTP 消息[cite: 2]。
- **自动排序与重命名 (Auto-Sort & Rename)**：自动将 `.session` 文件重命名为手机号码，并根据国家/地区代码将其组织到子文件夹中（例如 `/62/`、`/1/`、`/44/`）[cite: 2]。
- **交互式机器人与多 API 支持 (Interactive Bot & Multi-API)**：
  - 通过内联菜单按钮远程管理会话[cite: 2]。
  - **设置菜单 (Settings Menu)**：直接在 Telegram 内部更新 `BOT_TOKEN`、`TG_API_ID` 和 `TG_API_HASH`[cite: 2]。
  - **白名单与管理员面板 (Whitelist & Admin Dashboard)**：通过 `/admin` 命令进行严格的管理员访问控制及用户专属 API 配置。
- **备份工具 (Backup Utility)**：将所有会话文件压缩成 `.zip` 归档（支持 `.session`、`.json` 和 `TData` 结构）[cite: 2]。

---

### ✨ 最新新增功能

1. **基于官方 `@SpamBot` 的自动化账号状态检测**
   - 自动向 `@SpamBot` 发送 `/start` 并分析回复内容，精准判定账号受限状态。
   - 智能响应分类标准：
     - **`free_spam` (无限制/自由)**：包含 `"good news"` 或 `"no limits"` 的回复。
     - **`new_register` (新注册/受限)**：包含 `"unfortunately"` 的回复。
     - **`spam_limit` (垃圾邮件限制)**：包含 `"limited"` 的回复。
     - **`frozen` (冻结/封禁)**：包含明确封禁提示或触发 `UserDeactivatedBanError` 异常的账号。
     - **`invalid` (无效/损坏)**：损坏或无法读取的 Session 文件。

2. **自动化目录分类与国家/地区归类**
   - 动态将 Session 文件整理至结构化子目录中：
     `SESSION_DIR / <国家代码> / <状态文件夹>`
   - 支持的状态文件夹：`new_register`、`free_spam`、`spam_limit`、`frozen` 和 `invalid`。
   - 兼容旧版本目录（自动将旧版 `active` 目录迁移至 `free_spam`）。

3. **子菜单分类导出系统**
   - 将导出功能直接集成至国家和状态子菜单中。
   - **支持的导出格式：**
     - `.session`（标准 Telethon / Pyrogram 文件）
     - `.tdata`（Telegram Desktop 客户端数据格式）
     - `.json`（结构化元数据文件）
   - **导出数量模式：**
     - **导出全部文件 (Export All)**：一键打包下载该分类下的所有 Session。
     - **自定义数量 (Custom Amount)**：通过交互式 FSM 提示输入的具体文件数量。

4. **多用户访问控制与安全**
   - 通过 `whitelist.json` 实施白名单访问限制及角色管理。
   - 支持每个用户独立配置个人的 API ID 和 API Hash。

---

### 🚧 开发中的功能 (Under Development)

以下实用工具按钮已整合至主菜单中，并配置了占位提示，具体核心逻辑正在开发中：

- 🟢 **Check Live (在线检测)** – 实时检测账号 Session 是否有效。
- 🆔 **Check ID (ID 查询)** – 查询账号 User ID 及 Telegram 身份信息。
- 📧 **Change Mail (换绑邮箱)** – 自动化修改登录/2FA 关联邮箱。
- 💚 **Check Health (健康检查)** – 生成综合账号健康度报告。
- 🚫 **Check Spam (Spam 检测)** – 独立 Spam 状态检测。
- 🔓 **Remove 2FA (解绑 2FA)** – 移除两步验证密码。
- 🔄 **Change 2FA (修改 2FA)** – 更新现有的两步验证密码。
- 🔐 **Enable 2FA (开启 2FA)** – 设置新的两步验证密码。
- 🧹 **Clean Profile (清理资料)** – 重置个人简介、头像及昵称。
- 💬 **Clean Message (清理消息)** – 清理账号聊天记录与对话。
- ✂️ **Split Files (拆分文件)** – 将 Session 批量拆分至不同文件夹。
- 🔗 **Merge Files (合并文件)** – 合并多个 Session 目录。

---

## 📁 项目结构 (Project Structure)

```text
.
├── script.py             # Telegram 机器人主脚本 (aiogram 3 & Telethon)
├── .env                  # 环境变量配置文件（已被 git 忽略）[cite: 2]
├── .env.example          # 环境变量模板[cite: 2]
├── whitelist.json        # 用户授权名单与用户自定义 API 配置
├── .gitignore            # Git 排除设置[cite: 2]
└── README.md             # 项目文档[cite: 2]

```

---

## ⚙️ 安装与设置 (Installation & Setup)

### 1. 克隆并安装依赖

```bash
git clone [https://github.com/mchmddiazz/wfx-telegram-bot](https://github.com/mchmddiazz/wfx-telegram-bot)
cd wfx-telegram-bot
pip install -r requirements.txt
```

### 2. 配置环境变量

在项目根目录下创建一个 `.env` 文件:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TG_API_ID=12345678
TG_API_HASH=your_api_hash_here
ADMIN_ID=your_telegram_user_id
```

---

## 🚀 机器人使用方法 (Usage)

### 启动机器人服务

Start the bot service:

```bash
python bot_manager.py
```

打开您的 Telegram 机器人并发送以下指令:
- `/start` ：为普通用户/成员显示默认的交互式主菜单。
- `/admin` ：打开专用的管理员仪表板（仅限 `ADMIN_ID`），用于管理白名单权限和全局设置。
- 在机器人内部访问 ⚙️ Settings 菜单，配置您个人的 API ID 和 API Hash

---

## 🔒 安全提示 (Security Note)

- **切勿将 `.env` 、 `whitelist.json` 或 `.session` 文件提交到 Git！**
- 确保您的 `.gitignore` 包含正确的排除规则:

```gitignore
.env
*.session
backup/
whitelist.json
```

---
