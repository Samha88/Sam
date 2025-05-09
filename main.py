import asyncio
import re
from telethon import TelegramClient, events
from aiohttp import web
from channels_config import channels_config  # ← استيراد من ملف خارجي

# معلومات تيليجرام
api_id = 22707838
api_hash = '7822c50291a41745fa5e0d63f21bbfb6'
session_name = 'my_session'
allowed_chat_ids = {8113892076}

client = TelegramClient(session_name, api_id, api_hash)
selected_channels = set()
monitoring_active = False

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.chat_id not in allowed_chat_ids:
        return
    await event.respond(
        "مرحباً! أرسل أسماء القنوات التي تريد مراقبتها، مفصولة بفاصلة.\n"
        "مثال:\n"
        "ichancy_saw, ichancyTheKing\n\n"
        "ثم أرسل كلمة 's' لبدء المراقبة، أو 'st' لإيقافها."
    )

@client.on(events.NewMessage)
async def handle_user_commands(event):
    global selected_channels, monitoring_active
    if event.chat_id not in allowed_chat_ids:
        return

    message = event.raw_text.strip()

    if message.startswith('/'):
        return

    if message.lower() == "s":
        if not selected_channels:
            await event.respond("الرجاء اختيار القنوات أولاً.")
            return
        monitoring_active = True
        await event.respond("تم تفعيل المراقبة.")

    elif message.lower() == "st":
        selected_channels.clear()
        monitoring_active = False
        await event.respond("تم إيقاف المراقبة.")

    else:
        possible_channels = [name.strip() for name in message.split(',')]
        if all(name in channels_config for name in possible_channels):
            selected_channels = set(possible_channels)
            await event.respond(f"تم اختيار القنوات: {', '.join(selected_channels)}")
        else:
            await event.respond("بعض القنوات غير صحيحة، تأكد من كتابتها.")

@client.on(events.NewMessage)
async def monitor_handler(event):
    global monitoring_active
    if not monitoring_active or not event.message.message:
        return

    for name in selected_channels:
        config = channels_config[name]
        config_username = config["username"].lower()
        chat_username = (event.chat.username or "").lower()
        chat_title = (event.chat.title or "").lower()

        if config_username not in (chat_username, chat_title):
            continue

        match = re.findall(config["regex"], event.message.message)
        if not match:
            continue

        code = match[2] if config.get("pick_third") and len(match) >= 3 else match[0]
        bot = config["bot"]

        await client.send_message(bot, '/start')
        await asyncio.sleep(1)

        # البحث عن زر يحتوي على كلمة "كود"
        found = False
        async for msg in client.iter_messages(bot, limit=5):
            if msg.buttons:
                for row in msg.buttons:
                    for button in row:
                        if 'كود' in button.text:
                            await button.click()
                            found = True
                            break
                    if found:
                        break
            if found:
                break

        await client.send_message(bot, code)

        async for msg in client.iter_messages(bot, limit=5):
            if msg.buttons:
                for row in msg.buttons:
                    for button in row:
                        if 'إرسال' in button.text or 'ارسال' in button.text:
                            await button.click()
                            break
                break

        print(f"تم التفاعل مع البوت {bot} باستخدام الكود: {code}")
        break

# Web server
async def handle(request):
    return web.Response(text="Bot is running!")

app = web.Application()
app.router.add_get("/", handle)

async def start_all():
    await client.start()
    print("Bot is running...")
    client_loop = asyncio.create_task(client.run_until_disconnected())

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Web server is running on http://0.0.0.0:8080")
    await client_loop

if __name__ == "__main__":
    asyncio.run(start_all())
