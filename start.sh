#!/bin/bash
# Start script for Render - Runs web app, Discord bot, and Telegram bot

echo "========================================"
echo "Starting SCAM AI Services..."
echo "========================================"

# Start web app in background
echo "Starting Web API on port $PORT..."
gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 120 web_app:app &

# Wait a bit for web app to start
sleep 3

# Start Discord bot
echo "Starting Discord Bot..."
python discord_bot.py &

# Start Telegram bot
echo "Starting Telegram Bot..."
python telegram_bot.py &

echo "========================================"
echo "All services started!"
echo "========================================"

# Keep script running
wait
