# ============ IMPORTS ============
from flask import Flask
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
TOKEN = os.environ.get("BOT_TOKEN", "8265192837:AAGwwBfePTiCN-AoFDxyg9mCG6A9kYWM8FY")
ADMIN_IDS = [7687078555, 1315564307]

# ============ DATABASE URL ============
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres.qvdodaowbwkdxvlsvyyo:aayush0806q@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres")

# ============ FLASK ============
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8081))  # ðŸ”¥ 8080 â†’ 8081
    flask_app.run(host="0.0.0.0", port=port)

# ============ GLOBAL CONNECTION POOL ============
db_pool = None

async def get_db():
    global db_pool
    if db_pool is None or db_pool._closed:
        db_pool = await asyncpg.create_pool(
            DATABASE_URL,
            statement_cache_size=0,
            min_size=1,
            max_size=5
        )
    return db_pool

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
    
    # Claim table
    await db.execute('''
        CREATE TABLE IF NOT EXISTS claim (
            user_id BIGINT PRIMARY KEY,
            last_claim DATE
        )
    ''')
    
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
            highest_score INT DEFAULT 0
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
    
    print("âœ… PostgreSQL tables created!")

# ============ HELPER FUNCTIONS ============
async def is_registered(user_id):
    db = await get_db()
    result = await db.fetchval("SELECT user_id FROM users WHERE user_id = $1", user_id)
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
    return user

async def update_balance(user_id, amount):
    db = await get_db()
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)

async def get_balance(user_id):
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    return balance if balance else 0

# ============ LOTTERY GLOBALS ==========
import string

lottery_active = False
lottery_tickets = {}
lottery_total_tickets = 0
lottery_participants = []
lottery_winner = None
lottery_start_time = None

def generate_ticket_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# ============ HILO GAME GLOBALS ==========
hilo_games = {}

CARD_VALUES = {
    'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 11, 'Q': 12, 'K': 13
}

SUITS = ['â™ ï¸', 'â™¥ï¸', 'â™£ï¸', 'â™¦ï¸']

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
        await update.message.reply_text('âŒ Send /start first!')
        return
    bot_username = context.bot.username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await update.message.reply_text(f"ðŸ‘¥ REFERRAL SYSTEM\n\nInvite friends and earn 1,000 credits each!\n\nYour Link: {ref_link}\n\nNew users get +500 bonus!")

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
                        await context.bot.send_message(referred_by, f"ðŸŽ‰ REFERRAL REWARD!\n\n@{name} joined using your link!\nðŸ’° +1,000 credits!")
                    except:
                        pass
                    await update.message.reply_text("ðŸŽ‰ WELCOME!\n\nYou joined with a referral!\nðŸ’° +500 bonus credits!")
        
        keyboard = [
            [InlineKeyboardButton("ðŸ“¢ UPDATES", url="https://t.me/clbotofficial")],
            [InlineKeyboardButton("ðŸ‘¥ MAIN GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"âœ¨ WELCOME TO CL ZONE âœ¨\n\n"
            f"ðŸ‘‘ {name}, you've joined the elite club!\n"
            f"ðŸ’° 1000 credits | ðŸ† 0 pts\n\n"
            f"ðŸŽ¯ /claim - Daily rewards\n"
            f"ðŸŽ¡ /spin - Daily spin\n"
            f"ðŸ‘¤ /profile - Your stats\n"
            f"ðŸ† /leaderboard - Top players\n\n"
            f"ðŸ“Œ Join our channels for exclusive updates!",
            reply_markup=reply_markup
        )
    else:
        keyboard = [
            [InlineKeyboardButton("ðŸ“¢ UPDATES", url="https://t.me/clbotofficial")],
            [InlineKeyboardButton("ðŸ‘¥ MAIN GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"âœ¨ WELCOME BACK TO CL ZONE âœ¨\n\n"
            f"ðŸ‘‘ {name}\n"
            f"ðŸ’° {existing['balance']:,} credits | ðŸ† {existing['points']} pts\n\n"
            f"ðŸŽ¯ /claim - Daily rewards\n"
            f"ðŸŽ¡ /spin - Daily spin\n"
            f"ðŸ‘¤ /profile - Your stats\n"
            f"ðŸ† /leaderboard - Top players\n\n"
            f"ðŸ“Œ Stay connected with our community!",
            reply_markup=reply_markup
        )
    

# ============ SETPRICE COMMAND (ADMIN) ==========
async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('âŒ /setprice <player_id> <new_price>')
        return
    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('âŒ Invalid input!')
        return
    db = await get_db()
    player = await db.fetchrow("SELECT name FROM shop WHERE id = $1", player_id)
    if not player:
        await update.message.reply_text(f'âŒ Player ID {player_id} not found!')
        return
    await db.execute("UPDATE shop SET price = $1 WHERE id = $2", new_price, player_id)
    await update.message.reply_text(f"âœ… PRICE UPDATED!\n\n{player['name']}\nðŸ’° New Price: {new_price:,} ðŸ’°")


# ============ PROFILE ==========
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text("âŒ Send /start first!")
        return
    user = update.effective_user
    name = user.first_name if user.first_name else (user.username or "User")
    db = await get_db()
    data = await db.fetchrow("SELECT balance, points, won, total, photo, bio FROM users WHERE user_id = $1", user_id)
    if not data:
        await update.message.reply_text("âŒ Profile not found!")
        return
    bank_bal = await db.fetchval("SELECT balance FROM bank WHERE user_id = $1", user_id) or 0
    wallet_bal, points, won, total, photo, bio = data
    total_wealth = wallet_bal + bank_bal
    win_rate = int((won / total) * 100) if total > 0 else 0
    profile_text = f"ðŸ‘¤ PROFILE\n\nName: {name}\n"
    if bio:
        profile_text += f"Bio: {bio}\n\n"
    profile_text += f"ðŸ’° Wallet: {wallet_bal:,}\nðŸ¦ Bank: {bank_bal:,}\nðŸ’Ž Total: {total_wealth:,}\n\nðŸ† Points: {points}\nðŸ“Š Bets: {won}/{total}\nðŸ“ˆ Win Rate: {win_rate}%"
    if photo:
        await update.message.reply_photo(photo=photo, caption=profile_text)
    else:
        await update.message.reply_text(profile_text)

# ============ BIO & PFP ==========
async def setbio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /setbio <your bio>")
        return
    bio = " ".join(args)
    if len(bio) > 100:
        await update.message.reply_text("âŒ Bio too long!")
        return
    db = await get_db()
    await db.execute("UPDATE users SET bio = $1 WHERE user_id = $2", bio, user_id)
    await update.message.reply_text(f"âœ… Bio updated!\n\n{bio}")

async def rmbio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    await db.execute("UPDATE users SET bio = NULL WHERE user_id = $1", user_id)
    await update.message.reply_text("âœ… Bio removed!")

async def setpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    if not update.message.reply_to_message:
        await update.message.reply_text('âŒ Reply to a photo with /setpfp')
        return
    if not update.message.reply_to_message.photo:
        await update.message.reply_text('âŒ Reply to a PHOTO with /setpfp')
        return
    photo = update.message.reply_to_message.photo[-1].file_id
    db = await get_db()
    await db.execute("UPDATE users SET photo = $1 WHERE user_id = $2", photo, user_id)
    await update.message.reply_text('âœ… Profile photo updated!')

async def rmpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    await db.execute("UPDATE users SET photo = NULL WHERE user_id = $1", user_id)
    await update.message.reply_text('âŒ Profile photo removed!')

# ============ CLAIM ==========
# ============ CLAIM ==========
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    chat_type = update.message.chat.type

    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return

    CL_GROUP_ID = -1001661258033

    db = await get_db()
    
    last = await db.fetchval("SELECT last_claim FROM claim WHERE user_id = $1", user_id)

    today = datetime.now().date()
    today_str = today.strftime("%m/%d/%y")

    if last:
        if last == today:
            await update.message.reply_text("âš ï¸ Already claimed today!\nCome back tomorrow.")
            return

    if chat_type in ['group', 'supergroup'] and chat_id == CL_GROUP_ID:
        reward = 1000
        extra_note = "\n\nâœ¨ BONUS: You get 1000 credits in CL Zone Group!"
    else:
        reward = 500
        extra_note = f"\n\nðŸ’¡ Tip: Use /claim in CL Zone Group to get 1000 credits!"

    await db.execute("INSERT INTO claim (user_id, last_claim) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET last_claim = $2", user_id, today)
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", reward, user_id)
    
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)

    await update.message.reply_text(
        f"âœ… Claimed Daily Rewards!\n\nðŸ’° +{reward} credits\nðŸ“… {today_str}\nðŸ’³ New balance: {new_bal:,}{extra_note}\n\nðŸ”„ Next claim: tomorrow",
        disable_web_page_preview=True
    )

# ============ ACHIEVE COMMAND (ADMIN) ==========
async def achieve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    if not update.message.reply_to_message:
        await update.message.reply_text('âŒ Reply to user with /achieve ACHIEVEMENT_NAME')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /achieve ACHIEVEMENT_NAME')
        return
    achievement = ' '.join(args)
    target = update.message.reply_to_message.from_user
    db = await get_db()
    await db.execute("INSERT INTO achievements (user_id, achievement) VALUES ($1, $2)", target.id, achievement)
    await update.message.reply_text(f"âœ… ACHIEVEMENT GIVEN!\n\nUser: {target.first_name}\nAchievement: {achievement} ðŸ†")

# ============ RMACHIEVE COMMAND (ADMIN) ==========
async def rmachieve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /rmachieve <number>')
        return
    try:
        num = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid number')
        return
    target_id = update.effective_user.id
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    db = await get_db()
    achievements = await db.fetch("SELECT row_number() OVER () as rowid, achievement FROM achievements WHERE user_id = $1", target_id)
    if num < 1 or num > len(achievements):
        await update.message.reply_text(f'âŒ Choose 1-{len(achievements)}')
        return
    removed = achievements[num-1]
    await db.execute("DELETE FROM achievements WHERE user_id = $1 AND achievement = $2", target_id, removed['achievement'])
    await update.message.reply_text(f"âœ… ACHIEVEMENT REMOVED!\n\nRemoved: {removed['achievement']} ðŸ†")

# ============ UNLOCKMATCH COMMAND (ADMIN) ==========
async def unlockmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('âŒ /unlockmatch TEAM1 vs TEAM2')
        return
    team1 = args[0].upper()
    team2 = args[2].upper()
    db = await get_db()
    match = await db.fetchrow("SELECT id, team1, team2, locked FROM matches WHERE team1 = $1 AND team2 = $2", team1, team2)
    if not match:
        await update.message.reply_text(f'âŒ Match not found!')
        return
    if match['locked'] == 0:
        await update.message.reply_text(f'âš ï¸ Match is already UNLOCKED!')
        return
    await db.execute("UPDATE matches SET locked = 0 WHERE id = $1", match['id'])
    total = await db.fetchval("SELECT COALESCE(SUM(amount), 0) FROM bets WHERE match_id = $1", match['id'])
    count = await db.fetchval("SELECT COUNT(*) FROM bets WHERE match_id = $1", match['id'])
    await update.message.reply_text(f"ðŸ”“ MATCH UNLOCKED!\n\nðŸ {match['team1']} vs {match['team2']}\nðŸ“Š Current Bets: {count}\nðŸ’° Current Pool: {total:,} ðŸ’°")

# ============ CODELER COMMANDS (ADMIN) ==========
async def deletecode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("âŒ Usage: /deletecode CODE123")
        return
    code = args[0].upper()
    db = await get_db()
    exists = await db.fetchval("SELECT code FROM claim_codes WHERE code = $1", code)
    if not exists:
        await update.message.reply_text(f"âŒ Code '{code}' not found!")
        return
    await db.execute("DELETE FROM claim_codes WHERE code = $1", code)
    await db.execute("DELETE FROM code_claims WHERE code = $1", code)
    await update.message.reply_text(f"âœ… Code '{code}' deleted!")

async def codestats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    db = await get_db()
    total_codes = await db.fetchval("SELECT COUNT(*) FROM claim_codes")
    active_codes = await db.fetchval("SELECT COUNT(*) FROM claim_codes WHERE expires_at::timestamp > now() AND claimed_count < max_claims")
    total_claims = await db.fetchval("SELECT COUNT(*) FROM code_claims")
    total_given = await db.fetchval("SELECT COALESCE(SUM(amount), 0) FROM code_claims cc JOIN claim_codes c ON cc.code = c.code")
    unique_users = await db.fetchval("SELECT COUNT(DISTINCT user_id) FROM code_claims")
    await update.message.reply_text(f"ðŸ“Š CODE STATS\n\nðŸ“ Total codes: {total_codes}\nðŸŸ¢ Active codes: {active_codes}\nðŸŽ¯ Total claims: {total_claims}\nðŸ’° Credits given: {total_given:,}\nðŸ‘¥ Unique users: {unique_users}")


# ============ SPIN ==========
async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    last = await db.fetchval("SELECT last_claim FROM spin WHERE user_id = $1", user_id)
    
    now = datetime.now()
    today_str = now.strftime("%m/%d/%y")
    
    if last:
        last_date = datetime.fromisoformat(last)
        if last_date.date() == now.date():
            await update.message.reply_text(f"âš ï¸ Already spin today!\nat {last_date.strftime('%m/%d/%y')}\n\nðŸŽ¡ Next spin: tomorrow")
            return
    
    amount = random.randint(1000, 10000)
    await db.execute("INSERT INTO spin (user_id, last_claim) VALUES ($1, $2) ON CONFLICT (user_id) DO UPDATE SET last_claim = $2", user_id, now.isoformat())
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)
    
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    await update.message.reply_text(f"âœ… Claimed Daily Spin Rewards of {amount:,} Credits\nat {today_str}\n\nðŸ’° New balance: {new_bal:,} ðŸ’°\nðŸŽ¡ Next spin: tomorrow")

# ============ DICE ==========
async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('ðŸŽ² /dice <amount>\nMultipliers: 1(0x) 2(0.25x) 3(0.5x) 4(1.25x) 5(1.5x) 6(2.5x)')
        return
    
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('âŒ Minimum 100 credits')
        return
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < amount:
        await update.message.reply_text(f'âŒ Need {amount:,}, have {balance:,}')
        return
    
    roll = random.randint(1, 6)
    dice_emoji = {1:'âš€', 2:'âš', 3:'âš‚', 4:'âšƒ', 5:'âš„', 6:'âš…'}
    multi = {1:0, 2:0.25, 3:0.5, 4:1.25, 5:1.5, 6:2.5}
    win = int(amount * multi[roll])
    new_bal = balance - amount + win
    await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_bal, user_id)
    
    if win > 0:
        await update.message.reply_text(f"ðŸŽ² DICE\n\nðŸŽ² Rolled: {roll} {dice_emoji[roll]}\nâœ¨ You won {win:,} ðŸ’° ({multi[roll]}x)\nðŸ’° New balance: {new_bal:,} ðŸ’°")
    else:
        await update.message.reply_text(f"ðŸŽ² DICE\n\nðŸŽ² Rolled: {roll} {dice_emoji[roll]}\nðŸ’€ You lost {amount:,} ðŸ’°\nðŸ’° New balance: {new_bal:,} ðŸ’°")

# ============ FLIP ==========
async def flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('ðŸª™ /flip heads/tails <amount>\nExample: /flip heads 1000')
        return
    
    choice = args[0].lower()
    if choice not in ['heads', 'tails']:
        await update.message.reply_text('âŒ Choose heads or tails')
        return
    
    try:
        amount = int(args[1])
    except:
        await update.message.reply_text('âŒ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('âŒ Minimum 100 credits')
        return
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < amount:
        await update.message.reply_text(f'âŒ Need {amount:,}, have {balance:,}')
        return
    
    result = random.choice(['heads', 'tails'])
    if choice == result:
        win = amount * 2
        new_bal = balance - amount + win
        await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_bal, user_id)
        await update.message.reply_text(f"ðŸª™ {result.upper()}! You won {win:,} ðŸ’°\nðŸ’° New balance: {new_bal:,} ðŸ’°")
    else:
        new_bal = balance - amount
        await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_bal, user_id)
        await update.message.reply_text(f"ðŸ˜ž {result.upper()}! You lost {amount:,} ðŸ’°\nðŸ’° New balance: {new_bal:,} ðŸ’°")

# ============ HELP COMMAND ==========
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    msg = (
        "ðŸ“‹ CL ZONE - COMMAND LIST\n\n"
        
        "ðŸ‘¤ PROFILE\n"
        "â€¢ /start - Start bot\n"
        "â€¢ /profile - Your stats & collection\n"
        "â€¢ /leaderboard - Top 10 Richest users\n"
        "â€¢ /setbio <text> - Set bio\n"
        "â€¢ /rmbio - Remove bio\n"
        "â€¢ /setpfp - Set photo (reply to pic)\n"
        "â€¢ /rmpfp - Remove photo\n\n"
        
        "ðŸ’° EARN CREDITS\n"
        "â€¢ /claim - 500 daily\n"
        "â€¢ /spin - 1,000-10,000 daily\n"
        "â€¢ /dice <amount> - 0x to 2.5x\n"
        "â€¢ /flip heads/tails <amount> - 2x\n"
        "â€¢ /tip <amount> (reply) - Send credits\n\n"
        
        "ðŸ CRICKET BETTING\n"
        "â€¢ /matches - Live matches\n"
        "â€¢ /bet <team> <amount> - Place bet\n"
        "â€¢ /mybets - Your bets\n"
        "â€¢ /cancel <number> - Cancel bet\n"
        "â€¢ /allbets - All bets\n"
        "â€¢ /history - Win/loss record\n"
        "â€¢ /top_fantasy - Fantasy points ranking\n\n"
        
        "ðŸ† ACHIEVEMENTS\n"
        "â€¢ /achievements - Your badges\n\n"
        
        "ðŸ›’ SHOP\n"
        "â€¢ /shop - Buy players\n"
        "â€¢ /buy <id> - Purchase mens player\n"
        "â€¢ /buyw <id> - Purchase women player\n"
        "â€¢ /myteam - Your collection\n"
        "â€¢ /top - Top collectors\n\n"
        
        "ðŸ›ï¸ AFFORDABLE STORE\n"
        "â€¢ /shop2 - Budget players\n"
        "â€¢ /buy2 <id> - Purchase\n"
        "â€¢ /myteam2 - Your collection\n"
        "â€¢ /top2 - Top collectors\n\n"
        
        "ðŸ›’ TG PLAYERS\n"
        "â€¢ /shop3 - Telegram players\n"
        "â€¢ /buy3 <id> - Purchase\n"
        "â€¢ /myteam3 - Your collection\n"
        "â€¢ /top3 - Top collectors\n\n"
        
        "ðŸ¦ BANK\n"
        "â€¢ /bank - Check balance\n"
        "â€¢ /deposit <amount> - Add to bank\n"
        "â€¢ /withdraw <amount> - Take from bank\n"
        "â€¢ /claim_interest - 5% daily\n\n"
        
        "ðŸŽ° LOTTERY\n"
        "â€¢ /lottery - Lottery menu\n"
        "â€¢ /buy_ticket <qty> - Buy tickets (20k each)\n"
        "â€¢ /mytickets - Your tickets\n"
        "â€¢ /lottery_info - Lottery stats\n"
        "â€¢ /claim_coupon <code> - Claim free tickets\n\n"
        
        "ðŸŽ® GAMES\n"
        "â€¢ /hilo <bet> - HiLo card game (100-10k bet)\n"
        "â€¢ /ttt [amount] - Tic Tac Toe\n"
        "â€¢ /mines <amount> <bombs> - Mines game\n"
        "â€¢ /CLcricket [amount] - Cricket game\n"
        "â€¢ /rps [amount] - Rock Paper Scissors\n"
        "â€¢ /numguess - Number guessing game\n"
        "â€¢ /ng <number> - Make a guess\n"
        "â€¢ /claimcode <code> - Claim rewards\n"
        "â€¢ /activecodes - Active codes\n"
        "â€¢ /numpuz - Number puzzle\n\n"
        
        "ðŸŽ REFERRAL\n"
        "â€¢ /refer - Get your link (1k per refer)\n\n"
        
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
        "ðŸ’¡ Need help? @clbothelp"
    )
    
    await update.message.reply_text(msg)

# ============ LEADERBOARD ==========
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    users_data = await db.fetch("""
        SELECT u.name, u.balance + COALESCE(b.balance, 0) as total_wealth
        FROM users u LEFT JOIN bank b ON u.user_id = b.user_id
        ORDER BY total_wealth DESC LIMIT 10
    """)
    
    msg = "ðŸ† TOP 10 RICHEST (Wallet + Bank)\n\n"
    for i, u in enumerate(users_data, 1):
        medal = "ðŸ‘‘" if i==1 else "ðŸ¥ˆ" if i==2 else "ðŸ¥‰" if i==3 else f"{i}."
        msg += f"{medal} {u['name']} - {u['total_wealth']:,} ðŸ’°\n"
    
    user_total = await db.fetchval("""
        SELECT u.balance + COALESCE(b.balance, 0) FROM users u
        LEFT JOIN bank b ON u.user_id = b.user_id WHERE u.user_id = $1
    """, user_id)
    
    rank = await db.fetchval("""
        SELECT COUNT(*) + 1 FROM (
            SELECT u.balance + COALESCE(b.balance, 0) as total
            FROM users u LEFT JOIN bank b ON u.user_id = b.user_id
        ) t WHERE total > $1
    """, user_total)
    
    msg += f"\n---------------------\nYour rank: #{rank}\nTotal wealth: {(user_total or 0):,}"
    await update.message.reply_text(msg)

# ============ TOP FANTASY ==========
async def top_fantasy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    users_data = await db.fetch("SELECT name, points FROM users ORDER BY points DESC LIMIT 20")
    
    if not users_data:
        await update.message.reply_text('ðŸ“­ No fantasy points yet!')
        return
    
    msg = "ðŸ† FANTASY LEADERBOARD\n\n"
    for i, u in enumerate(users_data, 1):
        msg += f"{i}. {u['name']} - {u['points']} pts\n"
    
    user = await get_user(user_id)
    rank = await db.fetchval("SELECT COUNT(*) FROM users WHERE points > $1", user['points']) + 1
    msg += f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ“Š Your points: {user['points']} | Rank: #{rank}"
    await update.message.reply_text(msg)

# ============ TIP ==========
async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text('âŒ Reply to user with /tip AMOUNT')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /tip AMOUNT\nExample: /tip 500')
        return
    
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid amount')
        return
    
    sender = update.effective_user
    receiver = update.message.reply_to_message.from_user
    
    if sender.id == receiver.id:
        await update.message.reply_text('âŒ Cannot tip yourself!')
        return
    
    db = await get_db()
    sender_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", sender.id)
    
    if sender_bal is None:
        await update.message.reply_text("Send /start first!")
        return
    
    if sender_bal < amount:
        await update.message.reply_text(f"Need {amount:,}, have {sender_bal:,}")
        return
    
    # Check receiver is registered - do not lose credits to unregistered users
    receiver_exists = await db.fetchval("SELECT user_id FROM users WHERE user_id = $1", receiver.id)
    if not receiver_exists:
        await update.message.reply_text("That user has not registered yet! They must send /start to the bot first.")
        return
    
    # Use transaction to prevent race conditions
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", amount, sender.id)
            await conn.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, receiver.id)
    
    await update.message.reply_text(f"TIP SENT!\n\nTo: {receiver.first_name}\nAmount: {amount:,}\nYour balance: {sender_bal - amount:,}")

# ============ ACHIEVEMENTS ==========
async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    ach = await db.fetch("SELECT achievement FROM achievements WHERE user_id = $1", user_id)
    
    if not ach:
        await update.message.reply_text('ðŸ† MY ACHIEVEMENTS\n\nNo achievements yet!')
        return
    
    msg = "ðŸ† MY ACHIEVEMENTS\n\n"
    for i, a in enumerate(ach, 1):
        msg += f"{i}. {a['achievement']} ðŸ†\n"
    msg += f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nTotal: {len(ach)} achievements"
    await update.message.reply_text(msg)

# ============ SHOP ==========
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    keyboard = [
        [InlineKeyboardButton("ðŸ‡®ðŸ‡³ India", callback_data="shop_India")],
        [InlineKeyboardButton("ðŸ´ó §ó ¢ó ¥ó ®ó §ó ¿ England", callback_data="shop_England")],
        [InlineKeyboardButton("ðŸ‡¦ðŸ‡º Australia", callback_data="shop_Australia")],
        [InlineKeyboardButton("ðŸ‡³ðŸ‡¿ New Zealand", callback_data="shop_New Zealand")],
        [InlineKeyboardButton("ðŸ‘© Women Players", callback_data="shop_women")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("ðŸ›’ CRICKETER SHOP\n\nSelect country:", reply_markup=reply_markup)

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "shop_women":
        db = await get_db()
        players = await db.fetch("SELECT id, name, price FROM shop_women ORDER BY id")

        if not players:
            await query.edit_message_text("ðŸ‘© WOMEN CRICKETERS\n\nNo players yet!")
            return

        msg = "ðŸ‘© WOMEN CRICKETERS\n\n"
        for p in players:
            msg += f"{p['id']}. {p['name']} - {p['price']:,} ðŸ’°\n"
        msg += f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’¡ /buyw <number> to purchase"
        await query.edit_message_text(msg)
        return

    parts = data.split('_')
    if len(parts) < 2:
        await query.edit_message_text("âŒ Invalid selection")
        return

    country = parts[1]
    if len(parts) > 2:
        country = parts[1] + " " + parts[2]

    db = await get_db()
    players = await db.fetch("SELECT id, name, price, type FROM shop WHERE category = $1", country)

    if not players:
        await query.edit_message_text(f"âŒ No players found for {country}")
        return

    current_players = [p for p in players if p['type'] == 'current']
    legend_players = [p for p in players if p['type'] == 'legend']
    
    msg = f"ðŸ›’ {country} PLAYERS\n\n"
    
    if current_players:
        msg += f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ”µ CURRENT PLAYERS ({len(current_players)}):\n"
        for p in current_players:
            msg += f"{p['id']}. {p['name']} - {p['price']:,} ðŸ’°\n"
    
    if legend_players:
        msg += f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸŒŸ LEGENDS ({len(legend_players)}):\n"
        for p in legend_players:
            msg += f"{p['id']}. {p['name']} - {p['price']:,} ðŸ’°\n"
    
    msg += f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’¡ /buy <number> to purchase"
    await query.edit_message_text(msg)

# ============ BUY MENS ==========
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /buy <player_id>\nExample: /buy 1')
        return
    
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid ID')
        return
    
    db = await get_db()
    player = await db.fetchrow("SELECT name, price FROM shop WHERE id = $1", player_id)
    
    if not player:
        await update.message.reply_text(f'âŒ Player ID {player_id} not found!')
        return
    
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < player['price']:
        await update.message.reply_text(f'âŒ Need {player["price"]:,}, have {balance:,}')
        return
    
    owned = await db.fetchval("SELECT user_id FROM user_players WHERE user_id = $1 AND player_id = $2 AND type = 'mens'", user_id, player_id)
    if owned:
        await update.message.reply_text(f'âŒ You already own {player["name"]}!')
        return
    
    
    # Use transaction to prevent double-spend race condition
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            # Re-check balance inside transaction
            current_bal = await conn.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
            if current_bal < player['price']:
                await update.message.reply_text("Insufficient balance!")
                return
            already_owned = await conn.fetchval("SELECT user_id FROM user_players WHERE user_id = $1 AND player_id = $2 AND type = 'mens'", user_id, player_id)
            if already_owned:
                await update.message.reply_text("You already own this player!")
                return
            await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", player['price'], user_id)
            await conn.execute("INSERT INTO user_players (user_id, player_id, type) VALUES ($1, $2, 'mens')", user_id, player_id)
    
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    await update.message.reply_text(f"âœ… PURCHASED!\n\nðŸ {player['name']}\nðŸ’° Price: {player['price']:,} ðŸ’°\nðŸ“Š New balance: {new_bal:,} ðŸ’°")

# ============ BUY WOMEN ==========
async def buyw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /buyw <player_id>\nExample: /buyw 1')
        return
    
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid ID')
        return
    
    db = await get_db()
    player = await db.fetchrow("SELECT name, price FROM shop_women WHERE id = $1", player_id)
    
    if not player:
        await update.message.reply_text(f'âŒ Player ID {player_id} not found!')
        return
    
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < player['price']:
        await update.message.reply_text(f'âŒ Need {player["price"]:,}, have {balance:,}')
        return
    
    owned = await db.fetchval("SELECT user_id FROM user_players WHERE user_id = $1 AND player_id = $2 AND type = 'women'", user_id, player_id)
    if owned:
        await update.message.reply_text(f'âŒ You already own {player["name"]}!')
        return
    
    
    # Atomic transaction to prevent double-spend
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            cur_bal = await conn.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
            if cur_bal < player['price']:
                await update.message.reply_text("Insufficient balance!")
                return
            already = await conn.fetchval("SELECT user_id FROM user_players WHERE user_id = $1 AND player_id = $2 AND type = 'women'", user_id, player_id)
            if already:
                await update.message.reply_text("You already own this player!")
                return
            await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", player['price'], user_id)
            await conn.execute("INSERT INTO user_players (user_id, player_id, type) VALUES ($1, $2, 'women')", user_id, player_id)
    
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    await update.message.reply_text(f"âœ… PURCHASED!\n\nðŸ‘© {player['name']}\nðŸ’° Price: {player['price']:,} ðŸ’°\nðŸ“Š New balance: {new_bal:,} ðŸ’°")

# ============ MY TEAM ==========
async def myteam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    
    mens = await db.fetch("""
        SELECT p.name, p.price FROM user_players u JOIN shop p ON u.player_id = p.id 
        WHERE u.user_id = $1 AND u.type = 'mens'
    """, user_id)
    
    women = await db.fetch("""
        SELECT w.name, w.price FROM user_players u JOIN shop_women w ON u.player_id = w.id 
        WHERE u.user_id = $1 AND u.type = 'women'
    """, user_id)
    
    affordable = await db.fetch("""
        SELECT s.name, s.price FROM user_players2 u JOIN shop2 s ON u.player_id = s.id 
        WHERE u.user_id = $1
    """, user_id)
    
    shop3 = await db.fetch("""
        SELECT s.name, s.price FROM user_players3 u JOIN shop3 s ON u.player_id = s.id 
        WHERE u.user_id = $1
    """, user_id)
    
    
    mens_total = sum(p['price'] for p in mens)
    women_total = sum(w['price'] for w in women)
    affordable_total = sum(a['price'] for a in affordable)
    shop3_total = sum(s['price'] for s in shop3)
    
    msg = "ðŸ MY CRICKET TEAM\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ‘¨ MENS"
    if mens:
        msg += f" ({len(mens)})\n\n"
        for i, p in enumerate(mens, 1):
            msg += f"{i}. {p['name']} - {p['price']:,} ðŸ’°\n"
        msg += f"\nTotal: {mens_total:,} ðŸ’°"
    else:
        msg += "\n\nNo mens players. /shop to buy!"
    
    msg += "\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ›ï¸ AFFORDABLE"
    if affordable:
        msg += f" ({len(affordable)})\n\n"
        for i, a in enumerate(affordable, 1):
            msg += f"{i}. {a['name']} - {a['price']:,} ðŸ’°\n"
        msg += f"\nTotal: {affordable_total:,} ðŸ’°"
    else:
        msg += "\n\nNo affordable players. /shop2 to buy!"
    
    msg += "\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’Ž SHOP3"
    if shop3:
        msg += f" ({len(shop3)})\n\n"
        for i, s in enumerate(shop3, 1):
            msg += f"{i}. {s['name']} - {s['price']:,} ðŸ’°\n"
        msg += f"\nTotal: {shop3_total:,} ðŸ’°"
    else:
        msg += "\n\nNo shop3 players. /shop3 to buy!"
    
    msg += "\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ‘© WOMEN"
    if women:
        msg += f" ({len(women)})\n\n"
        for i, w in enumerate(women, 1):
            msg += f"{i}. {w['name']} - {w['price']:,} ðŸ’°\n"
        msg += f"\nTotal: {women_total:,} ðŸ’°"
    else:
        msg += "\n\nNo women players. /shop women section"
    
    grand_total = mens_total + affordable_total + shop3_total + women_total
    total_players = len(mens) + len(affordable) + len(shop3) + len(women)
    msg += f"\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’° GRAND TOTAL: {grand_total:,} ðŸ’°\nðŸ† TOTAL PLAYERS: {total_players}"
    
    await update.message.reply_text(msg)

# ============ TOP COLLECTORS ==========
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    tops = await db.fetch("""
        SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(p.price), 0) as total 
        FROM users u JOIN user_players up ON u.user_id = up.user_id 
        JOIN shop p ON up.player_id = p.id WHERE up.type = 'mens' 
        GROUP BY u.user_id ORDER BY total DESC LIMIT 10
    """)
    
    if not tops:
        await update.message.reply_text('ðŸ† TOP COLLECTORS\n\nNo one owns any players yet!')
        return
    
    msg = "ðŸ† TOP COLLECTORS\n\n"
    for i, t in enumerate(tops, 1):
        medal = "ðŸ‘‘" if i==1 else "ðŸ¥ˆ" if i==2 else "ðŸ¥‰" if i==3 else f"{i}."
        msg += f"{medal} {t['name']} - {t['count']} players ({t['total']:,} ðŸ’°)\n"
    
    user_data = await db.fetchrow("""
        SELECT COUNT(up.player_id) as count, COALESCE(SUM(p.price), 0) as total 
        FROM user_players up JOIN shop p ON up.player_id = p.id 
        WHERE up.user_id = $1 AND up.type = 'mens'
    """, user_id)
    player_count = user_data['count'] if user_data else 0
    total_value = user_data['total'] if user_data else 0
    
    
    msg += f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ“Š Your rank: N/A\nðŸ’° Collection value: {total_value:,} ðŸ’°\nðŸ† Players: {player_count}"
    await update.message.reply_text(msg)

# ============ BANK SYSTEM ==========
async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
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
    
    
    await update.message.reply_text(f"ðŸ¦ MY BANK ACCOUNT\n\nðŸ’° Bank Balance: {bank_bal:,} ðŸ’°\nðŸ‘› Wallet Balance: {wallet_bal:,} ðŸ’°\nðŸ“ˆ Interest Rate: 5% daily\nâ° Next interest: {next_time_str}\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’¡ /deposit <amount>\nðŸ’¡ /withdraw <amount>\nðŸ’¡ /claim_interest")

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /deposit <amount>\nExample: /deposit 5000')
        return
    
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('âŒ Minimum deposit is 100 credits')
        return
    
    db = await get_db()
    await db.execute("INSERT INTO bank (user_id, balance, last_interest) VALUES ($1, 0, $2) ON CONFLICT (user_id) DO NOTHING", user_id, datetime.now().isoformat())
    
    wallet_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if wallet_bal < amount:
        await update.message.reply_text(f'âŒ Insufficient wallet balance!\n\nNeed: {amount:,} ðŸ’°\nHave: {wallet_bal:,} ðŸ’°')
        return
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", amount, user_id)
    await db.execute("UPDATE bank SET balance = balance + $1 WHERE user_id = $2", amount, user_id)
    
    new_wallet = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    new_bank = await db.fetchval("SELECT balance FROM bank WHERE user_id = $1", user_id)
    
    await update.message.reply_text(f"âœ… DEPOSITED!\n\nAmount: +{amount:,} ðŸ’°\nWallet: {wallet_bal:,} â†’ {new_wallet:,} ðŸ’°\nBank: {new_bank - amount:,} â†’ {new_bank:,} ðŸ’°")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /withdraw <amount>\nExample: /withdraw 5000')
        return
    
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('âŒ Minimum withdrawal is 100 credits')
        return
    
    db = await get_db()
    await db.execute("INSERT INTO bank (user_id, balance, last_interest) VALUES ($1, 0, $2) ON CONFLICT (user_id) DO NOTHING", user_id, datetime.now().isoformat())
    
    bank_bal = await db.fetchval("SELECT balance FROM bank WHERE user_id = $1", user_id)
    
    if bank_bal < amount:
        await update.message.reply_text(f'âŒ Insufficient bank balance!\n\nNeed: {amount:,} ðŸ’°\nHave: {bank_bal:,} ðŸ’°')
        return
    
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)
    await db.execute("UPDATE bank SET balance = balance - $1 WHERE user_id = $2", amount, user_id)
    
    new_bank = await db.fetchval("SELECT balance FROM bank WHERE user_id = $1", user_id)
    new_wallet = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    await update.message.reply_text(f"âœ… WITHDRAWN!\n\nAmount: -{amount:,} ðŸ’°\nBank: {bank_bal:,} â†’ {new_bank:,} ðŸ’°\nWallet: {new_wallet - amount:,} â†’ {new_wallet:,} ðŸ’°")

async def claim_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    await db.execute("INSERT INTO bank (user_id, balance, last_interest) VALUES ($1, 0, $2) ON CONFLICT (user_id) DO NOTHING", user_id, datetime.now().isoformat())
    
    row = await db.fetchrow("SELECT balance, last_interest FROM bank WHERE user_id = $1", user_id)
    if not row:
        await update.message.reply_text('âŒ No bank account found! Use /bank first.')
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
            await update.message.reply_text(f"â° Interest not ready yet!\n\nCome back in {hours}h {mins}m")
            return
    
    interest = int(bank_bal * 0.05)
    new_bank = bank_bal + interest
    await db.execute("UPDATE bank SET balance = $1, last_interest = $2 WHERE user_id = $3", new_bank, now.isoformat(), user_id)
    
    await update.message.reply_text(f"ðŸ’° INTEREST CLAIMED!\n\nRate: 5%\nInterest: +{interest:,} ðŸ’°\nNew Bank Balance: {new_bank:,} ðŸ’°\n\nâ° Next interest: 24h")

# ============ LOTTERY SYSTEM ==========
async def lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    user_tickets = lottery_tickets.get(user_id, [])
    status_text = "ACTIVE" if lottery_active else "NOT ACTIVE"
    
    msg = f"ðŸŽ° LOTTERY SYSTEM\n\n"
    msg += f"ðŸ’° Balance: {balance:,}\n"
    msg += f"ðŸŽ« Your tickets: {len(user_tickets)}\n"
    msg += f"ðŸ“Š Status: {status_text}\n\n"
    msg += f"ðŸŽŸï¸ Ticket price: 20,000 credits\n"
    msg += f"ðŸ† Winner gets: ALL ticket money\n\n"
    msg += f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
    msg += f"ðŸ“Œ COMMANDS:\n"
    msg += f"/buy_ticket <qty> - Buy tickets\n"
    msg += f"/mytickets - Your tickets\n"
    msg += f"/lottery_info - Lottery stats"
    
    await update.message.reply_text(msg)

async def buy_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("âŒ Usage: /buy_ticket <quantity>\nExample: /buy_ticket 5")
        return
    
    try:
        quantity = int(args[0])
    except:
        await update.message.reply_text("âŒ Invalid quantity!")
        return
    
    if quantity < 1 or quantity > 100:
        await update.message.reply_text("âŒ Quantity must be 1-100")
        return
    
    if not lottery_active:
        await update.message.reply_text("âŒ Lottery not active! Wait for admin to start.")
        return
    
    cost = quantity * 20000
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < cost:
        await update.message.reply_text(f"âŒ Need {cost:,} credits! You have {balance:,}")
        return
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", cost, user_id)
    
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
    
    ticket_list = "\n".join([f"ðŸŽ« {t}" for t in new_tickets[:5]])
    if quantity > 5:
        ticket_list += f"\n... and {quantity-5} more"
    
    await update.message.reply_text(
        f"âœ… BOUGHT {quantity} TICKETS!\n\n"
        f"ðŸ’° Cost: {cost:,} credits\n"
        f"ðŸŽ« Your tickets:\n{ticket_list}\n\n"
        f"ðŸ’¡ /mytickets - Check all tickets"
    )

async def mytickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    user_tickets = lottery_tickets.get(user_id, [])
    
    if not user_tickets:
        await update.message.reply_text("ðŸŽ« You don't have any tickets!\nUse /buy_ticket to buy.")
        return
    
    ticket_list = "\n".join([f"ðŸŽ« {t}" for t in user_tickets[:10]])
    if len(user_tickets) > 10:
        ticket_list += f"\n... and {len(user_tickets)-10} more"
    
    await update.message.reply_text(
        f"ðŸŽ« MY TICKETS\n\n"
        f"Total: {len(user_tickets)}\n"
        f"Spent: {len(user_tickets) * 20000:,}\n\n"
        f"{ticket_list}"
    )

async def lottery_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    user_tickets = lottery_tickets.get(user_id, [])
    prize_pool = lottery_total_tickets * 20000
    win_chance = (len(user_tickets) / lottery_total_tickets * 100) if lottery_total_tickets > 0 else 0
    status_text = "ðŸŸ¢ ACTIVE" if lottery_active else "ðŸ”´ NOT ACTIVE"
    
    msg = f"ðŸŽ° LOTTERY INFO\n\n"
    msg += f"Status: {status_text}\n"
    msg += f"Total tickets: {lottery_total_tickets}\n"
    msg += f"Participants: {len(lottery_participants)}\n"
    msg += f"Prize pool: {prize_pool:,}\n\n"
    msg += f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
    msg += f"ðŸ“Š YOUR STATS:\n"
    msg += f"Your tickets: {len(user_tickets)}\n"
    msg += f"Contribution: {len(user_tickets) * 20000:,}\n"
    msg += f"Win chance: {win_chance:.1f}%"
    
    await update.message.reply_text(msg)

async def start_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    
    global lottery_active, lottery_tickets, lottery_total_tickets, lottery_participants, lottery_start_time
    
    if lottery_active:
        await update.message.reply_text("âŒ Lottery already active!")
        return
    
    lottery_active = True
    lottery_tickets = {}
    lottery_total_tickets = 0
    lottery_participants = []
    lottery_start_time = datetime.now()
    
    await update.message.reply_text(
        "âœ… LOTTERY STARTED!\n\n"
        "ðŸŽŸï¸ Ticket price: 20,000 credits\n"
        "ðŸ† Winner gets: ALL prize pool\n"
        "ðŸ“¢ Users can buy tickets:\n"
        "/buy_ticket <quantity>\n\n"
        "ðŸ’¡ /draw_winner - Draw winner"
    )

async def draw_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    
    global lottery_active, lottery_winner
    
    if not lottery_active:
        await update.message.reply_text("âŒ Lottery not active!")
        return
    
    if lottery_total_tickets == 0:
        await update.message.reply_text("âŒ No tickets sold!")
        return
    
    all_tickets = []
    for uid, tickets in lottery_tickets.items():
        for ticket in tickets:
            all_tickets.append((uid, ticket))
    
    winner_id, winner_ticket = random.choice(all_tickets)
    lottery_winner = winner_id
    prize_pool = lottery_total_tickets * 20000
    
    db = await get_db()
    winner_name = await db.fetchval("SELECT name FROM users WHERE user_id = $1", winner_id)
    current_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", winner_id)
    await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", current_bal + prize_pool, winner_id)
    
    try:
        await context.bot.send_message(
            winner_id,
            f"ðŸŽ‰ YOU WON THE LOTTERY! ðŸŽ‰\n\n"
            f"ðŸ† Ticket: {winner_ticket}\n"
            f"ðŸ’° Prize: {prize_pool:,}\n"
            f"ðŸ’³ New balance: {current_bal + prize_pool:,}"
        )
    except:
        pass
    
    await update.message.reply_text(
        f"ðŸŽ‰ LOTTERY WINNER! ðŸŽ‰\n\n"
        f"ðŸ† Winner: {winner_name}\n"
        f"ðŸŽ« Ticket: {winner_ticket}\n"
        f"ðŸ’° Prize: {prize_pool:,}\n\n"
        f"ðŸ’¡ /reset_lottery - Start new lottery"
    )
    
    lottery_active = False

async def reset_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    
    global lottery_active, lottery_tickets, lottery_total_tickets, lottery_participants, lottery_winner
    global lottery_active, lottery_tickets, lottery_total_tickets, lottery_participants, lottery_winner

    # Clear lottery tickets from DB (only tables that actually exist)
    db = await get_db()
    try:
        await db.execute("DELETE FROM lottery_tickets")
    except Exception:
        pass  # Table may not exist yet
    try:
        await db.execute("DELETE FROM coupon_used")
    except Exception:
        pass

    # Reset global in-memory state
    lottery_active = False
    lottery_tickets = {}
    lottery_total_tickets = 0
    lottery_participants = []
    lottery_winner = None

    await update.message.reply_text("Lottery reset! Use /start_lottery to begin.")

async def lottery_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /lottery_coupon <quantity>\nExample: /lottery_coupon 5")
        return
    
    try:
        quantity = int(args[0])
    except:
        await update.message.reply_text("âŒ Invalid quantity!")
        return
    
    coupon_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    
    db = await get_db()
    await db.execute("CREATE TABLE IF NOT EXISTS lottery_coupons (code TEXT PRIMARY KEY, quantity INT, used INT DEFAULT 0)")
    await db.execute("INSERT INTO lottery_coupons (code, quantity) VALUES ($1, $2)", coupon_code, quantity)
    
    await update.message.reply_text(
        f"âœ… COUPON GENERATED!\n\n"
        f"ðŸ”‘ Code: {coupon_code}\n"
        f"ðŸŽ« Free tickets: {quantity}\n\n"
        f"Claim: /claim_coupon {coupon_code}"
    )

async def claim_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("âŒ /claim_coupon <code>")
        return
    
    coupon_code = args[0].upper()
    
    db = await get_db()
    coupon = await db.fetchrow("SELECT quantity, used FROM lottery_coupons WHERE code = $1", coupon_code)
    
    if not coupon:
        await update.message.reply_text("âŒ Invalid coupon code!")
        return
    
    quantity, used = coupon['quantity'], coupon['used']
    
    if used >= quantity:
        await update.message.reply_text("âŒ This coupon has been fully used!")
        return
    
    await db.execute("CREATE TABLE IF NOT EXISTS coupon_used (code TEXT, user_id BIGINT, PRIMARY KEY (code, user_id))")
    already_used = await db.fetchval("SELECT code FROM coupon_used WHERE code = $1 AND user_id = $2", coupon_code, user_id)
    if already_used:
        await update.message.reply_text("âŒ You already used this coupon!")
        return
    
    await db.execute("INSERT INTO coupon_used (code, user_id) VALUES ($1, $2)", coupon_code, user_id)
    await db.execute("UPDATE lottery_coupons SET used = used + 1 WHERE code = $1", coupon_code)
    
    if not lottery_active:
        await update.message.reply_text(f"âœ… Coupon claimed! You got {quantity} free tickets.\nBut lottery is not active. Wait for /start_lottery")
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
    
    ticket_list = "\n".join([f"ðŸŽ« {t}" for t in new_tickets])
    
    await update.message.reply_text(
        f"âœ… COUPON CLAIMED!\n\n"
        f"ðŸŽ« Free tickets: {quantity}\n"
        f"{ticket_list}\n\n"
        f"Total tickets: {len(lottery_tickets[user_id])}"
    )

# ============ HILO GAME ==========
async def hilo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "ðŸ“ˆ HiLo Game\n\n"
            "Usage: /hilo <bet>\n"
            "Example: /hilo 500\n\n"
            "ðŸ’° Min bet: 100\n"
            "ðŸ’° Max bet: 10,000"
        )
        return
    
    try:
        bet = int(args[0])
    except:
        await update.message.reply_text("âŒ Invalid bet amount!")
        return
    
    if bet < 100 or bet > 10000:
        await update.message.reply_text("âŒ Bet must be between 100 and 10,000!")
        return
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < bet:
        await update.message.reply_text(f"âŒ Need {bet:,} credits! You have {balance:,}")
        return
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
    
    first_card = get_random_card()
    
    hilo_games[user_id] = {
        'bet': bet,
        'multiplier': 1.0,
        'current_card': first_card,
        'logs': [first_card],
        'active': True
    }
    
    keyboard = [
        [
            InlineKeyboardButton("ðŸ”¼ HIGH", callback_data=f"hilo_high_{user_id}"),
            InlineKeyboardButton("ðŸ”½ LOW", callback_data=f"hilo_low_{user_id}")
        ],
        [InlineKeyboardButton("ðŸ’° CASHOUT", callback_data=f"hilo_cashout_{user_id}")]
    ]
    
    msg = f"ðŸ“ˆ HiLo Game ðŸ“‰\n\n"
    msg += f"Bet amount: {bet:,} ðŸ’°\n"
    msg += f"Multiplier: None\n\n"
    msg += f"Your card: {first_card['suit']}{first_card['value']}\n"
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def hilo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if user_id not in hilo_games:
        await query.edit_message_text("âŒ No active game! Use /hilo")
        return
    
    game = hilo_games[user_id]
    
    if data == f"hilo_cashout_{user_id}":
        win_amount = int(game['bet'] * game['multiplier'])
        
        if win_amount > 0:
            db = await get_db()
            balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
            await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", win_amount, user_id)
        
        log_str = "".join([f"|{c['suit']}{c['value']}" for c in game['logs']])
        
        msg = f"ðŸ“ˆ HiLo Game ðŸ“‰\n\n"
        msg += f"Bet amount: {game['bet']:,} ðŸ’°\n"
        msg += f"Final Multiplier: {game['multiplier']:.3f}x\n"
        msg += f"You won: {win_amount:,} ðŸ’°\n\n"
        msg += f"Logs: {log_str}|"
        
        await query.edit_message_text(msg)
        del hilo_games[user_id]
        return
    
    guess = "high" if "high" in data else "low"
    
    new_card = get_random_card()
    game['logs'].append(new_card)
    
    current_rank = game['current_card']['rank']
    new_rank = new_card['rank']
    
    won = False
    if guess == "high" and new_rank > current_rank:
        won = True
    elif guess == "low" and new_rank < current_rank:
        won = True
    elif new_rank == current_rank:
        won = True
    
    if won:
        diff = abs(new_rank - current_rank)
        increase = get_multiplier_increase(diff)
        game['multiplier'] += increase
        game['current_card'] = new_card
        
        win_amount = int(game['bet'] * game['multiplier'])
        log_str = "".join([f"|{c['suit']}{c['value']}" for c in game['logs']])
        
        msg = f"ðŸ“ˆ HiLo Game ðŸ“‰\n\n"
        msg += f"Bet amount: {game['bet']:,} ðŸ’°\n"
        msg += f"Multiplier: {game['multiplier']:.3f}x\n"
        msg += f"Winning: {win_amount:,} ðŸ’°\n\n"
        msg += f"âœ… Card: {new_card['suit']}{new_card['value']} ({guess.upper()} won!)\n"
        msg += f"Your card: {game['current_card']['suit']}{game['current_card']['value']}\n\n"
        msg += f"Logs: {log_str}|\n"
        
        keyboard = [
            [
                InlineKeyboardButton("ðŸ”¼ HIGH", callback_data=f"hilo_high_{user_id}"),
                InlineKeyboardButton("ðŸ”½ LOW", callback_data=f"hilo_low_{user_id}")
            ],
            [InlineKeyboardButton("ðŸ’° CASHOUT", callback_data=f"hilo_cashout_{user_id}")]
        ]
        
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        log_str = "".join([f"|{c['suit']}{c['value']}" for c in game['logs']])
        
        msg = f"ðŸ“ˆ HiLo Game ðŸ“‰\n\n"
        msg += f"Bet amount: {game['bet']:,} ðŸ’°\n"
        msg += f"Multiplier: 0x\n\n"
        msg += f"âŒ Game Over!\n"
        msg += f"You bet {guess.upper()} on {new_card['suit']}{new_card['value']} and lost!\n\n"
        msg += f"Logs: {log_str}|"
        
        await query.edit_message_text(msg)
        del hilo_games[user_id]

# ============ MINES GAME ==========
active_mines = {}
mines_owner = {}
mines_next_id = 1

MAX_MULTIPLIER = {
    1: 5.0, 2: 7.0, 3: 9.0, 4: 10.5, 5: 12.0,
    6: 13.5, 7: 15.0, 8: 16.5, 9: 18.0, 10: 20.0,
    11: 22.0, 12: 24.0, 13: 26.0, 14: 28.0, 15: 30.0,
    16: 32.5, 17: 35.0, 18: 37.5, 19: 40.0, 20: 42.5,
    21: 45.0, 22: 47.5, 23: 49.0, 24: 50.0,
}

def calc_multiplier(bombs, safe):
    total_safe = 25 - bombs
    if safe == 0:
        return 1.0
    progress = safe / total_safe
    max_mult = MAX_MULTIPLIER.get(bombs, 50.0)
    mult = 1.0 + (max_mult - 1.0) * progress
    return round(mult, 2)

async def mines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "ðŸ’£ MINES\n"
            "/mines <amount> <bombs>\n"
            "Example: /mines 1000 3\n\n"
            "Min:100 | Max:10,000\n"
            "Bombs:1-24"
        )
        return
    
    try:
        bet = int(args[0])
        bombs = int(args[1])
    except:
        await update.message.reply_text("âŒ Invalid amount or bombs!")
        return
    
    if bet < 100 or bet > 10000:
        await update.message.reply_text("âŒ Bet must be between 100 and 10,000!")
        return
    
    if bombs < 1 or bombs > 24:
        await update.message.reply_text("âŒ Bombs must be between 1 and 24!")
        return
    
    db = await get_db()
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    
    if balance < bet:
        await update.message.reply_text(f"âŒ Need {bet:,} credits, you have {balance:,}")
        return
    
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
    
    global mines_next_id
    game_id = mines_next_id
    mines_next_id += 1
    
    bomb_positions = random.sample(range(25), bombs)
    max_mult = MAX_MULTIPLIER.get(bombs, 50.0)
    
    active_mines[game_id] = {
        'bet': bet,
        'bombs': bomb_positions,
        'revealed': [],
        'active': True,
        'bomb_count': bombs,
        'max_mult': max_mult,
        'owner_id': user_id,
        'chat_id': chat_id
    }
    mines_owner[game_id] = user_id
    
    keyboard = []
    for i in range(5):
        row = []
        for j in range(5):
            pos = i * 5 + j
            row.append(InlineKeyboardButton("â“", callback_data=f"mine_{game_id}_{pos}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("ðŸ’° CASHOUT", callback_data=f"mine_cashout_{game_id}")])
    
    await update.message.reply_text(
        f"ðŸ’£ MINES GAME STARTED\n\n"
        f"ðŸ’° Bet: {bet:,} credits\n"
        f"ðŸ’£ Bombs: {bombs}\n"
        f"ðŸŽ¯ Max Multiplier: {max_mult}x\n"
        f"ðŸ’Ž Current: 1.00x | {bet:,} credits\n\n"
        f"Click tiles to reveal safe spots.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def mine_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    parts = data.split("_")
    if parts[1] == "cashout":
        game_id = int(parts[2])
    else:
        game_id = int(parts[1])
    
    if game_id not in active_mines:
        await query.answer("Game not found or expired!", show_alert=True)
        await query.edit_message_text("âŒ No active game found.")
        return
    
    game = active_mines[game_id]
    
    if game['owner_id'] != user_id:
        await query.answer("This is not your game!", show_alert=True)
        return
    
    if data.startswith("mine_cashout_"):
        safe_count = len([t for t in game['revealed'] if t not in game['bombs']])
        multiplier = calc_multiplier(game['bomb_count'], safe_count)
        win_amount = int(game['bet'] * multiplier)
        
        db = await get_db()
        current_balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        new_balance = current_balance + win_amount
        await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_balance, user_id)
        
        await query.edit_message_text(
            f"ðŸ’° CASHOUT SUCCESSFUL!\n\n"
            f"ðŸ’Ž Multiplier: {multiplier}x\n"
            f"âœ… Safe tiles: {safe_count}/{25 - game['bomb_count']}\n"
            f"ðŸ’° Won: {win_amount:,} credits\n"
            f"ðŸ’³ New balance: {new_balance:,} credits"
        )
        
        del active_mines[game_id]
        del mines_owner[game_id]
        return
    
    position = int(parts[2])
    
    if position in game['revealed']:
        await query.answer("You already revealed this tile!", show_alert=True)
        return
    
    game['revealed'].append(position)
    
    if position in game['bombs']:
        await query.edit_message_text(
            f"ðŸ’£ BOOM! YOU HIT A BOMB!\n\n"
            f"ðŸ’° Lost: {game['bet']:,} credits\n"
            f"ðŸ˜µ Game Over!\n\n"
            f"Use /mines to play again."
        )
        del active_mines[game_id]
        del mines_owner[game_id]
        return
    
    safe_count = len([t for t in game['revealed'] if t not in game['bombs']])
    total_safe = 25 - game['bomb_count']
    multiplier = calc_multiplier(game['bomb_count'], safe_count)
    current_win = int(game['bet'] * multiplier)
    
    if safe_count >= total_safe:
        db = await get_db()
        current_balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        new_balance = current_balance + current_win
        await db.execute("UPDATE users SET balance = $1 WHERE user_id = $2", new_balance, user_id)
        
        await query.edit_message_text(
            f"ðŸŽ‰ PERFECT WIN! ðŸŽ‰\n\n"
            f"âœ… All {total_safe} safe tiles revealed!\n"
            f"ðŸ’Ž Multiplier: {multiplier}x\n"
            f"ðŸ’° Won: {current_win:,} credits\n"
            f"ðŸ’³ New balance: {new_balance:,} credits"
        )
        del active_mines[game_id]
        del mines_owner[game_id]
        return
    
    keyboard = []
    for i in range(5):
        row = []
        for j in range(5):
            pos = i * 5 + j
            if pos in game['revealed']:
                row.append(InlineKeyboardButton("ðŸ’Ž", callback_data=f"mine_{game_id}_{pos}"))
            else:
                row.append(InlineKeyboardButton("â“", callback_data=f"mine_{game_id}_{pos}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("ðŸ’° CASHOUT", callback_data=f"mine_cashout_{game_id}")])
    
    remaining = total_safe - safe_count
    max_mult = game['max_mult']
    
    await query.edit_message_text(
        f"ðŸ’Ž SAFE TILE!\n\n"
        f"ðŸ’° Bet: {game['bet']:,}\n"
        f"âœ… Safe found: {safe_count}/{total_safe}\n"
        f"ðŸ’Ž Current multiplier: {multiplier}x\n"
        f"ðŸ’° Cashout value: {current_win:,}\n"
        f"ðŸŽ¯ Max multiplier: {max_mult}x\n"
        f"ðŸ’š Remaining safe tiles: {remaining}\n\n"
        f"Click another tile or CASHOUT!",
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

async def update_cricket_stats_realtime(user_id, name, runs_added=0, wickets_added=0, current_match_runs=0):
    db = await get_db()
    stats = await db.fetchrow("SELECT * FROM cricket_stats WHERE user_id = $1", user_id)
    if stats:
        new_runs = stats['runs'] + runs_added
        new_wickets = stats['wickets'] + wickets_added
        new_highest = stats['highest_score']
        if current_match_runs > new_highest:
            new_highest = current_match_runs
        await db.execute("UPDATE cricket_stats SET runs = $1, wickets = $2, highest_score = $3 WHERE user_id = $4", new_runs, new_wickets, new_highest, user_id)
    else:
        await db.execute("INSERT INTO cricket_stats (user_id, name, runs, wickets, highest_score) VALUES ($1, $2, $3, $4, $5)", user_id, name, runs_added, wickets_added, current_match_runs)

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

    def get_deliveries(self):
        if self.mode == "1-3":
            return {"BNC": {"name": "BNC", "out_on": 1}, "YRK": {"name": "YRK", "out_on": 2}, "SHT": {"name": "SHT", "out_on": 3}}
        elif self.mode == "1-5":
            return {"RS": {"name": "RS", "out_on": 0}, "BNC": {"name": "BNC", "out_on": 1}, "YRK": {"name": "YRK", "out_on": 2}, "SHT": {"name": "SHT", "out_on": 3}, "SLW": {"name": "SLW", "out_on": 4}, "KNC": {"name": "KNC", "out_on": 6}}
        elif self.mode == "1-9":
            return {"YRK": {"name": "YRK", "out_on": 1}, "BNC": {"name": "BNC", "out_on": 2}, "SHT": {"name": "SHT", "out_on": 3}, "SLW": {"name": "SLW", "out_on": 4}, "LC": {"name": "LC", "out_on": 5}, "KNC": {"name": "KNC", "out_on": 6}, "OS": {"name": "OS", "out_on": 7}, "IS": {"name": "IS", "out_on": 8}, "OC": {"name": "OC", "out_on": 9}}
        else:
            return DELIVERIES

    def get_bat_numbers(self):
        if self.mode == "1-3":
            return [1, 2, 3]
        elif self.mode == "1-5":
            return [0, 1, 2, 3, 4, 6]
        elif self.mode == "1-9":
            return [1, 2, 3, 4, 5, 6, 7, 8, 9]
        else:
            return [0, 1, 2, 3, 4, 5, 6]

    def check_out(self, delivery_key, shot):
        return self.get_deliveries()[delivery_key]["out_on"] == shot

    def get_overs(self):
        overs = self.balls // 6
        balls = self.balls % 6
        return f"{overs}.{balls}"

async def clcricket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.message.chat.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    args = context.args
    bet = 0
    if args:
        try:
            bet = int(args[0])
            if bet < 100:
                await update.message.reply_text("âŒ Minimum bet is 100 credits!")
                return
        except:
            await update.message.reply_text("âŒ Invalid bet amount!")
            return
    if bet > 0:
        db = await get_db()
        balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        if balance < bet:
            await update.message.reply_text(f"âŒ You need {bet:,} credits to play!")
            return
    global cricket_next_id
    game_id = cricket_next_id
    cricket_next_id += 1
    cricket_lobby[game_id] = {"creator_id": user_id, "creator_name": user_name, "bet": bet, "chat_id": chat_id}
    bet_text = f"ðŸ’° Bet: {bet} | Prize: {bet*2}" if bet > 0 else "ðŸŽ® Normal Game"
    await update.message.reply_text(f"ðŸ CRICKET GAME\n\nðŸ‘‘ Host: {user_name}\n{bet_text}\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nâš¡ Select Mode:", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("1-3 MODE", callback_data=f"cricket_mode_{game_id}_1-3")],
        [InlineKeyboardButton("1-5 MODE", callback_data=f"cricket_mode_{game_id}_1-5")],
        [InlineKeyboardButton("1-9 MODE", callback_data=f"cricket_mode_{game_id}_1-9")],
        [InlineKeyboardButton("DEFAULT", callback_data=f"cricket_mode_{game_id}_default")]
    ]))

async def cricket_mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    mode = parts[3]
    
    if game_id not in cricket_lobby:
        await query.edit_message_text("âŒ Game expired!")
        return
    
    lobby = cricket_lobby[game_id]
    if update.effective_user.id != lobby["creator_id"]:
        await query.answer("Only host can select mode!", show_alert=True)
        return
    
    lobby["mode"] = mode
    bet_text = f"ðŸ’° Bet: {lobby['bet']} | Prize: {lobby['bet']*2}" if lobby['bet'] > 0 else "ðŸŽ® Normal Game"
    
    await query.edit_message_text(
        f"ðŸ CRICKET GAME\n\nðŸ‘‘ Host: {lobby['creator_name']}\n{bet_text}\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nâš¡ Waiting for opponent...",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ðŸ”µ JOIN GAME", callback_data=f"cricket_join_{game_id}")]])
    )

async def cricket_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = query.data
    game_id = int(data.split("_")[2])
    
    if game_id not in cricket_lobby:
        await query.edit_message_text("âŒ Game expired!")
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
        # Check joining player's balance
        balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        if balance is None:
            await query.edit_message_text("Send /start first!")
            return
        if balance < bet:
            await query.answer(f"Need {bet} credits!", show_alert=True)
            return
        # Check creator's balance too (may have spent credits since creating game)
        creator_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", creator_id)
        if creator_bal < bet:
            await query.answer("Game creator no longer has enough credits!", show_alert=True)
            del cricket_lobby[game_id]
            await query.edit_message_text("Game cancelled: creator has insufficient balance.")
            return
        # Atomic transaction: deduct from both players simultaneously
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, creator_id)
                await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
    
    game = CricketGame(game_id, creator_id, creator_name, bet, chat_id, mode)
    game.player2_id = user_id
    game.player2_name = user_name
    game.game_active = True
    cricket_games[game_id] = game
    del cricket_lobby[game_id]
    
    await query.edit_message_text(
        f"ðŸ CRICKET GAME\n\n{creator_name} vs {user_name}\n" + (f"ðŸ’° Bet: {bet} | Prize: {bet*2}\n" if bet > 0 else "") + f"\nðŸª™ TOSS TIME!\n\n{creator_name}, choose:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("HEADS", callback_data=f"cricket_toss_{game_id}_heads")],
            [InlineKeyboardButton("TAILS", callback_data=f"cricket_toss_{game_id}_tails")]
        ])
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
        f"ðŸ CRICKET GAME\n\nðŸª™ TOSS: {toss.upper()}!\nðŸ† {winner_name} won the toss!\n\nChoose:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("ðŸ BAT", callback_data=f"cricket_choice_{game_id}_bat")],
            [InlineKeyboardButton("ðŸŽ¯ BOWL", callback_data=f"cricket_choice_{game_id}_bowl")]
        ])
    )

async def cricket_choice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    choice = parts[3]
    
    game = cricket_games[game_id]
    
    if update.effective_user.id != game.toss_winner:
        await query.answer("Toss winner chooses!", show_alert=True)
        return
    
    if choice == "bat":
        game.current_batsman = game.toss_winner
        game.current_bowler = game.player2_id if game.toss_winner == game.player1_id else game.player1_id
    else:
        game.current_batsman = game.player2_id if game.toss_winner == game.player1_id else game.player1_id
        game.current_bowler = game.toss_winner
    
    game.score = 0
    game.wickets = 0
    game.balls = 0
    game.target = None
    game.waiting_for = "bowl"
    game.pending_delivery = None
    
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
    
    batsman = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
    bowler = game.player1_name if game.current_bowler == game.player1_id else game.player2_name
    
    await query.edit_message_text(
        f"ðŸ CRICKET GAME\n\n{batsman} Batting | {bowler} Bowling\n" + 
        (f"ðŸ’° Bet: {game.bet}\n" if game.bet > 0 else "") + 
        f"ðŸ“Š {game.score}/{game.wickets}\n\nðŸŽ¯ {bowler}'s turn:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cricket_bowl_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    delivery_key = parts[3]
    
    game = cricket_games[game_id]
    
    if update.effective_user.id != game.current_bowler:
        await query.answer("Not your turn!", show_alert=True)
        return
    
    if game.waiting_for != "bowl":
        await query.answer("Wait!", show_alert=True)
        return
    
    game.pending_delivery = delivery_key
    game.waiting_for = "bat"
    
    bowler_name = game.player1_name if game.current_bowler == game.player1_id else game.player2_name
    batsman_name = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
    
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
        f"ðŸ CRICKET GAME\n\n{batsman_name}, choose your shot:\nðŸ“Š {game.score}/{game.wickets} | {game.get_overs()} overs",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def cricket_bat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    shot = int(parts[3])
    
    game = cricket_games[game_id]
    
    if update.effective_user.id != game.current_batsman:
        await query.answer("Not your turn!", show_alert=True)
        return
    
    if game.waiting_for != "bat":
        await query.answer("Wait for bowler!", show_alert=True)
        return
    
    delivery_key = game.pending_delivery
    deliveries = game.get_deliveries()
    bowler = game.player1_name if game.current_bowler == game.player1_id else game.player2_name
    batsman = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
    delivery_name = deliveries[delivery_key]["name"]
    
    # Check if OUT
    if game.check_out(delivery_key, shot):
        if game.current_bowler == game.player1_id:
            game.player1_wickets_taken += 1
            await update_cricket_stats_realtime(game.player1_id, game.player1_name, 0, 1, 0)
        else:
            game.player2_wickets_taken += 1
            await update_cricket_stats_realtime(game.player2_id, game.player2_name, 0, 1, 0)
        
        game.wickets += 1
        game.balls += 1
        
        if game.target is None:
            game.target = game.score + 1
            
            game.current_batsman = game.player2_id if game.current_batsman == game.player1_id else game.player1_id
            game.current_bowler = game.player2_id if game.current_bowler == game.player1_id else game.player1_id
            game.score = 0
            game.wickets = 0
            game.balls = 0
            game.waiting_for = "bowl"
            game.pending_delivery = None
            
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
            
            batsman_name = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
            bowler_name = game.player1_name if game.current_bowler == game.player1_id else game.player2_name
            
            await query.edit_message_text(
                f"ðŸ CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\nâŒ OUT!\n\n"
                f"ðŸ“Š First Innings Score: {game.target - 1}\nðŸŽ¯ Target: {game.target}\n\n"
                f"{batsman_name} Batting | {bowler_name} Bowling\n"
                f"ðŸ“Š {game.score}/{game.wickets} | {game.get_overs()} overs\n\n"
                f"ðŸŽ¯ {bowler_name}'s turn:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        else:
            if game.score == game.target - 1:
                game.game_active = False
                
                if game.bet > 0:
                    db = await get_db()
                    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player1_id)
                    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player2_id)
                
                await query.edit_message_text(
                    f"ðŸ CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\nâŒ OUT!\n\n"
                    f"ðŸ“Š Final: {game.score}/{game.wickets}\nðŸŽ¯ Target: {game.target}\n\n"
                    f"ðŸ¤ DRAW! ðŸ¤" + (f"\nðŸ’° Money returned: {game.bet} each" if game.bet > 0 else "")
                )
                del cricket_games[game_id]
                return
            else:
                game.game_active = False
                game.winner = game.player2_id if game.current_batsman == game.player1_id else game.player1_id
                loser_id = game.player2_id if game.winner == game.player1_id else game.player1_id
                loser_name = game.player2_name if game.winner == game.player1_id else game.player1_name
                
                await update_wins_losses_realtime(game.winner, game.player1_name if game.winner == game.player1_id else game.player2_name, True)
                await update_wins_losses_realtime(loser_id, loser_name, False)
                
                if game.bet > 0:
                    db = await get_db()
                    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet*2, game.winner)
                
                winner_name = game.player1_name if game.winner == game.player1_id else game.player2_name
                
                await query.edit_message_text(
                    f"ðŸ CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\nâŒ OUT!\n\n"
                    f"ðŸ“Š Final: {game.score}/{game.wickets}\nðŸŽ¯ Target: {game.target}\n\n"
                    f"ðŸ† WINNER: {winner_name} ðŸ†" + (f"\nðŸ’° Prize: {game.bet*2}" if game.bet > 0 else "")
                )
                del cricket_games[game_id]
                return
    
    # SAFE - Add runs
    else:
        if game.current_batsman == game.player1_id:
            game.player1_match_runs += shot
            await update_cricket_stats_realtime(game.player1_id, game.player1_name, shot, 0, game.player1_match_runs)
        else:
            game.player2_match_runs += shot
            await update_cricket_stats_realtime(game.player2_id, game.player2_name, shot, 0, game.player2_match_runs)
        
        game.score += shot
        game.balls += 1
        
        if game.target and game.score >= game.target:
            game.game_active = False
            game.winner = game.current_batsman
            loser_id = game.player2_id if game.winner == game.player1_id else game.player1_id
            loser_name = game.player2_name if game.winner == game.player1_id else game.player1_name
            
            await update_wins_losses_realtime(game.winner, game.player1_name if game.winner == game.player1_id else game.player2_name, True)
            await update_wins_losses_realtime(loser_id, loser_name, False)
            
            if game.bet > 0:
                db = await get_db()
                await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet*2, game.winner)
            
            winner_name = game.player1_name if game.winner == game.player1_id else game.player2_name
            
            await query.edit_message_text(
                f"ðŸ CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\nâœ… {shot} runs!\n\n"
                f"ðŸ“Š Final: {game.score}/{game.wickets}\nðŸŽ¯ Target: {game.target}\n\n"
                f"ðŸ† WINNER: {winner_name} ðŸ†" + (f"\nðŸ’° Prize: {game.bet*2}" if game.bet > 0 else "")
            )
            del cricket_games[game_id]
            return
        
        game.waiting_for = "bowl"
        game.pending_delivery = None
        
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
        
        bowler_name = game.player1_name if game.current_bowler == game.player1_id else game.player2_name
        batsman_name = game.player1_name if game.current_batsman == game.player1_id else game.player2_name
        
        await query.edit_message_text(
            f"ðŸ CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\nâœ… {shot} runs!\n\n"
            f"{batsman_name} Batting | {bowler_name} Bowling\n"
            f"ðŸ“Š {game.score}/{game.wickets} | {game.get_overs()} overs\n\n"
            f"ðŸŽ¯ {bowler_name}'s turn:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ============ ADD ALL PLAYERS (20 Current + 20 Legends per country) ==========
async def add_all_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    
    db = await get_db()
    
    await db.execute("DELETE FROM shop")
    
    # ========== INDIA CURRENT (20) ==========
    india_current = [
        ("Virat Kohli", 2000000), ("Rohit Sharma", 1900000), ("Shubman Gill", 1700000),
        ("Hardik Pandya", 1800000), ("Jasprit Bumrah", 2000000), ("Ravindra Jadeja", 1600000),
        ("KL Rahul", 1500000), ("Suryakumar Yadav", 1750000), ("Mohammed Shami", 1650000),
        ("Rishabh Pant", 1550000), ("Mohammed Siraj", 1450000), ("Axar Patel", 1400000),
        ("Shreyas Iyer", 1480000), ("Ishan Kishan", 1380000), ("Deepak Chahar", 1350000),
        ("Sanju Samson", 1420000), ("Yuzvendra Chahal", 1390000), ("Bhuvneshwar Kumar", 1370000),
        ("Shardul Thakur", 1320000), ("Washington Sundar", 1300000)
    ]
    
    # ========== INDIA LEGENDS (20) ==========
    india_legends = [
        ("Sachin Tendulkar", 5000000), ("MS Dhoni", 4500000), ("Rahul Dravid", 4000000),
        ("Sourav Ganguly", 3800000), ("Virender Sehwag", 4200000), ("VVS Laxman", 3500000),
        ("Anil Kumble", 3600000), ("Kapil Dev", 4800000), ("Sunil Gavaskar", 4400000),
        ("Zaheer Khan", 3200000), ("Harbhajan Singh", 3100000), ("Yuvraj Singh", 4300000),
        ("Gautam Gambhir", 3400000), ("Mohammad Azharuddin", 3300000), ("Navjot Sidhu", 2800000),
        ("Kris Srikkanth", 2700000), ("Erapalli Prasanna", 2500000), ("Bishan Bedi", 2600000),
        ("Bhagwat Chandrasekhar", 2400000), ("Venkatesh Prasad", 2300000)
    ]
    
    # ========== ENGLAND CURRENT (20) ==========
    england_current = [
        ("Joe Root", 1800000), ("Ben Stokes", 1900000), ("Jos Buttler", 1700000),
        ("Jonny Bairstow", 1600000), ("Jofra Archer", 1750000), ("Moeen Ali", 1500000),
        ("Sam Curran", 1550000), ("Chris Woakes", 1400000), ("Mark Wood", 1450000),
        ("Adil Rashid", 1350000), ("Dawid Malan", 1300000), ("Jason Roy", 1250000),
        ("Liam Livingstone", 1450000), ("Harry Brook", 1500000), ("Reece Topley", 1200000),
        ("David Willey", 1150000), ("Phil Salt", 1100000), ("Will Jacks", 1050000),
        ("Gus Atkinson", 1000000), ("Tom Curran", 1080000)
    ]
    
    # ========== ENGLAND LEGENDS (20) ==========
    england_legends = [
        ("Ian Botham", 4800000), ("Alastair Cook", 4000000), ("Andrew Flintoff", 4500000),
        ("Kevin Pietersen", 4200000), ("James Anderson", 5000000), ("Stuart Broad", 4500000),
        ("Graeme Swann", 3800000), ("Michael Vaughan", 3500000), ("Alec Stewart", 3400000),
        ("Marcus Trescothick", 3300000), ("Paul Collingwood", 3200000), ("Monty Panesar", 2800000),
        ("Matthew Hoggard", 2700000), ("Steve Harmison", 3000000), ("Darren Gough", 2900000),
        ("Graeme Hick", 3100000), ("David Gower", 3500000), ("Geoffrey Boycott", 3800000),
        ("Fred Trueman", 4000000), ("WG Grace", 5000000)
    ]
    
    # ========== AUSTRALIA CURRENT (20) ==========
    australia_current = [
        ("Pat Cummins", 1900000), ("Steve Smith", 2000000), ("David Warner", 1800000),
        ("Mitchell Starc", 1850000), ("Glenn Maxwell", 1750000), ("Travis Head", 1650000),
        ("Marnus Labuschagne", 1700000), ("Josh Hazlewood", 1600000), ("Adam Zampa", 1500000),
        ("Marcus Stoinis", 1450000), ("Cameron Green", 1550000), ("Alex Carey", 1350000),
        ("Mitchell Marsh", 1400000), ("Nathan Lyon", 1480000), ("Matthew Wade", 1300000),
        ("Tim David", 1380000), ("Ashton Agar", 1250000), ("Sean Abbott", 1200000),
        ("Ben McDermott", 1150000), ("Kane Richardson", 1100000)
    ]
    
    # ========== AUSTRALIA LEGENDS (20) ==========
    australia_legends = [
        ("Don Bradman", 10000000), ("Ricky Ponting", 5500000), ("Shane Warne", 6000000),
        ("Glenn McGrath", 5500000), ("Adam Gilchrist", 5000000), ("Matthew Hayden", 4500000),
        ("Michael Clarke", 4200000), ("Steve Waugh", 4800000), ("Mark Waugh", 4000000),
        ("Brett Lee", 4500000), ("Dennis Lillee", 5000000), ("Jeff Thomson", 4200000),
        ("Allan Border", 4600000), ("Greg Chappell", 4400000), ("Ian Chappell", 4200000),
        ("David Boon", 3800000), ("Dean Jones", 3900000), ("Damien Martyn", 3700000),
        ("Jason Gillespie", 3600000), ("Michael Hussey", 4300000)
    ]
    
    # ========== NEW ZEALAND CURRENT (20) ==========
    nz_current = [
        ("Kane Williamson", 1900000), ("Trent Boult", 1800000), ("Devon Conway", 1600000),
        ("Daryl Mitchell", 1550000), ("Mitchell Santner", 1450000), ("Lockie Ferguson", 1500000),
        ("Tim Southee", 1400000), ("Glenn Phillips", 1350000), ("Michael Bracewell", 1250000),
        ("Finn Allen", 1300000), ("Adam Milne", 1200000), ("Ish Sodhi", 1150000),
        ("James Neesham", 1250000), ("Tom Latham", 1300000), ("Martin Guptill", 1400000),
        ("Matt Henry", 1200000), ("Kyle Jamieson", 1350000), ("Henry Nicholls", 1100000),
        ("Will Young", 1050000), ("Ben Sears", 1000000)
    ]
    
    # ========== NEW ZEALAND LEGENDS (20) ==========
    nz_legends = [
        ("Richard Hadlee", 5500000), ("Martin Crowe", 4800000), ("Brendon McCullum", 4500000),
        ("Daniel Vettori", 4200000), ("Stephen Fleming", 4000000), ("Chris Cairns", 3800000),
        ("Nathan Astle", 3600000), ("Craig McMillan", 3400000), ("Scott Styris", 3300000),
        ("Jacob Oram", 3200000), ("Shane Bond", 4500000), ("Geoff Allott", 2800000),
        ("Dion Nash", 2900000), ("John Wright", 3100000), ("Mark Greatbatch", 3000000),
        ("Ian Smith", 2900000), ("Lance Cairns", 3500000), ("Ewen Chatfield", 2800000),
        ("Bruce Taylor", 3000000), ("Bert Sutcliffe", 3200000)
    ]
    
    # ========== INSERT ALL ==========
    
    # India
    for name, price in india_current:
        await db.execute("INSERT INTO shop (name, price, category, type) VALUES ($1, $2, 'India', 'current')", name, price)
    for name, price in india_legends:
        await db.execute("INSERT INTO shop (name, price, category, type) VALUES ($1, $2, 'India', 'legend')", name, price)
    
    # England
    for name, price in england_current:
        await db.execute("INSERT INTO shop (name, price, category, type) VALUES ($1, $2, 'England', 'current')", name, price)
    for name, price in england_legends:
        await db.execute("INSERT INTO shop (name, price, category, type) VALUES ($1, $2, 'England', 'legend')", name, price)
    
    # Australia
    for name, price in australia_current:
        await db.execute("INSERT INTO shop (name, price, category, type) VALUES ($1, $2, 'Australia', 'current')", name, price)
    for name, price in australia_legends:
        await db.execute("INSERT INTO shop (name, price, category, type) VALUES ($1, $2, 'Australia', 'legend')", name, price)
    
    # New Zealand
    for name, price in nz_current:
        await db.execute("INSERT INTO shop (name, price, category, type) VALUES ($1, $2, 'New Zealand', 'current')", name, price)
    for name, price in nz_legends:
        await db.execute("INSERT INTO shop (name, price, category, type) VALUES ($1, $2, 'New Zealand', 'legend')", name, price)
    
    
    total = await db.fetchval("SELECT COUNT(*) FROM shop")
    current_count = await db.fetchval("SELECT COUNT(*) FROM shop WHERE type = 'current'")
    legend_count = await db.fetchval("SELECT COUNT(*) FROM shop WHERE type = 'legend'")
    
    
    await update.message.reply_text(
        f"âœ… ALL PLAYERS ADDED!\n\n"
        f"ðŸ TOTAL: {total} players\n"
        f"ðŸ“Š Current: {current_count} players\n"
        f"ðŸ“Š Legends: {legend_count} players\n\n"
        f"ðŸ‡®ðŸ‡³ India: 20 Current + 20 Legends\n"
        f"ðŸ´ó §ó ¢ó ¥ó ®ó §ó ¿ England: 20 Current + 20 Legends\n"
        f"ðŸ‡¦ðŸ‡º Australia: 20 Current + 20 Legends\n"
        f"ðŸ‡³ðŸ‡¿ New Zealand: 20 Current + 20 Legends\n\n"
        f"ðŸ’¡ /shop - Now buy players!"
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
            text = "â¬œ" if num == 0 else str(num)
            row.append(InlineKeyboardButton(text, callback_data=f"numpuz_{level}_{i}_{j}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

async def numpuz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    
    try:
        await db.execute("ALTER TABLE numpuz_progress ADD COLUMN chat_id BIGINT")
    except:
        pass
    try:
        await db.execute("ALTER TABLE numpuz_progress ADD COLUMN owner_id BIGINT")
    except:
        pass
    
    saved = await db.fetchrow("SELECT level, board, moves, owner_id FROM numpuz_progress WHERE chat_id = $1", chat_id)
    
    if saved and saved['board']:
        level = saved['level']
        board = json.loads(saved['board'])
        owner_id = saved['owner_id']
        
        owner_name = await db.fetchval("SELECT name FROM users WHERE user_id = $1", owner_id)
        owner_name = owner_name if owner_name else "Someone"
        
        keyboard = get_board_keyboard(board, level)
        
        await update.message.reply_text(
            f"ðŸ§© NUMBER PUZZLE - LEVEL {level}\n"
            f"ðŸŽ® Game started by: {owner_name}\n"
            f"ðŸ”’ Only {owner_name} can play!",
            reply_markup=keyboard
        )
        return
    
    level = 1
    size = get_size_for_level(level)
    while True:
        board = get_shuffled_board(size)
        if is_solvable(board):
            break
    
    await db.execute("INSERT INTO numpuz_progress (user_id, level, board, moves, chat_id, owner_id) VALUES ($1, $2, $3, $4, $5, $6)",
                     user_id, level, json.dumps(board), 0, chat_id, user_id)
    
    keyboard = get_board_keyboard(board, level)
    await update.message.reply_text(
        f"ðŸ§© NUMBER PUZZLE - LEVEL {level}\n"
        f"ðŸ‘‘ Started by: {update.effective_user.first_name}\n"
        f"ðŸ”’ Only you can play!",
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
    saved = await db.fetchrow("SELECT level, board, moves, owner_id FROM numpuz_progress WHERE chat_id = $1", chat_id)
    
    if not saved:
        await query.answer("No active game!", show_alert=True)
        return
    
    db_level, board_json, moves, owner_id = saved['level'], saved['board'], saved['moves'], saved['owner_id']
    
    if owner_id != user_id:
        await query.answer("âŒ Not your game!", show_alert=True)
        return
    
    board = json.loads(board_json)
    
    if db_level != level:
        await query.answer("Invalid!", show_alert=True)
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
            
            await db.execute("UPDATE numpuz_progress SET level = $1, board = $2, moves = $3, owner_id = $4 WHERE chat_id = $5",
                             next_level, json.dumps(new_board), 0, user_id, chat_id)
            
            keyboard = get_board_keyboard(new_board, next_level)
            await query.edit_message_text(
                f"ðŸŽ‰ LEVEL {db_level} COMPLETE!\nðŸ“Š Moves: {moves}\nâœ¨ Moving to LEVEL {next_level}!",
                reply_markup=keyboard
            )
            return
        
        await db.execute("UPDATE numpuz_progress SET board = $1, moves = $2 WHERE chat_id = $3", json.dumps(board), moves, chat_id)
        
        keyboard = get_board_keyboard(board, db_level)
        await query.edit_message_text(f"ðŸ§© LEVEL {db_level} | Moves: {moves}", reply_markup=keyboard)
    else:
        await query.answer("Invalid move!", show_alert=True)

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
        self.board = ['â¬œ', 'â¬œ', 'â¬œ', 'â¬œ', 'â¬œ', 'â¬œ', 'â¬œ', 'â¬œ', 'â¬œ']
        self.current_turn = player1_id
        self.game_active = False
        self.winner = None
    
    def make_move(self, position, user_id):
        if not self.game_active:
            return False, "Game not active"
        if user_id != self.current_turn:
            return False, "Not your turn!"
        if self.board[position] != 'â¬œ':
            return False, "Position taken!"
        
        symbol = 'âŒ' if user_id == self.player1_id else 'â­•'
        self.board[position] = symbol
        
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a,b,c in wins:
            if self.board[a] == symbol and self.board[b] == symbol and self.board[c] == symbol:
                self.winner = user_id
                self.game_active = False
                return True, "win"
        
        if all(cell != 'â¬œ' for cell in self.board):
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
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    args = context.args
    bet = 0
    if args:
        try:
            bet = int(args[0])
            if bet < 100:
                await update.message.reply_text("âŒ Minimum bet 100 credits!")
                return
        except:
            await update.message.reply_text("âŒ Invalid bet!")
            return
    
    if bet > 0:
        db = await get_db()
        balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        if balance < bet:
            await update.message.reply_text(f"âŒ Need {bet:,} credits!")
            return
    
    global ttt_next_id
    game_id = ttt_next_id
    ttt_next_id += 1
    
    ttt_lobby[game_id] = {"creator_id": user_id, "creator_name": user_name, "bet": bet, "chat_id": chat_id}
    bet_text = f"ðŸ’° Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "ðŸŽ® Normal Game"
    await update.message.reply_text(
        f"ðŸŽ¯ TIC TAC TOE\n\nðŸ‘‘ {user_name} (âŒ)\n{bet_text}\n\nâš¡ Waiting for opponent...",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ðŸ”µ JOIN", callback_data=f"ttt_join_{game_id}")]])
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
            await query.edit_message_text("âŒ Lobby expired!")
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
                await query.edit_message_text(f"Need {bet:,} credits!")
                return
            creator_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", creator_id)
            if creator_bal < bet:
                del ttt_lobby[game_id]
                await query.edit_message_text("Game cancelled: creator has insufficient balance.")
                return
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, creator_id)
                    await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
        
        game = TicTacToe(game_id, creator_id, creator_name, user_name, bet, chat_id)
        game.player2_id = user_id
        game.game_active = True
        ttt_games[game_id] = game
        del ttt_lobby[game_id]
        
        bet_text = f"ðŸ’° Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "ðŸŽ® Normal Game"
        await query.edit_message_text(f"ðŸŽ¯ TIC TAC TOE\nâŒ {creator_name} vs â­• {user_name}\n{bet_text}\nðŸŽ¯ {creator_name}'s Turn", reply_markup=game.get_keyboard())
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
                result_text = f"ðŸ† WINNER: {winner_name.upper()} ðŸ†\nðŸ’° +{game.bet*2:,} credits"
            else:
                result_text = f"ðŸ† WINNER: {winner_name.upper()} ðŸ†"
            
            await query.edit_message_text(f"ðŸŽ¯ TIC TAC TOE\n\nâŒ {game.player1_name} vs â­• {game.player2_name}\n\n{result_text}", reply_markup=game.get_keyboard())
            del ttt_games[game_id]
            return
        
        elif msg == "draw":
            if game.bet > 0:
                db = await get_db()
                await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player1_id)
                await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player2_id)
            
            await query.edit_message_text(f"ðŸŽ¯ TIC TAC TOE\n\nâŒ {game.player1_name} vs â­• {game.player2_name}\n\nðŸ¤ DRAW ðŸ¤", reply_markup=game.get_keyboard())
            del ttt_games[game_id]
            return
        
        else:
            turn_name = game.player1_name if game.current_turn == game.player1_id else game.player2_name
            turn_symbol = "âŒ" if game.current_turn == game.player1_id else "â­•"
            bet_text = f"ðŸ’° Bet: {game.bet:,} | Prize: {game.bet*2:,}" if game.bet > 0 else "ðŸŽ® Normal Game"
            await query.edit_message_text(f"ðŸŽ¯ TIC TAC TOE\nâŒ {game.player1_name} vs â­• {game.player2_name}\n{bet_text}\nðŸŽ¯ {turn_name}'s Turn ({turn_symbol})", reply_markup=game.get_keyboard())

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
        p1_emoji = {"rock": "âœŠ", "paper": "ðŸ“„", "scissors": "âœ‚ï¸"}[self.player1_choice]
        p2_emoji = {"rock": "âœŠ", "paper": "ðŸ“„", "scissors": "âœ‚ï¸"}[self.player2_choice]
        winner = self.check_winner()
        if winner == "draw":
            return f"{p1_emoji} {self.player1_name}: {self.player1_choice.upper()}\n{p2_emoji} {self.player2_name}: {self.player2_choice.upper()}\n\nðŸ¤ DRAW! ðŸ¤"
        else:
            winner_name = self.player1_name if winner == self.player1_id else self.player2_name
            return f"{p1_emoji} {self.player1_name}: {self.player1_choice.upper()}\n{p2_emoji} {self.player2_name}: {self.player2_choice.upper()}\n\nðŸ† WINNER: {winner_name.upper()} ðŸ†"

async def rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    chat_id = update.message.chat.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    args = context.args
    bet = 0
    if args:
        try:
            bet = int(args[0])
            if bet < 100:
                await update.message.reply_text("âŒ Minimum bet 100 credits!")
                return
        except:
            await update.message.reply_text("âŒ Invalid bet!")
            return
    if bet > 0:
        db = await get_db()
        balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
        if balance < bet:
            await update.message.reply_text(f"âŒ Need {bet:,} credits!")
            return
    global rps_next_id
    game_id = rps_next_id
    rps_next_id += 1
    rps_lobby[game_id] = {"creator_id": user_id, "creator_name": user_name, "bet": bet, "chat_id": chat_id}
    bet_text = f"ðŸ’° Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "ðŸŽ® Free Play"
    await update.message.reply_text(f"âœŠ ROCK PAPER SCISSORS\n\nðŸ‘‘ Host: {user_name}\n{bet_text}\n\nâš¡ Waiting for opponent...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ðŸ”µ JOIN", callback_data=f"rps_join_{game_id}")]]))

async def rps_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = query.data
    if data.startswith("rps_join_"):
        game_id = int(data.split("_")[2])
        if game_id not in rps_lobby:
            await query.edit_message_text("âŒ Lobby expired!")
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
                await query.answer(f"Need {bet} credits!", show_alert=True)
                return
            creator_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", creator_id)
            if creator_bal < bet:
                del rps_lobby[game_id]
                await query.edit_message_text("Game cancelled: creator has insufficient balance.")
                return
            async with db_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, creator_id)
                    await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", bet, user_id)
        game = RPSGame(game_id, creator_id, creator_name, bet, chat_id)
        game.player2_id = user_id
        game.player2_name = user_name
        game.game_active = True
        rps_games[game_id] = game
        del rps_lobby[game_id]
        keyboard = [
            [InlineKeyboardButton("âœŠ ROCK", callback_data=f"rps_move_{game_id}_rock")],
            [InlineKeyboardButton("ðŸ“„ PAPER", callback_data=f"rps_move_{game_id}_paper")],
            [InlineKeyboardButton("âœ‚ï¸ SCISSORS", callback_data=f"rps_move_{game_id}_scissors")]
        ]
        bet_text = f"ðŸ’° Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "ðŸŽ® Free Play"
        await query.edit_message_text(f"âœŠ RPS\n\n{creator_name} vs {user_name}\n{bet_text}\nðŸŽ¯ {creator_name}'s turn!", reply_markup=InlineKeyboardMarkup(keyboard))

async def rps_move_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    parts = data.split("_")
    game_id = int(parts[2])
    choice = parts[3]
    if game_id not in rps_games:
        await query.edit_message_text("âŒ Game not found!")
        return
    game = rps_games[game_id]
    if user_id != game.waiting_for:
        await query.answer("Not your turn!", show_alert=True)
        return
    if user_id == game.player1_id:
        game.player1_choice = choice
        game.waiting_for = game.player2_id
        keyboard = [
            [InlineKeyboardButton("âœŠ ROCK", callback_data=f"rps_move_{game_id}_rock")],
            [InlineKeyboardButton("ðŸ“„ PAPER", callback_data=f"rps_move_{game_id}_paper")],
            [InlineKeyboardButton("âœ‚ï¸ SCISSORS", callback_data=f"rps_move_{game_id}_scissors")]
        ]
        bet_text = f"ðŸ’° Bet: {game.bet:,} | Prize: {game.bet*2:,}" if game.bet > 0 else "ðŸŽ® Free Play"
        await query.edit_message_text(f"âœŠ RPS\n\n{game.player1_name} vs {game.player2_name}\n{bet_text}\nâœ… {game.player1_name} chose!\nðŸŽ¯ {game.player2_name}'s turn!", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        game.player2_choice = choice
        game.waiting_for = None
        game.game_active = False
        result_text = game.get_result_text()
        winner = game.check_winner()
        if game.bet > 0 and winner != "draw":
            db = await get_db()
            await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet*2, winner)
            winner_name = game.player1_name if winner == game.player1_id else game.player2_name
            result_text += f"\n\nðŸ’° Prize: {game.bet*2:,} credits\nðŸ† {winner_name} +{game.bet*2:,}"
        elif game.bet > 0 and winner == "draw":
            db = await get_db()
            await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player1_id)
            await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", game.bet, game.player2_id)
            result_text += f"\n\nðŸ’° Money returned: {game.bet:,} each"
        await query.edit_message_text(f"âœŠ RPS\n\n{result_text}")
        del rps_games[game_id]

async def rps_none_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Game Over!", show_alert=True)

# ============ ADMIN CRICKET COMMANDS ==========
async def addmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text('âŒ /addmatch TEAM1 vs TEAM2 YYYY-MM-DD')
        return
    team1 = args[0]
    team2 = args[2]
    date = args[3]
    db = await get_db()
    await db.execute("INSERT INTO matches (team1, team2, date, status, locked) VALUES ($1, $2, $3, 'upcoming', 0)", team1, team2, date)
    await update.message.reply_text(f"âœ… MATCH ADDED!\n\nðŸ {team1} vs {team2}\nðŸ“… {date}\nðŸ”“ Status: OPEN")

async def deletematch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('âŒ /deletematch TEAM1 vs TEAM2 [refund]')
        return
    team1 = args[0].upper()
    team2 = args[2].upper()
    do_refund = len(args) > 3 and args[3].lower() == 'refund'
    db = await get_db()
    match = await db.fetchrow("SELECT id, team1, team2 FROM matches WHERE team1 = $1 AND team2 = $2", team1, team2)
    if not match:
        await update.message.reply_text(f'âŒ Match not found!')
        return
    bets = await db.fetch("SELECT user_id, amount FROM bets WHERE match_id = $1", match['id'])
    refund_count = 0
    refund_total = 0
    if do_refund and bets:
        for bet in bets:
            await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", bet['amount'], bet['user_id'])
            refund_count += 1
            refund_total += bet['amount']
    await db.execute("DELETE FROM bets WHERE match_id = $1", match['id'])
    await db.execute("DELETE FROM matches WHERE id = $1", match['id'])
    if do_refund and refund_count > 0:
        await update.message.reply_text(f"ðŸ—‘ï¸ MATCH DELETED + REFUNDED!\n\nðŸ {match['team1']} vs {match['team2']}\nðŸ’° Refunded: {refund_count} users\nðŸ’° Total refund: {refund_total:,} credits")
    else:
        await update.message.reply_text(f"ðŸ—‘ï¸ MATCH DELETED!\n\nðŸ {match['team1']} vs {match['team2']}")

async def lockmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('âŒ /lockmatch TEAM1 vs TEAM2')
        return
    team1 = args[0].upper()
    team2 = args[2].upper()
    db = await get_db()
    match = await db.fetchrow("SELECT id, team1, team2 FROM matches WHERE team1 = $1 AND team2 = $2", team1, team2)
    if not match:
        await update.message.reply_text(f'âŒ Match not found!')
        return
    await db.execute("UPDATE matches SET locked = 1 WHERE id = $1", match['id'])
    total = await db.fetchval("SELECT COALESCE(SUM(amount), 0) FROM bets WHERE match_id = $1", match['id'])
    count = await db.fetchval("SELECT COUNT(*) FROM bets WHERE match_id = $1", match['id'])
    await update.message.reply_text(f"ðŸ”’ MATCH LOCKED!\n\nðŸ {match['team1']} vs {match['team2']}\nðŸ“Š Bets: {count}\nðŸ’° Pool: {total:,} ðŸ’°")

async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text('âŒ /result TEAM1 vs TEAM2 WINNER')
        return
    team1 = args[0].upper()
    team2 = args[2].upper()
    winner = args[3].upper()
    if winner not in [team1, team2]:
        await update.message.reply_text(f'âŒ Winner must be {team1} or {team2}!')
        return
    db = await get_db()
    match = await db.fetchrow("SELECT id, team1, team2 FROM matches WHERE team1 = $1 AND team2 = $2", team1, team2)
    if not match:
        await update.message.reply_text(f'âŒ Match not found!')
        return
    bets = await db.fetch("SELECT user_id, amount, team FROM bets WHERE match_id = $1", match['id'])
    winners = 0
    losers = 0
    total_paid = 0
    for bet in bets:
        user_id = bet['user_id']
        amount = bet['amount']
        bet_team = bet['team'].upper()
        user = await db.fetchrow("SELECT balance, won, points, name FROM users WHERE user_id = $1", user_id)
        if bet_team == winner:
            win_amount = amount * 2
            new_balance = user['balance'] + win_amount
            new_won = user['won'] + 1
            new_points = user['points'] + 10
            await db.execute("UPDATE users SET balance = $1, won = $2, points = $3 WHERE user_id = $4", new_balance, new_won, new_points, user_id)
            total_paid += win_amount
            winners += 1
        else:
            new_points = max(0, user['points'] - 5)  # Points never go below 0
            await db.execute("UPDATE users SET points = $1 WHERE user_id = $2", new_points, user_id)
            losers += 1
    await db.execute("DELETE FROM bets WHERE match_id = $1", match['id'])
    await db.execute("DELETE FROM matches WHERE id = $1", match['id'])
    await update.message.reply_text(f"ðŸ“¢ MATCH RESULT!\n\nðŸ {match['team1']} vs {match['team2']}\nðŸ† WINNER: {winner}\n\nâœ… WINNERS (+10 pts): {winners} users\nâŒ LOSERS (-5 pts): {losers} users\n\nðŸ’° TOTAL PAYOUT: {total_paid:,} ðŸ’°")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    if not update.message.reply_to_message:
        await update.message.reply_text('âŒ Reply to user with /add AMOUNT')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /add AMOUNT')
        return
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid amount')
        return
    target = update.message.reply_to_message.from_user
    db = await get_db()
    old = await db.fetchrow("SELECT balance, name FROM users WHERE user_id = $1", target.id)
    if not old:
        await update.message.reply_text('âŒ User not found!')
        return
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, target.id)
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", target.id)
    await update.message.reply_text(f"âœ… ADDED {amount:,} to {old['name']}\nðŸ’° Balance: {old['balance']:,} â†’ {new_bal:,} ðŸ’°")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    if not update.message.reply_to_message:
        await update.message.reply_text('âŒ Reply to user with /remove AMOUNT')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /remove AMOUNT')
        return
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid amount')
        return
    target = update.message.reply_to_message.from_user
    db = await get_db()
    old = await db.fetchrow("SELECT balance, name FROM users WHERE user_id = $1", target.id)
    if not old:
        await update.message.reply_text('âŒ User not found!')
        return
    if old['balance'] < amount:
        await update.message.reply_text(f'âŒ Insufficient! Balance: {old["balance"]:,} ðŸ’°')
        return
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", amount, target.id)
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", target.id)
    await update.message.reply_text(f"âŒ REMOVED {amount:,} from {old['name']}\nðŸ’° Balance: {old['balance']:,} â†’ {new_bal:,} ðŸ’°")

# ============ HALL OF FAME ==========
async def hof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    winners = await db.fetch("SELECT id, winner FROM hall_of_fame ORDER BY id ASC")
    if not winners:
        await update.message.reply_text("ðŸ† HALL OF FAME ðŸ†\n\nNo winners yet!")
        return
    msg = "ðŸ† HALL OF FAME ðŸ†\n\n"
    for i, w in enumerate(winners, 1):
        msg += f"{i}. {w['winner']}\n"
    msg += f"\nðŸ“Š Total Winners: {len(winners)}"
    await update.message.reply_text(msg)

async def addhof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /addhof <winner_name>")
        return
    winner = " ".join(args)
    db = await get_db()
    await db.execute("INSERT INTO hall_of_fame (winner, added_by, added_at) VALUES ($1, $2, $3)", winner, update.effective_user.id, datetime.now().isoformat())
    count = await db.fetchval("SELECT COUNT(*) FROM hall_of_fame")
    await update.message.reply_text(f"âœ… Added to Hall of Fame!\n\nðŸ† {winner}\n\nðŸ“Š Total Winners: {count}")

async def rmhof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /rmhof <number>")
        return
    try:
        num = int(args[0])
    except:
        await update.message.reply_text("âŒ Invalid number!")
        return
    db = await get_db()
    winners = await db.fetch("SELECT id, winner FROM hall_of_fame ORDER BY id ASC")
    if num < 1 or num > len(winners):
        await update.message.reply_text(f"âŒ Invalid! Choose 1-{len(winners)}")
        return
    winner_id = winners[num-1]['id']
    winner_text = winners[num-1]['winner']
    await db.execute("DELETE FROM hall_of_fame WHERE id = $1", winner_id)
    count = await db.fetchval("SELECT COUNT(*) FROM hall_of_fame")
    await update.message.reply_text(f"ðŸ—‘ï¸ Removed from Hall of Fame!\n\nâŒ Removed: {winner_text}\n\nðŸ“Š Total Winners: {count}")

async def edithof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /edithof <number> <new_text>")
        return
    try:
        num = int(args[0])
        new_text = " ".join(args[1:])
    except:
        await update.message.reply_text("âŒ Invalid number!")
        return
    db = await get_db()
    winners = await db.fetch("SELECT id, winner FROM hall_of_fame ORDER BY id ASC")
    if num < 1 or num > len(winners):
        await update.message.reply_text(f"âŒ Invalid! Choose 1-{len(winners)}")
        return
    winner_id = winners[num-1]['id']
    old_text = winners[num-1]['winner']
    await db.execute("UPDATE hall_of_fame SET winner = $1 WHERE id = $2", new_text, winner_id)
    await update.message.reply_text(f"âœï¸ EDITED HALL OF FAME!\n\nâŒ Old: {old_text}\nâœ… New: {new_text}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    await update.message.reply_text("ðŸ“ Pong!")

# ============ SHOP2 ==========
async def shop2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    players = await db.fetch("SELECT id, name, price FROM shop2 ORDER BY price ASC")
    if not players:
        await update.message.reply_text('ðŸ›’ AFFORDABLE SHOP\n\nNo players yet.\nðŸ‘‘ Admin: /addplayer2 <name> <price>')
        return
    msg = "ðŸ›’ AFFORDABLE PLAYERS SHOP\n\n"
    for p in players:
        msg += f"{p['id']}. {p['name']} - {p['price']:,} ðŸ’°\n"
    msg += "\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’¡ /buy2 <id> to purchase"
    await update.message.reply_text(msg)

async def buy2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /buy2 <player_id>')
        return
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid ID')
        return
    db = await get_db()
    player = await db.fetchrow("SELECT name, price FROM shop2 WHERE id = $1", player_id)
    if not player:
        await update.message.reply_text(f'âŒ Player ID {player_id} not found!')
        return
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    if balance < player['price']:
        await update.message.reply_text(f'âŒ Need {player["price"]:,}, have {balance:,}')
        return
    owned = await db.fetchval("SELECT user_id FROM user_players2 WHERE user_id = $1 AND player_id = $2", user_id, player_id)
    if owned:
        await update.message.reply_text(f'âŒ You already own {player["name"]}!')
        return
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", player['price'], user_id)
    await db.execute("INSERT INTO user_players2 (user_id, player_id) VALUES ($1, $2)", user_id, player_id)
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await update.message.reply_text(f"âœ… PURCHASED!\n\nðŸ {player['name']}\nðŸ’° Price: {player['price']:,} ðŸ’°\nðŸ“Š New balance: {new_bal:,} ðŸ’°")

async def myteam2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    players = await db.fetch("SELECT s.name, s.price FROM user_players2 u JOIN shop2 s ON u.player_id = s.id WHERE u.user_id = $1", user_id)
    if not players:
        await update.message.reply_text('ðŸ“­ No affordable players owned.\nUse /shop2 to buy!')
        return
    total = sum(p['price'] for p in players)
    msg = "ðŸ›ï¸ MY AFFORDABLE PLAYERS\n\n"
    for i, p in enumerate(players, 1):
        msg += f"{i}. {p['name']} - {p['price']:,} ðŸ’°\n"
    msg += f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’° Total spent: {total:,} ðŸ’°"
    await update.message.reply_text(msg)

async def top2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    tops = await db.fetch("SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(s.price), 0) as total FROM users u JOIN user_players2 up ON u.user_id = up.user_id JOIN shop2 s ON up.player_id = s.id GROUP BY u.user_id ORDER BY total DESC LIMIT 10")
    if not tops:
        await update.message.reply_text('ðŸ† AFFORDABLE PLAYERS TOP\n\nNo one owns any yet!')
        return
    msg = "ðŸ† AFFORDABLE PLAYERS TOP\n\n"
    for i, t in enumerate(tops, 1):
        medal = "ðŸ‘‘" if i==1 else "ðŸ¥ˆ" if i==2 else "ðŸ¥‰" if i==3 else f"{i}."
        msg += f"{medal} {t['name']} - {t['count']} players ({t['total']:,} ðŸ’°)\n"
    await update.message.reply_text(msg)

async def addplayer2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('âŒ /addplayer2 <name> <price>')
        return
    name = ' '.join(args[:-1])
    try:
        price = int(args[-1])
    except:
        await update.message.reply_text('âŒ Invalid price!')
        return
    db = await get_db()
    await db.execute("INSERT INTO shop2 (name, price) VALUES ($1, $2)", name, price)
    player_id = await db.fetchval("SELECT lastval()")
    await update.message.reply_text(f"âœ… PLAYER ADDED!\n\nID: {player_id} | {name}\nðŸ’° Price: {price:,} ðŸ’°")

# ============ SHOP3 ==========
async def shop3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    players = await db.fetch("SELECT id, name, price FROM shop3 ORDER BY price ASC")
    if not players:
        await update.message.reply_text('ðŸ›’ SHOP3\n\nNo players yet.\nðŸ‘‘ Admin: /addplayer3 <name> <price>')
        return
    msg = "ðŸ›’ SHOP3\n\n"
    for p in players:
        msg += f"{p['id']}. {p['name']} - {p['price']:,} ðŸ’°\n"
    msg += "\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’¡ /buy3 <id> to purchase"
    await update.message.reply_text(msg)

async def buy3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /buy3 <player_id>')
        return
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid ID')
        return
    db = await get_db()
    player = await db.fetchrow("SELECT name, price FROM shop3 WHERE id = $1", player_id)
    if not player:
        await update.message.reply_text(f'âŒ Player ID {player_id} not found!')
        return
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    if balance < player['price']:
        await update.message.reply_text(f'âŒ Need {player["price"]:,}, have {balance:,}')
        return
    owned = await db.fetchval("SELECT user_id FROM user_players3 WHERE user_id = $1 AND player_id = $2", user_id, player_id)
    if owned:
        await update.message.reply_text(f'âŒ You already own {player["name"]}!')
        return
    await db.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", player['price'], user_id)
    await db.execute("INSERT INTO user_players3 (user_id, player_id) VALUES ($1, $2)", user_id, player_id)
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await update.message.reply_text(f"âœ… PURCHASED!\n\nðŸ {player['name']}\nðŸ’° Price: {player['price']:,} ðŸ’°\nðŸ“Š New balance: {new_bal:,} ðŸ’°")

async def myteam3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    players = await db.fetch("SELECT s.name, s.price FROM user_players3 u JOIN shop3 s ON u.player_id = s.id WHERE u.user_id = $1", user_id)
    if not players:
        await update.message.reply_text('ðŸ“­ No shop3 players owned.\nUse /shop3 to buy!')
        return
    total = sum(p['price'] for p in players)
    msg = "ðŸ’Ž MY SHOP3 PLAYERS\n\n"
    for i, p in enumerate(players, 1):
        msg += f"{i}. {p['name']} - {p['price']:,} ðŸ’°\n"
    msg += f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’° Total spent: {total:,} ðŸ’°"
    await update.message.reply_text(msg)

async def top3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    tops = await db.fetch("SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(s.price), 0) as total FROM users u JOIN user_players3 up ON u.user_id = up.user_id JOIN shop3 s ON up.player_id = s.id GROUP BY u.user_id ORDER BY total DESC LIMIT 10")
    if not tops:
        await update.message.reply_text('ðŸ† SHOP3 TOP COLLECTORS\n\nNo one owns any yet!')
        return
    msg = "ðŸ† SHOP3 TOP COLLECTORS\n\n"
    for i, t in enumerate(tops, 1):
        medal = "ðŸ‘‘" if i==1 else "ðŸ¥ˆ" if i==2 else "ðŸ¥‰" if i==3 else f"{i}."
        msg += f"{medal} {t['name']} - {t['count']} players ({t['total']:,} ðŸ’°)\n"
    await update.message.reply_text(msg)

async def addplayer3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('âŒ /addplayer3 <name> <price>')
        return
    name = ' '.join(args[:-1])
    try:
        price = int(args[-1])
    except:
        await update.message.reply_text('âŒ Invalid price!')
        return
    db = await get_db()
    await db.execute("INSERT INTO shop3 (name, price) VALUES ($1, $2)", name, price)
    await update.message.reply_text(f"âœ… PLAYER ADDED TO SHOP3!\n\n{name}\nðŸ’° Price: {price:,} ðŸ’°")

# ============ SHOP4 ==========
async def shop4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    players = await db.fetch("SELECT id, name, price FROM shop4 ORDER BY price ASC")
    if not players:
        await update.message.reply_text('ðŸ›’ SHOP4\n\nNo players yet.\nðŸ‘‘ Admin: /addplayer4 <name> <price>')
        return
    msg = "ðŸ›’ SHOP4\n\n"
    for p in players:
        msg += f"{p['id']}. {p['name']} - {p['price']:,} ðŸ’°\n"
    msg += "\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’¡ /buy4 <id> to purchase"
    await update.message.reply_text(msg)

async def buy4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /buy4 <player_id>')
        return
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid ID')
        return
    db = await get_db()
    player = await db.fetchrow("SELECT name, price FROM shop4 WHERE id = $1", player_id)
    if not player:
        await update.message.reply_text(f'âŒ Player ID {player_id} not found!')
        return
    balance = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    if balance < player['price']:
        await update.message.reply_text(f'âŒ Need {player["price"]:,}, have {balance:,}')
        return
    owned = await db.fetchval("SELECT user_id FROM user_players4 WHERE user_id = $1 AND player_id = $2", user_id, player_id)
    if owned:
        await update.message.reply_text(f'âŒ You already own {player["name"]}!')
        return
    # Atomic transaction to prevent double-spend
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            cur_bal = await conn.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
            if cur_bal < player['price']:
                await update.message.reply_text("Insufficient balance!")
                return
            already = await conn.fetchval("SELECT user_id FROM user_players4 WHERE user_id = $1 AND player_id = $2", user_id, player_id)
            if already:
                await update.message.reply_text("You already own this player!")
                return
            await conn.execute("UPDATE users SET balance = balance - $1 WHERE user_id = $2", player['price'], user_id)
            await conn.execute("INSERT INTO user_players4 (user_id, player_id) VALUES ($1, $2)", user_id, player_id)
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await update.message.reply_text(f"âœ… PURCHASED!\n\nðŸ {player['name']}\nðŸ’° Price: {player['price']:,} ðŸ’°\nðŸ“Š New balance: {new_bal:,} ðŸ’°")

async def myteam4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    players = await db.fetch("SELECT s.name, s.price FROM user_players4 u JOIN shop4 s ON u.player_id = s.id WHERE u.user_id = $1", user_id)
    if not players:
        await update.message.reply_text('ðŸ“­ No shop4 players owned.\nUse /shop4 to buy!')
        return
    total = sum(p['price'] for p in players)
    msg = "ðŸ¤‘ MY SHOP4 PLAYERS\n\n"
    for i, p in enumerate(players, 1):
        msg += f"{i}. {p['name']} - {p['price']:,} ðŸ’°\n"
    msg += f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’° Total spent: {total:,} ðŸ’°"
    await update.message.reply_text(msg)

async def top4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    tops = await db.fetch("SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(s.price), 0) as total FROM users u JOIN user_players4 up ON u.user_id = up.user_id JOIN shop4 s ON up.player_id = s.id GROUP BY u.user_id ORDER BY total DESC LIMIT 10")
    if not tops:
        await update.message.reply_text('ðŸ† SHOP4 TOP COLLECTORS\n\nNo one owns any yet!')
        return
    msg = "ðŸ† SHOP4 TOP COLLECTORS\n\n"
    for i, t in enumerate(tops, 1):
        medal = "ðŸ‘‘" if i==1 else "ðŸ¥ˆ" if i==2 else "ðŸ¥‰" if i==3 else f"{i}."
        msg += f"{medal} {t['name']} - {t['count']} players ({t['total']:,} ðŸ’°)\n"
    await update.message.reply_text(msg)

async def addplayer4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('âŒ Admin only!')
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('âŒ /addplayer4 <name> <price>')
        return
    name = ' '.join(args[:-1])
    try:
        price = int(args[-1])
    except:
        await update.message.reply_text('âŒ Invalid price!')
        return
    db = await get_db()
    await db.execute("INSERT INTO shop4 (name, price) VALUES ($1, $2)", name, price)
    await update.message.reply_text(f"âœ… PLAYER ADDED TO SHOP4!\n\n{name}\nðŸ’° Price: {price:,} ðŸ’°")

# ============ CLAIM CODES ==========
async def createcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("ðŸ“ Usage: /createcode <amount> <code>\nExample: /createcode 1000 FESTIVAL10")
        return
    try:
        amount = int(args[0])
        code = args[1].upper()
    except:
        await update.message.reply_text("âŒ Invalid!")
        return
    if amount < 100:
        await update.message.reply_text("âŒ Minimum amount 100 credits!")
        return
    db = await get_db()
    exists = await db.fetchval("SELECT code FROM claim_codes WHERE code = $1", code)
    if exists:
        await update.message.reply_text(f"âŒ Code '{code}' already exists!")
        return
    now = datetime.now()
    expires_at = now + timedelta(hours=24)
    await db.execute("INSERT INTO claim_codes (code, amount, max_claims, created_by, created_at, expires_at) VALUES ($1, $2, 5, $3, $4, $5)", code, amount, update.effective_user.id, now.isoformat(), expires_at.isoformat())
    await update.message.reply_text(f"âœ… CODE CREATED!\n\nðŸ”‘ Code: {code}\nðŸ’° Amount: {amount:,} credits\nðŸ‘¥ Max claims: 5 users\nâ° Expires: 24 hours\n\nClaim: /claimcode {code}")

async def claimcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("âŒ Usage: /claimcode <code>")
        return
    code = args[0].upper()
    db = await get_db()
    result = await db.fetchrow("SELECT code, amount, max_claims, claimed_count, expires_at FROM claim_codes WHERE code = $1", code)
    if not result:
        await update.message.reply_text(f"âŒ Code '{code}' not found!")
        return
    expires = datetime.fromisoformat(result['expires_at'])
    if datetime.now() > expires:
        await update.message.reply_text(f"âŒ Code '{code}' expired!")
        return
    claimed = await db.fetchval("SELECT code FROM code_claims WHERE code = $1 AND user_id = $2", code, user_id)
    if claimed:
        await update.message.reply_text(f"âŒ You already claimed '{code}'!")
        return
    if result['claimed_count'] >= result['max_claims']:
        await update.message.reply_text(f"âŒ Code '{code}' max claims reached!")
        return
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", result['amount'], user_id)
    await db.execute("UPDATE claim_codes SET claimed_count = claimed_count + 1 WHERE code = $1", code)
    await db.execute("INSERT INTO code_claims (code, user_id, claimed_at) VALUES ($1, $2, $3)", code, user_id, datetime.now().isoformat())
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    remaining = result['max_claims'] - (result['claimed_count'] + 1)
    await update.message.reply_text(f"ðŸŽ‰ CODE CLAIMED!\n\nðŸ”‘ Code: {code}\nðŸ’° +{result['amount']:,} credits\nðŸ’³ New balance: {new_bal:,}\nðŸ“Š Remaining: {remaining}/{result['max_claims']}")

async def activecodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    codes = await db.fetch("SELECT code, amount, max_claims, claimed_count, expires_at FROM claim_codes WHERE expires_at::timestamp > now() AND claimed_count < max_claims ORDER BY created_at::timestamp DESC LIMIT 10")
    if not codes:
        await update.message.reply_text("ðŸ“­ NO ACTIVE CODES")
        return
    msg = "ðŸŽ ACTIVE CLAIM CODES\n\n"
    for code in codes:
        remaining = code['max_claims'] - code['claimed_count']
        msg += f"ðŸ”‘ {code['code']}\nðŸ’° {code['amount']:,} credits\nðŸ‘¥ {remaining}/{code['max_claims']} left\nðŸ’¡ /claimcode {code['code']}\n\n"
    await update.message.reply_text(msg)

# ============ NUMBER GUESS GAME ==========
game_data = {}

async def numguess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    if chat_id in game_data:
        await update.message.reply_text(f"âŒ Game active! Started by: {game_data[chat_id]['player_name']}\nUse /ngstop to stop.")
        return
    number = random.randint(1, 100)
    game_data[chat_id] = {"number": number, "attempts": 0, "player_id": user_id, "player_name": user_name, "chat_id": chat_id}
    await update.message.reply_text(f"ðŸŽ² Number Guessing Game!\nðŸ‘¤ Host: {user_name}\nðŸ“Š Number 1-100\nðŸ’¡ /ng <number> to guess!\nðŸ›‘ /ngstop to end")

async def ng(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    if chat_id not in game_data:
        await update.message.reply_text("âŒ No active game! Use /numguess")
        return
    game = game_data[chat_id]
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("âŒ /ng <number>")
        return
    try:
        guess = int(args[0])
    except:
        await update.message.reply_text("âŒ Invalid number!")
        return
    if guess < 1 or guess > 100:
        await update.message.reply_text("âŒ Number 1-100!")
        return
    game["attempts"] += 1
    target = game["number"]
    if guess == target:
        attempts = game["attempts"]
        user_name = update.effective_user.first_name
        if attempts == 1:
            reward = 5000
            msg = f"PERFECT! {user_name} guessed {target} in FIRST attempt! +{reward} coins!"
        elif attempts <= 3:
            reward = 2000
            msg = f"ðŸŽ‰ AMAZING! +{reward} coins!"
        elif attempts <= 5:
            reward = 1000
            msg = f"ðŸŽ‰ EXCELLENT! +{reward} coins!"
        elif attempts <= 7:
            reward = 500
            msg = f"ðŸŽ‰ GOOD JOB! +{reward} coins!"
        elif attempts <= 10:
            reward = 300
            msg = f"ðŸŽ‰ NOT BAD! +{reward} coins!"
        elif attempts <= 15:
            reward = 150
            msg = f"ðŸŽ‰ OKAY! +{reward} coins!"
        else:
            reward = 50
            msg = f"ðŸŽ‰ FINALLY! +{reward} coins!"
        db = await get_db()
        await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", reward, user_id)
        del game_data[chat_id]
        await update.message.reply_text(msg)
    elif guess < target:
        await update.message.reply_text(f"ðŸ“ˆ Too low! Attempts: {game['attempts']}")
    else:
        await update.message.reply_text(f"ðŸ“‰ Too high! Attempts: {game['attempts']}")

async def ngstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    if chat_id not in game_data:
        await update.message.reply_text("âŒ No active game!")
        return
    game = game_data[chat_id]
    if user_id not in ADMIN_IDS and game["player_id"] != user_id:
        await update.message.reply_text("âŒ Only host or admin can stop!")
        return
    target = game["number"]
    attempts = game["attempts"]
    host_name = game["player_name"]
    del game_data[chat_id]
    await update.message.reply_text(f"ðŸ›‘ Game Stopped!\nðŸ‘¤ Host: {host_name}\nðŸ”¢ Number was: {target}\nðŸ“Š Attempts: {attempts}")

# ============ GROUP TRACKING ==========
async def track_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        group_id = update.message.chat.id
        group_name = update.message.chat.title or "Unknown Group"
        db = await get_db()
        await db.execute("INSERT INTO groups (group_id, group_name, added_at) VALUES ($1, $2, $3) ON CONFLICT (group_id) DO NOTHING", group_id, group_name, datetime.now().isoformat())

# ============ BROADCAST ==========
async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    msg = update.message
    db = await get_db()
    users = [row['user_id'] for row in await db.fetch("SELECT user_id FROM users")]
    groups = [row['group_id'] for row in await db.fetch("SELECT group_id FROM groups")]
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
        await update.message.reply_text(f"ðŸ“¸ BROADCAST SENT! Total: {sent}")
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
    await update.message.reply_text(f"ðŸ“¢ BROADCAST SENT! Total: {sent}")

async def broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("âŒ Admin only!")
        return
    db = await get_db()
    users = await db.fetchval("SELECT COUNT(*) FROM users")
    groups = await db.fetchval("SELECT COUNT(*) FROM groups")
    await update.message.reply_text(f"ðŸ“Š BROADCAST STATS\n\nðŸ‘¤ Users: {users}\nðŸ‘¥ Groups: {groups}\nðŸ“¡ Total: {users + groups}")

# ============ STATS ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    keyboard = [
        [InlineKeyboardButton("ðŸ MOST RUNS", callback_data="stats_runs")],
        [InlineKeyboardButton("ðŸŽ¯ MOST WICKETS", callback_data="stats_wickets")],
        [InlineKeyboardButton("â­ HIGHEST SCORE", callback_data="stats_highest")],
        [InlineKeyboardButton("âœ… MOST WINS", callback_data="stats_wins")],
        [InlineKeyboardButton("âŒ MOST LOSSES", callback_data="stats_losses")],
    ]
    await update.message.reply_text("ðŸ CRICKET STATS\nSelect:", reply_markup=InlineKeyboardMarkup(keyboard))

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    db = await get_db()
    if data == "stats_runs":
        top = await db.fetch("SELECT name, runs FROM cricket_stats ORDER BY runs DESC LIMIT 5")
        msg = "ðŸ MOST RUNS\n\n"
        for i, t in enumerate(top, 1):
            msg += f"{i}. {t['name']} - {t['runs']} runs\n"
    elif data == "stats_wickets":
        top = await db.fetch("SELECT name, wickets FROM cricket_stats ORDER BY wickets DESC LIMIT 5")
        msg = "ðŸŽ¯ MOST WICKETS\n\n"
        for i, t in enumerate(top, 1):
            msg += f"{i}. {t['name']} - {t['wickets']} wickets\n"
    elif data == "stats_highest":
        top = await db.fetch("SELECT name, highest_score FROM cricket_stats ORDER BY highest_score DESC LIMIT 5")
        msg = "â­ HIGHEST SCORE\n\n"
        for i, t in enumerate(top, 1):
            msg += f"{i}. {t['name']} - {t['highest_score']} runs\n"
    elif data == "stats_wins":
        top = await db.fetch("SELECT name, wins FROM cricket_stats ORDER BY wins DESC LIMIT 5")
        msg = "âœ… MOST WINS\n\n"
        for i, t in enumerate(top, 1):
            msg += f"{i}. {t['name']} - {t['wins']} wins\n"
    elif data == "stats_losses":
        top = await db.fetch("SELECT name, losses FROM cricket_stats ORDER BY losses DESC LIMIT 5")
        msg = "âŒ MOST LOSSES\n\n"
        for i, t in enumerate(top, 1):
            msg += f"{i}. {t['name']} - {t['losses']} losses\n"
    else:
        return
    await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("â—€ï¸ BACK", callback_data="stats_back")]]))

async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    stats = await db.fetchrow("SELECT runs, wickets, highest_score, wins, losses FROM cricket_stats WHERE user_id = $1", user_id)
    if not stats:
        await update.message.reply_text("ðŸ YOUR CRICKET STATS\n\nNo stats yet! Play /CLcricket")
        return
    msg = f"ðŸ YOUR CRICKET STATS\n\n"
    msg += f"ðŸ Runs: {stats['runs']}\n"
    msg += f"ðŸŽ¯ Wickets: {stats['wickets']}\n"
    msg += f"â­ Highest: {stats['highest_score']}\n"
    msg += f"âœ… Wins: {stats['wins']}\n"
    msg += f"âŒ Losses: {stats['losses']}"
    await update.message.reply_text(msg)

# ============ MATCHES, BET, MYBETS, CANCEL, ALLBETS, HISTORY ==========
async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    matches_data = await db.fetch("SELECT id, team1, team2, date, locked FROM matches WHERE locked = 0")
    if not matches_data:
        await update.message.reply_text('ðŸ“­ No active matches')
        return
    msg = "ðŸ LIVE MATCHES\n\n"
    for m in matches_data:
        status = "ðŸ”“ OPEN" if m['locked'] == 0 else "ðŸ”’ LOCKED"
        msg += f"ðŸ”¥ {m['team1']} vs {m['team2']}\nðŸ“… {m['date']} | {status}\nðŸ’° /bet {m['team1']} <amount> | /bet {m['team2']} <amount>\n\n"
    user = await get_user(user_id)
    msg += f"â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’° Your balance: {user['balance']:,} ðŸ’°"
    await update.message.reply_text(msg)

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('âŒ /bet TEAM AMOUNT')
        return
    team = args[0].upper()
    try:
        amount = int(args[1])
    except:
        await update.message.reply_text('âŒ Invalid amount')
        return
    if amount < 100:
        await update.message.reply_text('âŒ Minimum 100 credits')
        return
    user = await get_user(user_id)
    if user['balance'] < amount:
        await update.message.reply_text(f'âŒ Need {amount:,}, have {user["balance"]:,}')
        return
    db = await get_db()
    match = await db.fetchrow("SELECT id, team1, team2, locked FROM matches WHERE (team1 = $1 OR team2 = $1) AND locked = 0", team)
    if not match:
        await update.message.reply_text(f'âŒ Match with {team} not found!')
        return
    if match['locked'] == 1:
        await update.message.reply_text(f'ðŸ”’ Betting closed!')
        return
    bet_count = await db.fetchval("SELECT COUNT(*) FROM bets WHERE user_id = $1 AND match_id = $2", user_id, match['id'])
    if bet_count >= 2:
        await update.message.reply_text("âŒ Max 2 bets per match!")
        return
    # Atomic transaction: insert bet + deduct balance together
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            # Re-check balance inside transaction
            current_bal = await conn.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
            if current_bal < amount:
                await update.message.reply_text(f"Insufficient balance! Have {current_bal:,}, need {amount:,}")
                return
            # Re-check bet count inside transaction
            bet_count2 = await conn.fetchval("SELECT COUNT(*) FROM bets WHERE user_id = $1 AND match_id = $2", user_id, match['id'])
            if bet_count2 >= 2:
                await update.message.reply_text("Max 2 bets per match!")
                return
            await conn.execute("INSERT INTO bets (user_id, match_id, team, amount) VALUES ($1, $2, $3, $4)", user_id, match['id'], team, amount)
            await conn.execute("UPDATE users SET balance = balance - $1, total = total + 1 WHERE user_id = $2", amount, user_id)
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await update.message.reply_text(f"âœ… BET PLACED!\n\nðŸ {match['team1']} vs {match['team2']}\nðŸŽ¯ {team}\nðŸ’° {amount:,} ðŸ’°\nðŸ“Š New balance: {new_bal:,} ðŸ’°")

async def mybets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    bets_data = await db.fetch("""
        SELECT b.id, b.team, b.amount, m.team1, m.team2, m.date
        FROM bets b JOIN matches m ON b.match_id = m.id 
        WHERE b.user_id = $1 AND m.locked = 0
    """, user_id)
    if not bets_data:
        await update.message.reply_text('ðŸ“­ No active bets')
        return
    msg = f"ðŸŽ¯ MY ACTIVE BETS ({len(bets_data)})\n\n"
    for i, bet in enumerate(bets_data, 1):
        msg += f"{i}ï¸âƒ£ {bet['team1']} vs {bet['team2']}\n   ðŸŽ¯ {bet['team']} | ðŸ’° {bet['amount']:,}\n   ðŸ“… {bet['date']}\n\n"
    msg += "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ’¡ /cancel <number>"
    await update.message.reply_text(msg)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('âŒ /cancel <bet_number>')
        return
    try:
        bet_number = int(args[0])
    except:
        await update.message.reply_text('âŒ Invalid number')
        return
    db = await get_db()
    bets_data = await db.fetch("""
        SELECT b.id, b.amount, m.team1, m.team2, m.locked
        FROM bets b JOIN matches m ON b.match_id = m.id 
        WHERE b.user_id = $1 AND m.locked = 0
    """, user_id)
    if bet_number < 1 or bet_number > len(bets_data):
        await update.message.reply_text(f'âŒ Choose 1-{len(bets_data)}')
        return
    bet_to_cancel = bets_data[bet_number - 1]
    await db.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", bet_to_cancel['amount'], user_id)
    await db.execute("DELETE FROM bets WHERE id = $1", bet_to_cancel['id'])
    await db.execute("UPDATE users SET total = total - 1 WHERE user_id = $1", user_id)
    new_bal = await db.fetchval("SELECT balance FROM users WHERE user_id = $1", user_id)
    await update.message.reply_text(f"âœ… BET CANCELLED!\n\nðŸ {bet_to_cancel['team1']} vs {bet_to_cancel['team2']}\nðŸ’° Refund: {bet_to_cancel['amount']:,} ðŸ’°\nðŸ“Š New balance: {new_bal:,} ðŸ’°")

async def allbets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    db = await get_db()
    matches_data = await db.fetch("SELECT id, team1, team2 FROM matches WHERE locked = 0")
    if not matches_data:
        await update.message.reply_text('ðŸ“­ No active bets')
        return
    full_msg = "ðŸ“Š ALL BETS\n\n"
    for match in matches_data:
        bets_data = await db.fetch("SELECT b.team, b.amount, u.name FROM bets b JOIN users u ON b.user_id = u.user_id WHERE b.match_id = $1", match['id'])
        if not bets_data:
            continue
        team1_amount = 0
        team2_amount = 0
        team1_users = []
        team2_users = []
        for bet in bets_data:
            if bet['team'] == match['team1']:
                team1_amount += bet['amount']
                team1_users.append(f"{bet['name']} - {bet['amount']:,}")
            else:
                team2_amount += bet['amount']
                team2_users.append(f"{bet['name']} - {bet['amount']:,}")
        full_msg += f"ðŸ {match['team1']} vs {match['team2']}\n"
        full_msg += f"ðŸŽ¯ {match['team1']}: {team1_amount:,} ðŸ’°\n"
        for u in team1_users[:3]:
            full_msg += f"   â€¢ {u}\n"
        full_msg += f"\nðŸŽ¯ {match['team2']}: {team2_amount:,} ðŸ’°\n"
        for u in team2_users[:3]:
            full_msg += f"   â€¢ {u}\n"
        full_msg += f"\nðŸ’£ Total Pool: {team1_amount + team2_amount:,} ðŸ’°\n\n"
    await update.message.reply_text(full_msg)

# ============ HISTORY ==========
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_registered(user_id):
        await update.message.reply_text('âŒ Send /start first!')
        return
    
    db = await get_db()
    user = await db.fetchrow("SELECT won, total, points FROM users WHERE user_id = $1", user_id)
    
    if not user:
        await update.message.reply_text('âŒ User not found!')
        return
    
    win_rate = int(user['won'] / user['total'] * 100) if user['total'] > 0 else 0
    lost = user['total'] - user['won']
    
    msg = f"ðŸ“œ BET HISTORY\n\n"
    msg += f"âœ… Won: {user['won']}\n"
    msg += f"âŒ Lost: {lost}\n"
    msg += f"ðŸ“Š Win Rate: {win_rate}%\n\n"
    msg += f"ðŸ† Fantasy Points: {user['points']}"
    
    await update.message.reply_text(msg)

# ============ DAILY ==========

# ============ MAIN ==========
# ============ GLOBAL ERROR HANDLER ==========
async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Silently handle known Telegram API errors; log unexpected ones."""
    from telegram.error import TimedOut, BadRequest, NetworkError, Forbidden
    import traceback
    
    error = context.error
    
    # --- Silently ignore expected/harmless Telegram errors ---
    if isinstance(error, TimedOut):
        return  # Network timeout - Telegram will retry delivery
    
    if isinstance(error, Forbidden):
        return  # Bot was blocked/kicked - nothing to do
    
    if isinstance(error, BadRequest):
        msg = str(error)
        # Old callback query - happens when bot restarts with existing keyboards
        if "query is too old" in msg.lower() or "query id is invalid" in msg.lower():
            return
        # Bot has no send permissions in a group
        if "not enough rights" in msg.lower():
            return
        # Message was deleted before bot could edit it
        if "message to edit not found" in msg.lower() or "message can't be edited" in msg.lower():
            return
        # Chat was deleted or migrated
        if "chat not found" in msg.lower():
            return
    
    if isinstance(error, NetworkError):
        return  # Transient network issue - PTB will retry
    
    # --- Log unexpected errors ---
    tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    print(f"[ERROR] Unhandled exception in update handler:\n{tb}")


async def main():
    await init_db()
    
    app = Application.builder().token(TOKEN).build()

    # User commands
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
    app.add_handler(CommandHandler("achievements", achievements))
    app.add_handler(CommandHandler("numguess", numguess))
    app.add_handler(CommandHandler("ng", ng))
    app.add_handler(CommandHandler("ngstop", ngstop))

    # Shop commands
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("buyw", buyw))
    app.add_handler(CommandHandler("myteam", myteam))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_"))

    # RPS Game
    app.add_handler(CommandHandler("rps", rps))
    app.add_handler(CallbackQueryHandler(rps_join_callback, pattern="^rps_join_"))
    app.add_handler(CallbackQueryHandler(rps_move_callback, pattern="^rps_move_"))
    app.add_handler(CallbackQueryHandler(rps_none_callback, pattern="^rps_none"))
    # Hilo Game
    app.add_handler(CommandHandler("hilo", hilo))
    app.add_handler(CallbackQueryHandler(hilo_callback, pattern="^hilo_"))
    # Lottery
    app.add_handler(CommandHandler("lottery", lottery))
    app.add_handler(CommandHandler("buy_ticket", buy_ticket))
    app.add_handler(CommandHandler("mytickets", mytickets_command))
    app.add_handler(CommandHandler("lottery_info", lottery_info_command))
    app.add_handler(CommandHandler("start_lottery", start_lottery))
    app.add_handler(CommandHandler("draw_winner", draw_winner))
    app.add_handler(CommandHandler("reset_lottery", reset_lottery))
    app.add_handler(CommandHandler("lottery_coupon", lottery_coupon))
    app.add_handler(CommandHandler("claim_coupon", claim_coupon))

    # Numpuz
    app.add_handler(CommandHandler("numpuz", numpuz))
    app.add_handler(CallbackQueryHandler(numpuz_callback, pattern="^numpuz_"))

    # Hall of Fame
    app.add_handler(CommandHandler("hof", hof))
    app.add_handler(CommandHandler("addhof", addhof))
    app.add_handler(CommandHandler("rmhof", rmhof))
    app.add_handler(CommandHandler("edithof", edithof))
    app.add_handler(CommandHandler("ping", ping))

    # Shop2, Shop3, Shop4
    app.add_handler(CommandHandler("shop2", shop2))
    app.add_handler(CommandHandler("buy2", buy2))
    app.add_handler(CommandHandler("myteam2", myteam2))
    app.add_handler(CommandHandler("top2", top2))
    app.add_handler(CommandHandler("addplayer2", addplayer2))
    app.add_handler(CommandHandler("shop3", shop3))
    app.add_handler(CommandHandler("buy3", buy3))
    app.add_handler(CommandHandler("myteam3", myteam3))
    app.add_handler(CommandHandler("top3", top3))
    app.add_handler(CommandHandler("addplayer3", addplayer3))
    app.add_handler(CommandHandler("shop4", shop4))
    app.add_handler(CommandHandler("buy4", buy4))
    app.add_handler(CommandHandler("myteam4", myteam4))
    app.add_handler(CommandHandler("top4", top4))
    app.add_handler(CommandHandler("addplayer4", addplayer4))

    # Bank
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("claim_interest", claim_interest))

    # Admin Cricket
    app.add_handler(CommandHandler("addmatch", addmatch))
    app.add_handler(CommandHandler("deletematch", deletematch))
    app.add_handler(CommandHandler("lockmatch", lockmatch))
    app.add_handler(CommandHandler("result", result))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("setprice", setprice))
    app.add_handler(CommandHandler("achieve", achieve))
    app.add_handler(CommandHandler("rmachieve", rmachieve))
    app.add_handler(CommandHandler("unlockmatch", unlockmatch))

    # CLcricket
    app.add_handler(CommandHandler("CLcricket", clcricket))
    app.add_handler(CallbackQueryHandler(cricket_mode_callback, pattern="^cricket_mode_"))
    app.add_handler(CallbackQueryHandler(cricket_join_callback, pattern="^cricket_join_"))
    app.add_handler(CallbackQueryHandler(cricket_toss_callback, pattern="^cricket_toss_"))
    app.add_handler(CallbackQueryHandler(cricket_choice_callback, pattern="^cricket_choice_"))
    app.add_handler(CallbackQueryHandler(cricket_bowl_callback, pattern="^cricket_bowl_"))
    app.add_handler(CallbackQueryHandler(cricket_bat_callback, pattern="^cricket_bat_"))

    # Mines
    app.add_handler(CommandHandler("mines", mines))
    app.add_handler(CallbackQueryHandler(mine_callback, pattern="^mine_"))
    app.add_handler(CommandHandler("add_all_players", add_all_players))

    # Claim Codes
    app.add_handler(CommandHandler("claimcode", claimcode))
    app.add_handler(CommandHandler("activecodes", activecodes))
    app.add_handler(CommandHandler("createcode", createcode))
    app.add_handler(CommandHandler("deletecode", deletecode))
    app.add_handler(CommandHandler("codestats", codestats))

    # Tic Tac Toe
    app.add_handler(CommandHandler("ttt", ttt))
    app.add_handler(CallbackQueryHandler(ttt_callback, pattern="^ttt_"))

    # Broadcast
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("broadcast_stats", broadcast_stats))

    # Stats
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("mystats", mystats))
    app.add_handler(CallbackQueryHandler(stats_callback, pattern="^stats_"))
    # (add_all_players already registered above in Mines section)

    # Group tracking
    app.add_handler(MessageHandler(filters.ChatType.GROUP | filters.ChatType.SUPERGROUP, track_group))

    # Global error handler - catches ALL unhandled Telegram errors
    app.add_error_handler(global_error_handler)

    print("ðŸ¤– Bot is running...")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await app.stop()
        await app.shutdown()

# ============ RUN ==========
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
