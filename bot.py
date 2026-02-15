import asyncio
import requests
import os
import json
from telegram import Bot
from telegram.constants import ParseMode

# ===== ENV VARIABLE (Render) =====
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = -1003685584078
URL = "https://pinksale-trending.s3.amazonaws.com/trending.json"
LAST_RANK_FILE = "last_rank.json"

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN not found in environment variables")

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
        return []
    except Exception as e:
        print("❌ Error fetching data:", e)
        return []

# ===== Load last rank =====
def load_last_rank():
    try:
        if os.path.exists(LAST_RANK_FILE):
            with open(LAST_RANK_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        print("⚠️ Failed to load last rank:", e)
    return {}

# ===== Save last rank =====
def save_last_rank(rank_dict):
    try:
        with open(LAST_RANK_FILE, "w") as f:
            json.dump(rank_dict, f)
    except Exception as e:
        print("⚠️ Failed to save last rank:", e)

# ===== Format message =====
def format_full_message(data, last_rank):
    message = "<b>Welcome to Pinksale Trending Alert.</b>\n\n"
    new_rank = {}

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

        if link:
            link_html = f'<a href="{link}">{token_name}</a>'
        else:
            link_html = token_name

        message += f"{emoji} <b>{i}. {link_html}</b>\n"

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

    message += "\n<b>Promotion:</b>\n"
    message += "Need expert marketing support for your project?\n"
    message += "Visit our website to see how we can help:\n"
    message += "https://cryptohub.marketing/\n\n"

    message += "<b>Contact Us:</b>\n"
    message += "☎️ For any questions or feedback about PinkSale trends,\n"
    message += "please contact us @TrendingServicesAgent"

    return message, new_rank

# ===== Main job =====
async def job():
    print("🔎 Checking trending...")

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
        print("✅ Update sent!")
    except Exception as e:
        print("❌ Failed to send:", e)

# ===== Infinite loop with protection =====
async def main():
    print("🚀 Bot started...")
    while True:
        try:
            await job()
        except Exception as e:
            print("🔥 Critical Error:", e)
        await asyncio.sleep(300)  # 5 minutes

if __name__ == "__main__":
    asyncio.run(main())
