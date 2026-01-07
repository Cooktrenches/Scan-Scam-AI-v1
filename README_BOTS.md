# 🤖 SCAM AI - Discord & Telegram Bots

AI-powered Solana token scanner bots for Discord and Telegram. Scan tokens directly from your favorite platforms!

## 🚀 Features

### Discord Bot
- **Slash Commands** (`/scan`, `/stats`, `/help`)
- Beautiful embed messages with color-coded risk levels
- Real-time AI predictions
- Interactive buttons and links
- Server-wide deployment

### Telegram Bot
- **Simple Commands** (`/scan`, `/stats`, `/help`, `/start`)
- Clean formatted messages with emojis
- Inline keyboards with useful links
- Privacy-friendly (no message storage)
- Works in groups and private chats

## 📋 Prerequisites

Before setting up the bots, you need:

1. ✅ SCAM AI web server running (`python web_app.py`)
2. ✅ Python 3.8+ installed
3. ✅ Bot tokens (see setup below)

## 🔧 Setup

### 1. Install Bot Dependencies

```bash
pip install discord.py python-telegram-bot httpx
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 2. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"**
3. Give it a name (e.g., "SCAM AI Scanner")
4. Go to **"Bot"** tab
5. Click **"Add Bot"** → Confirm
6. Click **"Reset Token"** and copy the token
7. Enable these **Privileged Gateway Intents**:
   - ✅ MESSAGE CONTENT INTENT
8. Go to **"OAuth2"** → **"URL Generator"**
9. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands`
10. Select bot permissions:
    - ✅ Send Messages
    - ✅ Embed Links
    - ✅ Read Message History
11. Copy the generated URL and invite the bot to your server

### 3. Create Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow the instructions:
   - Choose a name (e.g., "SCAM AI Scanner")
   - Choose a username (e.g., "RugAIScannerBot")
4. Copy the bot token
5. (Optional) Send `/setdescription` to add a description
6. (Optional) Send `/setabouttext` to add about text
7. (Optional) Send `/setuserpic` to add a profile picture

### 4. Configure Environment Variables

Add your bot tokens to `.env`:

```bash
# Discord Bot
DISCORD_BOT_TOKEN=your_discord_token_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_token_here

# API URL (default: http://localhost:5000)
API_URL=http://localhost:5000
```

**Important:** If you're hosting the web server on a different machine, update `API_URL` to point to it (e.g., `https://your-domain.com`)

## 🎯 Running the Bots

### Start the Web Server (Required)

First, make sure the SCAM AI web server is running:

```bash
python web_app.py
```

You should see:
```
Starting SCAM AI Web Server...
Access at: http://localhost:5000
```

### Run Discord Bot

```bash
python discord_bot.py
```

You should see:
```
╔══════════════════════════════════════════╗
║   SCAM AI DISCORD BOT - ONLINE            ║
╚══════════════════════════════════════════╝
Bot: SCAM AI Scanner
Servers: 1
Ready to scan tokens!
```

### Run Telegram Bot

```bash
python telegram_bot.py
```

You should see:
```
╔══════════════════════════════════════════╗
║   SCAM AI TELEGRAM BOT - STARTING        ║
╚══════════════════════════════════════════╝
✅ Bot is ready!
```

## 📖 Usage

### Discord Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/scan <address>` | Scan a Solana token | `/scan BDuWXaAcs88guisXQWvdiDGDVNn7eR7Wxw3Q5KLgpump` |
| `/stats` | View scanner statistics | `/stats` |
| `/help` | Show help message | `/help` |

**Example:**
```
/scan BDuWXaAcs88guisXQWvdiDGDVNn7eR7Wxw3Q5KLgpump
```

### Telegram Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message | `/start` |
| `/scan <address>` | Scan a Solana token | `/scan BDuWX...pump` |
| `/stats` | View statistics | `/stats` |
| `/help` | Show help | `/help` |

**Example:**
```
/scan BDuWXaAcs88guisXQWvdiDGDVNn7eR7Wxw3Q5KLgpump
```

## 🎨 Bot Features

### What the Bots Display

✅ **Risk Score** (0-100) with color coding:
- 🟢 Green (0-24): Low Risk
- 🟡 Yellow (25-49): Medium Risk
- 🔴 Red (50-74): High Risk
- ⛔ Dark Red (75-100): Extreme Risk

✅ **AI Prediction**:
- AI Score (0-100)
- Predicted Class (RUG/SAFE/SUCCESS)
- Confidence percentage

✅ **Analysis Confidence**:
- Reliability score
- Data completeness indicator

✅ **Market Data**:
- Price USD
- Market Cap
- Liquidity

✅ **Holder Information**:
- Total holders
- Top holder percentage

✅ **Red Flags**:
- List of detected issues
- Warnings and alerts

✅ **Quick Links**:
- View on Solscan
- View on DexScreener

## 🔐 Security & Privacy

✅ **No Data Storage**: Bots don't store any user data or scan history
✅ **Read-Only**: Bots only read messages, never modify
✅ **API Communication**: All analysis done via secure API calls
✅ **Rate Limiting**: API respects rate limits to prevent abuse

## 🚀 Deployment Options

### Local Development
- Run on your computer
- Good for testing
- Free

### Cloud Hosting

**Recommended Platforms:**

1. **Render.com** (Free Tier)
   ```bash
   # Deploy web_app.py
   # Run bots as background workers
   ```

2. **Railway.app** (Free Tier)
   ```bash
   # Deploy all 3 services
   # Auto-scaling available
   ```

3. **PythonAnywhere** (Free Tier)
   ```bash
   # Deploy web app
   # Run bots in console
   ```

4. **Heroku** (Free Tier Alternatives)
   - Use Render or Railway instead

### Docker Deployment

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  web:
    build: .
    command: python web_app.py
    ports:
      - "5000:5000"
    env_file:
      - .env

  discord-bot:
    build: .
    command: python discord_bot.py
    depends_on:
      - web
    env_file:
      - .env

  telegram-bot:
    build: .
    command: python telegram_bot.py
    depends_on:
      - web
    env_file:
      - .env
```

Run:
```bash
docker-compose up -d
```

## 🐛 Troubleshooting

### Bot Won't Start

**Error: `DISCORD_BOT_TOKEN not found`**
- ✅ Make sure `.env` file exists
- ✅ Check token is correctly copied
- ✅ No extra spaces in `.env`

**Error: `401 Unauthorized`**
- ✅ Regenerate bot token
- ✅ Update `.env` with new token

### Bot Not Responding

**Discord:**
- ✅ Check bot has permissions in server
- ✅ Make sure MESSAGE CONTENT INTENT is enabled
- ✅ Try `/help` command first

**Telegram:**
- ✅ Make sure you started the bot (`/start`)
- ✅ Check bot username is correct
- ✅ Try in private chat first

### API Connection Issues

**Error: `Connection refused`**
- ✅ Make sure `web_app.py` is running
- ✅ Check `API_URL` in `.env` is correct
- ✅ Try `http://localhost:5000` for local

**Error: `Timeout`**
- ✅ Token might be taking long to scan
- ✅ Check internet connection
- ✅ Try a different token

### Scan Fails

**Error: `Invalid Address`**
- ✅ Address must be 32-44 characters
- ✅ Use Solana token mint address
- ✅ Check for typos

**Error: `Analysis Failed`**
- ✅ Token might be too new (<1 hour)
- ✅ API keys might be missing
- ✅ Check API logs for errors

## 📊 Statistics

View bot usage:
- Total scans performed
- Risk distribution (High/Medium/Low)
- AI prediction accuracy
- Most scanned tokens

## 🔄 Updates

Keep your bots updated:

```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

Restart bots after updates.

## 💡 Tips

### Discord
- Create a dedicated `#token-scanner` channel
- Pin the bot's help message
- Use role permissions to restrict who can scan

### Telegram
- Add bot to groups for community scanning
- Use inline mode for quick scans
- Pin important messages

### Performance
- Run web server on fast hosting
- Use environment variables for API keys
- Monitor API rate limits
- Cache results when possible

## 📞 Support

- **GitHub**: [RugAIOfficial](https://github.com/RugAIOfficial)
- **Documentation**: [Main README](README.md)

## ⚠️ Disclaimer

**Educational Purposes Only**: These bots are for research and education.

**Not Financial Advice**: Never invest based solely on bot results.

**DYOR**: Always Do Your Own Research before investing.

**No Guarantees**: Bots can make mistakes. Use at your own risk.

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

**©SCAM AI 2025 - All Rights Reserved**

**Built with AI | Powered by Community**
