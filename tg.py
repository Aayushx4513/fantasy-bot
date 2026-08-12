from flask import Flask
import pytz
from telegram.ext import MessageHandler, filters
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import os
import threading
import json
import time
import asyncio
import asyncpg

# ============ TOKEN & ADMINS ============
TOKEN = os.environ.get("BOT_TOKEN", "8265192837:AAG1_1VOoX5hm87eQG7IP75_vD9aK2Yk9HI")
ADMIN_IDS = [7687078555, 1315564307, 7361215114]

# ============ DATABASE URL ============
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres.qvdodaowbwkdxvlsvyyo:aayush0806q@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres")

# ============ FLASK ============
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

# ============ GLOBAL CONNECTION ============
db_conn = None

async def get_db():
    global db_conn
    if db_conn is None or db_conn.is_closed():
        db_conn = await asyncpg.connect(
            DATABASE_URL,
            statement_cache_size=0  # 🔥 YEH ADD KARO
        )
    return db_conn

# ============ DATABASE INIT ============
async def init_db():
    db = await get_db()
    
    # Users table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            name TEXT,
            balance BIGINT DEFAULT 1000,
            points INT DEFAULT 0,
            won INT DEFAULT 0,
            total INT DEFAULT 0,
            photo TEXT,
            bio TEXT
        )
    ''')
    
    # Matches table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id SERIAL PRIMARY KEY,
            team1 TEXT,
            team2 TEXT,
            date TEXT,
            status TEXT,
            locked INT DEFAULT 0
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS auction_players (
            id SERIAL PRIMARY KEY,
            name TEXT,
            base_price INT,
            current_bid INT,
            highest_bidder BIGINT,
            added_by BIGINT,
            added_at TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'active'  -- active, ended, sold
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS cricket_stats (
            user_id BIGINT PRIMARY KEY,
            name TEXT,
            runs INT DEFAULT 0,
            wickets INT DEFAULT 0,
            wins INT DEFAULT 0,
            losses INT DEFAULT 0,
            highest_score INT DEFAULT 0,
            ducks INT DEFAULT 0
        )
    ''')


    await db.execute('''
        CREATE TABLE IF NOT EXISTS login_tracker (
            user_id BIGINT PRIMARY KEY,
            last_login DATE
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS penalty_history (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            penalty_date DATE,
            balance_after INT
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS user_players (
            user_id BIGINT,
            player_id INT,
            purchased_at TIMESTAMP,
            PRIMARY KEY (user_id, player_id)
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS bid_history (
            id SERIAL PRIMARY KEY,
            player_id INT,
            user_id BIGINT,
            amount INT,
            bid_at TIMESTAMP
        )
    ''')

    # Bets table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS bets (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            match_id INT,
            team TEXT,
            amount INT
        )
    ''')
    
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS login_tracker (
            user_id BIGINT PRIMARY KEY,
            last_login DATE
        )
    ''')


    await db.execute('''
        CREATE TABLE IF NOT EXISTS user_cooldown (
            user_id BIGINT PRIMARY KEY,
            last_flip TIMESTAMP,
            last_dice TIMESTAMP
        )
    ''')

    # Claim table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS claim (
            user_id BIGINT PRIMARY KEY,
            last_claim DATE
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS couple_data (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')


    await db.execute('''
        CREATE TABLE IF NOT EXISTS rain_cooldown (
            chat_id BIGINT PRIMARY KEY,
            last_rain TIMESTAMP
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id BIGINT,
            chat_id BIGINT,
            activity_score INT DEFAULT 0,
            last_active TIMESTAMP,
            PRIMARY KEY (user_id, chat_id)
        )
    ''')


    await db.execute('''
        CREATE TABLE IF NOT EXISTS hilo_games (
            game_id TEXT PRIMARY KEY,
            user_id BIGINT,
            data TEXT,
            created_at TIMESTAMP
        )
    ''')


    await db.execute("""
        CREATE TABLE IF NOT EXISTS daily_couples (
            id SERIAL PRIMARY KEY,
            group_id BIGINT,
            couple1_id BIGINT,
            couple1_name TEXT,
            couple2_id BIGINT,
            couple2_name TEXT,
            date DATE,
            UNIQUE(group_id, date)
        )
    """)


    # Spin table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS spin (
            user_id BIGINT PRIMARY KEY,
            last_claim TEXT
        )
    ''')
    
    # Shop tables
    await db.execute('''
        CREATE TABLE IF NOT EXISTS shop (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price INT,
            category TEXT,
            type TEXT
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS daily (
            user_id BIGINT PRIMARY KEY,
            last_claim DATE
        )
    ''')


    await db.execute('''
        CREATE TABLE IF NOT EXISTS lottery_tickets (
            user_id BIGINT,
            ticket TEXT,
            purchased_at TIMESTAMP
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS lottery_participants (
            user_id BIGINT PRIMARY KEY,
            name TEXT
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS lottery_data (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS shop_women (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price INT,
            country TEXT,
            type TEXT
        )
    ''')
    
    await db.execute('''
         CREATE TABLE IF NOT EXISTS shop2 (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price INT
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS shop3 (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price INT
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS shop4 (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price INT
        )
    ''')
    
    # User players
    await db.execute('''
        CREATE TABLE IF NOT EXISTS user_players (
            user_id BIGINT,
            player_id INT,
            type TEXT
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS user_players2 (
            user_id BIGINT,
            player_id INT
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS user_players3 (
            user_id BIGINT,
            player_id INT
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS user_players4 (
            user_id BIGINT,
            player_id INT
        )
    ''')
    
    # Bank table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS bank (
            user_id BIGINT PRIMARY KEY,
            balance BIGINT DEFAULT 0,
            last_interest TEXT
        )
    ''')
    
    # Achievements
    await db.execute('''
        CREATE TABLE IF NOT EXISTS achievements (
            user_id BIGINT,
            achievement TEXT
        )
    ''')
    
    # Claim codes
    await db.execute('''
        CREATE TABLE IF NOT EXISTS claim_codes (
            id SERIAL PRIMARY KEY,
            code TEXT UNIQUE,
            amount INT,
            max_claims INT,
            claimed_count INT DEFAULT 0,
            created_by BIGINT,
            created_at TEXT,
            expires_at TEXT
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS interest_history (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount INT,
            type TEXT,
            claimed_at TIMESTAMP
        )
    ''')

    await db.execute('''
        CREATE TABLE IF NOT EXISTS code_claims (
            code TEXT,
            user_id BIGINT,
            claimed_at TEXT,
            PRIMARY KEY (code, user_id)
        )
    ''')
    
    # Hall of Fame
    await db.execute('''
        CREATE TABLE IF NOT EXISTS hall_of_fame (
            id SERIAL PRIMARY KEY,
            winner TEXT,
            added_by BIGINT,
            added_at TEXT
        )
    ''')
    
    # Numpuz progress
    await db.execute('''
        CREATE TABLE IF NOT EXISTS numpuz_progress (
            user_id BIGINT PRIMARY KEY,
            level INT DEFAULT 1,
            board TEXT,
            moves INT DEFAULT 0,
            chat_id BIGINT,
            owner_id BIGINT
        )
    ''')
    
    # Cricket stats
    await db.execute('''
        CREATE TABLE IF NOT EXISTS cricket_stats (
            user_id BIGINT PRIMARY KEY,
            name TEXT,
            runs INT DEFAULT 0,
            wickets INT DEFAULT 0,
            wins INT DEFAULT 0,
            losses INT DEFAULT 0,
            highest_score INT DEFAULT 0,
            ducks INT DEFAULT 0
        )
    ''')
    
    # Groups
    await db.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            group_id BIGINT PRIMARY KEY,
            group_name TEXT,
            added_at TEXT
        )
    ''')
    
    # Referral
    await db.execute('''
        CREATE TABLE IF NOT EXISTS referral (
            user_id BIGINT PRIMARY KEY,
            referred_by BIGINT,
            referred_at TEXT
        )
    ''')
    
    # Lottery tables
    await db.execute('''
        CREATE TABLE IF NOT EXISTS lottery_tickets (
            user_id BIGINT,
            ticket TEXT,
            purchased_at TEXT
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS lottery_coupons (
            code TEXT PRIMARY KEY,
            quantity INT,
            used INT DEFAULT 0
        )
    ''')
    
    await db.execute('''
        CREATE TABLE IF NOT EXISTS coupon_used (
            code TEXT,
            user_id BIGINT,
            PRIMARY KEY (code, user_id)
        )
    ''')
    
    print("✅ PostgreSQL tables created!")
    await db.close()

# ============ HELPER FUNCTIONS ============
async def is_registered(user_id):
    db = await get_db()
    result = await db.fetchval("SELECT user_id FROM users WHERE user_id = $1", user_id)
    await db.close()
    return result is not None

async def get_user(user_id, name=""):
    db = await get_db()
    user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
    if not user:
        await db.execute(
            "INSERT INTO users (user_id, name, balance, points, won, total) VALUES ($1, $2, 1000, 0, 0, 0)",
            user_id, name
        )
        user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
    await db.close()
    return user

async def update_balance(user_id, amount):
    db = await get_db()
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)
    await db.close()

async def get_balance(user_id):
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await db.close()
    return balance if balance else 0

# ============ LOTTERY GLOBALS ==========
import random as rand
import string

lottery_active = False
lottery_tickets = {}
lottery_total_tickets = 0
lottery_participants = []
lottery_winner = None
lottery_start_time = None

def generate_ticket_number():
    return ''.join(rand.choices(string.ascii_uppercase + string.digits, k=8))

# ============ HILO GAME GLOBALS ==========
hilo_games = {}

CARD_VALUES = {
    'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 11, 'Q': 12, 'K': 13
}

SUITS = ['♠️', '♥️', '♣️', '♦️']

def get_random_card():
    value = rand.choice(list(CARD_VALUES.keys()))
    suit = rand.choice(SUITS)
    return {'value': value, 'suit': suit, 'rank': CARD_VALUES[value]}

def get_multiplier_increase(diff):
    if diff == 0: return 0.50
    elif diff == 1: return 0.05
    elif diff <= 3: return 0.08
    elif diff <= 6: return 0.12
    elif diff <= 9: return 0.18
    else: return 0.25

# ============ REFER ==========
async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    bot_username = context.bot.username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await update.message.reply_text(f"👥 REFERRAL SYSTEM\n\nInvite friends and earn 1,000 credits each!\n\nYour Link: {ref_link}\n\nNew users get +500 bonus!")

# ============ START COMMAND ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name if user.first_name else user.username or "User"
    user_id = user.id
    
    referred_by = None
    if context.args and len(context.args) > 0 and context.args[0].startswith("ref_"):
        try:
            referred_by = int(context.args[0].split("_")[1])
        except:
            pass
    
    db = await get_db()
    
    existing = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
    
    if not existing:
        await db.execute(
            "INSERT INTO users (user_id, name, balance, points, won, total) VALUES ($1, $2, 1000, 0, 0, 0)",
            user_id, name
        )
        
        if referred_by and referred_by != user_id:
            ref_exists = await db.fetchval("SELECT user_id FROM users WHERE user_id = $1", referred_by)
            if ref_exists:
                ref_used = await db.fetchval("SELECT user_id FROM referral WHERE user_id = $1", user_id)
                if not ref_used:
                    await db.execute(
                        "INSERT INTO referral (user_id, referred_by, referred_at) VALUES ($1, $2, $3)",
                        user_id, referred_by, datetime.now().isoformat()
                    )
                    await db.execute("UPDATE users SET balance = balance + 1000 WHERE user_id = $1", referred_by)
                    await db.execute("UPDATE users SET balance = balance + 500 WHERE user_id = $1", user_id)
                    try:
                        await context.bot.send_message(referred_by, f"🎉 REFERRAL REWARD!\n\n@{name} joined using your link!\n💰 +1,000 credits!")
                    except:
                        pass
                    await update.message.reply_text("🎉 WELCOME!\n\nYou joined with a referral!\n💰 +500 bonus credits!")
        
        keyboard = [
            [InlineKeyboardButton("📢 UPDATES", url="https://t.me/clbotofficial")],
            [InlineKeyboardButton("👥 MAIN GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✨ WELCOME TO CL ZONE ✨\n\n"
            f"👑 {name}, you've joined the elite club!\n"
            f"💰 1000 credits | 🏆 0 pts\n\n"
            f"🎯 /claim - Daily rewards\n"
            f"🎡 /spin - Daily spin\n"
            f"👤 /profile - Your stats\n"
            f"🏆 /leaderboard - Top players\n\n"
            f"📌 Join our channels for exclusive updates!",
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📢 UPDATES", url="https://t.me/clbotofficial")],
            [InlineKeyboardButton("👥 MAIN GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]
         ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✨ WELCOME BACK TO CL ZONE ✨\n\n"
            f"👑 {name}\n"
            f"💰 {existing['balance']:,} credits | 🏆 {existing['points']} pts\n\n"
            f"🎯 /claim - Daily rewards\n"
            f"🎡 /spin - Daily spin\n"
            f"👤 /profile - Your stats\n"
            f"🏆 /leaderboard - Top players\n\n"
            f"📌 Stay connected with our community!",
            reply_markup=reply_markup
        )
    
    await db.close()


import re

# ============ ESCAPE FUNCTION ==========
def escape_markdown(text):
    """Escape markdown special characters only"""
    # 🔥 . HATAO, SIRF SPECIAL CHARACTERS RAKHO
    special_chars = r'([_*\[\]()~`>#+\-=|{}])'
    return re.sub(special_chars, r'\\\1', text)

# ============ PROFILE ==========
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text("❌ *Send /start first!*", parse_mode="Markdown")
        return

    user = update.effective_user
    name = user.first_name if user.first_name else (user.username or "User")

    db = await get_db()
    data = await db.fetchrow("SELECT balance, points, won, total, photo, bio FROM users WHERE user_id = $1", user_id)

    if not data:
        await db.close()
        await update.message.reply_text("❌ *Profile not found!*", parse_mode="Markdown")
        return

    bank_bal = await db.fetchval("SELECT balance FROM bank WHERE user_id = $1", user_id) or 0

    wallet_bal, points, won, total, photo, bio = data
    total_wealth = wallet_bal + bank_bal

    if won > total:
        await db.execute("UPDATE users SET total = $1 WHERE user_id = $2", won, user_id)
        total = won

    if total > 0:
        win_rate = int((won / total) * 100)
        if win_rate > 100:
            win_rate = 100
    else:
        win_rate = 0

    await db.close()

    DEFAULT_BIO = "I Play With CL Bot!"

    # 🔥 ESCAPE NAMES (DOT ESCAPE NAHI HOGA)
    name_escaped = escape_markdown(name)
    bio_escaped = escape_markdown(bio) if bio else DEFAULT_BIO

    profile_text = f"👤 *PROFILE*\n\n"
    profile_text += f"*Name:* {name_escaped}\n"
    profile_text += f"*Bio:* {bio_escaped}\n"
    profile_text += f"\n💰 *Wallet:* {wallet_bal:,}\n"
    profile_text += f"🏦 *Bank:* {bank_bal:,}\n"
    profile_text += f"💎 *Total:* {total_wealth:,}\n\n"
    profile_text += f"🏆 *Points:* {points}\n"
    profile_text += f"📊 *Bets:* {won}/{total}\n"
    profile_text += f"📈 *Win Rate:* {win_rate}%"

    if photo:
        await update.message.reply_photo(photo=photo, caption=profile_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(profile_text, parse_mode="Markdown")


# ============ SETBIO ==========
async def setbio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ *Send /start first!*', parse_mode="Markdown")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ *Usage:* /setbio <your bio>", parse_mode="Markdown")
        return
    
    bio = " ".join(args)
    if len(bio) > 100:
        await update.message.reply_text("❌ *Bio too long!*", parse_mode="Markdown")
        return
    
    db = await get_db()
    await db.execute("UPDATE users SET bio = $1 WHERE user_id = $2", bio, user_id)
    await db.close()
    
    bio_escaped = escape_markdown(bio)
    await update.message.reply_text(f"✅ *Bio updated!*\n\n{bio_escaped}", parse_mode="Markdown")


# ============ RMBIO ==========
async def rmbio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ *Send /start first!*', parse_mode="Markdown")
        return
    
    db = await get_db()
    await db.execute("UPDATE users SET bio = 'I Play With CL Bot!' WHERE user_id = $1", user_id)
    await db.close()
    
    await update.message.reply_text("✅ *Bio reset to default!*\n\n*I Play With CL Bot!*", parse_mode="Markdown")


async def setpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    if not update.message.reply_to_message:
        await update.message.reply_text('❌ Reply to a photo with /setpfp')
        return
    if not update.message.reply_to_message.photo:
        await update.message.reply_text('❌ Reply to a PHOTO with /setpfp')
        return
    photo = update.message.reply_to_message.photo[-1].file_id
    db = await get_db()
    await db.execute("UPDATE users SET photo = $1 WHERE user_id = $2", photo, user_id)
    await db.close()
    await update.message.reply_text('✅ Profile photo updated!')

async def rmpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    db = await get_db()
    await db.execute("UPDATE users SET photo = NULL WHERE user_id = $1", user_id)
    await db.close()
    await update.message.reply_text('❌ Profile photo removed!')

# ============ CLAIM ==========
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    chat_type = update.message.chat.type

    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    CL_GROUP_ID = -1001661258033

    db = await get_db()

    last = await db.fetchval("SELECT last_claim FROM claim WHERE user_id = $1", user_id)

    today = datetime.now().date()
    today_str = today.strftime("%m/%d/%y")

    if last:
        if last == today:
            await update.message.reply_text("*⚠️ Already claimed today!*\n*Come back tomorrow.*", parse_mode="Markdown")
            await db.close()
            return

    if chat_type in ['group', 'supergroup'] and chat_id == CL_GROUP_ID:
        reward = 1000
        extra_note = "\n\n*💡 You got BONUS 1000 credits in CL Zone Group!*"
        keyboard = None  # 🔥 GC MEIN BUTTON NAHI
    else:
        reward = 500
        extra_note = "\n\n*💡 Tip: Use /claim in CL Zone Group to get 1000 credits!*"
        # 🔥 PRIVATE CHAT MEIN BUTTON
        keyboard = [
            [InlineKeyboardButton("👥 JOIN CL ZONE GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]
        ]

    await db.execute("INSERT INTO claim (user_id, last_claim) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET last_claim = $2", user_id, today)
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", reward, user_id)

    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await db.close()

    await update.message.reply_text(
        f"*✅ Claimed Daily Rewards!*\n\n"
        f"*💰 +{reward} credits*\n"
        f"*📅 {today_str}*\n"
        f"*💳 New balance: {new_bal:,}*"
        f"{extra_note}\n\n"
        f"*🔄 Next claim: tomorrow*",
        disable_web_page_preview=True,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )

# ============ ACHIEVE COMMAND (ADMIN) ==========
async def achieve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    if not update.message.reply_to_message:
        await update.message.reply_text('❌ Reply to user with /achieve ACHIEVEMENT_NAME')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /achieve ACHIEVEMENT_NAME')
        return
    achievement = ' '.join(args)
    target = update.message.reply_to_message.from_user
    db = await get_db()
    await db.execute("INSERT INTO achievements (user_id, achievement) VALUES ($1, $2)", target.id, achievement)
    await db.close()
    await update.message.reply_text(f"✅ ACHIEVEMENT GIVEN!\n\nUser: {target.first_name}\nAchievement: {achievement} 🏆")

# ============ RMACHIEVE COMMAND (ADMIN) ==========
async def rmachieve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /rmachieve <number>')
        return
    try:
        num = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid number')
        return
    target_id = update.effective_user.id
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    db = await get_db()
    achievements = await db.fetch("SELECT row_number() OVER () as rowid, achievement FROM achievements WHERE user_id = $1", target_id)
    if num < 1 or num > len(achievements):
        await update.message.reply_text(f'❌ Choose 1-{len(achievements)}')
        await db.close()
        return
    removed = achievements[num-1]
    await db.execute("DELETE FROM achievements WHERE user_id = $1 AND achievement = $2", target_id, removed['achievement'])
    await db.close()
    await update.message.reply_text(f"✅ ACHIEVEMENT REMOVED!\n\nRemoved: {removed['achievement']} 🏆")

# ============ UNLOCKMATCH COMMAND (ADMIN) ==========
async def unlockmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('❌ /unlockmatch TEAM1 vs TEAM2\nExample: /unlockmatch India vs Afghanistan')
        return
    
    team1 = args[0]
    team2 = args[2]
    
    db = await get_db()
    
    # 🔥 CASE INSENSITIVE SEARCH
    match = await db.fetchrow("""
        SELECT id, team1, team2, locked 
        FROM matches 
        WHERE LOWER(team1) = LOWER($1) AND LOWER(team2) = LOWER($2)
    """, team1, team2)
    
    if not match:
        await update.message.reply_text(f'❌ Match {team1} vs {team2} not found!')
        await db.close()
        return
    
    if match['locked'] == 0:
        await update.message.reply_text(f'⚠️ Match is already UNLOCKED!')
        await db.close()
        return
    
    await db.execute("UPDATE matches SET locked = 0 WHERE id = $1", match['id'])
    
    # Get total bets
    total = await db.fetchval("SELECT COALESCE(SUM(amount), 0) FROM bets WHERE match_id = $1", match['id'])
    count = await db.fetchval("SELECT COUNT(*) FROM bets WHERE match_id = $1", match['id'])
    
    await db.close()
    
    await update.message.reply_text(
        f"🔓 MATCH UNLOCKED!\n\n"
        f"🏏 {match['team1']} vs {match['team2']}\n"
        f"📊 Current Bets: {count}\n"
        f"💰 Current Pool: {total:,} 💰\n"
        f"✅ New bets are now accepted again!"
    )

# ============ CODELER COMMANDS (ADMIN) ==========
async def deletecode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: /deletecode CODE123")
        return
    code = args[0].upper()
    db = await get_db()
    exists = await db.fetchval("SELECT code FROM claim_codes WHERE code = $1", code)
    if not exists:
        await update.message.reply_text(f"❌ Code '{code}' not found!")
        await db.close()
        return
    await db.execute("DELETE FROM claim_codes WHERE code = $1", code)
    await db.execute("DELETE FROM code_claims WHERE code = $1", code)
    await db.close()
    await update.message.reply_text(f"✅ Code '{code}' deleted!")

async def codestats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    db = await get_db()
    total_codes = await db.fetchval("SELECT COUNT(*) FROM claim_codes")
    active_codes = await db.fetchval("SELECT COUNT(*) FROM claim_codes WHERE expires_at > now() AND claimed_count < max_claims")
    total_claims = await db.fetchval("SELECT COUNT(*) FROM code_claims")
    total_given = await db.fetchval("SELECT COALESCE(SUM(amount), 0) FROM code_claims cc JOIN claim_codes c ON cc.code = c.code")
    unique_users = await db.fetchval("SELECT COUNT(DISTINCT user_id) FROM code_claims")
    await db.close()
    await update.message.reply_text(f"📊 CODE STATS\n\n📝 Total codes: {total_codes}\n🟢 Active codes: {active_codes}\n🎯 Total claims: {total_claims}\n💰 Credits given: {total_given:,}\n👥 Unique users: {unique_users}")

# ============ SPIN ==========
async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('*❌ Send /start first!*', parse_mode="Markdown")
        return

    db = await get_db()
    last = await db.fetchval("SELECT last_claim FROM spin WHERE user_id = $1", user_id)

    now = datetime.now()
    today_str = now.strftime("%m/%d/%y")

    # 🔥 DAILY RESET - CLAIM JESA
    if last:
        last_date = datetime.fromisoformat(last).date()
        if last_date == now.date():
            await update.message.reply_text(
                f"*⚠️ Already spin today!*\n*Come back tomorrow.*",
                parse_mode="Markdown"
            )
            await db.close()
            return

    amount = random.randint(1000, 10000)

    await db.execute(
        "INSERT INTO spin (user_id, last_claim) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET last_claim = $2",
        user_id, now.isoformat()
    )
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)

    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await db.close()

    await update.message.reply_text(
        f"*✅ Claimed Daily Spin Rewards of {amount:,} Credits*\n"
        f"*at {today_str}*\n\n"
        f"*💰 New balance: {new_bal:,} 💰*\n"
        f"*🎡 Next spin: tomorrow*",
        parse_mode="Markdown"
    )

# ============ DICE ==========
async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    # 🔥 COOLDOWN CHECK (4 seconds)
    db = await get_db()
    last_dice = await db.fetchval("SELECT last_dice FROM user_cooldown WHERE user_id = $1", user_id)
    
    if last_dice and (datetime.now() - last_dice).seconds < 4:
        await update.message.reply_text("⏰ You are on cooldown of few seconds.")
        await db.close()
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text('🎲 /dice <amount>\n\nMultipliers: 1(0x) 2(0.25x) 3(0.5x) 4(1.25x) 5(1.5x) 6(2.5x)\n💰 Min: 100 | Max: 20,000')
        await db.close()
        return

    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid amount')
        await db.close()
        return

    if amount < 100:
        await update.message.reply_text('❌ Minimum 100 credits')
        await db.close()
        return

    if amount > 20000:
        await update.message.reply_text('❌ Maximum 20,000 credits')
        await db.close()
        return

    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)

    if balance < amount:
        await update.message.reply_text(f'❌ Need {amount:,}, have {balance:,}')
        await db.close()
        return

    roll = random.randint(1, 6)
    dice_emoji = {1:'⚀', 2:'⚁', 3:'⚂', 4:'⚃', 5:'⚄', 6:'⚅'}
    multi = {1:0, 2:0.25, 3:0.5, 4:1.25, 5:1.5, 6:2.5}
    win = int(amount * multi[roll])
    new_bal = balance - amount + win

    await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_bal, user_id)
    
    # 🔥 UPDATE LAST USED TIME
    await db.execute("INSERT INTO user_cooldown (user_id, last_dice) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET last_dice = $2", user_id, datetime.now())
    await db.close()

    if win > 0:
        await update.message.reply_text(f"🎲 DICE\n\n🎲 Rolled: {roll} {dice_emoji[roll]}\n✨ You won {win:,} 💰 ({multi[roll]}x)\n💰 New balance: {new_bal:,} 💰")
    else:
        await update.message.reply_text(f"🎲 DICE\n\n🎲 Rolled: {roll} {dice_emoji[roll]}\n💀 You lost {amount:,} 💰\n💰 New balance: {new_bal:,} 💰")

# ============ FLIP ==========
async def flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    # 🔥 COOLDOWN CHECK (4 seconds)
    db = await get_db()
    last_flip = await db.fetchval("SELECT last_flip FROM user_cooldown WHERE user_id = $1", user_id)
    
    if last_flip and (datetime.now() - last_flip).seconds < 4:
        await update.message.reply_text("⏰ You are on cooldown of few seconds.")
        await db.close()
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('🪙 /flip heads/tails <amount>\nExample: /flip heads 1000\n\n💰 Min: 100 | Max: 20,000')
        await db.close()
        return

    choice = args[0].lower()
    if choice not in ['heads', 'tails']:
        await update.message.reply_text('❌ Choose heads or tails')
        await db.close()
        return

    try:
        amount = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid amount')
        await db.close()
        return

    if amount < 100:
        await update.message.reply_text('❌ Minimum 100 credits')
        await db.close()
        return

    if amount > 20000:
        await update.message.reply_text('❌ Maximum 20,000 credits')
        await db.close()
        return

    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)

    if balance < amount:
        await update.message.reply_text(f'❌ Need {amount:,}, have {balance:,}')
        await db.close()
        return

    result = random.choice(['heads', 'tails'])

    if choice == result:
        win = amount * 2
        new_bal = balance - amount + win
        await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_bal, user_id)
        # 🔥 UPDATE LAST USED TIME
        await db.execute("INSERT INTO user_cooldown (user_id, last_flip) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET last_flip = $2", user_id, datetime.now())
        await db.close()
        await update.message.reply_text(f"🪙 {result.upper()}! You won {win:,} 💰\n💰 New balance: {new_bal:,} 💰")
    else:
        new_bal = balance - amount
        await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_bal, user_id)
        await db.execute("INSERT INTO user_cooldown (user_id, last_flip) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET last_flip = $2", user_id, datetime.now())
        await db.close()
        await update.message.reply_text(f"😞 {result.upper()}! You lost {amount:,} 💰\n💰 New balance: {new_bal:,} 💰")

# ============ HELP COMMAND ==========
# ============ HELP COMMAND ==========
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    msg = (
        "*📋 CL BOT - COMMAND LIST*\n\n"
        "*👤 PROFILE*\n"
        "• /start - Start bot\n"
        "• /profile - Your stats & collection\n"
        "• /balance - Check wallet balance\n"
        "• /leaderboard - Top 10 Richest users\n"
        "• /setbio <text> - Set bio\n"
        "• /rmbio - Remove bio\n"
        "• /setpfp - Set photo (reply to pic)\n"
        "• /rmpfp - Remove photo\n\n"
        "*💰 EARN CREDITS*\n"
        "• /claim - 500 daily\n"
        "• /spin - 1,000-10,000 daily\n"
        "• /dice <amount> - 0x to 2.5x\n"
        "• /flip heads/tails <amount> - 2x\n"
        "• /tip <amount> (reply) - Send credits\n\n"
        "*🏏 CRICKET BETTING*\n"
        "• /matches - Live matches\n"
        "• /bet <team> <amount> - Place bet\n"
        "• /mybets - Your bets\n"
        "• /cancel <number> - Cancel bet\n"
        "• /allbets - All bets\n"
        "• /history - Win/loss record\n"
        "• /top_fantasy - Fantasy points ranking\n\n"
        "*🏆 ACHIEVEMENTS*\n"
        "• /achievements - Your badges\n"
        "• /hof - Hall of Fame\n\n"
        "*🛒 SHOP*\n"
        "• /shop - Buy players\n"
        "• /buy <id> - Purchase mens player\n"
        "• /buyw <id> - Purchase women player\n"
        "• /myteam - Your collection\n"
        "• /top - Top collectors\n\n"
        "*🛍️ AFFORDABLE STORE*\n"
        "• /shop2 - Budget players\n"
        "• /buy2 <id> - Purchase\n"
        "• /myteam2 - Your collection\n"
        "• /top2 - Top collectors\n\n"
        "*🛒 TG PLAYERS*\n"
        "• /shop3 - Telegram players\n"
        "• /buy3 <id> - Purchase\n"
        "• /myteam3 - Your collection\n"
        "• /top3 - Top collectors\n\n"
        "*🏦 BANK*\n"
        "• /bank - Check balance\n"
        "• /deposit <amount> - Add to bank\n"
        "• /withdraw <amount> - Take from bank\n"
        "• /claim_interest - 5% daily\n\n"
        "*🎰 LOTTERY*\n"
        "• /lottery - Lottery menu\n"
        "• /buy_ticket <qty> - Buy tickets (20k each)\n"
        "• /mytickets - Your tickets\n"
        "• /lottery_info - Lottery stats\n"
        "• /claim_coupon <code> - Claim free tickets\n\n"
        "*🎮 GAMES*\n"
        "• /hilo <bet> - HiLo card game (100-10k bet)\n"
        "• /ttt [amount] - Tic Tac Toe\n"
        "• /mines <amount> <bombs> - Mines game\n"
        "• /CLcricket [amount] - Cricket game\n"
        "• /rps [amount] - Rock Paper Scissors\n"
        "• /numguess - Number guessing game\n"
        "• /ng <number> - Make a guess\n"
        "• /claimcode <code> - Claim rewards\n"
        "• /activecodes - Active codes\n"
        "• /numpuz - Number puzzle\n"
        "• /tower - Tower climb game\n\n"
        "*🎁 REFERRAL*\n"
        "• /refer - Get your link (1k per refer)\n\n"
        "*💡 Need help? @clbothelp*"
    )

    # 🔥 BUTTON - GROUP LINK
    keyboard = [
        [InlineKeyboardButton("👥 JOIN CL ZONE GROUP", url="https://t.me/+EsC9tYVccrJmNDY1")]
    ]

    await update.message.reply_text(
        msg,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============ LEADERBOARD ==========
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    db = await get_db()

    # 🔥 TOP 10 USERS (Wallet + Bank)
    users_data = await db.fetch("""
        SELECT u.name, u.balance + COALESCE(b.balance, 0) as total_wealth
        FROM users u
        LEFT JOIN bank b ON u.user_id = b.user_id
        ORDER BY total_wealth DESC
        LIMIT 10
    """)

    msg = "🌍 *Global Top 10 — Coins 🪙*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"

    # 🔥 EMOJIS
    emojis = ["👑", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, u in enumerate(users_data):
        name = u['name']
        wealth = u['total_wealth']
        msg += f"{emojis[i]} {name} : *{wealth:,}*\n"

    # 🔥 USER RANK
    user_total = await db.fetchval("""
        SELECT u.balance + COALESCE(b.balance, 0)
        FROM users u
        LEFT JOIN bank b ON u.user_id = b.user_id
        WHERE u.user_id = $1
    """, user_id)

    rank = await db.fetchval("""
        SELECT COUNT(*) + 1 FROM (
            SELECT u.balance + COALESCE(b.balance, 0) as total
            FROM users u
            LEFT JOIN bank b ON u.user_id = b.user_id
        ) t WHERE total > $1
    """, user_total)

    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📌 Your Position: #{rank}\n"
    msg += f"🪙 Total wealth : *{user_total:,}*"

    await update.message.reply_text(msg, parse_mode="Markdown")
    await db.close()

# ============ TOP FANTASY ==========
async def top_fantasy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    db = await get_db()
    
    users_data = await db.fetch("SELECT name, points FROM users ORDER BY points DESC LIMIT 20")

    if not users_data:
        await update.message.reply_text('📭 No fantasy points yet!')
        await db.close()
        return

    msg = "🏆 FANTASY LEADERBOARD\n\n"
    for i, u in enumerate(users_data, 1):
        msg += f"{i}. {u['name']} - {u['points']} pts\n"

    # 🔥 DIRECT DB SE USER POINTS LE
    user_points = await db.fetchval("SELECT points FROM users WHERE user_id = $1", user_id)
    
    if user_points is not None:
        rank = await db.fetchval("SELECT COUNT(*) + 1 FROM users WHERE points > $1", user_points)
        if rank is None:
            rank = 1
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your points: {user_points} | Rank: #{rank}"
    else:
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 You are not registered yet!"
    
    await db.close()
    await update.message.reply_text(msg)

import re

def escape_md(text):
    """Escape markdown special characters"""
    special_chars = r'([_*\[\]()~`>#+\-=|{}.!])'
    return re.sub(special_chars, r'\\\1', str(text))


# ============ TIP ==========
async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    ALLOWED_GROUP_ID = -1001661258033
    GROUP_LINK = "https://t.me/+eTD1m8Cjc_wyOTNl"

    if chat_type != 'supergroup' or chat_id != ALLOWED_GROUP_ID:
        await msg.reply_text(
            "🚫 Access Denied!\n\nThe /tip command can only be used in the Official Group Chat.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 JOIN CL ZONE GROUP", url=GROUP_LINK)]
            ])
        )
        return

    if not await is_registered(user_id):
        await msg.reply_text('❌ Send /start first!')
        return

    if not msg.reply_to_message:
        await msg.reply_text('❌ Reply to user with /tip AMOUNT')
        return

    args = context.args
    if len(args) < 1:
        await msg.reply_text('❌ /tip AMOUNT\nExample: /tip 500')
        return

    try:
        amount = int(args[0])
    except:
        await msg.reply_text('❌ Invalid amount')
        return

    if amount <= 0:
        await msg.reply_text('❌ Amount must be greater than 0!')
        return

    sender = update.effective_user
    receiver = msg.reply_to_message.from_user

    if sender.id == receiver.id:
        await msg.reply_text('❌ Cannot tip yourself!')
        return

    db = await get_db()
    sender_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", sender.id)

    if sender_bal is None:
        await msg.reply_text("❌ You are not registered! Send /start first.")
        await db.close()
        return

    if sender_bal < amount:
        await msg.reply_text(f'❌ Need {amount:,}, have {sender_bal:,}')
        await db.close()
        return

    fee = int(amount * 0.05)
    receiver_amount = amount - fee

    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", amount, sender.id)
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", receiver_amount, receiver.id)
    sender_new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", sender.id)
    await db.close()

    sender_name = f"@{sender.username}" if sender.username else sender.first_name
    receiver_name = f"@{receiver.username}" if receiver.username else receiver.first_name

    caption = (
        f"💝 TIP SENT!\n\n"
        f"FROM: {sender_name}\n"
        f"TO: {receiver_name}\n"
        f"💰 Amount: {amount:,}\n"
        f"💸 Fee (5%): {fee:,}\n"
        f"📥 Received: {receiver_amount:,}\n\n"
        f"📊 Your balance: {sender_new_bal:,} 💰"
    )

    await msg.reply_text(caption)

# ============ ACHIEVEMENTS ==========
async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('*❌ Send /start first!*', parse_mode="Markdown")
        return

    db = await get_db()
    ach = await db.fetch("SELECT achievement FROM achievements WHERE user_id = $1", user_id)
    await db.close()

    if not ach:
        await update.message.reply_text(
            "*🏆 MY ACHIEVEMENTS*\n\n"
            "*No achievements yet!*",
            parse_mode="Markdown"
        )
        return

    msg = "*🏆 MY ACHIEVEMENTS*\n\n"
    for i, a in enumerate(ach, 1):
        msg += f"*{i}. {a['achievement']} 🏆*\n"
    msg += f"\n*━━━━━━━━━━━━━━━━━━━━━━*\n"
    msg += f"*Total: {len(ach)} achievements*"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


# ============ BANK SYSTEM ==========
async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    
    # Insert if not exists
    await db.execute("INSERT INTO bank (user_id, balance, last_interest) VALUES ($1, 0, $2) ON CONFLICT (user_id) DO NOTHING", user_id, datetime.now().isoformat())
    
    row = await db.fetchrow("SELECT balance, last_interest FROM bank WHERE user_id = $1", user_id)
    bank_bal = row['balance'] if row else 0
    last_interest = row['last_interest'] if row else None
    
    wallet_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    next_time_str = "Available now"
    if last_interest:
        last = datetime.fromisoformat(last_interest)
        next_time = last + timedelta(hours=24)
        now = datetime.now()
        if now < next_time:
            remaining = next_time - now
            hours = remaining.seconds // 3600
            mins = (remaining.seconds % 3600) // 60
            next_time_str = f"{hours}h {mins}m"
    
    await db.close()
    
    await update.message.reply_text(f"🏦 MY BANK ACCOUNT\n\n💰 Bank Balance: {bank_bal:,} 💰\n👛 Wallet Balance: {wallet_bal:,} 💰\n📈 Interest Rate: 5% daily\n⏰ Next interest: {next_time_str}\n\n━━━━━━━━━━━━━━━━━━━━━━\n💡 /deposit <amount>\n💡 /withdraw <amount>\n💡 /claim_interest")

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /deposit <amount>\nExample: /deposit 5000')
        return
    
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('❌ Minimum deposit is 100 credits')
        return
    
    db = await get_db()
    await db.execute("INSERT INTO bank (user_id, balance, last_interest) VALUES ($1, 0, $2) ON CONFLICT (user_id) DO NOTHING", user_id, datetime.now().isoformat())
    
    wallet_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if wallet_bal < amount:
        await update.message.reply_text(f'❌ Insufficient wallet balance!\n\nNeed: {amount:,} 💰\nHave: {wallet_bal:,} 💰')
        await db.close()
        return
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", amount, user_id)
    await db.execute("UPDATE bank SET balance = balance + $1 WHERE user_id = $2", amount, user_id)
    
    new_wallet = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    new_bank = await db.fetchval("SELECT balance FROM bank WHERE user_id = $1", user_id)
    await db.close()
    
    await update.message.reply_text(f"✅ DEPOSITED!\n\nAmount: +{amount:,} 💰\nWallet: {wallet_bal:,} → {new_wallet:,} 💰\nBank: {new_bank - amount:,} → {new_bank:,} 💰")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /withdraw <amount>\nExample: /withdraw 5000')
        return
    
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('❌ Minimum withdrawal is 100 credits')
        return
    
    db = await get_db()
    await db.execute("INSERT INTO bank (user_id, balance, last_interest) VALUES ($1, 0, $2) ON CONFLICT (user_id) DO NOTHING", user_id, datetime.now().isoformat())
    
    bank_bal = await db.fetchval("SELECT balance FROM bank WHERE user_id = $1", user_id)
    
    if bank_bal < amount:
        await update.message.reply_text(f'❌ Insufficient bank balance!\n\nNeed: {amount:,} 💰\nHave: {bank_bal:,} 💰')
        await db.close()
        return
    
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)
    await db.execute("UPDATE bank SET balance = balance - $1 WHERE user_id = $2", amount, user_id)
    
    new_bank = await db.fetchval("SELECT balance FROM bank WHERE user_id = $1", user_id)
    new_wallet = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await db.close()
    
    await update.message.reply_text(f"✅ WITHDRAWN!\n\nAmount: -{amount:,} 💰\nBank: {bank_bal:,} → {new_bank:,} 💰\nWallet: {new_wallet - amount:,} → {new_wallet:,} 💰")

# ============ CLAIM INTEREST (SIMPLE) ==========
async def claim_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    db = await get_db()
    await db.execute("INSERT INTO bank (user_id, balance, last_interest) VALUES ($1, 0, $2) ON CONFLICT (user_id) DO NOTHING", user_id, datetime.now().isoformat())

    row = await db.fetchrow("SELECT balance, last_interest FROM bank WHERE user_id = $1", user_id)
    if not row:
        await update.message.reply_text('❌ No bank account found! Use /bank first.')
        await db.close()
        return

    bank_bal, last_interest = row['balance'], row['last_interest']
    now = datetime.now()

    if last_interest:
        last = datetime.fromisoformat(last_interest)
        next_time = last + timedelta(hours=24)
        if now < next_time:
            remaining = next_time - now
            hours = remaining.seconds // 3600
            mins = (remaining.seconds % 3600) // 60
            await update.message.reply_text(
                f"*⏰ Interest not ready yet!*\n\n*Come back in {hours}h {mins}m*",
                parse_mode="Markdown"
            )
            await db.close()
            return

    # 🔥 TIER SYSTEM
    if bank_bal <= 1000000:
        rate = 0.05
    elif bank_bal <= 5000000:
        rate = 0.03
    elif bank_bal <= 10000000:
        rate = 0.015
    elif bank_bal <= 20000000:
        rate = 0.01
    else:
        rate = 0.005

    interest = int(bank_bal * rate)
    new_bank = bank_bal + interest
    await db.execute("UPDATE bank SET balance = $1, last_interest = $2 WHERE user_id = $3", new_bank, now.isoformat(), user_id)
    await db.close()

    await update.message.reply_text(
        f"*💰 INTEREST CLAIMED!*\n\n"
        f"*Rate: {rate*100}%*\n"
        f"*Interest: +{interest:,} 💰*\n"
        f"*New Bank Balance: {new_bank:,} 💰*\n\n"
        f"*⏰ Next interest: 24h*",
        parse_mode="Markdown"
    )

# ============ LOTTERY SYSTEM ==========
async def lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await db.close()
    
    user_tickets = lottery_tickets.get(user_id, [])
    status_text = "ACTIVE" if lottery_active else "NOT ACTIVE"
    
    msg = f"🎰 LOTTERY SYSTEM\n\n"
    msg += f"💰 Balance: {balance:,}\n"
    msg += f"🎫 Your tickets: {len(user_tickets)}\n"
    msg += f"📊 Status: {status_text}\n\n"
    msg += f"🎟️ Ticket price: 20,000 credits\n"
    msg += f"🏆 Winner gets: ALL ticket money\n\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📌 COMMANDS:\n"
    msg += f"/buy_ticket <qty> - Buy tickets\n"
    msg += f"/mytickets - Your tickets\n"
    msg += f"/lottery_info - Lottery stats"
    
    await update.message.reply_text(msg)

async def buy_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.effective_user.first_name
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: /buy_ticket <quantity>\nExample: /buy_ticket 5\n\n⚠️ Max 5 tickets per user!")
        return
    
    try:
        quantity = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid quantity!")
        return
    
    if quantity < 1 or quantity > 5:
        await update.message.reply_text("❌ Quantity must be 1-5 (max 5 tickets per user!)")
        return
    
    if not lottery_active:
        await update.message.reply_text("❌ Lottery not active! Wait for admin to start.")
        return
    
    db = await get_db()
    
    # Check tickets already bought by user
    user_tickets_count = await db.fetchval("SELECT COUNT(*) FROM lottery_tickets WHERE user_id = $1", user_id)
    
    if user_tickets_count + quantity > 5:
        remaining = 5 - user_tickets_count
        await update.message.reply_text(f"❌ You can only buy maximum 5 tickets!\nYou already have {user_tickets_count} tickets.\nYou can buy {remaining} more.")
        await db.close()
        return
    
    cost = quantity * 20000
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < cost:
        await update.message.reply_text(f"❌ Need {cost:,} credits! You have {balance:,}")
        await db.close()
        return
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", cost, user_id)
    
    # Add participant if new
    await db.execute("INSERT INTO lottery_participants (user_id, name) VALUES ($1, $2) ON CONFLICT (user_id) DO NOTHING", user_id, name)
    
    new_tickets = []
    for _ in range(quantity):
        ticket = generate_ticket_number()
        await db.execute("INSERT INTO lottery_tickets (user_id, ticket, purchased_at) VALUES ($1, $2, $3)", user_id, ticket, datetime.now().isoformat())
        new_tickets.append(ticket)
    
    total_tickets = await db.fetchval("SELECT COUNT(*) FROM lottery_tickets")
    await db.execute("UPDATE lottery_data SET value = $1 WHERE key = 'total_tickets'", str(total_tickets))
    
    await db.close()
    
    ticket_list = "\n".join([f"🎫 {t}" for t in new_tickets])
    
    await update.message.reply_text(
        f"✅ BOUGHT {quantity} TICKETS!\n\n"
        f"💰 Cost: {cost:,} credits\n"
        f"🎫 Your tickets:\n{ticket_list}\n\n"
        f"📊 Total tickets you have: {user_tickets_count + quantity}/5\n"
        f"📊 Total tickets sold: {total_tickets}\n\n"
        f"💡 /mytickets - Check all tickets"
    )

async def mytickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    tickets = await db.fetch("SELECT ticket FROM lottery_tickets WHERE user_id = $1", user_id)
    total = await db.fetchval("SELECT COUNT(*) FROM lottery_tickets WHERE user_id = $1", user_id)
    await db.close()
    
    if not tickets:
        await update.message.reply_text("🎫 You don't have any tickets!\nUse /buy_ticket to buy.")
        return
    
    ticket_list = "\n".join([f"🎫 {t['ticket']}" for t in tickets[:10]])
    if len(tickets) > 10:
        ticket_list += f"\n... and {len(tickets)-10} more"
    
    await update.message.reply_text(
        f"🎫 MY TICKETS\n\n"
        f"Total: {total}\n"
        f"Spent: {total * 20000:,}\n\n"
        f"{ticket_list}"
    )

async def lottery_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    
    # Get lottery data from database
    active = await db.fetchval("SELECT value FROM lottery_data WHERE key = 'active'")
    lottery_active = active == 'true' if active else False
    
    total_tickets = await db.fetchval("SELECT value FROM lottery_data WHERE key = 'total_tickets'")
    total_tickets = int(total_tickets) if total_tickets else 0
    
    participants = await db.fetch("SELECT DISTINCT user_id FROM lottery_tickets")
    participant_count = len(participants)
    
    user_tickets = await db.fetchval("SELECT COUNT(*) FROM lottery_tickets WHERE user_id = $1", user_id)
    user_tickets = user_tickets if user_tickets else 0
    
    prize_pool = total_tickets * 20000
    win_chance = (user_tickets / total_tickets * 100) if total_tickets > 0 else 0
    status_text = "🟢 ACTIVE" if lottery_active else "🔴 NOT ACTIVE"
    
    await db.close()
    
    msg = f"🎰 LOTTERY INFO\n\n"
    msg += f"Status: {status_text}\n"
    msg += f"Total tickets: {total_tickets}\n"
    msg += f"Participants: {participant_count}\n"
    msg += f"Prize pool: {prize_pool:,}\n\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 YOUR STATS:\n"
    msg += f"Your tickets: {user_tickets}\n"
    msg += f"Contribution: {user_tickets * 20000:,}\n"
    msg += f"Win chance: {win_chance:.1f}%"
    
    await update.message.reply_text(msg)

async def start_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    global lottery_active
    
    if lottery_active:
        await update.message.reply_text("❌ Lottery already active!")
        return
    
    lottery_active = True
    
    db = await get_db()
    await db.execute("DELETE FROM lottery_tickets")
    await db.execute("DELETE FROM lottery_participants")
    await db.execute("INSERT INTO lottery_data (key, value) VALUES ('active', 'true') ON CONFLICT (key) DO UPDATE SET value = 'true'")
    await db.execute("INSERT INTO lottery_data (key, value) VALUES ('total_tickets', '0') ON CONFLICT (key) DO UPDATE SET value = '0'")
    await db.execute("INSERT INTO lottery_data (key, value) VALUES ('start_time', $1) ON CONFLICT (key) DO UPDATE SET value = $1", datetime.now().isoformat())
    await db.close()
    
    await update.message.reply_text(
        "✅ LOTTERY STARTED!\n\n"
        "🎟️ Ticket price: 20,000 credits\n"
        "🏆 Winner gets: ALL prize pool\n"
        "📢 Users can buy tickets:\n"
        "/buy_ticket <quantity>\n\n"
        "💡 /draw_winner - Draw winner"
    )

async def draw_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    global lottery_active
    
    db = await get_db()
    
    total_tickets = await db.fetchval("SELECT value FROM lottery_data WHERE key = 'total_tickets'")
    total_tickets = int(total_tickets) if total_tickets else 0
    
    if total_tickets == 0:
        await update.message.reply_text("❌ No tickets sold!")
        await db.close()
        return
    
    all_tickets = await db.fetch("SELECT user_id, ticket FROM lottery_tickets")
    
    winner = random.choice(all_tickets)
    winner_id = winner['user_id']
    winner_ticket = winner['ticket']
    prize_pool = total_tickets * 20000
    
    winner_name = await db.fetchval("SELECT name FROM users WHERE user_id = $1", winner_id)
    current_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", winner_id)
    await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", current_bal + prize_pool, winner_id)
    
    # Clear lottery data
    await db.execute("DELETE FROM lottery_tickets")
    await db.execute("DELETE FROM lottery_participants")
    await db.execute("UPDATE lottery_data SET value = 'false' WHERE key = 'active'")
    await db.close()
    
    lottery_active = False
    
    try:
        await context.bot.send_message(
            winner_id,
            f"🎉 YOU WON THE LOTTERY! 🎉\n\n"
            f"🏆 Ticket: {winner_ticket}\n"
            f"💰 Prize: {prize_pool:,}\n"
            f"💳 New balance: {current_bal + prize_pool:,}"
        )
    except:
        pass
    
    await update.message.reply_text(
        f"🎉 LOTTERY WINNER! 🎉\n\n"
        f"🏆 Winner: {winner_name}\n"
        f"🎫 Ticket: {winner_ticket}\n"
        f"💰 Prize: {prize_pool:,}\n\n"
        f"💡 /reset_lottery - Start new lottery"
    )

async def reset_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    global lottery_active, lottery_tickets, lottery_total_tickets, lottery_participants, lottery_winner
    
    lottery_active = False
    lottery_tickets = {}
    lottery_total_tickets = 0
    lottery_participants = []
    lottery_winner = None
    
    await update.message.reply_text("✅ Lottery reset! Use /start_lottery to begin.")

async def lottery_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /lottery_coupon <quantity>\nExample: /lottery_coupon 5")
        return
    
    try:
        quantity = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid quantity!")
        return
    
    coupon_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    db = await get_db()
    await db.execute("CREATE TABLE IF NOT EXISTS lottery_coupons (code TEXT PRIMARY KEY, quantity INT, used INT DEFAULT 0)")
    await db.execute("INSERT INTO lottery_coupons (code, quantity) VALUES ($1, $2)", coupon_code, quantity)
    await db.close()
    
    await update.message.reply_text(
        f"✅ COUPON GENERATED!\n\n"
        f"🔑 Code: {coupon_code}\n"
        f"🎫 Free tickets: {quantity}\n\n"
        f"Claim: /claim_coupon {coupon_code}"
    )

async def claim_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ /claim_coupon <code>")
        return
    
    coupon_code = args[0].upper()
    
    db = await get_db()
    coupon = await db.fetchrow("SELECT quantity, used FROM lottery_coupons WHERE code = $1", coupon_code)
    
    if not coupon:
        await update.message.reply_text("❌ Invalid coupon code!")
        await db.close()
        return
    
    quantity, used = coupon['quantity'], coupon['used']
    
    if used >= quantity:
        await update.message.reply_text("❌ This coupon has been fully used!")
        await db.close()
        return
    
    await db.execute("CREATE TABLE IF NOT EXISTS coupon_used (code TEXT, user_id BIGINT, PRIMARY KEY (code, user_id))")
    already_used = await db.fetchval("SELECT code FROM coupon_used WHERE code = $1 AND user_id = $2", coupon_code, user_id)
    if already_used:
        await update.message.reply_text("❌ You already used this coupon!")
        await db.close()
        return
    
    await db.execute("INSERT INTO coupon_used (code, user_id) VALUES ($1, $2)", coupon_code, user_id)
    await db.execute("UPDATE lottery_coupons SET used = used + 1 WHERE code = $1", coupon_code)
    await db.close()
    
    if not lottery_active:
        await update.message.reply_text(f"✅ Coupon claimed! You got {quantity} free tickets.\nBut lottery is not active. Wait for /start_lottery")
        return
    
    if user_id not in lottery_tickets:
        lottery_tickets[user_id] = []
        if user_id not in lottery_participants:
            lottery_participants.append(user_id)
    
    new_tickets = []
    for _ in range(quantity):
        ticket = generate_ticket_number()
        lottery_tickets[user_id].append(ticket)
        new_tickets.append(ticket)
    
    global lottery_total_tickets
    lottery_total_tickets += quantity
    
    ticket_list = "\n".join([f"🎫 {t}" for t in new_tickets])
    
    await update.message.reply_text(
        f"✅ COUPON CLAIMED!\n\n"
        f"🎫 Free tickets: {quantity}\n"
        f"{ticket_list}\n\n"
        f"Total tickets: {len(lottery_tickets[user_id])}"
    )

# ============ HILO GAME (Fixed - Game ID based, others can't affect) ==========
# ============ HILO GAME ==========
import random

hilo_games = {}

CARD_VALUES = {'A':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':11, 'Q':12, 'K':13}
SUITS = ['♠️', '♥️', '♣️', '♦️']

def get_random_card():
    value = random.choice(list(CARD_VALUES.keys()))
    suit = random.choice(SUITS)
    return {'value': value, 'suit': suit, 'rank': CARD_VALUES[value]}

def get_multiplier(diff):
    if diff == 0: return 0.50
    elif diff == 1: return 0.05
    elif diff <= 3: return 0.08
    elif diff <= 6: return 0.12
    elif diff <= 9: return 0.18
    else: return 0.25

async def hilo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    if len(args) < 1:
        await update.message.reply_text("📈 HiLo Game\n\n/hilo <bet>\nMin: 100 | Max: 10,000")
        return
    
    try:
        bet = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid bet!")
        return
    
    if bet < 100 or bet > 10000:
        await update.message.reply_text("❌ Bet must be 100-10,000!")
        return
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < bet:
        await update.message.reply_text(f"❌ Need {bet:,} credits! You have {balance:,}")
        await db.close()
        return
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
    await db.close()
    
    first_card = get_random_card()
    
    hilo_games[user_id] = {
        'bet': bet,
        'multiplier': 1.0,
        'current_card': first_card,
        'logs': [first_card],
        'owner': user_id
    }
    
    keyboard = [
        [InlineKeyboardButton("🔼 HIGH", callback_data=f"hilo_H_{user_id}"),
         InlineKeyboardButton("🔽 LOW", callback_data=f"hilo_L_{user_id}")],
        [InlineKeyboardButton("💰 CASHOUT", callback_data=f"hilo_C_{user_id}")]
    ]
    
    msg = f"📈 HiLo Game 📉\n\n💰 Bet: {bet:,}\n📈 Multiplier: None\n\n🃏 Your card: {first_card['suit']}{first_card['value']}"
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def hilo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data
    
    parts = data.split("_")
    action = parts[1]  # H, L, C
    owner_id = int(parts[2])
    
    if owner_id != user_id:
        await query.answer("❌ Not your game!", show_alert=True)
        return
    
    if owner_id not in hilo_games:
        await query.answer("❌ No active game! Use /hilo", show_alert=True)
        return
    
    game = hilo_games[owner_id]
    await query.answer()
    
    # CASHOUT
    if action == "C":
        win_amount = int(game['bet'] * game['multiplier'])
        if win_amount > 0:
            db = await get_db()
            await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", win_amount, owner_id)
            await db.close()
        
        log_str = "".join([f"|{c['suit']}{c['value']}" for c in game['logs']])
        msg = f"📈 HiLo Game 📉\n\n💰 Bet: {game['bet']:,}\n📈 Multiplier: {game['multiplier']:.3f}x\n🎉 You won: {win_amount:,} 💰\n\n📜 Logs: {log_str}|"
        await query.edit_message_text(msg)
        del hilo_games[owner_id]
        return
    
    # PLAY (HIGH or LOW)
    guess = "HIGH" if action == "H" else "LOW"
    new_card = get_random_card()
    game['logs'].append(new_card)
    
    current_rank = game['current_card']['rank']
    new_rank = new_card['rank']
    
    # Check win
    if (action == "H" and new_rank > current_rank) or (action == "L" and new_rank < current_rank) or (new_rank == current_rank):
        diff = abs(new_rank - current_rank)
        increase = get_multiplier(diff)
        game['multiplier'] += increase
        game['current_card'] = new_card
        
        win_amount = int(game['bet'] * game['multiplier'])
        log_str = "".join([f"|{c['suit']}{c['value']}" for c in game['logs']])
        
        msg = f"📈 HiLo Game 📉\n\n💰 Bet: {game['bet']:,}\n📈 Multiplier: {game['multiplier']:.3f}x\n🏆 Winning: {win_amount:,} 💰\n\n✅ Card: {new_card['suit']}{new_card['value']} ({guess} won!)\n🃏 Your card: {game['current_card']['suit']}{game['current_card']['value']}\n\n📜 Logs: {log_str}|"
        
        keyboard = [
            [InlineKeyboardButton("🔼 HIGH", callback_data=f"hilo_H_{owner_id}"),
             InlineKeyboardButton("🔽 LOW", callback_data=f"hilo_L_{owner_id}")],
            [InlineKeyboardButton("💰 CASHOUT", callback_data=f"hilo_C_{owner_id}")]
        ]
        
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        log_str = "".join([f"|{c['suit']}{c['value']}" for c in game['logs']])
        msg = f"📈 HiLo Game 📉\n\n💰 Bet: {game['bet']:,}\n📈 Multiplier: 0x\n\n💀 Game Over!\n❌ You bet {guess} on {new_card['suit']}{new_card['value']} and lost!\n\n📜 Logs: {log_str}|"
        
        await query.edit_message_text(msg)
        del hilo_games[owner_id]

# ============ MINES GAME (With Cashout Button) ==========
active_mines = {}
mines_owner = {}
mines_next_id = 1

MINES_PROGRESSION = {
    1: [1.03, 1.08, 1.12, 1.18, 1.24, 1.30, 1.37, 1.46, 1.55, 1.65, 1.77, 1.90, 2.06, 2.25, 2.47, 2.75, 3.09, 3.54, 4.12, 4.95, 6.19, 8.25, 12.37, 24.75],
    2: [1.08, 1.17, 1.29, 1.41, 1.56, 1.74, 1.94, 2.18, 2.47, 2.83, 3.26, 3.81, 4.50, 5.40, 6.60, 8.25, 10.61, 14.14, 19.80, 29.70, 49.50, 99.00, 297.00],
    3: [1.12, 1.29, 1.48, 1.71, 2.00, 2.35, 2.79, 3.35, 4.07, 5.00, 6.26, 7.96, 10.35, 13.80, 18.97, 27.11, 40.66, 65.06, 113.85, 227.70, 596.25, 2277.00],
    4: [1.18, 1.41, 1.71, 2.09, 2.58, 3.23, 4.09, 5.26, 6.88, 9.17, 12.51, 17.52, 25.30, 37.95, 59.64, 99.39, 178.91, 357.81, 834.90, 2504.70, 12523.50],
    5: [1.24, 1.56, 2.00, 2.58, 3.39, 4.52, 6.14, 8.50, 12.04, 17.52, 26.27, 40.87, 66.41, 113.85, 208.72, 417.45, 939.26, 2504.70, 8766.45, 52598.70],
    6: [1.30, 1.74, 2.35, 3.32, 4.52, 6.46, 9.44, 14.17, 21.89, 35.03, 58.38, 102.17, 189.75, 379.50, 834.90, 2087.25, 6261.75, 25047.00, 175329.00],
    7: [1.37, 1.94, 2.79, 4.09, 6.14, 9.44, 14.95, 24.47, 41.60, 73.95, 138.66, 277.33, 600.87, 1442.10, 3965.77, 13219.25, 59486.62, 475893.00],
    8: [1.46, 2.18, 3.35, 5.26, 8.50, 14.17, 24.47, 44.05, 83.20, 166.40, 356.56, 831.98, 2163.15, 6489.45, 23794.65, 118973.25, 1070759.25],
    9: [1.55, 2.47, 4.07, 6.88, 12.04, 21.89, 41.60, 83.20, 176.80, 404.10, 1010.26, 2828.73, 9193.39, 36773.55, 202254.52, 2022545.25],
    10: [1.65, 2.83, 5.00, 9.17, 17.52, 35.03, 73.95, 166.50, 404.10, 1077.61, 3232.84, 11314.94, 49301.40, 294188.40, 3236072.40],
    11: [1.77, 3.26, 6.26, 15.21, 26.27, 58.38, 138.66, 356.56, 1010.26, 3232.84, 12123.15, 56574.69, 367735.50, 4412826],
    12: [1.90, 3.81, 7.96, 17.52, 40.87, 102.17, 277.33, 831.98, 2828.73, 11314.94, 56574.69, 396022.85, 5148297],
    13: [2.06, 4.50, 10.35, 25.30, 66.41, 189.75, 600.87, 2163.15, 9139.39, 49031.40, 367735.50, 5148297],
    14: [2.25, 5.40, 13.80, 37.95, 113.85, 379.50, 1442.10, 6489.45, 36773.55, 294188.40, 4412826],
    15: [2.47, 6.60, 18.97, 59.64, 208.72, 834.90, 3965.77, 23794.65, 202254.52, 3236072.40],
    16: [2.75, 8.25, 27.11, 99.39, 417.45, 2087.25, 13219.25, 118973.25, 2022545.25],
    17: [3.09, 10.61, 40.66, 178.91, 939.26, 6261.75, 59486.62, 1070759.25],
    18: [3.54, 14.14, 65.06, 357.81, 2504.70, 25047, 475893],
    19: [4.12, 19.80, 113.85, 834.90, 8766.45, 175329],
    20: [4.95, 29.70, 227.70, 2504.70, 52598.70],
    21: [6.19, 49.50, 569.25, 12523.50],
    22: [8.25, 99, 2277],
    23: [12.38, 297],
    24: [24.75],
}

async def mines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "💣 MINES\n"
            "/mines <amount> <bombs>\n"
            "Example: /mines 1000 3\n\n"
            "Min: 100 | Max: 10,000\n"
            "Bombs: 1-24"
        )
        return
    
    try:
        bet = int(args[0])
        bombs = int(args[1])
    except:
        await update.message.reply_text("❌ Invalid amount or bombs!")
        return
    
    if bet < 100 or bet > 10000:
        await update.message.reply_text("❌ Bet must be between 100 and 10,000!")
        return
    
    if bombs < 1 or bombs > 24:
        await update.message.reply_text("❌ Bombs must be between 1 and 24!")
        return
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < bet:
        await update.message.reply_text(f"❌ Need {bet:,}, you have {balance:,}")
        await db.close()
        return
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
    await db.close()
    
    global mines_next_id
    game_id = mines_next_id
    mines_next_id += 1
    
    bomb_positions = random.sample(range(25), bombs)
    progression = MINES_PROGRESSION.get(bombs, [1.0] * 25)
    
    active_mines[game_id] = {
        'bet': bet,
        'bombs': bomb_positions,
        'revealed': [],
        'active': True,
        'bomb_count': bombs,
        'progression': progression,
        'owner_id': user_id,
        'chat_id': chat_id,
        'game_over': False
    }
    mines_owner[game_id] = user_id
    
    # 🔥 KEYBOARD WITH CASHOUT BUTTON
    keyboard = []
    for i in range(5):
        row = []
        for j in range(5):
            pos = i * 5 + j
            row.append(InlineKeyboardButton("❓", callback_data=f"mine_{game_id}_{pos}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("💰 CASHOUT", callback_data=f"mine_cashout_{game_id}")])
    
    await update.message.reply_text(
        f"💣 MINES\n\n"
        f"💰 Bet: {bet:,}\n"
        f"📈 Multiplier: 1.00x\n"
        f"💎 Cashout: {bet:,}\n\n"
        f"Click tiles to reveal safe spots. Don't hit a bomb!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def mine_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    parts = data.split("_")

    # Handle cashout
    if parts[1] == "cashout":
        game_id = int(parts[2])

        if game_id not in active_mines:
            await query.answer("Game expired!", show_alert=True)
            return

        game = active_mines[game_id]

        if game['owner_id'] != user_id:
            await query.answer("❌ Not your game!", show_alert=True)
            return

        if game['game_over']:
            await query.answer("Game already over!", show_alert=True)
            return

        safe_count = len([t for t in game['revealed'] if t not in game['bombs']])
        progression = game['progression']

        if safe_count <= len(progression):
            multiplier = progression[safe_count - 1] if safe_count > 0 else 1.0
        else:
            multiplier = progression[-1]

        win_amount = int(game['bet'] * multiplier)

        db = await get_db()
        current_balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        new_balance = current_balance + win_amount
        await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_balance, user_id)
        await db.close()

        await query.edit_message_text(
            f"💰 CASHOUT SUCCESSFUL!\n\n"
            f"💰 Bet: {game['bet']:,}\n"
            f"📈 Multiplier: {multiplier:.2f}x\n"
            f"💎 Won: {win_amount:,}\n"
            f"💳 New balance: {new_balance:,}"
        )
        del active_mines[game_id]
        del mines_owner[game_id]
        return

    # Regular tile click
    game_id = int(parts[1])
    position = int(parts[2])

    if game_id not in active_mines:
        await query.answer("Game expired!", show_alert=True)
        await query.edit_message_text("❌ Game expired. Use /mines to start new game.")
        return

    game = active_mines[game_id]

    if game['owner_id'] != user_id:
        await query.answer("❌ Not your game!", show_alert=True)
        return

    if game['game_over']:
        await query.answer("Game already over!", show_alert=True)
        return

    if position in game['revealed']:
        await query.answer("Already revealed!", show_alert=True)
        return

    game['revealed'].append(position)

    # Check if bomb
    if position in game['bombs']:
        # Reveal all bombs
        keyboard = []
        for i in range(5):
            row = []
            for j in range(5):
                pos = i * 5 + j
                if pos in game['bombs']:
                    row.append(InlineKeyboardButton("💣", callback_data=f"mine_{game_id}_{pos}"))
                elif pos in game['revealed']:
                    row.append(InlineKeyboardButton("💎", callback_data=f"mine_{game_id}_{pos}"))
                else:
                    row.append(InlineKeyboardButton("❓", callback_data=f"mine_{game_id}_{pos}"))
            keyboard.append(row)


        await query.edit_message_text(
            f"💣 BOOM! GAME OVER!\n\n"
            f"💰 Bet: {game['bet']:,}\n"
            f"💣 You hit a bomb!\n\n"
            f"Use /mines to play again!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        game['game_over'] = True
        return

    # Safe tile
    safe_count = len([t for t in game['revealed'] if t not in game['bombs']])
    progression = game['progression']

    if safe_count <= len(progression):
        multiplier = progression[safe_count - 1] if safe_count > 0 else 1.0
    else:
        multiplier = progression[-1]

    cashout = int(game['bet'] * multiplier)

    # Update keyboard with cashout button
    keyboard = []
    for i in range(5):
        row = []
        for j in range(5):
            pos = i * 5 + j
            if pos in game['revealed']:
                row.append(InlineKeyboardButton("💎", callback_data=f"mine_{game_id}_{pos}"))
            else:
                row.append(InlineKeyboardButton("❓", callback_data=f"mine_{game_id}_{pos}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("💰 CASHOUT", callback_data=f"mine_cashout_{game_id}")])

    total_safe = 25 - game['bomb_count']

    # Check perfect win
    if safe_count >= total_safe:
        db = await get_db()
        current_balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        new_balance = current_balance + cashout
        await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_balance, user_id)
        await db.close()

        # Reveal all as 💎
        keyboard = []
        for i in range(5):
            row = []
            for j in range(5):
                pos = i * 5 + j
                if pos in game['bombs']:
                    row.append(InlineKeyboardButton("💣", callback_data=f"mine_{game_id}_{pos}"))
                else:
                    row.append(InlineKeyboardButton("💎", callback_data=f"mine_{game_id}_{pos}"))
            keyboard.append(row)

        await query.edit_message_text(
            f"🎉 PERFECT WIN! 🎉\n\n"
            f"💰 Bet: {game['bet']:,}\n"
            f"📈 Multiplier: {multiplier:.2f}x\n"
            f"💎 Won: {cashout:,}\n\n"
            f"All safe tiles revealed!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        del active_mines[game_id]
        del mines_owner[game_id]
        return

    await query.edit_message_text(
        f"💣 MINES\n\n"
        f"💰 Bet: {game['bet']:,}\n"
        f"📈 Multiplier: {multiplier:.2f}x\n"
        f"💎 Cashout: {cashout:,}\n\n"
        f"✅ Safe tiles: {safe_count}/{total_safe}\n"
        f"Click a tile or CASHOUT!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============ CLCRICKET GAME ==========
cricket_games = {}
cricket_lobby = {}
cricket_next_id = 1

DELIVERIES = {
    "RS": {"name": "RS", "out_on": 0},
    "BNC": {"name": "BNC", "out_on": 1},
    "YRK": {"name": "YRK", "out_on": 2},
    "SHT": {"name": "SHT", "out_on": 3},
    "SLW": {"name": "SLW", "out_on": 4},
    "LC": {"name": "LC", "out_on": 5},
    "KNC": {"name": "KNC", "out_on": 6},
}

async def update_cricket_stats_realtime(user_id, name, runs_added=0, wickets_added=0, current_match_runs=0, ducks_added=0):
    db = await get_db()
    stats = await db.fetchrow("SELECT * FROM cricket_stats WHERE user_id = $1", user_id)
    if stats:
        new_runs = stats['runs'] + runs_added
        new_wickets = stats['wickets'] + wickets_added
        new_highest = stats['highest_score']
        new_ducks = (stats['ducks'] or 0) + ducks_added
        if current_match_runs > new_highest:
            new_highest = current_match_runs
        await db.execute(
            "UPDATE cricket_stats SET runs = $1, wickets = $2, highest_score = $3, ducks = $4 WHERE user_id = $5",
            new_runs, new_wickets, new_highest, new_ducks, user_id
        )
    else:
        await db.execute(
            "INSERT INTO cricket_stats (user_id, name, runs, wickets, highest_score, ducks) VALUES ($1, $2, $3, $4, $5, $6)",
            user_id, name, runs_added, wickets_added, current_match_runs, ducks_added
        )
    await db.close()

async def update_wins_losses_realtime(user_id, name, won):
    db = await get_db()
    stats = await db.fetchrow("SELECT * FROM cricket_stats WHERE user_id = $1", user_id)
    if stats:
        if won:
            await db.execute("UPDATE cricket_stats SET wins = wins + 1 WHERE user_id = $1", user_id)
        else:
            await db.execute("UPDATE cricket_stats SET losses = losses + 1 WHERE user_id = $1", user_id)
    else:
        await db.execute("INSERT INTO cricket_stats (user_id, name, wins, losses) VALUES ($1, $2, $3, $4)", user_id, name, 1 if won else 0, 0 if won else 1)
    await db.close()

class CricketGame:
    def __init__(self, game_id, player1_id, player1_name, bet, chat_id, mode):
        self.game_id = game_id
        self.player1_id = player1_id
        self.player1_name = player1_name
        self.player2_id = None
        self.player2_name = None
        self.bet = bet
        self.chat_id = chat_id
        self.mode = mode
        self.toss_winner = None
        self.current_bowler = None
        self.current_batsman = None
        self.score = 0
        self.wickets = 0
        self.balls = 0
        self.target = None
        self.game_active = False
        self.waiting_for = None
        self.pending_delivery = None
        self.player1_match_runs = 0
        self.player2_match_runs = 0
        self.player1_wickets_taken = 0
        self.player2_wickets_taken = 0
        self.innings1_balls = 0
        self.innings2_balls = 0

    def get_deliveries(self):
        if self.mode == "1-3":
            return {
                "1": {"name": "1", "out_on": 1},
                "2": {"name": "2", "out_on": 2},
                "3": {"name": "3", "out_on": 3}
            }
        elif self.mode == "1-5":
            return {
                "0": {"name": "0", "out_on": 0},
                "1": {"name": "1", "out_on": 1},
                "2": {"name": "2", "out_on": 2},
                "3": {"name": "3", "out_on": 3},
                "4": {"name": "4", "out_on": 4},
                "6": {"name": "6", "out_on": 6}
            }
        elif self.mode == "1-9":
            return {
                "1": {"name": "1", "out_on": 1},
                "2": {"name": "2", "out_on": 2},
                "3": {"name": "3", "out_on": 3},
                "4": {"name": "4", "out_on": 4},
                "5": {"name": "5", "out_on": 5},
                "6": {"name": "6", "out_on": 6},
                "7": {"name": "7", "out_on": 7},
                "8": {"name": "8", "out_on": 8},
                "9": {"name": "9", "out_on": 9}
            }
        else:
            return {
                "1": {"name": "1", "out_on": 1},
                "2": {"name": "2", "out_on": 2},
                "3": {"name": "3", "out_on": 3},
                "4": {"name": "4", "out_on": 4},
                "5": {"name": "5", "out_on": 5},
                "6": {"name": "6", "out_on": 6}
            }

    def get_bat_numbers(self):
        if self.mode == "1-3":
            return [1, 2, 3]
        elif self.mode == "1-5":
            return [0, 1, 2, 3, 4, 6]
        elif self.mode == "1-9":
            return [1, 2, 3, 4, 5, 6, 7, 8, 9]
        else:
            return [1, 2, 3, 4, 5, 6]

    def check_out(self, delivery_key, shot):
        return self.get_deliveries()[delivery_key]["out_on"] == shot

    def get_overs(self, innings=None):
        if innings == 1:
            balls = self.innings1_balls
        elif innings == 2:
            balls = self.innings2_balls
        else:
            balls = self.balls
        overs = balls // 6
        rem_balls = balls % 6
        return f"{overs}.{rem_balls}"


async def clcricket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.message.chat.id
    
    # 🔥 ESCAPE NAME
    user_name_escaped = escape_md(user_name)
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    args = context.args
    bet = 0
    if args:
        try:
            bet = int(args[0])
            if bet < 100:
                await update.message.reply_text("*❌ Minimum bet is 100 credits!*", parse_mode="Markdown")
                return
        except:
            await update.message.reply_text("*❌ Invalid bet amount!*", parse_mode="Markdown")
            return
    if bet > 0:
        db = await get_db()
        balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        await db.close()
        if balance < bet:
            await update.message.reply_text(f"*❌ You need {bet:,} credits to play!*", parse_mode="Markdown")
            return
    global cricket_next_id
    game_id = cricket_next_id
    cricket_next_id += 1
    cricket_lobby[game_id] = {"creator_id": user_id, "creator_name": user_name, "bet": bet, "chat_id": chat_id}
    bet_text = f"💰 Bet: {bet} | Prize: {bet*2}" if bet > 0 else "🎮 Normal Game"

    await update.message.reply_text(
        f"*🏏 CRICKET GAME*\n\n"
        f"*👑 Host:* {user_name_escaped}\n"  # 🔥 ESCAPED NAME
        f"{bet_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*⚡ Select Mode*",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("1-3 Mode", callback_data=f"cricket_mode_{game_id}_1-3"), InlineKeyboardButton("No 5 Mode", callback_data=f"cricket_mode_{game_id}_1-5")],
            [InlineKeyboardButton("1-9 Mode", callback_data=f"cricket_mode_{game_id}_1-9"), InlineKeyboardButton("Default Mode", callback_data=f"cricket_mode_{game_id}_default")]
        ]),
        parse_mode="Markdown"
    )

async def cricket_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    mode = parts[3]

    if game_id not in cricket_lobby:
        await query.edit_message_text("*❌ Game expired!*", parse_mode="Markdown")
        return

    lobby = cricket_lobby[game_id]
    if update.effective_user.id != lobby["creator_id"]:
        await query.answer("Only host can select mode!", show_alert=True)
        return

    lobby["mode"] = mode
    bet_text = f"💰 Bet: {lobby['bet']} | Prize: {lobby['bet']*2}" if lobby['bet'] > 0 else "🎮 Normal Game"

    await query.edit_message_text(
        f"*🏏 CRICKET GAME*\n\n"
        f"*👑 Host:* {lobby['creator_name']}\n"
        f"{bet_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*⚡ Waiting for opponent...*",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 JOIN GAME", callback_data=f"cricket_join_{game_id}")]]),
        parse_mode="Markdown"
    )

async def cricket_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = query.data
    game_id = int(data.split("_")[2])

    if game_id not in cricket_lobby:
        try:
            await query.edit_message_text("*❌ Game expired!*", parse_mode="Markdown")
        except:
            pass
        return

    lobby = cricket_lobby[game_id]
    creator_id = lobby["creator_id"]
    creator_name = lobby["creator_name"]
    bet = lobby["bet"]
    chat_id = lobby["chat_id"]
    mode = lobby.get("mode", "default")

    if creator_id == user_id:
        await query.answer("You cannot join your own game!", show_alert=True)
        return

    if bet > 0:
        db = await get_db()
        balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        if balance is None:
            try:
                await query.edit_message_text("*❌ Send /start first!*", parse_mode="Markdown")
            except:
                pass
            await db.close()
            return
        if balance < bet:
            await query.answer(f"❌ Need {bet} credits!", show_alert=True)
            await db.close()
            return
        await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, creator_id)
        await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
        await db.close()

    game = CricketGame(game_id, creator_id, creator_name, bet, chat_id, mode)
    game.player2_id = user_id
    game.player2_name = user_name
    game.game_active = True
    cricket_games[game_id] = game
    del cricket_lobby[game_id]

    await query.edit_message_text(
        f"*🏏 CRICKET GAME*\n\n"
        f"*{creator_name}* vs *{user_name}*\n"
        + (f"💰 Bet: {bet} | Prize: {bet*2}\n" if bet > 0 else "")
        + f"\n*🪙 TOSS TIME!*\n\n"
        f"*{creator_name}, choose:*",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("HEADS", callback_data=f"cricket_toss_{game_id}_heads")],
            [InlineKeyboardButton("TAILS", callback_data=f"cricket_toss_{game_id}_tails")]
        ]),
        parse_mode="Markdown"
    )


async def cricket_toss_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    choice = parts[3]

    game = cricket_games[game_id]
    if update.effective_user.id != game.player1_id:
        await query.answer("Wait for host!", show_alert=True)
        return

    toss = random.choice(["heads", "tails"])
    winner_id = game.player1_id if choice == toss else game.player2_id
    winner_name = game.player1_name if winner_id == game.player1_id else game.player2_name
    game.toss_winner = winner_id

    await query.edit_message_text(
        f"*🏏 Match Started!*\n\n"
        f"*🪙 TOSS: {toss.upper()}!*\n"
        f"*🏆 {winner_name} won the toss!*\n\n"
        f"*📋 {game.mode.upper()} MODE*\n\n"
        f"*Choose:*",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏏 BAT", callback_data=f"cricket_choice_{game_id}_bat")],
            [InlineKeyboardButton("🎯 BOWL", callback_data=f"cricket_choice_{game_id}_bowl")]
        ]),
        parse_mode="Markdown"
    )

async def cricket_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    choice = parts[3]

    if game_id not in cricket_games:
        await query.edit_message_text("*❌ Game expired!*", parse_mode="Markdown")
        return

    game = cricket_games[game_id]

    if update.effective_user.id != game.toss_winner:
        await query.answer("Only toss winner can choose Bat or Bowl!", show_alert=True)
        return

    # 🔥 SET BATSMAN AND BOWLER
    if choice == "bat":
        game.current_batsman = game.toss_winner
        if game.toss_winner == game.player1_id:
            game.current_bowler = game.player2_id
        else:
            game.current_bowler = game.player1_id
    else:  # bowl
        game.current_bowler = game.toss_winner
        if game.toss_winner == game.player1_id:
            game.current_batsman = game.player2_id
        else:
            game.current_batsman = game.player1_id

    game.score = 0
    game.wickets = 0
    game.balls = 0
    game.target = None
    game.waiting_for = "bat"
    game.pending_delivery = None
    game.innings = 1
    game.player1_match_runs = 0
    game.player2_match_runs = 0
    game.player1_wickets_taken = 0
    game.player2_wickets_taken = 0
    game.innings1_balls = 0
    game.innings2_balls = 0

    batsman_name = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
    bowler_name = game.player1_name if game.current_bowler == game.player1_id else game.player2_name

    bat_numbers = game.get_bat_numbers()
    keyboard = []
    row = []
    for num in bat_numbers:
        row.append(InlineKeyboardButton(str(num), callback_data=f"cricket_bat_{game_id}_{num}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    await query.edit_message_text(
        f"*🏏 Match Started!*\n"
        f"*📋 {game.mode.upper()} MODE*\n\n"
        f"*👤 Batter:* {batsman_name}\n"
        f"*🧤 Bowler:* {bowler_name}\n\n"
        f"*🏏 {batsman_name}, choose your shot.*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def cricket_bowl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    delivery_key = parts[3]

    if game_id not in cricket_games:
        await query.edit_message_text("*❌ Game expired!*", parse_mode="Markdown")
        return

    game = cricket_games[game_id]
    user_id = update.effective_user.id

    if user_id != game.current_bowler:
        await query.answer("Not your turn!", show_alert=True)
        return

    if game.waiting_for != "bowl":
        await query.answer("Wait!", show_alert=True)
        return

    bat_number = game.pending_bat_number
    game.pending_bat_number = None
    game.balls += 1

    if game.innings == 1:
        game.innings1_balls += 1
    else:
        game.innings2_balls += 1

    deliveries = game.get_deliveries()
    bowl_number = deliveries[delivery_key]["out_on"]

    batsman_name = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
    bowler_name = game.player1_name if game.current_bowler == game.player1_id else game.player2_name

    is_out = (bat_number == bowl_number)

    if game.innings == 1:
        innings_tag = "FIRST INNINGS"
        overs_display = game.get_overs(1)
    else:
        innings_tag = f"TARGET : {game.target}"
        overs_display = game.get_overs(2)

    msg = f"*🏏 Over {overs_display} ({innings_tag})*\n\n"
    msg += f"*{batsman_name} played: {bat_number}  | {bowler_name} bowled: {bowl_number}*\n\n"

    if is_out:
        # 🔥 DUCK CHECK - SIRF TAB JAB BATTER NE 0 RUNS BANAYE
        if game.score == 0:
            db = await get_db()
            if game.current_batsman == game.player1_id:
                await db.execute("UPDATE cricket_stats SET ducks = ducks + 1 WHERE user_id = $1", game.player1_id)
            else:
                await db.execute("UPDATE cricket_stats SET ducks = ducks + 1 WHERE user_id = $1", game.player2_id)
            await db.close()
        
        if game.current_bowler == game.player1_id:
            game.player1_wickets_taken += 1
            await update_cricket_stats_realtime(game.player1_id, game.player1_name, 0, 1, 0)
        else:
            game.player2_wickets_taken += 1
            await update_cricket_stats_realtime(game.player2_id, game.player2_name, 0, 1, 0)

        game.wickets += 1
        msg += "*❌ OUT!*\n\n"
    else:
        runs = bat_number
        game.score += runs
        msg += f"*✅ {runs} runs!*\n\n"

        if game.current_batsman == game.player1_id:
            game.player1_match_runs += runs
            await update_cricket_stats_realtime(game.player1_id, game.player1_name, runs, 0, game.player1_match_runs)
        else:
            game.player2_match_runs += runs
            await update_cricket_stats_realtime(game.player2_id, game.player2_name, runs, 0, game.player2_match_runs)

    if not hasattr(game, "current_over_shots"):
        game.current_over_shots = []

    game.current_over_shots.append(str(bat_number))

    msg += f"*📊 Score: {game.score}/{game.wickets}*\n"

    if game.current_over_shots:
        shots_display = ', '.join(game.current_over_shots)
        msg += f"*🎯 This Over: {shots_display}*\n\n"
    else:
        msg += f"\n"

    if game.balls % 6 == 0:
        game.current_over_shots = []

    # ============ FIRST INNINGS END ============
    if game.innings == 1 and (game.wickets >= 1 or game.balls >= 60):
        first_batsman = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
        first_bowler = game.player1_name if game.current_bowler == game.player1_id else game.player2_name

        game.innings = 2
        game.current_over_shots = []
        game.target = game.score + 1
        innings_score = game.score
        first_innings_wickets = game.wickets
        game.score = 0
        game.wickets = 0
        game.balls = 0
        game.waiting_for = "bat"

        old_batsman = game.current_batsman
        old_bowler = game.current_bowler
        game.current_batsman = old_bowler
        game.current_bowler = old_batsman

        batsman_name = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
        bowler_name = game.player1_name if game.current_bowler == game.player1_id else game.player2_name

        msg = f"*🏏 Over {overs_display} (FIRST INNINGS ENDED)*\n\n"
        msg += f"*{first_batsman} played: {bat_number}  | {first_bowler} bowled: {bowl_number}*\n\n"
        msg += f"*📊 Score: {innings_score}/{first_innings_wickets}*\n"
        msg += f"*🎯 Target: {game.target} runs*\n\n"
        msg += f"*🔄 Innings Changed*\n\n"
        msg += f"*🏏 {batsman_name}, choose your shot.*"

        bat_numbers = game.get_bat_numbers()
        keyboard = []
        row = []
        for num in bat_numbers:
            row.append(InlineKeyboardButton(str(num), callback_data=f"cricket_bat_{game_id}_{num}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    # ============ SECOND INNINGS WIN ============
    if game.innings == 2 and game.score >= game.target:
        game.game_active = False
        winner_id = game.current_batsman
        winner_name = game.player1_name if winner_id == game.player1_id else game.player2_name

        await update_wins_losses_realtime(winner_id, winner_name, True)

        if game.bet > 0:
            db = await get_db()
            await db.execute(
                "UPDATE users SET balance = balance + $1 WHERE user_id = $2",
                game.bet * 2,
                winner_id
            )
            await db.close()

        if winner_id == game.player1_id:
            margin = game.player1_match_runs - game.player2_match_runs
        else:
            margin = game.player2_match_runs - game.player1_match_runs

        player1_overs = game.get_overs(1)
        player2_overs = game.get_overs(2)

        if game.player1_id == winner_id:
            p1_wickets = game.wickets
            p2_wickets = game.player2_wickets_taken
        else:
            p2_wickets = game.wickets
            p1_wickets = game.player1_wickets_taken

        summary = f"*🏆 MATCH RESULT*\n"
        summary += f"━━━━━━━━━━━━━━━━\n"
        summary += f"*{game.player1_name} — {game.player1_match_runs}/{p1_wickets} ({player1_overs} ov)*\n"
        summary += f"*{game.player2_name} — {game.player2_match_runs}/{p2_wickets} ({player2_overs} ov)*\n"
        summary += f"━━━━━━━━━━━━━━━━\n"
        summary += f"*🏆 {winner_name} won by {abs(margin)} runs!*\n"

        if game.bet > 0:
            summary += f"*💰 Prize: {game.bet * 2:,}*"

        await query.edit_message_text(summary, parse_mode="Markdown")
        del cricket_games[game_id]
        return

    # ============ SECOND INNINGS ALL OUT ============
    if game.innings == 2 and game.wickets >= 1:
        game.game_active = False
        winner_id = game.current_bowler
        winner_name = game.player1_name if winner_id == game.player1_id else game.player2_name

        await update_wins_losses_realtime(winner_id, winner_name, True)

        if game.bet > 0:
            db = await get_db()
            await db.execute(
                "UPDATE users SET balance = balance + $1 WHERE user_id = $2",
                game.bet * 2,
                winner_id
            )
            await db.close()

        runs_left = abs(game.player1_match_runs - game.player2_match_runs)
        player1_overs = game.get_overs(1)
        player2_overs = game.get_overs(2)

        if game.player1_id == winner_id:
            p1_wickets = game.player1_wickets_taken
            p2_wickets = game.wickets
        else:
            p2_wickets = game.player2_wickets_taken
            p1_wickets = game.wickets

        summary = f"*🏆 MATCH RESULT*\n"
        summary += f"━━━━━━━━━━━━━━━━\n"
        summary += f"*{game.player1_name} — {game.player1_match_runs}/{p1_wickets} ({player1_overs} ov)*\n"
        summary += f"*{game.player2_name} — {game.player2_match_runs}/{p2_wickets} ({player2_overs} ov)*\n"
        summary += f"━━━━━━━━━━━━━━━━\n"

        if game.player1_match_runs == game.player2_match_runs:
            summary += "*🤝 It's a Draw!*\n"
        else:
            summary += f"*🏆 {winner_name} won by {runs_left} runs!*\n"

        if game.bet > 0:
            summary += f"*💰 Prize: {game.bet * 2:,}*"

        await query.edit_message_text(summary, parse_mode="Markdown")
        del cricket_games[game_id]
        return

    # ============ CONTINUE GAME ============
    game.waiting_for = "bat"

    bat_numbers = game.get_bat_numbers()
    keyboard = []
    row = []
    for num in bat_numbers:
        row.append(InlineKeyboardButton(str(num), callback_data=f"cricket_bat_{game_id}_{num}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    msg += f"*🎮 {batsman_name} choose your shot :-*"

    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def cricket_bat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    shot = int(parts[3])

    if game_id not in cricket_games:
        await query.edit_message_text("*❌ Game expired!*", parse_mode="Markdown")
        return

    game = cricket_games[game_id]
    user_id = update.effective_user.id

    if user_id != game.current_batsman:
        await query.answer("Not your turn!", show_alert=True)
        return

    if game.waiting_for != "bat":
        await query.answer("Wait for your turn!", show_alert=True)
        return

    game.pending_bat_number = shot
    game.waiting_for = "bowl"

    batsman_name = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
    bowler_name = game.player1_name if game.current_bowler == game.player1_id else game.player2_name

    deliveries = game.get_deliveries()
    keyboard = []
    row = []
    for key, d in deliveries.items():
        row.append(InlineKeyboardButton(d["name"], callback_data=f"cricket_bowl_{game_id}_{key}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    if game.innings == 1:
        innings_tag = "FIRST INNINGS"
        overs_display = game.get_overs(1)
    else:
        innings_tag = f"TARGET : {game.target}"
        overs_display = game.get_overs(2)

    await query.edit_message_text(
        f"*🏏 Over {overs_display} ({innings_tag})*\n\n"
        f"*🏏 Batter:* {batsman_name}\n"
        f"*🧤 Bowler:* {bowler_name}\n\n"
        f"*✅ {batsman_name} has selected a number.*\n\n"
        f"*🧤 {bowler_name}, it's your turn to bowl.*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


# ============ NUMPUZ GAME ==========
def get_size_for_level(level):
    if level == 1: return 3
    elif level == 2: return 4
    elif level == 3: return 5
    elif level == 4: return 6
    elif level == 5: return 7
    elif level == 6: return 8
    else: return 9

def get_shuffled_board(size):
    max_num = size * size - 1
    numbers = list(range(1, max_num + 1)) + [0]
    random.shuffle(numbers)
    board = []
    for i in range(size):
        row = []
        for j in range(size):
            row.append(numbers[i * size + j])
        board.append(row)
    return board

def is_solvable(board):
    size = len(board)
    flat = []
    for row in board:
        for num in row:
            if num != 0:
                flat.append(num)
    inversions = 0
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            if flat[i] > flat[j]:
                inversions += 1
    if size % 2 == 1:
        return inversions % 2 == 0
    blank_row = 0
    for i in range(size):
        if 0 in board[i]:
            blank_row = size - i
            break
    return (blank_row % 2 == 0) == (inversions % 2 == 1)

def is_win(board):
    size = len(board)
    expected = 1
    for i in range(size):
        for j in range(size):
            if i == size - 1 and j == size - 1:
                if board[i][j] != 0:
                    return False
            else:
                if board[i][j] != expected:
                    return False
                expected += 1
    return True

def get_blank_position(board):
    size = len(board)
    for i in range(size):
        for j in range(size):
            if board[i][j] == 0:
                return i, j
    return None, None

def can_move(board, row, col):
    blank_row, blank_col = get_blank_position(board)
    if blank_row is None:
        return False
    return (abs(row - blank_row) + abs(col - blank_col)) == 1

def move_tile(board, row, col):
    blank_row, blank_col = get_blank_position(board)
    if can_move(board, row, col):
        board[blank_row][blank_col], board[row][col] = board[row][col], board[blank_row][blank_col]
        return True
    return False

def get_board_keyboard(board, level):
    size = len(board)
    keyboard = []
    for i in range(size):
        row = []
        for j in range(size):
            num = board[i][j]
            text = "⬜" if num == 0 else str(num)
            row.append(InlineKeyboardButton(text, callback_data=f"numpuz_{level}_{i}_{j}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def numpuz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    
    # Add columns if not exists
    try:
        await db.execute("ALTER TABLE numpuz_progress ADD COLUMN chat_id BIGINT")
    except:
        pass
    try:
        await db.execute("ALTER TABLE numpuz_progress ADD COLUMN owner_id BIGINT")
    except:
        pass
    
    # 🔥 FIX: Always create new game, ignore existing
    saved = None
    
    if saved and saved['board']:
        level = saved['level']
        board = json.loads(saved['board'])
        owner_id = saved['owner_id']
        
        owner_name = await db.fetchval("SELECT name FROM users WHERE user_id = $1", owner_id)
        owner_name = owner_name if owner_name else "Someone"
        
        keyboard = get_board_keyboard(board, level)
        size = len(board)
        await db.close()
        
        await update.message.reply_text(
            f"🧩 NUMBER PUZZLE - LEVEL {level}\n"
            f"🎮 Game started by: {owner_name}\n"
            f"🔒 Only {owner_name} can play this game!\n"
            f"Arrange numbers from 1 to {size*size - 1}\n"
            f"⬜ is the empty space.",
            reply_markup=keyboard
        )
        return
    
    # Create new game for this chat
    level = 1
    size = get_size_for_level(level)
    while True:
        board = get_shuffled_board(size)
        if is_solvable(board):
            break
    
    # Delete any existing game for this user first
    await db.execute("DELETE FROM numpuz_progress WHERE user_id = $1", user_id)
    
    await db.execute("""
        INSERT INTO numpuz_progress (user_id, level, board, moves, chat_id, owner_id) 
        VALUES ($1, $2, $3, $4, $5, $6)
    """, user_id, level, json.dumps(board), 0, chat_id, user_id)
    
    await db.close()
    
    keyboard = get_board_keyboard(board, level)
    await update.message.reply_text(
        f"🧩 NUMBER PUZZLE - LEVEL {level}\n"
        f"👑 Game started by: {update.effective_user.first_name}\n"
        f"🔒 Only you can play this game!\n"
        f"Arrange numbers from 1 to {size*size - 1}\n"
        f"⬜ is the empty space. Click adjacent tiles to move.",
        reply_markup=keyboard
    )

async def numpuz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    data = query.data
    
    if not data.startswith("numpuz_"):
        return
    
    parts = data.split("_")
    level = int(parts[1])
    row = int(parts[2])
    col = int(parts[3])
    
    db = await get_db()
    
    # Get game for this user
    saved = await db.fetchrow("SELECT level, board, moves, owner_id FROM numpuz_progress WHERE user_id = $1", user_id)
    
    if not saved:
        await query.answer("No active game! Use /numpuz", show_alert=True)
        await db.close()
        return
    
    db_level, board_json, moves, owner_id = saved['level'], saved['board'], saved['moves'], saved['owner_id']
    
    if owner_id != user_id:
        await query.answer("❌ This is not your game!", show_alert=True)
        await db.close()
        return
    
    board = json.loads(board_json)
    
    if db_level != level:
        await query.answer("Invalid move!", show_alert=True)
        await db.close()
        return
    
    if move_tile(board, row, col):
        moves += 1
        
        if is_win(board):
            next_level = db_level + 1
            next_size = get_size_for_level(next_level)
            
            while True:
                new_board = get_shuffled_board(next_size)
                if is_solvable(new_board):
                    break
            
            await db.execute("UPDATE numpuz_progress SET level = $1, board = $2, moves = $3, owner_id = $4 WHERE user_id = $5",
                             next_level, json.dumps(new_board), 0, user_id, user_id)
            await db.close()
            
            keyboard = get_board_keyboard(new_board, next_level)
            await query.edit_message_text(
                f"🎉 LEVEL {db_level} COMPLETE! 🎉\n\n"
                f"📊 Moves taken: {moves}\n"
                f"✨ Moving to LEVEL {next_level}!",
                reply_markup=keyboard
            )
            return
        
        await db.execute("UPDATE numpuz_progress SET board = $1, moves = $2 WHERE user_id = $3",
                         json.dumps(board), moves, user_id)
        await db.close()
        
        keyboard = get_board_keyboard(board, db_level)
        await query.edit_message_text(
            f"🧩 NUMBER PUZZLE - LEVEL {db_level}\n"
            f"📊 Moves: {moves}",
            reply_markup=keyboard
        )
    else:
        await db.close()
        await query.answer("Invalid move! Click tile adjacent to ⬜", show_alert=True)

# ============ TIC TAC TOE ==========
ttt_games = {}
ttt_lobby = {}
ttt_next_id = 1

class TicTacToe:
    def __init__(self, game_id, player1_id, player1_name, player2_name, bet, chat_id):
        self.game_id = game_id
        self.player1_id = player1_id
        self.player1_name = player1_name
        self.player2_id = None
        self.player2_name = player2_name
        self.bet = bet
        self.chat_id = chat_id
        self.board = ['⬜', '⬜', '⬜', '⬜', '⬜', '⬜', '⬜', '⬜', '⬜']
        self.current_turn = player1_id
        self.game_active = False
        self.winner = None
    
    def make_move(self, position, user_id):
        if not self.game_active:
            return False, "Game not active"
        if user_id != self.current_turn:
            return False, "Not your turn!"
        if self.board[position] != '⬜':
            return False, "Position taken!"
        
        symbol = '❌' if user_id == self.player1_id else '⭕'
        self.board[position] = symbol
        
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a,b,c in wins:
            if self.board[a] == symbol and self.board[b] == symbol and self.board[c] == symbol:
                self.winner = user_id
                self.game_active = False
                return True, "win"
        
        if all(cell != '⬜' for cell in self.board):
            self.game_active = False
            return True, "draw"
        
        self.current_turn = self.player2_id if user_id == self.player1_id else self.player1_id
        return True, "continue"
    
    def get_keyboard(self):
        keyboard = []
        row = []
        for i in range(9):
            row.append(InlineKeyboardButton(self.board[i], callback_data=f"ttt_{self.game_id}_{i}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        return InlineKeyboardMarkup(keyboard)

async def ttt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.message.chat.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    bet = 0
    if args:
        try:
            bet = int(args[0])
            if bet < 100:
                await update.message.reply_text("❌ Minimum bet 100 credits!")
                return
        except:
            await update.message.reply_text("❌ Invalid bet!")
            return
    
    if bet > 0:
        db = await get_db()
        balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        await db.close()
        if balance < bet:
            await update.message.reply_text(f"❌ Need {bet:,} credits!")
            return
    
    global ttt_next_id
    game_id = ttt_next_id
    ttt_next_id += 1
    
    ttt_lobby[game_id] = {"creator_id": user_id, "creator_name": user_name, "bet": bet, "chat_id": chat_id}
    bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Normal Game"
    await update.message.reply_text(
        f"🎯 TIC TAC TOE\n\n👑 {user_name} (❌)\n{bet_text}\n\n⚡ Waiting for opponent...",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 JOIN", callback_data=f"ttt_join_{game_id}")]])
    )

async def ttt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = query.data
    
    if data.startswith("ttt_join_"):
        game_id = int(data.split("_")[2])
        if game_id not in ttt_lobby:
            await query.edit_message_text("❌ Lobby expired!")
            return
        
        lobby = ttt_lobby[game_id]
        creator_id = lobby["creator_id"]
        creator_name = lobby["creator_name"]
        bet = lobby["bet"]
        chat_id = lobby["chat_id"]
        
        if creator_id == user_id:
            await query.answer("Can't join own game!", show_alert=True)
            return
        
        if bet > 0:
            db = await get_db()
            balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
            if balance < bet:
                await query.edit_message_text(f"❌ Need {bet:,} credits!")
                await db.close()
                return
            await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, creator_id)
            await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
            await db.close()
        
        game = TicTacToe(game_id, creator_id, creator_name, user_name, bet, chat_id)
        game.player2_id = user_id
        game.game_active = True
        ttt_games[game_id] = game
        del ttt_lobby[game_id]
        
        bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Normal Game"
        await query.edit_message_text(f"🎯 TIC TAC TOE\n❌ {creator_name} vs ⭕ {user_name}\n{bet_text}\n🎯 {creator_name}'s Turn", reply_markup=game.get_keyboard())
        return
    
    if data.startswith("ttt_"):
        parts = data.split("_")
        game_id = int(parts[1])
        pos = int(parts[2])
        
        if game_id not in ttt_games:
            await query.answer("Game not found!", show_alert=True)
            return
        
        game = ttt_games[game_id]
        
        if user_id != game.player1_id and user_id != game.player2_id:
            await query.answer("Not your game!", show_alert=True)
            return
        
        result, msg = game.make_move(pos, user_id)
        if not result:
            await query.answer(msg, show_alert=True)
            return
        
        if msg == "win":
            winner_id = game.winner
            winner_name = game.player1_name if winner_id == game.player1_id else game.player2_name
            
            if game.bet > 0:
                db = await get_db()
                current_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", winner_id)
                new_bal = current_bal + (game.bet * 2)
                await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_bal, winner_id)
                await db.close()
                result_text = f"🏆 WINNER: {winner_name.upper()} 🏆\n💰 +{game.bet*2:,} credits"
            else:
                result_text = f"🏆 WINNER: {winner_name.upper()} 🏆"
            
            await query.edit_message_text(f"🎯 TIC TAC TOE\n\n❌ {game.player1_name} vs ⭕ {game.player2_name}\n\n{result_text}", reply_markup=game.get_keyboard())
            del ttt_games[game_id]
            return
        
        elif msg == "draw":
            if game.bet > 0:
                db = await get_db()
                await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player1_id)
                await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player2_id)
                await db.close()
            
            await query.edit_message_text(f"🎯 TIC TAC TOE\n\n❌ {game.player1_name} vs ⭕ {game.player2_name}\n\n🤝 DRAW 🤝", reply_markup=game.get_keyboard())
            del ttt_games[game_id]
            return
        
        else:
            turn_name = game.player1_name if game.current_turn == game.player1_id else game.player2_name
            turn_symbol = "❌" if game.current_turn == game.player1_id else "⭕"
            bet_text = f"💰 Bet: {game.bet:,} | Prize: {game.bet*2:,}" if game.bet > 0 else "🎮 Normal Game"
            await query.edit_message_text(f"🎯 TIC TAC TOE\n❌ {game.player1_name} vs ⭕ {game.player2_name}\n{bet_text}\n🎯 {turn_name}'s Turn ({turn_symbol})", reply_markup=game.get_keyboard())

# ============ RPS GAME ==========
rps_games = {}
rps_lobby = {}
rps_next_id = 1

class RPSGame:
    def __init__(self, game_id, player1_id, player1_name, bet, chat_id):
        self.game_id = game_id
        self.player1_id = player1_id
        self.player1_name = player1_name
        self.player2_id = None
        self.player2_name = None
        self.bet = bet
        self.chat_id = chat_id
        self.player1_choice = None
        self.player2_choice = None
        self.game_active = False
        self.waiting_for = player1_id
    
    def check_winner(self):
        if self.player1_choice == self.player2_choice:
            return "draw"
        if (self.player1_choice == "rock" and self.player2_choice == "scissors") or \
           (self.player1_choice == "paper" and self.player2_choice == "rock") or \
           (self.player1_choice == "scissors" and self.player2_choice == "paper"):
            return self.player1_id
        return self.player2_id
    
    def get_result_text(self):
        p1_emoji = {"rock": "✊", "paper": "📄", "scissors": "✂️"}[self.player1_choice]
        p2_emoji = {"rock": "✊", "paper": "📄", "scissors": "✂️"}[self.player2_choice]
        winner = self.check_winner()
        if winner == "draw":
            return f"{p1_emoji} {self.player1_name}: {self.player1_choice.upper()}\n{p2_emoji} {self.player2_name}: {self.player2_choice.upper()}\n\n🤝 DRAW! 🤝"
        else:
            winner_name = self.player1_name if winner == self.player1_id else self.player2_name
            return f"{p1_emoji} {self.player1_name}: {self.player1_choice.upper()}\n{p2_emoji} {self.player2_name}: {self.player2_choice.upper()}\n\n🏆 WINNER: {winner_name.upper()} 🏆"

async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.message.chat.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    args = context.args
    bet = 0
    if args:
        try:
            bet = int(args[0])
            if bet < 100:
                await update.message.reply_text("❌ Minimum bet 100 credits!")
                return
        except:
            await update.message.reply_text("❌ Invalid bet!")
            return
    if bet > 0:
        db = await get_db()
        balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        await db.close()
        if balance < bet:
            await update.message.reply_text(f"❌ Need {bet:,} credits!")
            return
    global rps_next_id
    game_id = rps_next_id
    rps_next_id += 1
    rps_lobby[game_id] = {"creator_id": user_id, "creator_name": user_name, "bet": bet, "chat_id": chat_id}
    bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Free Play"
    await update.message.reply_text(f"✊ ROCK PAPER SCISSORS\n\n👑 Host: {user_name}\n{bet_text}\n\n⚡ Waiting for opponent...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 JOIN", callback_data=f"rps_join_{game_id}")]]))

async def rps_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = query.data
    if data.startswith("rps_join_"):
        game_id = int(data.split("_")[2])
        if game_id not in rps_lobby:
            await query.edit_message_text("❌ Lobby expired!")
            return
        lobby = rps_lobby[game_id]
        creator_id = lobby["creator_id"]
        creator_name = lobby["creator_name"]
        bet = lobby["bet"]
        chat_id = lobby["chat_id"]
        if creator_id == user_id:
            await query.answer("Can't join own game!", show_alert=True)
            return
        if bet > 0:
            db = await get_db()
            balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
            if balance < bet:
                await query.answer(f"❌ Need {bet} credits!", show_alert=True)
                await db.close()
                return
            await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, creator_id)
            await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
            await db.close()
        game = RPSGame(game_id, creator_id, creator_name, bet, chat_id)
        game.player2_id = user_id
        game.player2_name = user_name
        game.game_active = True
        rps_games[game_id] = game
        del rps_lobby[game_id]
        keyboard = [
            [InlineKeyboardButton("✊ ROCK", callback_data=f"rps_move_{game_id}_rock")],
            [InlineKeyboardButton("📄 PAPER", callback_data=f"rps_move_{game_id}_paper")],
            [InlineKeyboardButton("✂️ SCISSORS", callback_data=f"rps_move_{game_id}_scissors")]
        ]
        bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Free Play"
        await query.edit_message_text(f"✊ RPS\n\n{creator_name} vs {user_name}\n{bet_text}\n🎯 {creator_name}'s turn!", reply_markup=InlineKeyboardMarkup(keyboard))

async def rps_move_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    choice = parts[3]
    if game_id not in rps_games:
        await query.edit_message_text("❌ Game not found!")
        return
    game = rps_games[game_id]
    if user_id != game.waiting_for:
        await query.answer("Not your turn!", show_alert=True)
        return
    if user_id == game.player1_id:
        game.player1_choice = choice
        game.waiting_for = game.player2_id
        keyboard = [
            [InlineKeyboardButton("✊ ROCK", callback_data=f"rps_move_{game_id}_rock")],
            [InlineKeyboardButton("📄 PAPER", callback_data=f"rps_move_{game_id}_paper")],
            [InlineKeyboardButton("✂️ SCISSORS", callback_data=f"rps_move_{game_id}_scissors")]
        ]
        bet_text = f"💰 Bet: {game.bet:,} | Prize: {game.bet*2:,}" if game.bet > 0 else "🎮 Free Play"
        await query.edit_message_text(f"✊ RPS\n\n{game.player1_name} vs {game.player2_name}\n{bet_text}\n✅ {game.player1_name} chose!\n🎯 {game.player2_name}'s turn!", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        game.player2_choice = choice
        game.waiting_for = None
        game.game_active = False
        result_text = game.get_result_text()
        winner = game.check_winner()
        if game.bet > 0 and winner != "draw":
            db = await get_db()
            await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet*2, winner)
            await db.close()
            winner_name = game.player1_name if winner == game.player1_id else game.player2_name
            result_text += f"\n\n💰 Prize: {game.bet*2:,} credits\n🏆 {winner_name} +{game.bet*2:,}"
        elif game.bet > 0 and winner == "draw":
            db = await get_db()
            await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player1_id)
            await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player2_id)
            await db.close()
            result_text += f"\n\n💰 Money returned: {game.bet:,} each"
        await query.edit_message_text(f"✊ RPS\n\n{result_text}")
        del rps_games[game_id]

async def rps_none_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Game Over!", show_alert=True)

# ============ ADMIN CRICKET COMMANDS ==========
async def addmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text('❌ /addmatch TEAM1 vs TEAM2 YYYY-MM-DD')
        return
    team1 = args[0]
    team2 = args[2]
    date = args[3]
    db = await get_db()
    await db.execute("INSERT INTO matches (team1, team2, date, status, locked) VALUES ($1, $2, $3, 'upcoming', 0)", team1, team2, date)
    await db.close()
    await update.message.reply_text(f"✅ MATCH ADDED!\n\n🏏 {team1} vs {team2}\n📅 {date}\n🔓 Status: OPEN")

# ============ DELETE MATCH (Auto Refund) ==========
async def deletematch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('❌ /deletematch TEAM1 vs TEAM2\nExample: /deletematch India vs Afghanistan')
        return
    
    team1 = args[0].upper()
    team2 = args[2].upper()
    
    db = await get_db()
    
    # Find match
    match = await db.fetchrow("SELECT id, team1, team2 FROM matches WHERE LOWER(team1) = LOWER($1) AND LOWER(team2) = LOWER($2)", team1, team2)
    
    if not match:
        await update.message.reply_text(f'❌ Match {team1} vs {team2} not found!')
        await db.close()
        return
    
    # Get all bets for this match
    bets = await db.fetch("SELECT user_id, amount FROM bets WHERE match_id = $1", match['id'])
    
    refund_count = 0
    refund_total = 0
    
    # Refund all bets
    for bet in bets:
        user_id = bet['user_id']
        amount = bet['amount']
        await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)
        refund_count += 1
        refund_total += amount
    
    # Delete bets and match
    await db.execute("DELETE FROM bets WHERE match_id = $1", match['id'])
    await db.execute("DELETE FROM matches WHERE id = $1", match['id'])
    
    await db.close()
    
    await update.message.reply_text(
        f"🗑️ MATCH DELETED + REFUNDED!\n\n"
        f"🏏 {match['team1']} vs {match['team2']}\n"
        f"💰 Refunded: {refund_count} users\n"
        f"💰 Total refund: {refund_total:,} credits"
    )

async def lockmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('❌ /lockmatch TEAM1 vs TEAM2\nExample: /lockmatch India vs Afghanistan')
        return
    
    team1 = args[0]
    team2 = args[2]
    
    db = await get_db()
    
    # 🔥 CASE INSENSITIVE SEARCH
    match = await db.fetchrow("""
        SELECT id, team1, team2, locked 
        FROM matches 
        WHERE LOWER(team1) = LOWER($1) AND LOWER(team2) = LOWER($2)
    """, team1, team2)
    
    if not match:
        await update.message.reply_text(f'❌ Match {team1} vs {team2} not found!')
        await db.close()
        return
    
    if match['locked'] == 1:
        await update.message.reply_text(f'⚠️ Match is already LOCKED!')
        await db.close()
        return
    
    await db.execute("UPDATE matches SET locked = 1 WHERE id = $1", match['id'])
    
    # Get total bets
    total = await db.fetchval("SELECT COALESCE(SUM(amount), 0) FROM bets WHERE match_id = $1", match['id'])
    count = await db.fetchval("SELECT COUNT(*) FROM bets WHERE match_id = $1", match['id'])
    
    await db.close()
    
    await update.message.reply_text(
        f"🔒 MATCH LOCKED!\n\n"
        f"🏏 {match['team1']} vs {match['team2']}\n"
        f"📊 Bets: {count}\n"
        f"💰 Pool: {total:,} 💰\n"
        f"❌ No more bets accepted!"
    )

# ============ RESULT ==========
async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return

    args = context.args
    if len(args) < 4:
        await update.message.reply_text('❌ /result TEAM1 vs TEAM2 WINNER\nExample: /result India vs Afghanistan India')
        return

    team1 = args[0]
    team2 = args[2]
    winner = args[3]

    db = await get_db()

    match = await db.fetchrow("""
        SELECT id, team1, team2 FROM matches
        WHERE LOWER(team1) = LOWER($1) AND LOWER(team2) = LOWER($2)
    """, team1, team2)

    if not match:
        await update.message.reply_text(f'❌ Match {team1} vs {team2} not found!')
        await db.close()
        return

    if winner.upper() not in [match['team1'].upper(), match['team2'].upper()]:
        await update.message.reply_text(f'❌ Winner must be {match["team1"]} or {match["team2"]}!')
        await db.close()
        return

    bets = await db.fetch("SELECT user_id, amount, team FROM bets WHERE match_id = $1", match['id'])

    winners_count = 0
    losers_count = 0
    total_paid = 0

    # 🔥 HAR BET COUNT KARO (NO SKIP!)
    for bet in bets:
        user_id = bet['user_id']
        amount = bet['amount']
        bet_team = bet['team']

        user = await db.fetchrow("SELECT balance, won, total, points FROM users WHERE user_id = $1", user_id)

        if bet_team.upper() == winner.upper():
            win_amount = amount * 2
            new_balance = user['balance'] + win_amount
            new_won = user['won'] + 1
            new_total = user['total'] + 1
            new_points = user['points'] + 10
            await db.execute("""
                UPDATE users SET balance = $1, won = $2, total = $3, points = $4
                WHERE user_id = $5
            """, new_balance, new_won, new_total, new_points, user_id)
            total_paid += win_amount
            winners_count += 1
        else:
            new_total = user['total'] + 1
            new_points = user['points'] - 5
            await db.execute("UPDATE users SET total = $1, points = $2 WHERE user_id = $3", new_total, new_points, user_id)
            losers_count += 1

    await db.execute("DELETE FROM bets WHERE match_id = $1", match['id'])
    await db.execute("DELETE FROM matches WHERE id = $1", match['id'])

    await db.close()

    await update.message.reply_text(
        f"📢 MATCH RESULT!\n\n"
        f"🏏 {match['team1']} vs {match['team2']}\n"
        f"🏆 WINNER: {winner.upper()}\n\n"
        f"✅ WINNERS (+10 pts): {winners_count} users\n"
        f"❌ LOSERS (-5 pts): {losers_count} users\n\n"
        f"💰 TOTAL PAYOUT: {total_paid:,} 💰"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return  # ❌ SIRF CHUP RAHEGA, KUCH NAHI BOLEGA
    
    if not update.message.reply_to_message:
        return  # ❌ SIRF CHUP RAHEGA
    
    args = context.args
    if len(args) < 1:
        return  # ❌ SIRF CHUP RAHEGA
    
    try:
        amount = int(args[0])
    except:
        return
    
    target = update.message.reply_to_message.from_user
    
    db = await get_db()
    old = await db.fetchrow("SELECT balance, name FROM users WHERE user_id = $1", target.id)
    if not old:
        await update.message.reply_text('❌ User not found!')
        await db.close()
        return
    
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, target.id)
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", target.id)
    await db.close()
    
    await update.message.reply_text(
        f"✅ ADDED {amount:,} to {old['name']}\n"
        f"💰 Balance: {old['balance']:,} → {new_bal:,} 💰"
    )

# ============ REMOVE FROM WALLET ONLY ==========
async def removew(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not update.message.reply_to_message:
        return
    
    args = context.args
    if len(args) < 1:
        return
    
    try:
        amount = int(args[0])
    except:
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    
    db = await get_db()
    
    user = await db.fetchrow("SELECT balance FROM users WHERE user_id = $1", target_id)
    if not user:
        await update.message.reply_text('❌ User not found!')
        await db.close()
        return
    
    wallet_bal = user['balance']
    
    if wallet_bal < amount:
        await update.message.reply_text(f'❌ Insufficient wallet balance! Have: {wallet_bal:,}')
        await db.close()
        return
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", amount, target_id)
    new_wallet = wallet_bal - amount
    
    await db.close()
    
    await update.message.reply_text(
        f"❌ REMOVED {amount:,} from {target.first_name}'s WALLET\n\n"
        f"💰 Wallet: {wallet_bal:,} → {new_wallet:,}"
    )


# ============ REMOVE FROM BANK ONLY ==========
async def removeb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    if not update.message.reply_to_message:
        return
    
    args = context.args
    if len(args) < 1:
        return
    
    try:
        amount = int(args[0])
    except:
        return
    
    target = update.message.reply_to_message.from_user
    target_id = target.id
    
    db = await get_db()
    
    bank = await db.fetchrow("SELECT balance FROM bank WHERE user_id = $1", target_id)
    if not bank:
        await update.message.reply_text('❌ No bank account found!')
        await db.close()
        return
    
    bank_bal = bank['balance']
    
    if bank_bal < amount:
        await update.message.reply_text(f'❌ Insufficient bank balance! Have: {bank_bal:,}')
        await db.close()
        return
    
    await db.execute("UPDATE bank SET balance = balance - $1 WHERE user_id = $2", amount, target_id)
    new_bank = bank_bal - amount
    
    await db.close()
    
    await update.message.reply_text(
        f"❌ REMOVED {amount:,} from {target.first_name}'s BANK\n\n"
        f"🏦 Bank: {bank_bal:,} → {new_bank:,}"
    )

# ============ HALL OF FAME ==========
async def hof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    db = await get_db()
    winners = await db.fetch("SELECT id, winner FROM hall_of_fame ORDER BY id ASC")
    await db.close()
    if not winners:
        await update.message.reply_text("🏆 HALL OF FAME 🏆\n\nNo winners yet!")
        return
    msg = "🏆 HALL OF FAME 🏆\n\n"
    for i, w in enumerate(winners, 1):
        msg += f"{i}. {w['winner']}\n"
    msg += f"\n📊 Total Winners: {len(winners)}"
    await update.message.reply_text(msg)

async def addhof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /addhof <winner_name>")
        return
    winner = " ".join(args)
    db = await get_db()
    await db.execute("INSERT INTO hall_of_fame (winner, added_by, added_at) VALUES ($1, $2, $3)", winner, update.effective_user.id, datetime.now().isoformat())
    count = await db.fetchval("SELECT COUNT(*) FROM hall_of_fame")
    await db.close()
    await update.message.reply_text(f"✅ Added to Hall of Fame!\n\n🏆 {winner}\n\n📊 Total Winners: {count}")

async def rmhof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /rmhof <number>")
        return
    try:
        num = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid number!")
        return
    db = await get_db()
    winners = await db.fetch("SELECT id, winner FROM hall_of_fame ORDER BY id ASC")
    if num < 1 or num > len(winners):
        await update.message.reply_text(f"❌ Invalid! Choose 1-{len(winners)}")
        await db.close()
        return
    winner_id = winners[num-1]['id']
    winner_text = winners[num-1]['winner']
    await db.execute("DELETE FROM hall_of_fame WHERE id = $1", winner_id)
    count = await db.fetchval("SELECT COUNT(*) FROM hall_of_fame")
    await db.close()
    await update.message.reply_text(f"🗑️ Removed from Hall of Fame!\n\n❌ Removed: {winner_text}\n\n📊 Total Winners: {count}")

async def edithof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /edithof <number> <new_text>")
        return
    try:
        num = int(args[0])
        new_text = " ".join(args[1:])
    except:
        await update.message.reply_text("❌ Invalid number!")
        return
    db = await get_db()
    winners = await db.fetch("SELECT id, winner FROM hall_of_fame ORDER BY id ASC")
    if num < 1 or num > len(winners):
        await update.message.reply_text(f"❌ Invalid! Choose 1-{len(winners)}")
        await db.close()
        return
    winner_id = winners[num-1]['id']
    old_text = winners[num-1]['winner']
    await db.execute("UPDATE hall_of_fame SET winner = $1 WHERE id = $2", new_text, winner_id)
    await db.close()
    await update.message.reply_text(f"✏️ EDITED HALL OF FAME!\n\n❌ Old: {old_text}\n✅ New: {new_text}")



# ============ CLAIM CODES ==========
async def createcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("📝 Usage: /createcode <amount> <code>\nExample: /createcode 1000 FESTIVAL10")
        return
    try:
        amount = int(args[0])
        code = args[1].upper()
    except:
        await update.message.reply_text("❌ Invalid!")
        return
    if amount < 100:
        await update.message.reply_text("❌ Minimum amount 100 credits!")
        return
    db = await get_db()
    exists = await db.fetchval("SELECT code FROM claim_codes WHERE code = $1", code)
    if exists:
        await update.message.reply_text(f"❌ Code '{code}' already exists!")
        await db.close()
        return
    now = datetime.now()
    expires_at = now + timedelta(hours=24)
    await db.execute("INSERT INTO claim_codes (code, amount, max_claims, created_by, created_at, expires_at) VALUES ($1, $2, 5, $3, $4, $5)", code, amount, update.effective_user.id, now.isoformat(), expires_at.isoformat())
    await db.close()
    await update.message.reply_text(f"✅ CODE CREATED!\n\n🔑 Code: {code}\n💰 Amount: {amount:,} credits\n👥 Max claims: 5 users\n⏰ Expires: 24 hours\n\nClaim: /claimcode {code}")

async def claimcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: /claimcode <code>")
        return
    code = args[0].upper()
    db = await get_db()
    result = await db.fetchrow("SELECT code, amount, max_claims, claimed_count, expires_at FROM claim_codes WHERE code = $1", code)
    if not result:
        await update.message.reply_text(f"❌ Code '{code}' not found!")
        await db.close()
        return
    expires = datetime.fromisoformat(result['expires_at'])
    if datetime.now() > expires:
        await update.message.reply_text(f"❌ Code '{code}' expired!")
        await db.close()
        return
    claimed = await db.fetchval("SELECT code FROM code_claims WHERE code = $1 AND user_id = $2", code, user_id)
    if claimed:
        await update.message.reply_text(f"❌ You already claimed '{code}'!")
        await db.close()
        return
    if result['claimed_count'] >= result['max_claims']:
        await update.message.reply_text(f"❌ Code '{code}' max claims reached!")
        await db.close()
        return
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", result['amount'], user_id)
    await db.execute("UPDATE claim_codes SET claimed_count = claimed_count + 1 WHERE code = $1", code)
    await db.execute("INSERT INTO code_claims (code, user_id, claimed_at) VALUES ($1, $2, $3)", code, user_id, datetime.now().isoformat())
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    remaining = result['max_claims'] - (result['claimed_count'] + 1)
    await db.close()
    await update.message.reply_text(f"🎉 CODE CLAIMED!\n\n🔑 Code: {code}\n💰 +{result['amount']:,} credits\n💳 New balance: {new_bal:,}\n📊 Remaining: {remaining}/{result['max_claims']}")

# ============ ACTIVECODES ==========
# ============ ACTIVECODES ==========
async def activecodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    
    # 🔥 FIX: expires_at ko text se timestamp mein cast karo
    codes = await db.fetch("""
        SELECT code, amount, max_claims, claimed_count, expires_at 
        FROM claim_codes 
        WHERE expires_at::timestamptz > NOW() AND claimed_count < max_claims 
        ORDER BY created_at DESC 
        LIMIT 10
    """)
    
    await db.close()
    
    if not codes:
        await update.message.reply_text(
            "📭 NO ACTIVE CODES\n\n"
            "No codes available right now!\n"
            "Check back later for rewards! 🎁"
        )
        return
    
    msg = "🎁 ACTIVE CLAIM CODES\n\n"
    for code in codes:
        remaining = code['max_claims'] - code['claimed_count']
        msg += f"🔑 Code: `{code['code']}`\n"
        msg += f"💰 Amount: {code['amount']:,} credits\n"
        msg += f"👥 Remaining: {remaining}/{code['max_claims']} claims\n"
        msg += f"💡 /claimcode {code['code']}\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Use /claimcode <code> to claim rewards!"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

# ============ NUMBER GUESS GAME ==========
game_data = {}

async def numguess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    if chat_id in game_data:
        await update.message.reply_text(f"❌ Game active! Started by: {game_data[chat_id]['player_name']}\nUse /ngstop to stop.")
        return
    number = random.randint(1, 100)
    game_data[chat_id] = {"number": number, "attempts": 0, "player_id": user_id, "player_name": user_name, "chat_id": chat_id}
    await update.message.reply_text(f"🎲 Number Guessing Game!\n👤 Host: {user_name}\n📊 Number 1-100\n💡 /ng <number> to guess!\n🛑 /ngstop to end")

async def ng(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    if chat_id not in game_data:
        await update.message.reply_text("❌ No active game! Use /numguess")
        return
    game = game_data[chat_id]
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ /ng <number>")
        return
    try:
        guess = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid number!")
        return
    if guess < 1 or guess > 100:
        await update.message.reply_text("❌ Number 1-100!")
        return
    game["attempts"] += 1
    target = game["number"]
    if guess == target:
        attempts = game["attempts"]
        if attempts == 1:
            reward = 5000
            msg = f"🎉 PERFECT! {user_id} guessed {target} in FIRST attempt! +{reward} coins!"
        elif attempts <= 3:
            reward = 2000
            msg = f"🎉 AMAZING! +{reward} coins!"
        elif attempts <= 5:
            reward = 1000
            msg = f"🎉 EXCELLENT! +{reward} coins!"
        elif attempts <= 7:
            reward = 500
            msg = f"🎉 GOOD JOB! +{reward} coins!"
        elif attempts <= 10:
            reward = 300
            msg = f"🎉 NOT BAD! +{reward} coins!"
        elif attempts <= 15:
            reward = 150
            msg = f"🎉 OKAY! +{reward} coins!"
        else:
            reward = 50
            msg = f"🎉 FINALLY! +{reward} coins!"
        db = await get_db()
        await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", reward, user_id)
        await db.close()
        del game_data[chat_id]
        await update.message.reply_text(msg)
    elif guess < target:
        await update.message.reply_text(f"📈 Too low! Attempts: {game['attempts']}")
    else:
        await update.message.reply_text(f"📉 Too high! Attempts: {game['attempts']}")

async def ngstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    if chat_id not in game_data:
        await update.message.reply_text("❌ No active game!")
        return
    game = game_data[chat_id]
    if user_id not in ADMIN_IDS and game["player_id"] != user_id:
        await update.message.reply_text("❌ Only host or admin can stop!")
        return
    target = game["number"]
    attempts = game["attempts"]
    host_name = game["player_name"]
    del game_data[chat_id]
    await update.message.reply_text(f"🛑 Game Stopped!\n👤 Host: {host_name}\n🔢 Number was: {target}\n📊 Attempts: {attempts}")

# ============ GROUP TRACKING ==========
async def track_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        group_id = update.message.chat.id
        group_name = update.message.chat.title or "Unknown Group"
        db = await get_db()
        await db.execute("INSERT INTO groups (group_id, group_name, added_at) VALUES ($1, $2, $3) ON CONFLICT (group_id) DO NOTHING", group_id, group_name, datetime.now().isoformat())
        await db.close()

# ============ BROADCAST ==========
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    msg = update.message
    db = await get_db()
    users = [row['user_id'] for row in await db.fetch("SELECT user_id FROM users")]
    groups = [row['group_id'] for row in await db.fetch("SELECT group_id FROM groups")]
    await db.close()
    sent = 0
    if msg.reply_to_message and msg.reply_to_message.photo:
        photo = msg.reply_to_message.photo[-1].file_id
        caption = msg.reply_to_message.caption or ""
        for uid in users:
            try:
                await context.bot.send_photo(uid, photo, caption=caption)
                sent += 1
            except:
                pass
        for gid in groups:
            try:
                await context.bot.send_photo(gid, photo, caption=caption)
                sent += 1
            except:
                pass
        await update.message.reply_text(f"📸 BROADCAST SENT! Total: {sent}")
        return
    content = msg.reply_to_message.text if msg.reply_to_message else " ".join(context.args)
    for uid in users:
        try:
            await context.bot.send_message(uid, content)
            sent += 1
        except:
            pass
    for gid in groups:
        try:
            await context.bot.send_message(gid, content)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"📢 BROADCAST SENT! Total: {sent}")

async def broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    db = await get_db()
    users = await db.fetchval("SELECT COUNT(*) FROM users")
    groups = await db.fetchval("SELECT COUNT(*) FROM groups")
    await db.close()
    await update.message.reply_text(f"📊 BROADCAST STATS\n\n👤 Users: {users}\n👥 Groups: {groups}\n📡 Total: {users + groups}")

# ============ STATS ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    keyboard = [
        [InlineKeyboardButton("🏏 MOST RUNS", callback_data="stats_runs")],
        [InlineKeyboardButton("🎯 MOST WICKETS", callback_data="stats_wickets")],
        [InlineKeyboardButton("⭐ HIGHEST SCORE", callback_data="stats_highest")],
        [InlineKeyboardButton("✅ MOST WINS", callback_data="stats_wins")],
        [InlineKeyboardButton("❌ MOST LOSSES", callback_data="stats_losses")],
        [InlineKeyboardButton("🦆 MOST DUCKS", callback_data="stats_ducks")],
        [InlineKeyboardButton("🏆 OVERALL TOP 5", callback_data="stats_mvp")],
    ]
    await update.message.reply_text("🏏 CRICKET STATS LEADERBOARD\n\nSelect stat to view:", reply_markup=InlineKeyboardMarkup(keyboard))

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    db = await get_db()

    if data == "stats_runs":
        top = await db.fetch("SELECT name, runs FROM cricket_stats ORDER BY runs DESC LIMIT 5")
        msg = "🏏 MOST RUNS LEADERBOARD\n\n"
        medals = ["1.", "2.", "3.", "4.", "5."]
        for i, t in enumerate(top):
            msg += f"{medals[i]} {t['name']} - {t['runs']} runs\n"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "stats_wickets":
        top = await db.fetch("SELECT name, wickets FROM cricket_stats ORDER BY wickets DESC LIMIT 5")
        msg = "🎯 MOST WICKETS LEADERBOARD\n\n"
        medals = ["1.", "2.", "3.", "4.", "5."]
        for i, t in enumerate(top):
            msg += f"{medals[i]} {t['name']} - {t['wickets']} wickets\n"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "stats_highest":
        top = await db.fetch("SELECT name, highest_score FROM cricket_stats ORDER BY highest_score DESC LIMIT 5")
        msg = "⭐ HIGHEST SCORE LEADERBOARD\n\n"
        medals = ["1.", "2.", "3.", "4.", "5."]
        for i, t in enumerate(top):
            msg += f"{medals[i]} {t['name']} - {t['highest_score']} runs\n"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "stats_wins":
        top = await db.fetch("SELECT name, wins FROM cricket_stats ORDER BY wins DESC LIMIT 5")
        msg = "✅ MOST WINS LEADERBOARD\n\n"
        medals = ["1.", "2.", "3.", "4.", "5."]
        for i, t in enumerate(top):
            msg += f"{medals[i]} {t['name']} - {t['wins']} wins\n"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "stats_losses":
        top = await db.fetch("SELECT name, losses FROM cricket_stats ORDER BY losses DESC LIMIT 5")
        msg = "❌ MOST LOSSES LEADERBOARD\n\n"
        medals = ["1.", "2.", "3.", "4.", "5."]
        for i, t in enumerate(top):
            msg += f"{medals[i]} {t['name']} - {t['losses']} losses\n"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "stats_ducks":
        top = await db.fetch("SELECT name, ducks FROM cricket_stats WHERE ducks > 0 ORDER BY ducks DESC LIMIT 5")
        msg = "🦆 MOST DUCKS LEADERBOARD\n\n"
        medals = ["1.", "2.", "3.", "4.", "5."]
        for i, t in enumerate(top):
            msg += f"{medals[i]} {t['name']} - {t['ducks']} ducks\n"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "stats_mvp":
        # 🔥 FIXED: LOSSES AND DUCKS ARE NEGATIVE
        players = await db.fetch("""
            SELECT name, runs, wickets, highest_score, wins, losses, ducks,
                   (runs * 2) + (wickets * 3) + (highest_score * 2) + (wins * 2) - (losses * 2) - (ducks * 5) as total_score
            FROM cricket_stats
            ORDER BY total_score DESC
            LIMIT 5
        """)

        msg = "🏆 OVERALL TOP 5 PLAYERS\n\n"
        medals = ["1.", "2.", "3.", "4.", "5."]

        for i, p in enumerate(players):
            msg += f"{medals[i]} {p['name']}\n"
            msg += f"   Runs: *{p['runs']}*  Wickets: *{p['wickets']}*  HS: *{p['highest_score']}*  Wins: *{p['wins']}*  Losses: *{p['losses']}*"
            if p['ducks'] > 0:
                msg += f"  Ducks: *{p['ducks']}*"
            msg += f"\n\n"

        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "stats_back":
        keyboard = [
            [InlineKeyboardButton("🏏 MOST RUNS", callback_data="stats_runs")],
            [InlineKeyboardButton("🎯 MOST WICKETS", callback_data="stats_wickets")],
            [InlineKeyboardButton("⭐ HIGHEST SCORE", callback_data="stats_highest")],
            [InlineKeyboardButton("✅ MOST WINS", callback_data="stats_wins")],
            [InlineKeyboardButton("❌ MOST LOSSES", callback_data="stats_losses")],
            [InlineKeyboardButton("🦆 MOST DUCKS", callback_data="stats_ducks")],
            [InlineKeyboardButton("🏆 OVERALL TOP 5", callback_data="stats_mvp")],
        ]
        await query.edit_message_text("🏏 CRICKET STATS LEADERBOARD\n\nSelect stat to view:", reply_markup=InlineKeyboardMarkup(keyboard))

    await db.close()

# ============ MYSTATS ==========
async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user
    name = user.first_name if user.first_name else (user.username or "User")

    if not await is_registered(user_id):
        await update.message.reply_text('*❌ Send /start first!*', parse_mode="Markdown")
        return

    db = await get_db()
    stats = await db.fetchrow("SELECT runs, wickets, highest_score, wins, losses, ducks FROM cricket_stats WHERE user_id = $1", user_id)

    if not stats:
        await db.close()
        await update.message.reply_text(
            f"*🏏 MY CRICKET STATS*\n\n"
            f"*👤 {name}*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"*🏏 Runs:* 0 *(📊 Rank: N/A)*\n"
            f"*🎯 Wickets:* 0 *(📊 Rank: N/A)*\n"
            f"*⭐ Highest Score:* 0 *(📊 Rank: N/A)*\n"
            f"*✅ Wins:* 0 *(📊 Rank: N/A)*\n"
            f"*❌ Losses:* 0 *(📊 Rank: N/A)*\n"
            f"*🦆 Ducks:* 0 *(📊 Rank: N/A)*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"*💡 Play /CLcricket to start!*",
            parse_mode="Markdown"
        )
        return

    runs = stats['runs']
    wickets = stats['wickets']
    highest_score = stats['highest_score']
    wins = stats['wins']
    losses = stats['losses']
    ducks = stats['ducks'] or 0

    runs_rank = await db.fetchval("SELECT COUNT(*) + 1 FROM cricket_stats WHERE runs > $1", runs) if runs > 0 else None
    wickets_rank = await db.fetchval("SELECT COUNT(*) + 1 FROM cricket_stats WHERE wickets > $1", wickets) if wickets > 0 else None
    highest_rank = await db.fetchval("SELECT COUNT(*) + 1 FROM cricket_stats WHERE highest_score > $1", highest_score) if highest_score > 0 else None
    wins_rank = await db.fetchval("SELECT COUNT(*) + 1 FROM cricket_stats WHERE wins > $1", wins) if wins > 0 else None
    losses_rank = await db.fetchval("SELECT COUNT(*) + 1 FROM cricket_stats WHERE losses > $1", losses) if losses > 0 else None
    ducks_rank = await db.fetchval("SELECT COUNT(*) + 1 FROM cricket_stats WHERE ducks > $1", ducks) if ducks > 0 else None

    await db.close()

    msg = f"*🏏 MY CRICKET STATS*\n\n"
    msg += f"*👤 {name}*\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"*🏏 Runs:* {runs} *(📊 Rank: #{runs_rank if runs_rank else 'N/A'})*\n"
    msg += f"*🎯 Wickets:* {wickets} *(📊 Rank: #{wickets_rank if wickets_rank else 'N/A'})*\n"
    msg += f"*⭐ Highest Score:* {highest_score} *(📊 Rank: #{highest_rank if highest_rank else 'N/A'})*\n"
    msg += f"*✅ Wins:* {wins} *(📊 Rank: #{wins_rank if wins_rank else 'N/A'})*\n"
    msg += f"*❌ Losses:* {losses} *(📊 Rank: #{losses_rank if losses_rank else 'N/A'})*\n"
    if ducks > 0:
        msg += f"*🦆 Ducks:* {ducks} *(📊 Rank: #{ducks_rank if ducks_rank else 'N/A'})*\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━"

    await update.message.reply_text(msg, parse_mode="Markdown")


# ============ MATCHES ==========
async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('*❌ Send /start first!*', parse_mode="Markdown")
        return

    db = await get_db()
    matches_data = await db.fetch("SELECT id, team1, team2, date, locked FROM matches")

    if not matches_data:
        await update.message.reply_text('*📭 No matches found!*', parse_mode="Markdown")
        await db.close()
        return

    msg = "*🏏 LIVE MATCHES*\n\n"
    for m in matches_data:
        status = "🔒 LOCKED" if m['locked'] == 1 else "🔓 OPEN"
        msg += f"*🔥 {m['team1']} vs {m['team2']}*\n"
        msg += f"*📅 {m['date']} | {status}*\n"
        if m['locked'] == 0:
            msg += f"*💰 /bet {m['team1']} <amount> | /bet {m['team2']} <amount>*\n"
        else:
            msg += f"*⚠️ Betting closed!*\n"
        msg += "\n"

    user = await get_user(user_id)
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n*💰 Your balance: {user['balance']:,} 💰*"
    
    await update.message.reply_text(msg, parse_mode="Markdown")
    await db.close()

# ============ MYBETS ==========
async def mybets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    
    bets_data = await db.fetch("""
        SELECT b.id, b.team, b.amount, m.team1, m.team2, m.date, m.locked
        FROM bets b 
        JOIN matches m ON b.match_id = m.id 
        WHERE b.user_id = $1
        ORDER BY m.date DESC
    """, user_id)
    
    await db.close()
    
    if not bets_data:
        await update.message.reply_text('📭 No bets placed yet!')
        return
    
    msg = f"🎯 MY BETS ({len(bets_data)})\n\n"
    for i, bet in enumerate(bets_data, 1):
        status = "🔒 LOCKED" if bet['locked'] == 1 else "🔓 OPEN"
        msg += f"{i}️⃣ {bet['team1']} vs {bet['team2']}\n"
        msg += f"   🎯 {bet['team']} | 💰 {bet['amount']:,}\n"
        msg += f"   📅 {bet['date']} | {status}\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "💡 /cancel <number> to cancel bet (only if match is OPEN)"
    
    await update.message.reply_text(msg)

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /bet TEAM AMOUNT\nExample: /bet India 1000\n\n💰 Min: 100 | Max: 35,000')
        return
    
    team = args[0]
    try:
        amount = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('❌ Minimum 100 credits')
        return
    
    if amount > 35000:
        await update.message.reply_text('❌ Maximum 35,000 credits per bet!')
        return
    
    db = await get_db()
    
    match = await db.fetchrow("""
        SELECT id, team1, team2, locked 
        FROM matches 
        WHERE LOWER(team1) = LOWER($1) OR LOWER(team2) = LOWER($1)
    """, team)
    
    if not match:
        await update.message.reply_text(f'❌ Match with {team} not found!')
        await db.close()
        return
    
    if match['locked'] == 1:
        await update.message.reply_text(f'🔒 Match is LOCKED! Betting closed for {match["team1"]} vs {match["team2"]}')
        await db.close()
        return
    
    bet_count = await db.fetchval("""
        SELECT COUNT(*) FROM bets 
        WHERE user_id = $1 AND match_id = $2
    """, user_id, match['id'])
    
    if bet_count >= 2:
        await update.message.reply_text("❌ You can only place up to 2 bets per match!")
        await db.close()
        return
    
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < amount:
        await update.message.reply_text(f'❌ Need {amount:,}, have {balance:,}')
        await db.close()
        return
    
    bet_team = match['team1'] if match['team1'].lower() == team.lower() else match['team2']
    
    await db.execute("""
        INSERT INTO bets (user_id, match_id, team, amount) 
        VALUES ($1, $2, $3, $4)
    """, user_id, match['id'], bet_team, amount)
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", amount, user_id)
    
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await db.close()
    
    # 🔥 BOLD KE LIYE ESCAPE
    team1_escaped = escape_markdown(match['team1'])
    team2_escaped = escape_markdown(match['team2'])
    bet_team_escaped = escape_markdown(bet_team)
    
    await update.message.reply_text(
        f"✅ *BET PLACED!* (PENDING)\n\n"
        f"🏏 *{team1_escaped}* vs *{team2_escaped}*\n"
        f"🎯 *{bet_team_escaped}*\n"
        f"💰 *{amount:,}* 💰\n\n"
        f"📊 Status: ⏳ *PENDING*\n"
        f"💡 Result will be announced after match ends!\n\n"
        f"📊 Current balance: *{new_bal:,}* 💰",
        parse_mode="Markdown"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 🔥 FIX: CHECK KARO update.message HAI YA NAHI
    if update.message is None:
        return
    
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /cancel <bet_number>')
        return
    
    try:
        bet_number = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid number')
        return
    
    db = await get_db()
    bets_data = await db.fetch("""
        SELECT b.id, b.amount, m.team1, m.team2, m.locked
        FROM bets b JOIN matches m ON b.match_id = m.id
        WHERE b.user_id = $1 AND m.locked = 0
    """, user_id)
    
    if bet_number < 1 or bet_number > len(bets_data):
        await update.message.reply_text(f'❌ Choose 1-{len(bets_data)}')
        await db.close()
        return
    
    bet_to_cancel = bets_data[bet_number - 1]
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", bet_to_cancel['amount'], user_id)
    await db.execute("DELETE FROM bets WHERE id = $1", bet_to_cancel['id'])
    await db.execute("UPDATE users SET total = total - 1 WHERE user_id = $1", user_id)
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await db.close()
    
    await update.message.reply_text(f"✅ BET CANCELLED!\n\n🏏 {bet_to_cancel['team1']} vs {bet_to_cancel['team2']}\n💰 Refund: {bet_to_cancel['amount']:,} 💰\n📊 New balance: {new_bal:,} 💰")

# ============ ALLBETS WITH BUTTONS ============
async def allbets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all matches with buttons"""
    user_id = update.effective_user.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    matches = await db.fetch("SELECT id, team1, team2, locked FROM matches ORDER BY id DESC")
    
    if not matches:
        await update.message.reply_text('📭 No matches found!')
        await db.close()
        return
    
    # Summary message
    total_pool = 0
    total_users = set()
    summary_msg = "📊 ALL BETS\n\n"
    
    for i, m in enumerate(matches, 1):
        bets = await db.fetch("SELECT team, amount, user_id FROM bets WHERE match_id = $1", m['id'])
        
        team1_total = sum(b['amount'] for b in bets if b['team'] == m['team1'])
        team2_total = sum(b['amount'] for b in bets if b['team'] == m['team2'])
        unique_users = len(set(b['user_id'] for b in bets))
        
        total_pool += team1_total + team2_total
        for b in bets:
            total_users.add(b['user_id'])
        
        status = "🔓 OPEN" if m['locked'] == 0 else "🔒 LOCKED"
        summary_msg += f"{i}️⃣ {m['team1']} vs {m['team2']} [{status}]\n"
        summary_msg += f"💰 {m['team1']}: {team1_total:,} | {m['team2']}: {team2_total:,}\n"
        summary_msg += f"👥 Users: {unique_users} | Pool: {team1_total + team2_total:,}\n\n"
    
    summary_msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    summary_msg += f"💰 Total Pool: {total_pool:,}\n"
    summary_msg += f"👥 Total Bets: {len(total_users)} users"
    
    # 🔥 BUTTONS - SIRF MATCHES KE (NO BACK TO SUMMARY)
    keyboard = []
    for i, m in enumerate(matches, 1):
        status = "🔓" if m['locked'] == 0 else "🔒"
        btn_text = f"{i}️⃣ {m['team1']} vs {m['team2']} {status}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"allbets_detail_{m['id']}")])
    
    # 🔥 YEH LINE HATAO (BACK TO SUMMARY)
    # keyboard.append([InlineKeyboardButton("📊 BACK TO SUMMARY", callback_data="allbets_summary")])
    
    await db.close()
    await update.message.reply_text(summary_msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def allbets_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle allbets button clicks"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    db = await get_db()
    
    # Handle Match Detail
    if data.startswith("allbets_detail_"):
        match_id = int(data.split("_")[2])
        
        match = await db.fetchrow("SELECT id, team1, team2, locked FROM matches WHERE id = $1", match_id)
        
        if not match:
            await query.edit_message_text("❌ Match not found!")
            await db.close()
            return
        
        bets_data = await db.fetch("""
            SELECT b.team, b.amount, u.name
            FROM bets b
            JOIN users u ON b.user_id = u.user_id
            WHERE b.match_id = $1
            ORDER BY b.amount DESC
        """, match_id)
        
        team1_amount = 0
        team2_amount = 0
        team1_users = []
        team2_users = []
        
        for bet in bets_data:
            if bet['team'] == match['team1']:
                team1_amount += bet['amount']
                team1_users.append(f"• {bet['name']} - {bet['amount']:,}")
            else:
                team2_amount += bet['amount']
                team2_users.append(f"• {bet['name']} - {bet['amount']:,}")
        
        status = "🔓 OPEN" if match['locked'] == 0 else "🔒 LOCKED"
        
        msg = f"📊 MATCH DETAILS\n\n"
        msg += f"🏏 {match['team1']} vs {match['team2']} [{status}]\n\n"
        
        msg += f"🎯 {match['team1']} (Total: {team1_amount:,} 💰):\n"
        if team1_users:
            msg += "\n".join(team1_users) + "\n"
        else:
            msg += "   No bets\n"
        
        msg += f"\n🎯 {match['team2']} (Total: {team2_amount:,} 💰):\n"
        if team2_users:
            msg += "\n".join(team2_users) + "\n"
        else:
            msg += "   No bets\n"
        
        msg += f"\n💣 Total Pool: {team1_amount + team2_amount:,} 💰"
        
        # 🔥 NO BACK BUTTON - SIRF MESSAGE
        await query.edit_message_text(msg)
        await db.close()
        return
    
    # 🔥 SUMMARY HANDLER HATAO (AB ZAROORAT NAHI)
    # if data == "allbets_summary":
    #     ...

async def track_all_activity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.from_user:
        user_id = update.message.from_user.id
        chat_id = update.message.chat.id
        
        if not await is_registered(user_id):
            return
        
        db = await get_db()
        await db.execute("""
            INSERT INTO user_activity (user_id, chat_id, activity_score, last_active)
            VALUES ($1, $2, 1, NOW())
            ON CONFLICT (user_id, chat_id) DO UPDATE SET
                activity_score = user_activity.activity_score + 1,
                last_active = NOW()
        """, user_id, chat_id)
        await db.close()

async def rain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type

    if chat_type not in ['group', 'supergroup']:
        await update.message.reply_text("❌ Groups only!")
        return

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return

    db = await get_db()

    # Check cooldown
    last_rain = await db.fetchval("SELECT last_rain FROM rain_cooldown WHERE chat_id = $1", chat_id)

    if last_rain:
        last_time = last_rain
        next_time = last_time + timedelta(hours=1)
        if datetime.now() < next_time:
            remaining = next_time - datetime.now()
            minutes = remaining.seconds // 60
            await update.message.reply_text(f"⏰ Next rain in {minutes} minutes!")
            await db.close()
            return

    # Get active users (last 24 hours) - TOP 10 ONLY
    active_users = await db.fetch("""
        SELECT u.user_id, u.name, ua.activity_score
        FROM user_activity ua
        JOIN users u ON ua.user_id = u.user_id
        WHERE ua.chat_id = $1 AND ua.last_active > NOW() - INTERVAL '24 hours'
        ORDER BY ua.activity_score DESC
        LIMIT 10
    """, chat_id)

    if not active_users:
        await update.message.reply_text("❌ No active users!")
        await db.close()
        return

    # 🔥 HAR USER KO 1,000 CREDITS
    per_user_coins = 1000

    results = []

    for user in active_users:
        results.append({
            'user_id': user['user_id'],
            'name': user['name'],
            'coins': per_user_coins
        })

    # Update cooldown
    await db.execute("INSERT INTO rain_cooldown (chat_id, last_rain) VALUES ($1, $2) ON CONFLICT (chat_id) DO UPDATE SET last_rain = $2",
                     chat_id, datetime.now())

    # Send message and update balances
    msg = "🌧️💰 THE COIN RAIN HAS FALLEN! 💰🌧️\n\n"

    for i, r in enumerate(results, 1):
        await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", r['coins'], r['user_id'])
        msg += f"{i}. {r['name']} - 💰 {r['coins']:,} credits\n"

    await db.close()
    await update.message.reply_text(msg)


# ============ HISTORY ==========
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    user = await db.fetchrow("SELECT won, total, points FROM users WHERE user_id = $1", user_id)
    await db.close()
    
    if not user:
        await update.message.reply_text('❌ User not found!')
        return
    
    # 🔥 FIX 1: Lost positive karo
    lost = user['total'] - user['won']
    if lost < 0:
        lost = 0
    
    # 🔥 FIX 2: Win rate max 100%
    if user['total'] > 0:
        win_rate = int((user['won'] / user['total']) * 100)
        if win_rate > 100:
            win_rate = 100
    else:
        win_rate = 0
    
    msg = f"📜 BET HISTORY\n\n"
    msg += f"✅ Won: {user['won']}\n"
    msg += f"❌ Lost: {lost}\n"
    msg += f"📊 Win Rate: {win_rate}%\n\n"
    msg += f"🏆 Fantasy Points: {user['points']}"
    
    await update.message.reply_text(msg)


# ============ TOWER CLIMB GAME ============

import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler

# Store active games
tower_games = {}

# Floor configurations
FLOORS = [
    {"floor": 1, "safe": 2, "bombs": 1, "multiplier": 1.3},
    {"floor": 2, "safe": 2, "bombs": 1, "multiplier": 1.7},
    {"floor": 3, "safe": 2, "bombs": 1, "multiplier": 2.2},
    {"floor": 4, "safe": 2, "bombs": 1, "multiplier": 3.4},
    {"floor": 5, "safe": 1, "bombs": 2, "multiplier": 4.0},
    {"floor": 6, "safe": 1, "bombs": 2, "multiplier": 5.0},
]

class TowerGame:
    def __init__(self, user_id, bet):
        self.user_id = user_id
        self.bet = bet
        self.current_floor = 0
        self.multiplier = 1.0
        self.win_amount = bet
        self.game_active = True
        self.doors = self.generate_doors(0)
    
    def generate_doors(self, floor_index):
        """Generate doors for current floor (1=safe, 0=bomb)"""
        floor = FLOORS[floor_index]
        doors = [1] * floor["safe"] + [0] * floor["bombs"]
        random.shuffle(doors)
        return doors
    
    def open_door(self, door_index):
        """Open a door, return (is_safe, win_amount)"""
        if not self.game_active:
            return False, 0
        
        if self.current_floor >= len(FLOORS):
            return False, 0
        
        # Check if door is safe
        is_safe = self.doors[door_index] == 1
        
        if is_safe:
            self.current_floor += 1
            if self.current_floor < len(FLOORS):
                floor = FLOORS[self.current_floor]
                self.multiplier = floor["multiplier"]
                self.win_amount = int(self.bet * self.multiplier)
                self.doors = self.generate_doors(self.current_floor)
            else:
                # All floors completed!
                self.game_active = False
                self.win_amount = int(self.bet * 5.0)
            return True, self.win_amount
        else:
            # Bomb hit
            self.game_active = False
            self.win_amount = 0
            return False, 0
    
    def cashout(self):
        """Cashout current winnings"""
        if not self.game_active:
            return 0
        self.game_active = False
        return self.win_amount
    
    def get_current_floor_data(self):
        if self.current_floor >= len(FLOORS):
            return None
        return FLOORS[self.current_floor]
    
    def get_floor_display(self):
        floor_data = self.get_current_floor_data()
        if not floor_data:
            return "🏆 COMPLETED!"
        
        floor_num = floor_data["floor"]
        safe = floor_data["safe"]
        bombs = floor_data["bombs"]
        multi = floor_data["multiplier"]
        
        if floor_num <= 4:
            emoji = ["🟢", "🟡", "🟠", "🔴"][floor_num - 1]
        else:
            emoji = "💀" if floor_num == 5 else "☠️"
        
        return f"{emoji} FLOOR {floor_num}\n🚪 {safe} Safe | 💣 {bombs} Bombs\n💸 Multiplier: {multi}x"


def get_tower_keyboard(game):
    """Create keyboard for tower game"""
    keyboard = [
        [
            InlineKeyboardButton("🚪 1", callback_data=f"tower_door_{game.user_id}_0"),
            InlineKeyboardButton("🚪 2", callback_data=f"tower_door_{game.user_id}_1"),
            InlineKeyboardButton("🚪 3", callback_data=f"tower_door_{game.user_id}_2")
        ],
        [InlineKeyboardButton("💰 CASHOUT", callback_data=f"tower_cashout_{game.user_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def tower(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Tower Climb game - /tower <amount>"""
    user_id = update.effective_user.id
    
    # 🔥 FIX 1: await lagao
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "🏰 **TOWER CLIMB**\n\n"
            "Usage: `/tower <amount>`\n"
            "Example: `/tower 500`\n\n"
            "⚡ Min bet: 100\n"
            "⚡ Max bet: 7,000\n"
            "🎯 Climb 6 floors to win 5x!\n"
            "💀 One wrong door = lose all!\n"
            "💰 Cashout anytime!",
            parse_mode="Markdown"
        )
        return
    
    try:
        bet = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid bet amount!")
        return
    
    if bet < 100:
        await update.message.reply_text("❌ Minimum bet is 100 coins!")
        return
    
    if bet > 7000:
        await update.message.reply_text("❌ Maximum bet is 7,000 coins!")
        return
    
    # 🔥 FIX 2: asyncpg style use karo
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance is None:
        await update.message.reply_text("❌ User not found! Send /start first!")
        await db.close()
        return
    
    if balance < bet:
        await update.message.reply_text(f"❌ Need {bet:,} coins, have {balance:,}")
        await db.close()
        return
    
    # Deduct bet
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
    await db.close()
    
    # Create game
    game = TowerGame(user_id, bet)
    tower_games[user_id] = game
    
    floor_display = game.get_floor_display()
    keyboard = get_tower_keyboard(game)
    
    await update.message.reply_text(
        f"🏰 **TOWER CLIMB**\n\n"
        f"💰 Bet: {bet:,} coins\n"
        f"📊 {floor_display}\n"
        f"💎 Win: {game.win_amount:,} coins\n\n"
        f"Choose a door:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def tower_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle tower game button clicks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data.startswith("tower_"):
        parts = data.split("_")
        action = parts[1]
        game_user_id = int(parts[2])
        
        if user_id != game_user_id:
            await query.answer("Not your game!", show_alert=True)
            return
        
        if user_id not in tower_games:
            await query.edit_message_text(
                "❌ No active game!\nUse `/tower <amount>` to start!",
                parse_mode="Markdown"
            )
            return
        
        game = tower_games[user_id]
        
        if not game.game_active:
            await query.edit_message_text(
                "❌ Game already ended!\nUse `/tower <amount>` to start!",
                parse_mode="Markdown"
            )
            return
        
        # Handle cashout
        if action == "cashout":
            win_amount = game.cashout()
            
            if win_amount > 0:
                # 🔥 FIX 3: asyncpg style
                db = await get_db()
                current_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
                await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", win_amount, user_id)
                await db.close()
                
                await query.edit_message_text(
                    f"💰 **CASHOUT!**\n\n"
                    f"🛗 Climbed {game.current_floor}/6 floors\n"
                    f"📈 Multiplier: {game.multiplier}x\n"
                    f"💎 You won: {win_amount:,} coins\n"
                    f"💳 Balance: {current_bal + win_amount:,}\n\n"
                    f"💡 /tower to play again!",
                    parse_mode="Markdown"
                )
                del tower_games[user_id]
                return
            else:
                await query.edit_message_text(
                    f"❌ No winnings to cashout!\n"
                    f"💡 /tower to play again!",
                    parse_mode="Markdown"
                )
                del tower_games[user_id]
                return
        
        # Handle door click
        if action == "door":
            door_index = int(parts[3])
            
            is_safe, win_amount = game.open_door(door_index)
            
            if is_safe:
                # Check if all floors completed
                if game.current_floor >= len(FLOORS):
                    # Full win!
                    # 🔥 FIX 4: asyncpg style
                    db = await get_db()
                    current_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
                    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", win_amount, user_id)
                    await db.close()
                    
                    await query.edit_message_text(
                        f"🎉 **YOU CONQUERED THE TOWER!** 🎉\n\n"
                        f"🏆 All 6 floors cleared!\n"
                        f"💎 You won: {win_amount:,} coins!\n"
                        f"📈 Multiplier: 5x\n"
                        f"💳 Balance: {current_bal + win_amount:,}\n\n"
                        f"👑 YOU ARE THE TOWER MASTER!",
                        parse_mode="Markdown"
                    )
                    del tower_games[user_id]
                    return
                
                # Continue to next floor
                floor_display = game.get_floor_display()
                keyboard = get_tower_keyboard(game)
                
                await query.edit_message_text(
                    f"🏰 **TOWER CLIMB**\n\n"
                    f"✅ **SAFE!** Floor {game.current_floor}/{len(FLOORS)} cleared!\n\n"
                    f"💰 Bet: {game.bet:,} coins\n"
                    f"📊 {floor_display}\n"
                    f"💎 Win: {game.win_amount:,} coins\n\n"
                    f"Choose a door:",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                # Bomb hit - game over
                await query.edit_message_text(
                    f"💣 **BOOM!**\n\n"
                    f"💀 You hit a bomb on Floor {game.current_floor + 1}!\n"
                    f"💔 Lost: {game.bet:,} coins\n"
                    f"🛗 Climbed: {game.current_floor}/6 floors\n\n"
                    f"😵 Game Over!\n"
                    f"💡 /tower to try again!",
                    parse_mode="Markdown"
                )
                del tower_games[user_id]
                return
        else:
            await query.answer("Invalid action!", show_alert=True)

# ============ BALANCE COMMAND ==========
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check your wallet balance only"""
    user_id = update.effective_user.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await db.close()
    
    if balance is None:
        await update.message.reply_text("❌ User not found! Send /start first.")
        return
    
    user = update.effective_user
    name = user.first_name if user.first_name else (user.username or "User")
    
    await update.message.reply_text(
        f"💰 **BALANCE**\n\n"
        f"👤 {name}\n"
        f"💳 Wallet: **{balance:,}** credits\n\n"
        f"💡 Use /bank to check bank balance",
        parse_mode="Markdown"
    )



# ============ REMOVE DUPLICATE PLAYERS ==========
async def fix_duplicates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    db = await get_db()
    
    # 🔥 Find duplicates with COUNT
    duplicates = await db.fetch("""
        SELECT user_id, player_id, type, COUNT(*) as count
        FROM user_players
        GROUP BY user_id, player_id, type
        HAVING COUNT(*) > 1
    """)
    
    if not duplicates:
        await update.message.reply_text("✅ No duplicate players found!")
        await db.close()
        return
    
    removed = 0
    for dup in duplicates:
        user_id = dup['user_id']
        player_id = dup['player_id']
        ptype = dup['type']
        count = dup['count']
        
        # 🔥 Keep only 1, delete rest using CTID
        await db.execute("""
            DELETE FROM user_players 
            WHERE ctid IN (
                SELECT ctid FROM user_players 
                WHERE user_id = $1 AND player_id = $2 AND type = $3
                LIMIT $4 OFFSET 1
            )
        """, user_id, player_id, ptype, count - 1)
        
        removed += count - 1
    
    await db.close()
    
    await update.message.reply_text(
        f"✅ FIXED DUPLICATES!\n\n"
        f"🗑️ Removed: {removed} duplicate entries"
    )
async def fix_achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fix all achievement duplicates - Admin only"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    db = await get_db()
    
    # 1️⃣ DELETE ALL DUPLICATES (Keep only 1 per user)
    await db.execute("""
        DELETE FROM achievements a
        USING achievements b
        WHERE a.user_id = b.user_id 
        AND a.achievement = b.achievement
        AND a.ctid > b.ctid
    """)
    
    # 2️⃣ ADD UNIQUE CONSTRAINT (Prevent future duplicates)
    try:
        await db.execute("""
            ALTER TABLE achievements 
            ADD CONSTRAINT unique_user_achievement 
            UNIQUE (user_id, achievement)
        """)
    except:
        pass  # Already exists
    
    # 3️⃣ GET FINAL COUNT
    count = await db.fetchval("SELECT COUNT(*) FROM achievements")
    await db.close()
    
    await update.message.reply_text(
        f"✅ ACHIEVEMENTS FIXED!\n\n"
        f"📊 Total achievements: {count}\n"
        f"🔒 Duplicate protection added!\n\n"
        f"💡 Now /achievements will show correctly."
    )

# ============ ADD PLAYER (FIXED - BOLD) ==========
async def add_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await update.message.reply_text("*❌ Admin only!*", parse_mode="Markdown")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "*❌ Usage:* `/add_player <name> <base_price>`\n\n"
            "*Example:* `/add_player Virat 5000`\n\n"
            "*💡 Minimum price: 1,000*",
            parse_mode="Markdown"
        )
        return

    name = " ".join(args[:-1])

    try:
        base_price = int(args[-1])
    except:
        await update.message.reply_text("*❌ Invalid price!*", parse_mode="Markdown")
        return

    if base_price < 1000:
        await update.message.reply_text("*❌ Base price must be at least 1,000!*", parse_mode="Markdown")
        return

    db = await get_db()
    now = datetime.now()

    await db.execute(
        "INSERT INTO auction_players (name, base_price, current_bid, added_by, added_at, end_time, status) VALUES ($1, $2, $3, $4, $5, NULL, 'active')",
        name, base_price, base_price, user_id, now.isoformat()
    )

    player_id = await db.fetchval("SELECT lastval()")
    await db.close()

    await update.message.reply_text(
        f"*✅ PLAYER ADDED!*\n\n"
        f"*🏏 Name:* {name}\n"
        f"*💰 Base Price:* {base_price:,}\n"
        f"*🆔 ID:* {player_id}\n"
        f"*⏰ Time:* TBD\n\n"
        f"*💡 Use /players to see all players*",
        parse_mode="Markdown"
    )

# ============ PLAYERS LIST ==========
async def players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('*❌ Send /start first!*', parse_mode="Markdown")
        return

    db = await get_db()

    players_data = await db.fetch("""
        SELECT id, name, base_price, current_bid, highest_bidder, end_time
        FROM auction_players
        WHERE status = 'active'
        ORDER BY id
    """)

    if not players_data:
        await update.message.reply_text("*📭 No players available right now!*", parse_mode="Markdown")
        await db.close()
        return

    msg = "*🏏 AVAILABLE PLAYERS*\n\n"
    for p in players_data:
        # 🔥 TIME HATAO - Sirf "TBD" dikhao
        time_left = "⏰ TBD"

        bidder_name = "No bids"
        if p['highest_bidder']:
            bidder = await db.fetchval("SELECT name FROM users WHERE user_id = $1", p['highest_bidder'])
            bidder_name = bidder if bidder else "Unknown"

        msg += f"*🆔 {p['id']}. {p['name']}*\n"
        msg += f"   *💰 Base:* {p['base_price']:,} | *Current:* {p['current_bid']:,}\n"
        msg += f"   *👤 Highest Bidder:* {bidder_name}\n"
        msg += f"   *{time_left}*\n\n"

    msg += "*💡 /bid <id> <amount> to place bid*"

    await update.message.reply_text(msg, parse_mode="Markdown")
    await db.close()

# ============ BID ==========
async def bid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('*❌ Send /start first!*', parse_mode="Markdown")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "*❌ Usage:* `/bid <player_id> <amount>`\n\n"
            "*Example:* `/bid 1 60000`\n\n"
            "*💡 Use /players to see available players.*",
            parse_mode="Markdown"
        )
        return

    try:
        player_id = int(args[0])
        amount = int(args[1])
    except:
        await update.message.reply_text("*❌ Invalid input! Use numbers only.*", parse_mode="Markdown")
        return

    if amount < 1000:
        await update.message.reply_text("*❌ Minimum bid is 1,000!*", parse_mode="Markdown")
        return

    db = await get_db()

    player = await db.fetchrow("SELECT * FROM auction_players WHERE id = $1 AND status = 'active'", player_id)
    if not player:
        await update.message.reply_text("*❌ Player not found or auction ended!*", parse_mode="Markdown")
        await db.close()
        return

    end_time = datetime.fromisoformat(player['end_time'])
    if datetime.now() > end_time:
        await update.message.reply_text("*⏰ Auction for this player has ended!*", parse_mode="Markdown")
        await db.close()
        return

    if amount <= player['current_bid']:
        await update.message.reply_text(
            f"*❌ Bid must be higher than current bid!*\n\n"
            f"*Current Bid:* {player['current_bid']:,}\n"
            f"*Minimum Bid:* {player['current_bid'] + 1:,}",
            parse_mode="Markdown"
        )
        await db.close()
        return

    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    if balance < amount:
        await update.message.reply_text(
            f"*❌ Insufficient balance!*\n\n"
            f"*Your Balance:* {balance:,}\n"
            f"*Required:* {amount:,}",
            parse_mode="Markdown"
        )
        await db.close()
        return

    # 🔥 DEDUCT BALANCE
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", amount, user_id)

    # 🔥 UPDATE CURRENT BID
    await db.execute(
        "UPDATE auction_players SET current_bid = $1, highest_bidder = $2 WHERE id = $3",
        amount, user_id, player_id
    )

    # 🔥 SAVE BID HISTORY
    await db.execute(
        "INSERT INTO bid_history (player_id, user_id, amount, bid_at) VALUES ($1, $2, $3, $4)",
        player_id, user_id, amount, datetime.now().isoformat()
    )

    await db.close()

    await update.message.reply_text(
        f"*✅ BID PLACED!*\n\n"
        f"*🏏 Player:* {player['name']}\n"
        f"*💰 Your Bid:* {amount:,}\n"
        f"*👤 Current Highest:* You\n"
        f"*⏰ Time left:* {remaining_time}",
        parse_mode="Markdown"
    )

# ============ RESULT AUCTION ==========
async def result_auction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("*❌ Admin only!*", parse_mode="Markdown")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "*❌ Usage:* `/result_auction <player_id>`",
            parse_mode="Markdown"
        )
        return

    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text("*❌ Invalid player ID!*", parse_mode="Markdown")
        return

    db = await get_db()

    player = await db.fetchrow("SELECT * FROM auction_players WHERE id = $1 AND status = 'active'", player_id)
    if not player:
        await update.message.reply_text("*❌ Player not found or already sold!*", parse_mode="Markdown")
        await db.close()
        return

    if not player['highest_bidder']:
        await update.message.reply_text("*❌ No bids placed on this player!*", parse_mode="Markdown")
        await db.close()
        return

    # 🔥 TIME CHECK HATAO - Admin manually result karega
    winner_id = player['highest_bidder']
    winner_name = await db.fetchval("SELECT name FROM users WHERE user_id = $1", winner_id)
    winning_bid = player['current_bid']

    await db.execute("UPDATE auction_players SET status = 'sold' WHERE id = $1", player_id)

    await db.execute(
        "INSERT INTO user_players (user_id, player_id, purchased_at) VALUES ($1, $2, $3)",
        winner_id, player_id, datetime.now().isoformat()
    )

    await db.close()

    await update.message.reply_text(
        f"*🏆 AUCTION RESULT!*\n\n"
        f"*🏏 Player:* {player['name']}\n"
        f"*👤 Winner:* {winner_name} 🎉\n"
        f"*💰 Winning Bid:* {winning_bid:,}\n\n"
        f"*✅ Player added to {winner_name}'s team!*",
        parse_mode="Markdown"
    )

async def myteam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('*❌ Send /start first!*', parse_mode="Markdown")
        return

    db = await get_db()

    players = await db.fetch("""
        SELECT p.id, p.name, p.current_bid
        FROM user_players up
        JOIN auction_players p ON up.player_id = p.id
        WHERE up.user_id = $1
        ORDER BY up.purchased_at DESC
    """, user_id)

    if not players:
        await update.message.reply_text(
            "*📭 You haven't won any players yet!*\n\n"
            "*💡 Bid on players using /players*",
            parse_mode="Markdown"
        )
        await db.close()
        return

    msg = "*🏏 MY CRICKET TEAM*\n\n"
    total = 0
    for i, p in enumerate(players, 1):
        msg += f"*{i}. {p['name']} - {p['current_bid']:,} 💰*\n"
        total += p['current_bid']

    msg += f"\n*━━━━━━━━━━━━━━━━━━━━━━*\n"
    msg += f"*💰 Total Value: {total:,} 💰*\n"
    msg += f"*🏆 Total Players: {len(players)}*"

    await update.message.reply_text(msg, parse_mode="Markdown")
    await db.close()

# ============ TOP COLLECTORS ==========
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('*❌ Send /start first!*', parse_mode="Markdown")
        return

    db = await get_db()

    tops = await db.fetch("""
        SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(p.current_bid), 0) as total
        FROM user_players up
        JOIN auction_players p ON up.player_id = p.id
        JOIN users u ON up.user_id = u.user_id
        GROUP BY u.user_id, u.name
        ORDER BY total DESC
        LIMIT 10
    """)

    if not tops:
        await update.message.reply_text("*🏆 TOP COLLECTORS*\n\n*No one has won any players yet!*", parse_mode="Markdown")
        await db.close()
        return

    msg = "*🏆 TOP COLLECTORS*\n\n"
    medals = ["🥇", "🥈", "🥉"]
    for i, t in enumerate(tops, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        msg += f"*{medal} {t['name']} - {t['count']} players ({t['total']:,} 💰)*\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
    await db.close()

# ============ REMOVE PLAYER WITH REFUND ==========
async def rmplayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("*❌ Admin only!*", parse_mode="Markdown")
        return

    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "*❌ Usage:* `/rmplayer <player_id>`\n\n"
            "*Example:* `/rmplayer 1`\n\n"
            "*💡 All bidders will get a refund.*",
            parse_mode="Markdown"
        )
        return

    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text("*❌ Invalid player ID!*", parse_mode="Markdown")
        return

    db = await get_db()

    player = await db.fetchrow("SELECT name, highest_bidder, current_bid FROM auction_players WHERE id = $1", player_id)
    if not player:
        await update.message.reply_text("*❌ Player not found!*", parse_mode="Markdown")
        await db.close()
        return

    # 🔥 GET ALL BIDDERS
    bidders = await db.fetch("SELECT DISTINCT user_id, amount FROM bid_history WHERE player_id = $1", player_id)

    refund_count = 0
    refund_total = 0

    # 🔥 REFUND ALL BIDDERS
    for bid in bidders:
        await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", bid['amount'], bid['user_id'])
        refund_count += 1
        refund_total += bid['amount']

    # 🔥 DELETE FROM AUCTION_PLAYERS
    await db.execute("DELETE FROM auction_players WHERE id = $1", player_id)

    # 🔥 DELETE FROM USER_PLAYERS (AGAR KISI NE KHARIDA HO)
    await db.execute("DELETE FROM user_players WHERE player_id = $1", player_id)

    # 🔥 DELETE BID HISTORY
    await db.execute("DELETE FROM bid_history WHERE player_id = $1", player_id)

    await db.close()

    await update.message.reply_text(
        f"*🗑️ PLAYER REMOVED + REFUNDED!*\n\n"
        f"*🏏 Name:* {player['name']}\n"
        f"*🆔 ID:* {player_id}\n\n"
        f"*💰 Refunded {refund_count} users*\n"
        f"*💰 Total Refund: {refund_total:,} 💰*\n\n"
        f"*✅ Removed from auction, teams, and history!*",
        parse_mode="Markdown"
    )


# ============ PING ==========
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return

    try:
        import time
        start_time = time.time()

        # Send initial message
        temp_msg = await msg.reply_text("🏓 Pinging...")

        end_time = time.time()
        latency = (end_time - start_time) * 1000

        await temp_msg.edit_text(
            f"*🏓 Pong!*\n"
            f"*⏱️ Latency:* {latency:.2f}ms\n"
            f"*💎 Gamble Man is active.*",
            parse_mode="Markdown"
        )

    except Exception as e:
        if "503" in str(e):
            print("⚠️ Proxy 503: Ping failed.")
            try:
                await msg.reply_text("🏓 Pong! (Lag detected)")
            except:
                pass
        else:
            print(f"❌ Ping Error: {e}")



# ============ LOGIN ============
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_registered(user_id):
        await update.message.reply_text("❌ Send /start first!")
        return

    db = await get_db()

    try:
        today = datetime.now().date()

        # Current total wealth
        total_wealth = await db.fetchval("""
            SELECT u.balance + COALESCE(b.balance, 0)
            FROM users u
            LEFT JOIN bank b ON u.user_id = b.user_id
            WHERE u.user_id = $1
        """, user_id)

        if total_wealth is None:
            total_wealth = 0

        # Rank based on total wealth
        rank = await db.fetchval("""
            SELECT COUNT(*) + 1
            FROM (
                SELECT u.user_id,
                       u.balance + COALESCE(b.balance, 0) AS total_wealth
                FROM users u
                LEFT JOIN bank b ON u.user_id = b.user_id
            ) t
            WHERE t.total_wealth > $1
        """, total_wealth)

        # Only Top 10 need daily login
        if rank > 10:
            await update.message.reply_text(
                "*ℹ️ You are not in Top 10.*\n\n"
                "*✅ Daily login is not required for you.*",
                parse_mode="Markdown"
            )
            return

        # Already logged in today?
        last_login = await db.fetchval(
            "SELECT last_login FROM login_tracker WHERE user_id = $1",
            user_id
        )

        if last_login == today:
            await update.message.reply_text(
                "*⚠️ Already logged in today!*\n\n"
                f"*📅 {today.strftime('%d %b %Y')}*\n\n"
                "*💡 Come back tomorrow!*",
                parse_mode="Markdown"
            )
            return

        # Save today's login
        await db.execute("""
            INSERT INTO login_tracker (user_id, last_login)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET last_login = EXCLUDED.last_login
        """, user_id, today)

        await update.message.reply_text(
            "*✅ Daily Login Successful!*\n\n"
            f"*📅 {today.strftime('%d %b %Y')}*\n"
            f"*🏆 Your Rank: #{rank}*\n"
            f"*🪙 Total Wealth: {total_wealth:,}*\n\n"
            "*🛡️ Today's penalty is avoided!*",
            parse_mode="Markdown"
        )

    finally:
        await db.close()

# ============ DAILY PENALTY ============
async def check_penalty():
    """
    Runs once every day.
    Only current Top 10 users are checked.
    Users who didn't login today receive a penalty.
    """

    db = await get_db()

    try:
        today = datetime.now().date()

        # Get CURRENT Top 10
        top_10 = await db.fetch("""
            SELECT
                u.user_id,
                u.balance AS wallet,
                COALESCE(b.balance, 0) AS bank,
                u.balance + COALESCE(b.balance, 0) AS total_wealth
            FROM users u
            LEFT JOIN bank b ON u.user_id = b.user_id
            ORDER BY total_wealth DESC
            LIMIT 10
        """)

        for user in top_10:

            user_id = user["user_id"]
            wallet = user["wallet"] or 0
            bank = user["bank"] or 0
            total = user["total_wealth"] or 0

            # Wealth below/equal 5000 = no penalty
            if total <= 5000:
                continue

            # Did user login today?
            last_login = await db.fetchval(
                "SELECT last_login FROM login_tracker WHERE user_id = $1",
                user_id
            )

            if last_login == today:
                continue

            # ============ PENALTY RATE ============
            if total <= 100_000:
                rate = 0.001       # 0.1%
            elif total <= 500_000:
                rate = 0.002       # 0.2%
            elif total <= 1_000_000:
                rate = 0.003       # 0.3%
            elif total <= 2_500_000:
                rate = 0.005       # 0.5%
            else:
                rate = 0.01        # 1%

            penalty = max(1, int(total * rate))

            # Never take more than total wealth
            penalty = min(penalty, total)

            # ============ TAKE FROM WALLET FIRST ============
            if wallet >= penalty:
                new_wallet = wallet - penalty
                new_bank = bank
            else:
                remaining = penalty - wallet

                new_wallet = 0
                new_bank = max(0, bank - remaining)

            new_total = new_wallet + new_bank

            # Update wallet
            await db.execute("""
                UPDATE users
                SET balance = $1
                WHERE user_id = $2
            """, new_wallet, user_id)

            # Update bank
            await db.execute("""
                INSERT INTO bank (user_id, balance)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET balance = EXCLUDED.balance
            """, user_id, new_bank)

            # Save history
            await db.execute("""
                INSERT INTO penalty_history
                (user_id, amount, penalty_date, balance_after)
                VALUES ($1, $2, $3, $4)
            """, user_id, penalty, today, new_total)

            print(
                f"💰 DAILY PENALTY | "
                f"User: {user_id} | "
                f"Penalty: {penalty:,} | "
                f"Remaining: {new_total:,}"
            )

    finally:
        await db.close()


# ============ DAILY PENALTY SCHEDULER ============
async def schedule_penalty():
    """
    Runs every day at 11:59 PM.
    """

    while True:

        now = datetime.now()

        next_run = now.replace(
            hour=23,
            minute=59,
            second=0,
            microsecond=0
        )

        if now >= next_run:
            next_run += timedelta(days=1)

        wait_seconds = (next_run - now).total_seconds()

        print(
            f"⏰ Next penalty check: "
            f"{next_run.strftime('%d %b %Y %H:%M:%S')}"
        )

        await asyncio.sleep(wait_seconds)

        try:
            await check_penalty()
            print("✅ Daily penalty check completed!")

        except Exception as e:
            print(f"❌ Penalty error: {e}")

# ============ LOGIN LOG (ADMIN) ==========
async def login_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return

    db = await get_db()
    today = datetime.now().date()

    # 🔥 CURRENT TOP 10 (TOTAL WEALTH)
    top_10 = await db.fetch("""
        SELECT u.user_id, u.name, u.balance + COALESCE(b.balance, 0) as total_wealth
        FROM users u
        LEFT JOIN bank b ON u.user_id = b.user_id
        ORDER BY total_wealth DESC
        LIMIT 10
    """)

    # 🔥 TODAY'S LOGIN
    logged_in = await db.fetch("SELECT user_id FROM login_tracker WHERE last_login = $1", today)
    logged_in_ids = [row['user_id'] for row in logged_in]

    msg = f"🌍 Global Top 10 — Coins 🪙\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"

    medals = ["👑", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    for i, u in enumerate(top_10):
        user_id = u['user_id']
        balance = u['total_wealth']
        name = u['name']

        if user_id in logged_in_ids:
            status = "✅"
        else:
            status = "❌"

        msg += f"{medals[i]} {name} : {balance:,} - {status}\n"

    # 🔥 USER RANK
    user_id = update.effective_user.id
    user_total = await db.fetchval("""
        SELECT u.balance + COALESCE(b.balance, 0)
        FROM users u
        LEFT JOIN bank b ON u.user_id = b.user_id
        WHERE u.user_id = $1
    """, user_id)

    rank = await db.fetchval("""
        SELECT COUNT(*) + 1 FROM (
            SELECT u.user_id, u.balance + COALESCE(b.balance, 0) as total
            FROM users u
            LEFT JOIN bank b ON u.user_id = b.user_id
        ) t WHERE total > $1
    """, user_total)

    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📌 Your Position: #{rank}\n"
    msg += f"🪙 Total wealth : {user_total:,}"

    await update.message.reply_text(msg)
    await db.close()


# ============ PENALTY HISTORY (ADMIN) ==========
async def penalty_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return

    db = await get_db()
    today = datetime.now().date()
    
    # 🔥 SIRF UNHE DIKHAO JINHONE AAJ LOGIN NAHI KIYA
    penalties = await db.fetch("""
        SELECT u.name, p.amount, p.penalty_date, p.balance_after
        FROM penalty_history p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.user_id NOT IN (
            SELECT user_id FROM login_tracker WHERE last_login = $1
        )
        ORDER BY p.penalty_date DESC, p.amount DESC
        LIMIT 20
    """, today)
    
    if not penalties:
        await update.message.reply_text("✅ No pending penalties! All Top 10 users have logged in today.")
        await db.close()
        return
    
    msg = f"📊 PENALTY HISTORY (Pending - Not Logged In Today)\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📅 {today.strftime('%d %b %Y')}\n\n"
    
    for p in penalties:
        msg += f"👤 {p['name']}\n"
        msg += f"   💰 -{p['amount']:,} (New Balance: {p['balance_after']:,})\n"
        msg += f"   📅 {p['penalty_date'].strftime('%d %b %Y')}\n\n"
    
    await update.message.reply_text(msg)
    await db.close()

# ============ PART 5 — OPTIONAL: PENALTY SETTINGS ============
# Is part se penalty ko easily control kar sakte ho.

# 🔧 PENALTY SETTINGS
PENALTY_ENABLED = True

# Minimum total wealth jiske neeche penalty nahi lagegi
MIN_WEALTH_FOR_PENALTY = 5_000

# Top kitne players ko daily penalty lagegi
PENALTY_TOP_PLAYERS = 10


# ============ GET PENALTY RATE ============
def get_penalty_rate(total_wealth):

    if total_wealth <= 100_000:
        return 0.001       # 0.1%

    elif total_wealth <= 500_000:
        return 0.002       # 0.2%

    elif total_wealth <= 1_000_000:
        return 0.003       # 0.3%

    elif total_wealth <= 2_500_000:
        return 0.005       # 0.5%

    else:
        return 0.01        # 1%


# ============ PENALTY PREVIEW ============
async def penalty_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not await is_registered(user_id):
        await update.message.reply_text(
            "❌ Send /start first!"
        )
        return

    db = await get_db()

    total_wealth = await db.fetchval("""
        SELECT
            u.balance + COALESCE(b.balance, 0)
        FROM users u
        LEFT JOIN bank b
            ON u.user_id = b.user_id
        WHERE u.user_id = $1
    """, user_id)

    if total_wealth is None:
        total_wealth = 0

    if total_wealth <= MIN_WEALTH_FOR_PENALTY:

        await db.close()

        await update.message.reply_text(
            "🛡️ *PENALTY PREVIEW*\n\n"
            f"🪙 Your Wealth: *{total_wealth:,}*\n"
            "💸 Possible Penalty: *0*\n\n"
            "✅ Your wealth is below the penalty limit.",
            parse_mode="Markdown"
        )
        return

    rate = get_penalty_rate(total_wealth)
    penalty = max(1, int(total_wealth * rate))

    await db.close()

    await update.message.reply_text(
        "⚠️ *PENALTY PREVIEW*\n\n"
        f"🪙 Total Wealth: *{total_wealth:,}*\n"
        f"📉 Penalty Rate: *{rate * 100:.1f}%*\n"
        f"💸 Possible Penalty: *-{penalty:,}*\n"
        f"🪙 After Penalty: *{total_wealth - penalty:,}*\n\n"
        "💡 Use /login daily to avoid the penalty.",
        parse_mode="Markdown"
    )


# ============ ADMIN: PENALTY STATUS ============
async def penalty_status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text(
            "❌ Admin only!"
        )
        return

    db = await get_db()

    today = datetime.now(IST).date()

    logged_count = await db.fetchval("""
        SELECT COUNT(*)
        FROM login_tracker
        WHERE last_login = $1
    """, today)

    penalty_count = await db.fetchval("""
        SELECT COUNT(*)
        FROM penalty_history
        WHERE penalty_date = $1
    """, today)

    penalty_total = await db.fetchval("""
        SELECT COALESCE(SUM(amount), 0)
        FROM penalty_history
        WHERE penalty_date = $1
    """, today)

    await db.close()

    await update.message.reply_text(
        "📊 *DAILY PENALTY STATUS*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 Date: *{today.strftime('%d %b %Y')}*\n"
        f"✅ Logged in: *{logged_count}*\n"
        f"💸 Penalized: *{penalty_count}*\n"
        f"🪙 Total Coins Removed: *{penalty_total:,}*\n\n"
        f"🔝 Penalty applies to Top *{PENALTY_TOP_PLAYERS}*\n"
        f"💰 Minimum Wealth: *{MIN_WEALTH_FOR_PENALTY:,}*",
        parse_mode="Markdown"
    ))



# ============ MAIN ==========
async def main():
    await init_db()

    # 🔥 START DAILY LOGIN + PENALTY SCHEDULER
    asyncio.create_task(schedule_penalty())
    print("✅ Daily login + penalty scheduler started!")

    app = Application.builder().token(TOKEN).build()

    # ============ USER COMMANDS ==========
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("refer", refer))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("setbio", setbio))
    app.add_handler(CommandHandler("rmbio", rmbio))
    app.add_handler(CommandHandler("setpfp", setpfp))
    app.add_handler(CommandHandler("rmpfp", rmpfp))
    app.add_handler(CommandHandler("claim", claim))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("flip", flip))
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("bet", bet))
    app.add_handler(CommandHandler("mybets", mybets))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("allbets", allbets))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("top_fantasy", top_fantasy))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(CommandHandler("fix_achievements", fix_achievements))
    app.add_handler(CommandHandler("achievements", achievements))
    app.add_handler(CommandHandler("numguess", numguess))
    app.add_handler(CommandHandler("ng", ng))
    app.add_handler(CommandHandler("ngstop", ngstop))
    app.add_handler(CommandHandler("tower", tower))
    app.add_handler(CallbackQueryHandler(tower_callback, pattern="^tower_"))
    app.add_handler(CommandHandler("fix_duplicates", fix_duplicates))
    app.add_handler(CommandHandler("ping", ping))

    # ============ PLAYER AUCTION ==========
    app.add_handler(CommandHandler("add_player", add_player))
    app.add_handler(CommandHandler("players", players))
    app.add_handler(CommandHandler("bid", bid))
    app.add_handler(CommandHandler("myteam", myteam))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("result_auction", result_auction))
    app.add_handler(CommandHandler("rmplayer", rmplayer))
    app.add_handler(CommandHandler("balance", balance))

    # ============ RPS GAME ==========
    app.add_handler(CommandHandler("rps", rps))
    app.add_handler(CallbackQueryHandler(rps_join_callback, pattern="^rps_join_"))
    app.add_handler(CallbackQueryHandler(rps_move_callback, pattern="^rps_move_"))
    app.add_handler(CallbackQueryHandler(rps_none_callback, pattern="^rps_none"))

    # ============ LOGIN / PENALTY ==========
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("login_log", login_log))
    app.add_handler(CommandHandler("penalty_history", penalty_history))
    app.add_handler(CommandHandler("penalty", penalty_preview))
    app.add_handler(CommandHandler("penaltystatus", penalty_status))

    # ============ HILO GAME ==========
    app.add_handler(CommandHandler("hilo", hilo))
    app.add_handler(CallbackQueryHandler(hilo_callback, pattern="^hilo_"))

    # ============ LOTTERY ==========
    app.add_handler(CommandHandler("lottery", lottery))
    app.add_handler(CommandHandler("buy_ticket", buy_ticket))
    app.add_handler(CommandHandler("mytickets", mytickets_command))
    app.add_handler(CommandHandler("lottery_info", lottery_info_command))
    app.add_handler(CommandHandler("start_lottery", start_lottery))
    app.add_handler(CommandHandler("draw_winner", draw_winner))
    app.add_handler(CommandHandler("reset_lottery", reset_lottery))
    app.add_handler(CommandHandler("lottery_coupon", lottery_coupon))
    app.add_handler(CommandHandler("claim_coupon", claim_coupon))

    # ============ NUMPUZ ==========
    app.add_handler(CommandHandler("numpuz", numpuz))
    app.add_handler(CallbackQueryHandler(numpuz_callback, pattern="^numpuz_"))

    # ============ HALL OF FAME ==========
    app.add_handler(CommandHandler("hof", hof))
    app.add_handler(CommandHandler("addhof", addhof))
    app.add_handler(CommandHandler("rmhof", rmhof))
    app.add_handler(CommandHandler("edithof", edithof))

    # ============ BANK ==========
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("claim_interest", claim_interest))

       # ============ ADMIN CRICKET ==========
    app.add_handler(CommandHandler("addmatch", addmatch))
    app.add_handler(CommandHandler("deletematch", deletematch))
    app.add_handler(CommandHandler("lockmatch", lockmatch))
    app.add_handler(CommandHandler("result", result))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("removew", removew))
    app.add_handler(CommandHandler("removeb", removeb))
    app.add_handler(CommandHandler("achieve", achieve))
    app.add_handler(CommandHandler("rmachieve", rmachieve))
    app.add_handler(CommandHandler("unlockmatch", unlockmatch))
    app.add_handler(CallbackQueryHandler(allbets_callback, pattern="^allbets_"))

    # ============ CLCRICKET ==========
    app.add_handler(CommandHandler("CLcricket", clcricket))
    app.add_handler(CallbackQueryHandler(cricket_mode_callback, pattern="^cricket_mode_"))
    app.add_handler(CallbackQueryHandler(cricket_join_callback, pattern="^cricket_join_"))
    app.add_handler(CallbackQueryHandler(cricket_toss_callback, pattern="^cricket_toss_"))
    app.add_handler(CallbackQueryHandler(cricket_choice_callback, pattern="^cricket_choice_"))
    app.add_handler(CallbackQueryHandler(cricket_bowl_callback, pattern="^cricket_bowl_"))
    app.add_handler(CallbackQueryHandler(cricket_bat_callback, pattern="^cricket_bat_"))

    # ============ MINES ==========
    app.add_handler(CommandHandler("mines", mines))
    app.add_handler(CallbackQueryHandler(mine_callback, pattern="^mine_"))
       # ============ CLAIM CODES ==========
    app.add_handler(CommandHandler("claimcode", claimcode))
    app.add_handler(CommandHandler("activecodes", activecodes))
    app.add_handler(CommandHandler("createcode", createcode))
    app.add_handler(CommandHandler("deletecode", deletecode))
    app.add_handler(CommandHandler("codestats", codestats))

    # ============ TIC TAC TOE ==========
    app.add_handler(CommandHandler("ttt", ttt))
    app.add_handler(CallbackQueryHandler(ttt_callback, pattern="^ttt_"))

    # ============ BROADCAST ==========
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("broadcast_stats", broadcast_stats))
    app.add_handler(CommandHandler("rain", rain))

        # ============ STATS ==========
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("mystats", mystats))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats_"))
    # ============ GROUP TRACKING ==========
    app.add_handler(MessageHandler(filters.ALL, track_all_activity), group=0)
    app.add_handler(MessageHandler(filters.ChatType.GROUP | filters.ChatType.SUPERGROUP, track_group))



    print("🤖 Bot is running...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


# ============ RUN ==========
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
