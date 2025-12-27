# 🎧 Discord Music Bot — README

This project is an open‑source Discord music bot created for learning, experimentation, and personal use. It provides a simple foundation for anyone who wants to understand how Discord bots work, how audio playback is handled, and how to customize features in Python. This bot is not meant to compete with or replace any existing services. It exists purely as an educational tool and a fun project for people who enjoy building things themselves.

# 📘 Purpose of This Project

The goal of this bot is to help users:
- learn how Discord bots function
- understand how audio streaming works
- explore Python code in a hands‑on way
- practice debugging and improving real code
- customize features to fit their own server

Some small errors and unfinished parts are intentionally left in the code. These do **not** stop the bot from working — the bot runs fine with them. They are included on purpose so learners can practice fixing and improving real code.

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

# 📦 Installation

## 1. Install Python 3.10+
Make sure Python is installed and added to PATH.

## 2. Install dependencies
Since this project does not include a requirements.txt file, install the following manually:

pip install discord.py pynacl yt-dlp aiohttp requests colorlog python-dotenv spotipy websockets mutagen

You must also install **FFmpeg** on your system.

## 3. Run the bot
python bot.py

# 🧰 Requirements (Python Packages Needed)

These are the packages the bot uses:
- discord.py
- PyNaCl
- yt-dlp
- ffmpeg (system dependency)
- asyncio
- aiohttp
- requests
- colorlog
- python-dotenv
- spotipy
- websockets
- mutagen

Manual install command:
pip install discord.py pynacl yt-dlp aiohttp requests colorlog python-dotenv spotipy websockets mutagen

Make sure FFmpeg is installed on your system.

# 🏗️ Educational Notes

This project intentionally includes a few small, harmless errors and rough edges in the code. These do **not** prevent the bot from working — the bot runs fine as‑is. They are included to give learners something real to explore and improve. Fixing small bugs is a great way to understand how Discord bots work and how Python handles audio, events, and commands.

Users are encouraged to:
- read through the code
- fix or improve the small errors
- experiment with new features
- reorganize or rewrite parts of the bot
- learn by doing

This bot is meant to be a **learning tool**, not a polished commercial product.

# 🏢 Hosting Guidelines

You may host the bot:
- on your own computer
- on any VPS
- on any cloud provider
- on any hosting service

As long as:
- you are **not making money** from hosting it
- you are **not selling access**
- you are **not offering paid hosting**
- you are **not charging subscriptions**

This project is for **education and personal enjoyment**, not commercial use.

# 📝 Mandatory Bot Description

Any public instance of the bot must include:
“This is an open‑source bot based on the Discord Music Bot project.”

This ensures transparency and proper attribution.

# 🧩 Customization

You are free to:
- rename the bot
- change the avatar
- modify commands
- add features
- fix bugs
- fork the project
- rebrand your instance

As long as you keep the license and follow the non‑commercial rules.

# 🔒 Credits

Created by **CodeBullet23**  
Discord: **yoshi12345700**  
GitHub: **CodeBullet23**
