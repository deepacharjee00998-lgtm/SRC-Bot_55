import logging
import asyncio
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid
from motor.motor_asyncio import AsyncIOMotorClient
import config

logging.basicConfig(level=logging.INFO)

app = Client(
    "restricted_content_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

db_client = AsyncIOMotorClient(config.MONGO_URI)
db = db_client["restricted_bot_db"]
users_col = db["users"]

user_states = {}

def main_menu_markup(is_logged_in=False, target_set=False):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start Forwarding Now", callback_data="start_forward")],
        [InlineKeyboardButton("👑 Buy VIP Premium Plan", callback_data="buy_plan"),
         InlineKeyboardButton("❓ Help & Guide", callback_data="help_guide")],
        [InlineKeyboardButton("🆘 Any Help", callback_data="any_help")],
        [InlineKeyboardButton("🔄 Full Account Reset", callback_data="reset_account"),
         InlineKeyboardButton("🚪 Logout", callback_data="logout")]
    ])

@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    user = await users_col.find_one({"user_id": user_id})
    
    now = datetime.utcnow()
    if not user:
        trial_expire = now + timedelta(minutes=30)
        user = {
            "user_id": user_id,
            "plan": "Free Trial",
            "plan_expire": trial_expire,
            "used": 0,
            "session_string": None,
            "destination_id": None
        }
        await users_col.insert_one(user)
    else:
        if user.get("plan") in ["VIP", "Free Trial"] and user.get("plan_expire"):
            if now > user.get("plan_expire"):
                await users_col.update_one({"user_id": user_id}, {"$set": {"plan": "Free"}})
                user["plan"] = "Free"
    
    is_logged = bool(user.get("session_string"))
    has_target = bool(user.get("destination_id"))
    plan_name = user.get('plan', 'Free')
    
    text = (
        "🔥 **ULTRA HIGH-SPEED RESTRICTED CONTENT EXTRACTOR** 🔥\n\n"
        f"🛡️ **PLAN:** `{plan_name}`\n"
        "⚡ Bina kisi restriction ke kisi bhi Private/Public Channel se files download aur forward karein!\n"
        "🚀 *Lightning-Fast Speed | Zero Master Bot Load | 100% Secure Sessions*\n\n"
        f"👤 **User:** {message.from_user.first_name}\n"
        f"🔑 **Session:** {'✅ Connected' if is_logged else '❌ Disconnected'} | 🎯 **Target:** {'✅ Set' if has_target else '❌ Not Set'}\n\n"
        "👇 *Apna operation niche diye gaye buttons se shuru karein:*"
    )
    await message.reply_text(text, reply_markup=main_menu_markup(is_logged, has_target))

@app.on_callback_query()
async def callback_handler(client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    user = await users_col.find_one({"user_id": user_id})
    
    if data == "buy_plan":
        text = (
            "👑 **VIP PREMIUM PLANS & PRICING**\n\n"
            "Apne zaroorat ke hisaab se plan select karein aur niche diye gaye UPI par payment karein:\n\n"
            "• **1 Day:** ₹20\n"
            "• **5 Days:** ₹30\n"
            "• **7 Days:** ₹50\n"
            "• **30 Days:** ₹120\n\n"
            f"💳 **UPI ID:** `{config.UPI_ID}`\n\n"
            "Payment karne ke baad **'I Have Paid'** button par click karein."
        )
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ I Have Paid", callback_data="i_have_paid")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_home")]
        ])
        await query.message.edit_text(text, reply_markup=markup)
        
    elif data == "i_have_paid":
        user_states[user_id] = {"step": "waiting_payment_proof"}
        await query.message.reply_text(
            "📤 Kripya apne **Payment ka Screenshot** ya **Transaction ID (TXN ID)** yahan bhej dein.\n"
            "Verification ke baad aapka VIP plan activate kar diya jayega!"
        )
        
    elif data == "help_guide":
        help_text = (
            "📖 **Bot Usage Guide & Commands:**\n\n"
            "• `/login` - Apna Telegram user account connect karne ke liye.\n"
            "• `/setchannel` - Destination channel set karne ke liye.\n"
            "• `/forward` - Private/Restricted channel post link ke liye.\n"
            "• `/publicforward` - Public channel transfer ke liye.\n"
            "• `/myplan` - Apna current plan check karne ke liye.\n"
            "• `/logout` - Account disconnect karne ke liye.\n"
            "• `/reset` - Settings reset karne ke liye."
        )
        await query.message.edit_text(help_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_home")]]))
        
    elif data == "any_help":
        await query.message.reply_text("🆘 Kisi bhi madad ke liye admin se sampark karein.")
        
    elif data == "reset_account" or data == "logout":
        await users_col.update_one({"user_id": user_id}, {"$set": {"session_string": None, "destination_id": None, "used": 0}})
        await query.message.edit_text("🔄 Account successfully reset / logged out!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Home", callback_data="back_home")]]))
        
    elif data == "start_forward":
        if not user or not user.get("session_string"):
            await query.message.reply_text("⚠️ Pehle apna Telegram account login karein. Command use karein: `/login`")
        elif not user.get("destination_id"):
            await query.message.reply_text("⚠️ Pehle destination channel set karein. Command use karein: `/setchannel`")
        else:
            await query.message.reply_text("✅ Sabhi setup ready hain! Ab jis restricted/private channel se content copy karna hai, uska post link yahan bhejein.")
            
    elif data == "back_home":
        is_logged = bool(user and user.get("session_string"))
        has_target = bool(user and user.get("destination_id"))
        text = (
            "🔥 **ULTRA HIGH-SPEED RESTRICTED CONTENT EXTRACTOR** 🔥\n\n"
            f"🛡️ **PLAN:** `{user.get('plan', 'Free')}`\n\n"
            "👇 *Apna operation niche diye gaye buttons se shuru karein:*"
        )
        await query.message.edit_text(text, reply_markup=main_menu_markup(is_logged, has_target))

@app.on_message(filters.command("login"))
async def login_command(client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "waiting_phone"}
    await message.reply_text("📱 Kripya apna Telegram phone number country code ke sath bhejein (jaise: `+919876543210`):")

@app.on_message(filters.command("setchannel"))
async def setchannel_command(client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "waiting_destination"}
    await message.reply_text("🎯 Kripya apne destination channel ka username ya ID bhejein (jaise `@mychannel` ya `-100xxxxxx`):")

@app.on_message(filters.command("myplan"))
async def myplan_command(client, message: Message):
    user_id = message.from_user.id
    user = await users_col.find_one({"user_id": user_id})
    if user:
        await message.reply_text(f"📊 **Your Plan Details:**\n\n• Plan: **{user.get('plan', 'Free')}**\n• Destination ID: {user.get('destination_id', 'Not Set')}")
    else:
        await message.reply_text("Pehle `/start` dabayein.")

@app.on_message(filters.text & filters.private)
async def text_handler(client, message: Message):
    user_id = message.from_user.id
    text = message.text
    
    if user_id in user_states:
        state = user_states[user_id].get("step")
        
        if state == "waiting_phone":
            phone = text.strip()
            try:
                temp_client = Client(f"session_{user_id}", api_id=config.API_ID, api_hash=config.API_HASH, in_memory=True)
                await temp_client.connect()
                sent_code = await temp_client.send_code(phone)
                user_states[user_id] = {
                    "step": "waiting_code",
                    "phone": phone,
                    "phone_code_hash": sent_code.phone_code_hash,
                    "temp_client": temp_client
                }
                await message.reply_text("📲 Telegram par ek OTP code aaya hoga. Kripya code bhejein:")
            except Exception as e:
                await message.reply_text(f"❌ Error: {str(e)}\nDobara `/login` try karein.")
                del user_states[user_id]
                
        elif state == "waiting_code":
            code = text.strip()
            st = user_states[user_id]
            temp_client = st["temp_client"]
            try:
                await temp_client.sign_in(st["phone"], st["phone_code_hash"], code)
                session_str = await temp_client.export_session_string()
                await temp_client.disconnect()
                
                await users_col.update_one({"user_id": user_id}, {"$set": {"session_string": session_str}}, upsert=True)
                await message.reply_text("✅ Account successfully connected and session saved!")
                del user_states[user_id]
            except SessionPasswordNeeded:
                user_states[user_id]["step"] = "waiting_password"
                await message.reply_text("🔐 Two-Step Verification Password bhejein:")
            except Exception as e:
                await message.reply_text(f"❌ Invalid Code: {str(e)}\nDobara `/login` try karein.")
                del user_states[user_id]
                
        elif state == "waiting_password":
            password = text.strip()
            st = user_states[user_id]
            temp_client = st["temp_client"]
            try:
                await temp_client.check_password(password)
                session_str = await temp_client.export_session_string()
                await temp_client.disconnect()
                
                await users_col.update_one({"user_id": user_id}, {"$set": {"session_string": session_str}}, upsert=True)
                await message.reply_text("✅ Account successfully connected with Password!")
                del user_states[user_id]
            except Exception as e:
                await message.reply_text(f"❌ Invalid Password: {str(e)}\nDobara `/login` try karein.")
                del user_states[user_id]
                
        elif state == "waiting_destination":
            dest = text.strip()
            await users_col.update_one({"user_id": user_id}, {"$set": {"destination_id": dest}}, upsert=True)
            await message.reply_text(f"✅ Destination channel successfully set to: `{dest}`")
            del user_states[user_id]
            
        elif state == "waiting_payment_proof":
            username = message.from_user.username or message.from_user.first_name
            markup = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
                ]
            ])
            await client.send_message(
                chat_id=config.ADMIN_ID,
                text=f"🔔 **New Payment Verification (TXN ID)!**\n\nUser: @{username} (ID: `{user_id}`)\nProof/Text: `{text}`",
                reply_markup=markup
            )
            await message.reply_text("⏳ Aapka payment proof admin ke paas bhej diya gaya hai. Verification ke baad plan activate hoga.")
            del user_states[user_id]

@app.on_message(filters.photo & filters.private)
async def handle_payment_screenshot(client, message: Message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id].get("step") == "waiting_payment_proof":
        username = message.from_user.username or message.from_user.first_name
        markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
            ]
        ])
        
        await client.send_photo(
            chat_id=config.ADMIN_ID,
            photo=message.photo.file_id,
            caption=f"🔔 **New Payment Screenshot Verification!**\n\nUser: @{username} (ID: `{user_id}`)",
            reply_markup=markup
        )
        await message.reply_text("⏳ Aapka payment screenshot admin ke paas approval ke liye bhej diya gaya hai.")
        del user_states[user_id]

@app.on_callback_query(filters.regex(r"^(approve|reject)_"))
async def admin_approval(client, query: CallbackQuery):
    if query.from_user.id != config.ADMIN_ID:
        await query.answer("Aap admin nahi hain!", show_alert=True)
        return
        
    action, user_id = query.data.split("_")
    user_id = int(user_id)
    
    if action == "approve":
        expire_time = datetime.utcnow() + timedelta(days=30)
        await users_col.update_one({"user_id": user_id}, {"$set": {"plan": "VIP (Approved)", "plan_expire": expire_time}})
        await client.send_message(user_id, "🎉 Badhai ho! Aapka VIP Premium Plan Admin dwara **Approve** kar diya gaya hai.")
        if query.message.photo:
            await query.message.edit_caption("✅ **Status: Approved & VIP Activated**")
        else:
            await query.message.edit_text("✅ **Status: Approved & VIP Activated**")
    else:
        await client.send_message(user_id, "❌ Maaf kijiye, aapka payment proof reject kar diya gaya hai.")
        if query.message.photo:
            await query.message.edit_caption("❌ **Status: Rejected**")
        else:
            await query.message.edit_text("❌ **Status: Rejected**")

print("Bot is running...")
app.run()
