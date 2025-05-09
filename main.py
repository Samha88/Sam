import asyncio
import re
from telethon import TelegramClient, events, Button
from aiohttp import web
import config  # استيراد ملف config.py

# معلومات الحساب
api_id = 22707838
api_hash = '7822c50291a41745fa5e0d63f21bbfb6'
session_name = 'my_session'
allowed_chat_ids = {8113892076}

# تحميل إعدادات القنوات من config.py
channels_config = config.channels_config

client = TelegramClient(session_name, api_id, api_hash)
selected_channels = set()
monitoring_active = False

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.chat_id not in allowed_chat_ids:
        return
    await event.respond(
        "أهلا! أرسل أسماء القنوات يلي بدك تراقبها مفصولة بفاصلة.\n"
        "مثال:\nichancy_saw, ichancyTheKing\n\n"
        "بعدين أرسل s لتشغيل المراقبة أو st لإيقافها."
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
            await event.respond("اختار القنوات بالأول.")
            return
        monitoring_active = True
        await event.respond("شغلت المراقبة.")

    elif message.lower() == "st":
        selected_channels.clear()
        monitoring_active = False
        await event.respond("وقفت المراقبة.")

    else:
        possible_channels = [name.strip() for name in message.split(',')]
        if all(name in channels_config for name in possible_channels):
            selected_channels = set(possible_channels)
            await event.respond(f"اخترت القنوات: {', '.join(selected_channels)}")
        else:
            await event.respond("في قنوات غلط، تأكد من كتابتها صح.")

# التفاعل مع البوت (زر وكتابة الكود)
async def send_code_to_bot(bot_username, code):
    try:
        # إرسال /start للبوت
        async with client.conversation(bot_username, timeout=30) as conv:
            await conv.send_message("/start")
            response = await conv.get_response()

            # البحث عن زر فيه كلمة "كود"
            buttons = response.buttons
            code_button = None
            if buttons:
                for row in buttons:
                    for btn in row:
                        if "كود" in btn.text:
                            code_button = btn
                            break

            if code_button:
                await conv.send_click(code_button)
                await asyncio.sleep(1)
                await conv.send_message(code)
                print(f"تم إرسال الكود: {code} إلى {bot_username}")
            else:
                print(f"ما لقيت زر فيه كلمة 'كود' عند {bot_username}")
    except Exception as e:
        print(f"فشل التفاعل مع {bot_username}: {e}")

# مراقبة القنوات
@client.on(events.NewMessage)
async def monitor_handler(event):
    if not monitoring_active or not event.chat:
        return

    for channel_name in selected_channels:
        config = channels_config[channel_name]
        if getattr(event.chat, 'username', None) != config["username"]:
            continue

        match = re.findall(config["regex"], event.message.message)
        if match:
            code = match[2] if config.get("pick_third") and len(match) >= 3 else match[0]
            await send_code_to_bot(config["bot"], code)
            break

# Web check
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
