import asyncio
import requests
from telegram import Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv
import os
import json

# ===== Load token =====
load_dotenv("token.env")
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = -1003685584078
URL = "https://pinksale-trending.s3.amazonaws.com/trending.json"
LAST_RANK_FILE = "last_rank.json"

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
            return []
        elif isinstance(data, list):
            return data
        else:
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

# ===== Format full message (HTML) =====
def format_full_message(data, last_rank):
    message = "<b>Welcome to Pinksale Trending Alert.</b>\n\n"
    new_rank = {}

    # ===== Top 12 Trending =====
    message += "<b>Top 12 Trending Now:</b>\n"
    for i, item in enumerate(data[:12], 1):
        token_name = item.get("token", "Unknown")
        chain_id = item.get("chainId")
        address = item.get("address", "")
        presale_base = CHAINID_URLS.get(chain_id, "")
        link = presale_base + address if presale_base else ""

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
        # Wrap links in HTML <a> (no preview anyway)
        if link:
            link_html = f'<a href="{link}">{token_name}</a>'
        else:
            link_html = token_name

        message += f"{emoji} <b>{i}. {link_html}</b>\n"

    # ===== Next Trending =====
    if len(data) > 12:
        message += "\n<b>Next Trending:</b>\n"
        for i, item in enumerate(data[12:], 13):
            token_name = item.get("token", "Unknown")
            chain_id = item.get("chainId")
            address = item.get("address", "")
            presale_base = CHAINID_URLS.get(chain_id, "")
            link = presale_base + address if presale_base else ""

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
            if link:
                link_html = f'<a href="{link}">{token_name}</a>'
            else:
                link_html = token_name

            message += f"{emoji} <b>{i}. {link_html}</b>\n"

    # ===== Promotion Section =====
    message += "\n<b>Promotion:</b>\n"
    message += "Need expert marketing support for your project?\n"
    message += "Visit our website to see how we can help:\n"
    message += "https://cryptohub.marketing/\n\n"

    # ===== Contact Section =====
    message += "<b>Contact Us:</b>\n"
    message += "☎️ For any questions or feedback about PinkSale trends,\n"
    message += "please contact us @TrendingServicesAgent"

    return message, new_rank

# ===== Main async job =====
async def job():
    print("🔎 Checking trending...")
    data = get_trending()
    if not data:
        print("⚠️ No trending data")
        return

    last_rank = load_last_rank()
    message, new_rank = format_full_message(data, last_rank)

    try:
        # Send single message with ALL previews disabled
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True  # ❌ disables all link previews
        )
        save_last_rank(new_rank)
        print("✅ Update sent!")
    except Exception as e:
        print("❌ Failed to send:", e)

# ===== Async loop every 5 minutes =====
async def main():
    print("🚀 Bot started...")
    while True:
        await job()
        await asyncio.sleep(300)  # 5 minutes

if __name__ == "__main__":
    asyncio.run(main())
