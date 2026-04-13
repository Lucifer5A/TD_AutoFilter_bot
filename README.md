<div align="center">

# 🚀 Auto Filter bot

![Banner](https://i.ibb.co/s9VTJWrS/your-image.jpg)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="dark-mode-banner.jpg">
  <img alt="TD Bot Dev 🇮🇳" src="1000073126.jpeg" width="90%">
</picture>

[![Deploy to Heroku](https://img.shields.io/badge/Deploy-Heroku-purple)](https://heroku.com/deploy)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://python.org)
[![License MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Powerful Telegram Bot to Manage & Save Content Easily**

</div>

---

## Auto Filter bot 📌 About

**** allows users to download or forward restricted Telegram content from channels where forwarding is disabled.  

Designed for **high performance, stability, and easy deployment**.

---

## ✨ Features

- 🔐 File db Auto save 
- ⚡ Fast processing serching 
- 🧠 Smart detection of media files  
- 🐳 Docker deployment supported  
- ☁️ Cloud deploy ready (Render / VPS)  
- 🛠 Clean and modular code
- 🔉language filter
- 🔎 session and episodes filter
- 📖 quality filter 

---


## ⚙️ Environment Variables

Already have `config.py` file with the following:

```
API_ID=Api_id
API_HASH=YOUR_API_HASH
BOT_TOKEN=YOUR_BOT_TOKEN
OWNER_ID=YOUR_TELEGRAM_ID
DB_CHANNEL=YOUR_CHANNEL_ID
```

---

## 💰 VPS Providers

| Provider | RAM | Storage | Price | Contact |
|--------|------|--------|------|--------|
| **𝕀𝖓𝖽𝖨𝖆𝖓 𝖵𝖯𝖲** | 1.4GB | 40GB | **100 INR** | [TD Bot Dev 🇮🇳](https://t.me/TDBotDev) |
| **𝕀𝖓𝖽𝖨𝖆𝖓 𝖵𝖯𝖲** | 2.8GB | 80GB | **200 INR** | [TD Bot Dev 🇮🇳](https://t.me/TDBotDev) |
| **𝕀𝖓𝖽𝖨𝖆𝖓 𝖵𝖯𝖲** | 4.2GB | 120GB | **300 INR** | [TD Bot Dev 🇮🇳](https://t.me/TDBotDev) |
| **𝕀𝖓𝖽𝖨𝖆𝖓 𝖵𝖯𝖲** | 5.6GB | 160GB | **400 INR** | [TD Bot Dev 🇮🇳](https://t.me/TDBotDev) |

> **Note:** LXC Virtualized • Scripts/Bots only • No web servers/public ports/IPs

---

## 🚀 VPS Deploy Guide

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
apt install docker.io -y
systemctl start docker
systemctl enable docker

# Clone repository
rm -rf savebot
git clone {your repository link}.git savebot
cd savebot

# Build Docker image
docker build -t savebot .

# Run container
docker run -d --name Filter--restart always Filter

# Check logs
docker logs -f Filter
```

---

## ☁️ Render Deploy

1. Upload project to GitHub  
2. Go to Render  
3. Create **New Web Service**  
4. Connect your repository  
5. Add environment variables  
6. Deploy  

<a href="https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2Ftdbotdev-source%2FFix-save-restricted">
  <img src="https://render.com/images/deploy-to-render-button.svg" alt="Deploy to Render">
</a>

---

## 🤖 Bot Commands

| Command      | Description |
|-------------|-------------|
| `/start`    | 🚀 Start the bot |
| `/help`     | 🆘 How to use the bot |
| `/delete_file` | delete your DB files(admin)|
| `/reset`   | ❌ Total reset(only owner)|
| `/broadcast`| ⚡ Broadcast message (admin) |
| `/stats`    | 👀 Bot statistics (admin) |
| `/restart`  | ♻️ Restart bot (admin) |

---

## 🫟 batfather Set Command 

```
start - 🚀 Start the bot
delete_file - delete your DB files(admin)
reset - ❌ Total reset(only owner)
broadcast -⚡ Broadcast message (admin)
stats - 👀 Bot statistics (admin)
restart - ♻️ Restart bot (admin)

```
<h3>⚙️ Settings Features</h3>

<div style="display:flex; flex-direction:column; gap:5px; max-width:400px;">

  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">/settings — Manage bot settings</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Upload Mode — Telegram</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Send As — Document</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Set Upload Destination</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Set Caption</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Thumbnail</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Suffix</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Prefix</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Set Auto Rename</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Metadata ✓</div>
  <div style="border:1px solid #ccc; padding:8px; border-radius:5px;">Remove / Replace Words</div>

</div>
---

## 🔧 Requirements

Python **3.10+**

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 👨‍💻 Developer

**Teligram channel**:- [TD Bot Dev 🇮🇳](https://t.me/TDBotDev)

Telegram Bot Developer

---

## 📜 License

This project is licensed under the **MIT License**.

---

⭐ **Star this repository if you like this project**
