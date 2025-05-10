import asyncio import re from telethon import TelegramClient, events from aiohttp import web

Telegram credentials

api_id = 22707838 api_hash = '7822c50291a41745fa5e0d63f21bbfb6' session_name = 'my_session.session'

Allowed user

allowed_chat_ids = {8113892076}

Channel configuration using chat_id

channels_config = { "ichancy_zeus": { "chat_id": 2326208433, "regex": r"\b[a-zA-Z0-9]{8,12}\b", "bot": "@Ichancy_zeus_bot" }, "ichancyTheKing": { "chat_id": 2176585065, "regex": r"\b[a-zA-Z0-9]{5,}\b", "bot": "@Ichancy_TheKingBot" }, "IchancyTeacher": { "chat_id": 2557439706, "regex": r"\b[a-zA-Z0-9]{5,}\b", "bot": "@teacher_ichancy_bot" }, "IchancyDiamond": { "chat_id": 2687534765, "regex": r"\b[a-zA-Z0-9]{5,}\b", "bot": "@DiamondIchancyBot" }, "captain_ichancy": { "chat_id": 2199003618, "regex": r"\b[a-zA-Z0-9]{6,12}\b", "bot": "@ichancy_captain_bot", "pick_third": True }, "IchancyBasel": { "chat_id": 2115470972, "regex": r"\b[a-zA-Z0-9]{5,}\b", "bot": "@Ichancy_basel_bot" }, "ichancyDragon": { "chat_id": 2169021286, "regex": r"\b[a-zA-Z0-9]{5,}\b", "bot": "@ichancy_dragon_bot" }, "Malaki": { "chat_id": 2342644827, "regex": r"\b[a-zA-Z0-9]{5,}\b", "bot": "@almalaki_ichancy_bot" }, "Usd1": { # "chat_id": ,  # Add later "regex": r"\b[a-zA-Z0-9]{8,12}\b", "bot": "@ichancy_usd_bot" }, "Usd2": { # "chat_id": ,  # Add later "regex": r"\b[a-zA-Z0-9]{5,}\b", "bot": "@ichancy_tiger_usd_bot" }, "Usd3": { # "chat_id": ,  # Add later "regex": r"\b[a-zA-Z0-9]{5,}\b", "bot": "@ichancy_alcont_usd_bot" }, "Usd4": { # "chat_id": ,  # Add later "regex": r"\b[a-zA-Z0-9]{5,}\b", "bot": "@ichancy_betting_usd_bot" }, "savana": { "chat_id": 2389797854, "regex": r"\b[a-zA-Z0-9]{8,12}\b", "bot": "@ichancy_savana_bot", "pick_third": True } }

client = TelegramClient(session_name, api_id, api_hash) selected_channels = set() monitoring_active = False

@client.on(events.NewMessage(pattern='/start')) async def start_handler(event): if event.chat_id not in allowed_chat_ids: return await event.respond( "مرحباً! أرسل أسماء القنوات التي تريد مراقبتها، مفصولة بفاصلة.\n" "مثال:\n" "ichancy_zeus, ichancyTheKing\n\n" "ثم أرسل كلمة 's' لبدء المراقبة، أو 'st' لإيقافها." )

@client.on(events.NewMessage) async def handle_user_commands(event): global selected_channels, monitoring_active

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
        await event.respond("بعض القنوات غير صحيحة، تأكد من كتابتها بشكل دقيق.")

@client.on(events.NewMessage) async def monitor_handler(event): global monitoring_active if not monitoring_active: return

for channel_name in selected_channels:
    config = channels_config[channel_name]
    channel_id = config.get("chat_id")
    if not channel_id or event.chat_id != channel_id:
        continue

    match = re.findall(config["regex"], event.message.message)
    if match:
        try:
            code = match[2] if config.get("pick_third") and len(match) >= 3 else match[0]
            bot = config["bot"]

            async with client.conversation(bot, timeout=30) as conv:
                await conv.send_message('/start')
                response = await conv.get_response()

                # التعامل مع زر فيه كلمة "كود"
                button_pressed = False
                btns = response.buttons or []
                for row in btns:
                    for btn in row:
                        if 'كود' in btn.text:
                            await btn.click()
                            button_pressed = True
                            break
                    if button_pressed:
                        break

                if not button_pressed:
                    await client.send_message(
                        list(allowed_chat_ids)[0],
                        f"ما تم العثور على زر 'كود' في البوت {bot} بعد /start"
                    )
                    return

                await conv.send_message(code)

                await client.send_message(
                    list(allowed_chat_ids)[0],
                    f"تم استخراج كود من قناة ID {event.chat_id}:\n"
                    f"الكود: `{code}`\n"
                    f"تم إرساله إلى البوت: {bot}"
                )

                print(f"أُرسل الكود: {code} إلى {bot}")

        except Exception as e:
            await client.send_message(
                list(allowed_chat_ids)[0],
                f"حصل خطأ أثناء التعامل مع البوت {config['bot']}:\n{str(e)}"
            )
        break

Web server

async def handle(request): return web.Response(text="Bot is running!")

app = web.Application() app.router.add_get("/", handle)

async def start_all(): await client.start() print("Bot is running...") client_loop = asyncio.create_task(client.run_until_disconnected())

runner = web.AppRunner(app)
await runner.setup()
site = web.TCPSite(runner, '0.0.0.0', 8080)
await site.start()
print("Web server is running on http://0.0.0.0:8080")
await client_loop

if name == "main": asyncio.run(start_all())

