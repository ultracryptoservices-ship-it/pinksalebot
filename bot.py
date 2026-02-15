import asyncio
import requests
from telegram import Bot
from telegram.constants import ParseMode
import os
import json
import subprocess  # untuk git commands

# ===== ENV =====
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = -1003685584078
URL = "https://pinksale-trending.s3.amazonaws.com/trending.json"
LAST_RANK_FILE = "last_rank.json"

if not TOKEN:
    raise ValueError("BOT_TOKEN not found in environment variables")

bot = Bot(token=TOKEN)

# ===== ChainId → Presale Base URL =====
CHAINID_URLS = {
    137: "https://www.pinksale.finance/launchpad/polygon/",
    42161: "https://www.pinksale.finance/launchpad/arbitrum/",
    56: "https://www.pinksale.finance/launchpad/bsc/",
    1: "https://www.pinksale.finance/launchpad/ethereum/",
    501424: "https://www.pinksale.finance/launchpad/solana/launchpad/",
    8453: "https://www.pinksale.finance/launchpad/base/",
}

# ===== Fetch trending data =====
def get_trending():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "trending" in data:
            return data["trending"]
        elif isinstance(data, dict):
            for v in data.values():
                if isinstance(v, list):
                    return v
        elif isinstance(data, list):
            return data
        return []
    except Exception as e:
        print("❌ Error fetching data:", e)
        return []

# ===== Load last rank =====
def load_last_rank():
    if os.path.exists(LAST_RANK_FILE):
        with open(LAST_RANK_FILE, "r") as f:
            return json.load(f)
    return {}

# ===== Save last rank =====
def save_last_rank(rank_dict):
    with open(LAST_RANK_FILE, "w") as f:
        json.dump(rank_dict, f)

# ===== Git auto commit helper =====
def git_commit_push():
    try:
        subprocess.run(["git", "config", "--global", "user.name", "github-actions"], check=True)
        subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"], check=True)
        subprocess.run(["git", "add", LAST_RANK_FILE], check=True)
        subprocess.run(["git", "commit", "-m", "Update last_rank.json [skip ci]"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ last_rank.json committed & pushed")
    except subprocess.CalledProcessError as e:
        print("⚠️ Git push failed:", e)

# ===== Format message =====
def format_full_message(data, last_rank):
    message = "<b>Welcome to Pinksale Trending Alert.</b>\n\n"
    new_rank = {}

    # Top 12
    message += "<b>Top 12 Trending Now:</b>\n"
    for i, item in enumerate(data[:12], 1):
        token_name = item.get("token", "Unknown")
        chain_id = item.get("chainId")
        address = item.get("address", "")
        base = CHAINID_URLS.get(chain_id, "")
        link = base + address if base else ""

        prev_rank = last_rank.get(token_name)
        if prev_rank is None:
            emoji = "⚪️"
        elif i < prev_rank:
            emoji = "🟢"
        elif i > prev_rank:
            emoji = "🔴"
        else:
            emoji = "⚪️"

        new_rank[token_name] = i
        token_html = f'<a href="{link}">{token_name}</a>' if link else token_name
        message += f"{emoji} <b>{i}. {token_html}</b>\n"

    # Next Trending
    if len(data) > 12:
        message += "\n<b>Next Trending:</b>\n"
        for i, item in enumerate(data[12:], 13):
            token_name = item.get("token", "Unknown")
            chain_id = item.get("chainId")
            address = item.get("address", "")
            base = CHAINID_URLS.get(chain_id, "")
            link = base + address if base else ""

            prev_rank = last_rank.get(token_name)
            if prev_rank is None:
                emoji = "⚪️"
            elif i < prev_rank:
                emoji = "🟢"
            elif i > prev_rank:
                emoji = "🔴"
            else:
                emoji = "⚪️"

            new_rank[token_name] = i
            token_html = f'<a href="{link}">{token_name}</a>' if link else token_name
            message += f"{emoji} <b>{i}. {token_html}</b>\n"

    # Promotion & Contact
    message += "\n<b>Promotion:</b>\nNeed expert marketing support for your project?\n"
    message += "https://cryptohub.marketing/\n\n"
    message += "<b>Contact Us:</b>\n☎️ For any questions, contact @TrendingServicesAgent"

    return message, new_rank

# ===== Main job =====
async def main():
    data = get_trending()
    if not data:
        print("⚠️ No trending data")
        return

    last_rank = load_last_rank()
    message, new_rank = format_full_message(data, last_rank)

    try:
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        save_last_rank(new_rank)
        git_commit_push()
        print("✅ Update sent and last_rank.json updated")
    except Exception as e:
        print("❌ Failed to send:", e)

if __name__ == "__main__":
    asyncio.run(main())
