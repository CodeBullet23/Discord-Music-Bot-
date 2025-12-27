# 🎧 SentinelWaveFM — README

SentinelWaveFM is an open‑source, non‑commercial Discord radio bot created by CodeBullet23.  
It’s designed for fun, learning, and giving communities a free alternative to paid music bots.

This guide explains how to set it up, what to edit, and how to run it.

---

# 🔧 Required Configuration

Before running the bot, edit the following four values in the main configuration section:

## 1. Discord Bot Token
Create a bot at: https://discord.com/developers/applications  
Then replace:

TOKEN = "YOUR_BOT_TOKEN_HERE_1234567890"

## 2. Rank ID #1
This is usually your DJ/Admin role.

RANK_ID_1 = 111111111111111111

## 3. Rank ID #2
A second permission role (optional but recommended).

RANK_ID_2 = 222222222222222222

## 4. Webhook URL
Used for logging or status messages.

WEBHOOK_URL = "https://discord.com/api/webhooks/000000000000000000/REPLACE_ME_WITH_YOUR_WEBHOOK"

---

# 📦 Installation

## 1. Install Python 3.10+
Make sure Python is installed and added to PATH.

## 2. Install dependencies
Since this project does not include a requirements.txt file, install the following manually:

pip install discord.py pynacl yt-dlp aiohttp requests colorlog python-dotenv spotipy websockets mutagen

You must also install **FFmpeg** on your system.

## 3. Run the bot

python bot.py

---

# 🏢 Hosting Rules

You may host the bot:
- On your own computer  
- On any VPS  
- On any cloud provider  
- On any hosting service  

As long as:
- You are **NOT** making money from the bot  
- You are **NOT** selling access  
- You are **NOT** offering paid hosting  
- You are **NOT** charging subscriptions  

This bot is for fun, education, and community use only.

---

# 📝 Mandatory Bot Description

Any public instance of the bot must include:

“This is an open‑source bot based on SentinelWaveFM.”

This ensures transparency and proper attribution.

---

# 🧩 Customization

You may:
- Rename the bot  
- Change the avatar  
- Modify commands  
- Add features  
- Fork the project  
- Rebrand your instance  

As long as you keep the license and follow the non‑commercial rules.

---

# 🔒 Credits

Created by **CodeBullet23**  
Discord: **yoshi12345700**  
GitHub: **CodeBullet23**
