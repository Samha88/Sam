import asyncio
import re
from telethon import TelegramClient, events
from aiohttp import web

# Telegram credentials
api_id = 22707838
api_hash = '7822c50291a41745fa5e0d63f21bbfb6'
session_name = 'my_session.session'

# Admin user ID
allowed_chat_ids = {8113892076}

# Channel configs
channels_config = {
    "ichancy_zeus": {
        "username": "ichancyzeusbot",
        "regex": r"\b[a-zA-Z0-9]{8,12}\b",
        "bot": "@Ichancy_zeus_bot"
    },
    "ichancyTheKing": {
        "username": "ichancyTheKing",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@Ichancy_TheKingBot"
    },
    "IchancyTeacher": {
        "username": "ichancyteacherbot",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@teacher_ichancy_bot"
    },
    "IchancyDiamond": {
        "username": "diamondichancy",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@DiamondIchancyBot"
    },
    "captain_ichancy": {
        "username": "captain_ichancy",
        "regex": r"\b[a-zA-Z0-9]{6,12}\b",
        "bot": "@ichancy_captain_bot",
        "pick_third": True
    },
    "IchancyBasel": {
        "username": "basel2255",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@Ichancy_basel_bot"
    },
    "ichancyDragon": {
        "username": "ichancy_Bot_Dragon",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@ichancy_dragon_bot"
    },
    "Malaki": {
        "username": "almalaki_ichancy",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@almalaki_ichancy_bot"
    },
    "Usd1": {
        "username": "Ichancy_Usd",
        "regex": r"\b[a-zA-Z0-9]{8,12}\b",
        "bot": "@ichancy_usd_bot"
    },
    "Usd2": {
        "username": "IchancyUsd",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@ichancy_tiger_usd_bot"
    },
    "Usd3": {
        "username": "AlcontBotUSD",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@ichancy_alcont_usd_bot"
    },
    "Usd4": {
        "username": "ichancy_bettingusd_bot",
        "regex": r"\b[a-zA-Z0-9]{5,}\b",
        "bot": "@ichancy_betting_usd_bot"
    },
    "savana": {
        "username": "savanarobertt",
        "regex": r"\b[a-zA-Z0-9]{8,12}\b",
        "bot": "@ichancy_savana_bot",
        "pick_third": True
    }
}

client = TelegramClient(session_name, api_id, api_hash)
selected_channels = set()
monitoring_active = False
log_buffer = []

# Logger to Telegram
async def send_log(message):
    for chat_id in allowed_chat_ids:
        try:
            await client.send_message(chat_id, f"[Log] {message}")
        except:
            pass

def custom_print(*args, **kwargs):
    msg = ' '.join(map(str, args))
    log_buffer.append(msg)
    asyncio.create_task(send_log(msg))
    original_print(*args, **kwargs)

original_print = print
print = custom_print

# Command handler
@client.on(events.NewMessage)
async def command_handler(event):
    global selected_channels, monitoring_active

    if event.chat_id not in allowed_chat_ids:
        return

    text = event.raw_text.strip()

    if text == "/start":
        await event.respond(
            "مرحباً! أرسل أسماء القنوات التي تريد مراقبتها، مفصولة بفاصلة.\n"
            "مثال:\n"
            "ichancy_zeus, ichancyTheKing\n\n"
            "ثم أرسل كلمة 's' لبدء المراقبة، أو 'st' لإيقافها."
        )
        return

    if text.lower() == "s":
        if not selected_channels:
            await event.respond("الرجاء اختيار القنوات أولاً.")
            return
        monitoring_active = True
        print("Monitoring activated.")
        await event.respond("تم تفعيل المراقبة.")
        return

    if text.lower() == "st":
        selected_channels.clear()
        monitoring_active = False
        print("Monitoring stopped.")
        await event.respond("تم إيقاف المراقبة.")
        return

    possible = [x.strip() for x in text.split(',')]
    if all(name in channels_config for name in possible):
        selected_channels = set(possible)
        await event.respond(f"تم اختيار القنوات: {', '.join(selected_channels)}")
        print(f"Selected channels: {selected_channels}")
    else:
        await event.respond("بعض القنوات غير صحيحة.")

# Monitoring
@client.on(events.NewMessage)
async def monitor_handler(event):
    if not monitoring_active or not event.chat or not getattr(event.chat, 'username', None):
        return

    for name in selected_channels:
        conf = channels_config[name]
        if event.chat.username != conf["username"]:
            continue

        matches = re.findall(conf["regex"], event.raw_text)
        if matches:
            try:
                code = matches[2] if conf.get("pick_third") and len(matches) >= 3 else matches[0]
                bot = conf["bot"]

                async with client.conversation(bot, timeout=30) as conv:
                    await conv.send_message('/start')
                    res = await conv.get_response()

                    btn_pressed = False
                    for row in res.buttons or []:
                        for btn in (row if isinstance(row, list) else [row]):
                            if 'كود' in btn.text:
                                await btn.click()
                                btn_pressed = True
                                break
                        if btn_pressed:
                            break

                    if not btn_pressed:
                        await client.send_message(list(allowed_chat_ids)[0], f"ما تم العثور على زر 'كود' في {bot}")
                        print(f"زر كود غير موجود في {bot}")
                        return

                    await conv.send_message(code)
                    await client.send_message(list(allowed_chat_ids)[0], f"تم استخراج الكود من @{conf['username']}:\n`{code}`\nأُرسل إلى: {bot}")
                    print(f"Code `{code}` sent to bot {bot}")
            except Exception as e:
                err_msg = f"خطأ مع البوت {bot}: {str(e)}"
                await client.send_message(list(allowed_chat_ids)[0], err_msg)
                print(err_msg)
            break

# Web endpoint
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

async def start_all():
    await client.start()
    print("Bot started...")
    for msg in log_buffer:
        await send_log(msg)
    log_buffer.clear()
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', 8080).start()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(start_all())
