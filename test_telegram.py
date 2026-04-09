"""
test_telegram.py
----------------
Run this to confirm your Telegram bot can post to your channel.
Trigger via GitHub Actions: Actions tab → PassiveFlow Weekly Swarm → Run workflow → mode: status
OR add a separate workflow step temporarily.
"""

import os
import sys
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "")

if not BOT_TOKEN or not CHANNEL_ID:
    print("❌ TELEGRAM_BOT_TOKEN or TELEGRAM_CHANNEL_ID not set in environment.")
    print("   Check your GitHub Secrets.")
    sys.exit(1)

print(f"Bot token: {BOT_TOKEN[:10]}...")
print(f"Channel ID: {CHANNEL_ID}")

# Step 1: Check bot info
r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
bot_info = r.json()
if not bot_info.get("ok"):
    print(f"❌ Bot token is invalid: {bot_info}")
    sys.exit(1)
print(f"✅ Bot name: @{bot_info['result']['username']}")

# Step 2: Send test message
msg = "✅ PassiveFlow bot is connected. This is a test message — your weekly automation is working."
r = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
    json={"chat_id": CHANNEL_ID, "text": msg},
    timeout=10
)
result = r.json()
if result.get("ok"):
    print(f"✅ Message sent successfully to {CHANNEL_ID}")
    print(f"   Message ID: {result['result']['message_id']}")
else:
    print(f"❌ Failed to send message: {result.get('description')}")
    print("\nCommon fixes:")
    print("  - Bot must be an admin of the channel with 'Post Messages' permission")
    print("  - Channel ID must include @ like @yourchannel")
    print("  - For private channels, use the numeric ID (forward a message to @userinfobot)")
    sys.exit(1)
