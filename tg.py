from flask import Flask
from telegram.ext import MessageHandler
import asyncio
from db_postgres import init_db as init_postgres, get_db, is_registered, get_user, update_balance, get_balance
from telegram.ext import filters
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import os
import threading
import json
import time

TOKEN = "8265192837:AAF_42Gi6nk2vYHPFhlr_hkqNGn2CrNUz3k"
ADMIN_IDS = [7687078555, 1315564307]

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)

def get_db():
    conn = sqlite3.connect('fantasy.db', timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, name TEXT, balance INTEGER, points INTEGER, won INTEGER, total INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS matches
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, team1 TEXT, team2 TEXT, date TEXT, status TEXT, locked INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, match_id INTEGER, team TEXT, amount INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS claim
                 (user_id INTEGER PRIMARY KEY, last_claim DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS spin
                 (user_id INTEGER PRIMARY KEY, last_claim TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS shop
                 (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, country TEXT, type TEXT, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS shop_women
                 (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, country TEXT, type TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_players
                 (user_id INTEGER, player_id INTEGER, type TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS shop2
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_players2
                 (user_id INTEGER, player_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS achievements
                 (user_id INTEGER, achievement TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bank
                 (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, last_interest TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS shop3
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_players3
                 (user_id INTEGER, player_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS shop4
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_players4
                 (user_id INTEGER, player_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (user_id INTEGER PRIMARY KEY, photo TEXT DEFAULT NULL, bio TEXT DEFAULT NULL,
                  points INTEGER DEFAULT 0, won INTEGER DEFAULT 0, total INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS referral
                 (user_id INTEGER PRIMARY KEY, referred_by INTEGER, referred_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (group_id INTEGER PRIMARY KEY, group_name TEXT, added_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cricket_stats
                 (user_id INTEGER PRIMARY KEY, name TEXT, runs INTEGER DEFAULT 0,
                  wickets INTEGER DEFAULT 0, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0,
                  highest_score INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS claim_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE, amount INTEGER,
                  max_claims INTEGER, claimed_count INTEGER DEFAULT 0, created_by INTEGER,
                  created_at TEXT, expires_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS code_claims
                 (code TEXT, user_id INTEGER, claimed_at TEXT, PRIMARY KEY (code, user_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS hall_of_fame
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, winner TEXT, added_by INTEGER, added_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS numpuz_progress
                 (user_id INTEGER PRIMARY KEY, level INTEGER DEFAULT 1, board TEXT, moves INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ttt_stats
                 (user_id INTEGER PRIMARY KEY, wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, draws INTEGER DEFAULT 0)''')
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN photo TEXT")
    except:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    except:
        pass

    conn.commit()
    conn.close()

init_db()

def is_registered(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_user(user_id, name=""):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (user_id, name, balance, points, won, total) VALUES (?, ?, 1000, 0, 0, 0)", (user_id, name))
        conn.commit()
        user = (user_id, name, 1000, 0, 0, 0, None)
    conn.close()
    return user

# ============ START ============
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
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing = c.fetchone()
    
    if not existing:
        c.execute("INSERT INTO users (user_id, name, balance, points, won, total) VALUES (?, ?, 1000, 0, 0, 0)", (user_id, name))
        
        if referred_by and referred_by != user_id:
            c.execute("SELECT user_id FROM users WHERE user_id=?", (referred_by,))
            if c.fetchone():
                c.execute("SELECT * FROM referrals WHERE user_id=?", (user_id,))
                if not c.fetchone():
                    c.execute("INSERT INTO referrals (user_id, referred_by, referred_at) VALUES (?, ?, ?)",
                              (user_id, referred_by, datetime.now().isoformat()))
                    c.execute("UPDATE users SET balance = balance + 1000 WHERE user_id=?", (referred_by,))
                    c.execute("UPDATE users SET balance = balance + 500 WHERE user_id=?", (user_id,))
                    conn.commit()
                    try:
                        await context.bot.send_message(referred_by, f"🎉 REFERRAL REWARD!\n\n@{name} joined using your link!\n💰 +1,000 credits!")
                    except:
                        pass
                    await update.message.reply_text("🎉 WELCOME!\n\nYou joined with a referral!\n💰 +500 bonus credits!")
        
        conn.commit()
        
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
            f"🏆 /leaderboard - Top players\n"
            f"🌾 /farm - Start farming\n\n"
            f"📌 Join our channels for exclusive updates!",
            reply_markup=reply_markup
        )
    else:
        conn.close()
        
        keyboard = [
            [InlineKeyboardButton("📢 UPDATES", url="https://t.me/clbotofficial")],
            [InlineKeyboardButton("👥 MAIN GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✨ WELCOME BACK TO CL ZONE ✨\n\n"
            f"👑 {name}\n"
            f"💰 {existing[2]:,} credits | 🏆 {existing[3]} pts\n\n"
            f"🎯 /claim - Daily rewards\n"
            f"🎡 /spin - Daily spin\n"
            f"👤 /profile - Your stats\n"
            f"🏆 /leaderboard - Top players\n"
            f"🌾 /farm - Your farm\n\n"
            f"📌 Stay connected with our community!",
            reply_markup=reply_markup
        )
    conn.close()


# ============ HELP COMMAND ==========

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    msg = (
        "📋 CL ZONE - COMMAND LIST\n\n"
        
        "👤 PROFILE\n"
        "• /start - Start bot\n"
        "• /profile - Your stats & collection\n"
        "• /leaderboard - Top 10 Richest users\n"
        "• /setbio <text> - Set bio\n"
        "• /rmbio - Remove bio\n"
        "• /setpfp - Set photo (reply to pic)\n"
        "• /rmpfp - Remove photo\n\n"
        
        "💰 EARN CREDITS\n"
        "• /claim - 500 daily\n"
        "• /spin - 1,000-10,000 daily\n"
        "• /dice <amount> - 0x to 2.5x\n"
        "• /flip heads/tails <amount> - 2x\n"
        "• /tip <amount> (reply) - Send credits\n\n"
        
        "🏏 CRICKET BETTING\n"
        "• /matches - Live matches\n"
        "• /bet <team> <amount> - Place bet\n"
        "• /mybets - Your bets\n"
        "• /cancel <number> - Cancel bet\n"
        "• /allbets - All bets\n"
        "• /history - Win/loss record\n"
        "• /top_fantasy - Fantasy points ranking\n\n"
        
        "🏆 ACHIEVEMENTS\n"
        "• /achievements - Your badges\n\n"
        
        "🛒 SHOP\n"
        "• /shop - Buy players\n"
        "• /buy <id> - Purchase mens player\n"
        "• /buyw <id> - Purchase women player\n"
        "• /myteam - Your collection\n"
        "• /top - Top collectors\n\n"
        
        "🛍️ AFFORDABLE STORE\n"
        "• /shop2 - Budget players\n"
        "• /buy2 <id> - Purchase\n"
        "• /myteam2 - Your collection\n"
        "• /top2 - Top collectors\n\n"
        
        "🛒 TG PLAYERS\n"
        "• /shop3 - Telegram players\n"
        "• /buy3 <id> - Purchase\n"
        "• /myteam3 - Your collection\n"
        "• /top3 - Top collectors\n\n"
        
        "🏦 BANK\n"
        "• /bank - Check balance\n"
        "• /deposit <amount> - Add to bank\n"
        "• /withdraw <amount> - Take from bank\n"
        "• /claim_interest - 5% daily\n\n"
        
        "🎰 LOTTERY\n"
        "• /lottery - Lottery menu\n"
        "• /buy_ticket <qty> - Buy tickets (20k each)\n"
        "• /mytickets - Your tickets\n"
        "• /lottery_info - Lottery stats\n"
        "• /claim_coupon <code> - Claim free tickets\n\n"
        
        "🎮 GAMES\n"
        "• /hilo <bet> - HiLo card game (0-10k bet)\n"
        "• /ttt [amount] - Tic Tac Toe\n"
        "• /mines <amount> <bombs> - Mines game\n"
        "• /CLcricket [amount] - Cricket game\n"
        "• /rps [amount] - Rock Paper Scissors\n"
        "• /numguess - Number guessing game\n"
        "• /ng <number> - Make a guess\n"
        "• /claimcode <code> - Claim rewards\n"
        "• /activecodes - Active codes\n"
        "• /numpuz - Number puzzle\n\n"
        
        "🎁 REFERRAL\n"
        "• /refer - Get your link (1k per refer)\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Need help? @clbothelp"
    )
    
    await update.message.reply_text(msg)

# ============ REFER ============
async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    bot_username = context.bot.username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await update.message.reply_text(f"👥 REFERRAL SYSTEM\n\nInvite friends and earn 1,000 credits each!\n\nYour Link: {ref_link}\n\nNew users get +500 bonus!")


# ============ PROFILE ============
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text("❌ Send /start first!")
        return
    user = update.effective_user
    name = user.first_name if user.first_name else (user.username or "User")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, points, won, total, photo, bio FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    if not data:
        conn.close()
        await update.message.reply_text("❌ Profile not found!")
        return
    c.execute("SELECT balance FROM bank WHERE user_id=?", (user_id,))
    bank_row = c.fetchone()
    bank_bal = bank_row[0] if bank_row else 0
    conn.close()
    wallet_bal, points, won, total, photo, bio = data
    total_wealth = wallet_bal + bank_bal
    win_rate = int((won / total) * 100) if total > 0 else 0
    profile_text = f"👤 PROFILE\n\nName: {name}\n"
    if bio:
        profile_text += f"Bio: {bio}\n\n"
    profile_text += f"💰 Wallet: {wallet_bal:,}\n🏦 Bank: {bank_bal:,}\n💎 Total: {total_wealth:,}\n\n🏆 Points: {points}\n📊 Bets: {won}/{total}\n📈 Win Rate: {win_rate}%"
    if photo:
        await update.message.reply_photo(photo=photo, caption=profile_text)
    else:
        await update.message.reply_text(profile_text)


# ============ BIO & PFP ============
async def setbio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /setbio <your bio>")
        return
    bio = " ".join(args)
    if len(bio) > 100:
        await update.message.reply_text("❌ Bio too long!")
        return
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    except:
        pass
    c.execute("UPDATE users SET bio = ? WHERE user_id = ?", (bio, user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Bio updated!\n\n{bio}")

async def rmbio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET bio = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("✅ Bio removed!")

async def setpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    # 🔥 CHECK - Reply to a message or not
    if not update.message.reply_to_message:
        await update.message.reply_text('❌ Reply to a photo with /setpfp')
        return

    if not update.message.reply_to_message.photo:
        await update.message.reply_text('❌ Reply to a PHOTO with /setpfp')
        return

    photo = update.message.reply_to_message.photo[-1].file_id
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN photo TEXT")
    except:
        pass
    c.execute("UPDATE users SET photo=? WHERE user_id=?", (photo, user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text('✅ Profile photo updated!')

async def rmpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET photo=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text('❌ Profile photo removed!')

# ============ CLAIM ============
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    chat_type = update.message.chat.type

    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    CL_GROUP_ID = -1001661258033
    CL_GROUP_LINK = "https://t.me/+eTD1m8Cjc_wyOTNl"

    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS claim (user_id INTEGER PRIMARY KEY, last_claim DATE)")
    c.execute("SELECT last_claim FROM claim WHERE user_id=?", (user_id,))
    row = c.fetchone()

    today = datetime.now().date()
    today_str = today.strftime("%m/%d/%y")

    if row and row[0]:
        last = datetime.fromisoformat(row[0]).date()
        if last == today:
            await update.message.reply_text("⚠️ Already claimed today!\nCome back tomorrow.")
            conn.close()
            return

    if chat_type in ['group', 'supergroup'] and chat_id == CL_GROUP_ID:
        reward = 1000
        extra_note = "\n\n✨ BONUS: You get 1000 credits in CL Zone Group!"
    else:
        reward = 500
        extra_note = f"\n\n💡 Tip: Use /claim in CL Zone Group to get 1000 credits!"

    c.execute("INSERT OR REPLACE INTO claim (user_id, last_claim) VALUES (?, ?)", (user_id, today.isoformat()))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (reward, user_id))
    conn.commit()

    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()

    await update.message.reply_text(
        f"✅ Claimed Daily Rewards!\n\n💰 +{reward} credits\n📅 {today_str}\n💳 New balance: {new_bal:,}{extra_note}\n\n🔄 Next claim: tomorrow",
        disable_web_page_preview=True
    )


# ============ SPIN ============
async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS spin (user_id INTEGER PRIMARY KEY, last_claim TEXT)")
    c.execute("SELECT last_claim FROM spin WHERE user_id=?", (user_id,))
    row = c.fetchone()
    
    now = datetime.now()
    today_str = now.strftime("%m/%d/%y")
    
    if row and row[0]:
        last = datetime.fromisoformat(row[0])
        if last.date() == now.date():
            await update.message.reply_text(f"⚠️ Already spin today!\nat {last.strftime('%m/%d/%y')}\n\n🎡 Next spin: tomorrow")
            conn.close()
            return
    
    amount = random.randint(1000, 10000)
    c.execute("INSERT OR REPLACE INTO spin (user_id, last_claim) VALUES (?, ?)", (user_id, now.isoformat()))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"✅ Claimed Daily Spin Rewards of {amount:,} Credits\nat {today_str}\n\n💰 New balance: {new_bal:,} 💰\n🎡 Next spin: tomorrow")


# ============ DICE ============
async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('🎲 /dice <amount>\nMultipliers: 1(0x) 2(0.25x) 3(0.5x) 4(1.25x) 5(1.5x) 6(2.5x)')
        return
    
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('❌ Minimum 100 credits')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < amount:
        await update.message.reply_text(f'❌ Need {amount:,}, have {balance:,}')
        conn.close()
        return
    
    roll = random.randint(1, 6)
    dice_emoji = {1:'⚀', 2:'⚁', 3:'⚂', 4:'⚃', 5:'⚄', 6:'⚅'}
    multi = {1:0, 2:0.25, 3:0.5, 4:1.25, 5:1.5, 6:2.5}
    win = int(amount * multi[roll])
    new_bal = balance - amount + win
    c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, user_id))
    conn.commit()
    conn.close()
    
    if win > 0:
        await update.message.reply_text(f"🎲 DICE\n\n🎲 Rolled: {roll} {dice_emoji[roll]}\n✨ You won {win:,} 💰 ({multi[roll]}x)\n💰 New balance: {new_bal:,} 💰")
    else:
        await update.message.reply_text(f"🎲 DICE\n\n🎲 Rolled: {roll} {dice_emoji[roll]}\n💀 You lost {amount:,} 💰\n💰 New balance: {new_bal:,} 💰")


# ============ FLIP ============
async def flip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('🪙 /flip heads/tails <amount>\nExample: /flip heads 1000')
        return
    
    choice = args[0].lower()
    if choice not in ['heads', 'tails']:
        await update.message.reply_text('❌ Choose heads or tails')
        return
    
    try:
        amount = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('❌ Minimum 100 credits')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < amount:
        await update.message.reply_text(f'❌ Need {amount:,}, have {balance:,}')
        conn.close()
        return
    
    result = random.choice(['heads', 'tails'])
    if choice == result:
        win = amount * 2
        new_bal = balance - amount + win
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"🪙 {result.upper()}! You won {win:,} 💰\n💰 New balance: {new_bal:,} 💰")
    else:
        new_bal = balance - amount
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"😞 {result.upper()}! You lost {amount:,} 💰\n💰 New balance: {new_bal:,} 💰")


# ============ MATCHES ============
async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2, date, locked FROM matches WHERE locked=0")
    matches_data = c.fetchall()
    
    if not matches_data:
        await update.message.reply_text('📭 No active matches')
        conn.close()
        return
    
    msg = "🏏 LIVE MATCHES\n\n"
    for m in matches_data:
        status = "🔓 OPEN" if m[4] == 0 else "🔒 LOCKED"
        msg += f"🔥 {m[1]} vs {m[2]}\n📅 {m[3]} | {status}\n💰 /bet {m[1]} <amount> | /bet {m[2]} <amount>\n\n"
    
    user = get_user(user_id)
    msg += f"━━━━━━━━━━━━━━━━━━━━━━\n💰 Your balance: {user[2]:,} 💰"
    await update.message.reply_text(msg)
    conn.close()


# ============ BET ============
async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /bet TEAM AMOUNT\nExample: /bet KKR 1000')
        return
    
    team = args[0].upper()
    try:
        amount = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid amount')
        return
    
    if amount < 100:
        await update.message.reply_text('❌ Minimum 100 credits')
        return
    
    user = get_user(user_id)
    if user[2] < amount:
        await update.message.reply_text(f'❌ Need {amount:,}, have {user[2]:,}')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2, locked FROM matches WHERE (team1=? OR team2=?) AND locked=0", (team, team))
    match = c.fetchone()
    
    if not match:
        await update.message.reply_text(f'❌ Match with {team} not found!')
        conn.close()
        return
    
    if match[3] == 1:
        await update.message.reply_text(f'🔒 Betting closed!')
        conn.close()
        return
    
    c.execute("SELECT COUNT(*) FROM bets WHERE user_id = ? AND match_id = ?", (user_id, match[0]))
    bet_count = c.fetchone()[0]
    
    if bet_count >= 2:
        await update.message.reply_text("❌ You can only place up to 2 bets per match!")
        conn.close()
        return
    
    c.execute("INSERT INTO bets (user_id, match_id, team, amount) VALUES (?, ?, ?, ?)", (user_id, match[0], team, amount))
    c.execute("UPDATE users SET balance = balance - ?, total = total + 1 WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ BET PLACED!\n\n🏏 {match[1]} vs {match[2]}\n🎯 {team}\n💰 {amount:,} 💰\n\n📊 New balance: {user[2]-amount:,} 💰\n💡 /mybets to check")


# ============ MYBETS ============
async def mybets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT b.id, b.team, b.amount, m.team1, m.team2, m.date
                 FROM bets b JOIN matches m ON b.match_id = m.id 
                 WHERE b.user_id = ? AND m.locked = 0""", (user_id,))
    bets_data = c.fetchall()
    conn.close()
    
    if not bets_data:
        await update.message.reply_text('📭 No active bets')
        return
    
    msg = f"🎯 MY ACTIVE BETS ({len(bets_data)})\n\n"
    for i, bet in enumerate(bets_data, 1):
        msg += f"{i}️⃣ {bet[3]} vs {bet[4]}\n   🎯 {bet[1]} | 💰 {bet[2]:,}\n   📅 {bet[5]}\n\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n💡 /cancel <number> to cancel bet"
    await update.message.reply_text(msg)


# ============ CANCEL ============
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /cancel <bet_number>\nExample: /cancel 1\n\nUse /mybets to see numbers')
        return
    
    try:
        bet_number = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid number')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT b.id, b.amount, m.team1, m.team2, m.locked
                 FROM bets b JOIN matches m ON b.match_id = m.id 
                 WHERE b.user_id = ? AND m.locked = 0""", (user_id,))
    bets_data = c.fetchall()
    
    if bet_number < 1 or bet_number > len(bets_data):
        await update.message.reply_text(f'❌ Invalid! Choose 1-{len(bets_data)}')
        conn.close()
        return
    
    bet_to_cancel = bets_data[bet_number - 1]
    
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (bet_to_cancel[1], user_id))
    c.execute("DELETE FROM bets WHERE id=?", (bet_to_cancel[0],))
    c.execute("UPDATE users SET total = total - 1 WHERE user_id=?", (user_id,))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"✅ BET CANCELLED!\n\n🏏 {bet_to_cancel[2]} vs {bet_to_cancel[3]}\n💰 Refund: {bet_to_cancel[1]:,} 💰\n📊 New balance: {new_bal:,} 💰")


# ============ ALLBETS ============
async def allbets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2 FROM matches WHERE locked=0")
    matches_data = c.fetchall()
    
    if not matches_data:
        await update.message.reply_text('📭 No active bets')
        conn.close()
        return
    
    full_msg = "📊 ALL BETS\n\n"
    for match in matches_data:
        c.execute("SELECT b.team, b.amount, u.name FROM bets b JOIN users u ON b.user_id=u.user_id WHERE b.match_id=?", (match[0],))
        bets_data = c.fetchall()
        
        if not bets_data:
            continue
        
        team1_amount = 0
        team2_amount = 0
        team1_users = []
        team2_users = []
        
        for bet in bets_data:
            if bet[0] == match[1]:
                team1_amount += bet[1]
                team1_users.append(f"{bet[2]} - {bet[1]:,}")
            else:
                team2_amount += bet[1]
                team2_users.append(f"{bet[2]} - {bet[1]:,}")
        
        full_msg += f"🏏 {match[1]} vs {match[2]}\n"
        full_msg += f"🎯 {match[1]} (Total: {team1_amount:,} 💰):\n"
        for i, u in enumerate(team1_users, 1):
            full_msg += f"   {i}. {u}\n"
        full_msg += f"\n🎯 {match[2]} (Total: {team2_amount:,} 💰):\n"
        for i, u in enumerate(team2_users, 1):
            full_msg += f"   {i}. {u}\n"
        full_msg += f"\n💣 Total Pool: {team1_amount + team2_amount:,} 💰\n\n"
    
    await update.message.reply_text(full_msg)
    conn.close()


# ============ HISTORY ============
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    user = get_user(user_id)
    win_rate = int(user[4]/user[5]*100) if user[5] > 0 else 0
    await update.message.reply_text(f'📜 BET HISTORY\n\n✅ Won: {user[4]}\n❌ Lost: {user[5]-user[4]}\n📊 Win Rate: {win_rate}%\n\n🏆 Fantasy Points: {user[3]}')


# ============ LEADERBOARD ============
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT u.name, u.balance + COALESCE(b.balance, 0) as total_wealth
                 FROM users u LEFT JOIN bank b ON u.user_id = b.user_id
                 ORDER BY total_wealth DESC LIMIT 10""")
    users_data = c.fetchall()
    
    msg = "🏆 TOP 10 RICHEST (Wallet + Bank)\n\n"
    for i, u in enumerate(users_data, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {u[0]} - {u[1]:,} 💰\n"
    
    c.execute("""SELECT u.balance + COALESCE(b.balance, 0) FROM users u
                 LEFT JOIN bank b ON u.user_id = b.user_id WHERE u.user_id = ?""", (user_id,))
    user_total = c.fetchone()[0]
    
    rank = c.execute("""SELECT COUNT(*) + 1 FROM (SELECT u.balance + COALESCE(b.balance, 0) as total
                 FROM users u LEFT JOIN bank b ON u.user_id = b.user_id) WHERE total > ?""", (user_total,)).fetchone()[0]
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{rank}\n💰 Total wealth: {user_total:,} 💰"
    await update.message.reply_text(msg)
    conn.close()


# ============ TOP FANTASY ============
async def top_fantasy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, points FROM users ORDER BY points DESC LIMIT 20")
    users_data = c.fetchall()
    
    if not users_data:
        await update.message.reply_text('📭 No fantasy points yet!')
        conn.close()
        return
    
    msg = "🏆 FANTASY LEADERBOARD\n\n"
    for i, u in enumerate(users_data, 1):
        msg += f"{i}. {u[0]} - {u[1]} pts\n"
    
    user = get_user(user_id)
    rank = c.execute("SELECT COUNT(*) FROM users WHERE points > ?", (user[3],)).fetchone()[0] + 1
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your points: {user[3]} | Rank: #{rank}"
    await update.message.reply_text(msg)
    conn.close()


# ============ TIP ============
async def tip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    if not update.message.reply_to_message:
        await update.message.reply_text('❌ Reply to user with /tip AMOUNT')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /tip AMOUNT\nExample: /tip 500')
        return
    
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid amount')
        return
    
    sender = update.effective_user
    receiver = update.message.reply_to_message.from_user
    
    if sender.id == receiver.id:
        await update.message.reply_text('❌ Cannot tip yourself!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (sender.id,))
    sender_bal = c.fetchone()[0]
    
    if sender_bal < amount:
        await update.message.reply_text(f'❌ Need {amount:,}, have {sender_bal:,}')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, sender.id))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, receiver.id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"💝 TIP SENT!\n\n📤 To: {receiver.first_name}\n💰 Amount: {amount:,} 💰\n📊 Your balance: {sender_bal - amount:,} 💰")


# ============ ACHIEVEMENTS ============
async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT achievement FROM achievements WHERE user_id=?", (user_id,))
    ach = c.fetchall()
    conn.close()
    
    if not ach:
        await update.message.reply_text('🏆 MY ACHIEVEMENTS\n\nNo achievements yet!')
        return
    
    msg = "🏆 MY ACHIEVEMENTS\n\n"
    for i, a in enumerate(ach, 1):
        msg += f"{i}. {a[0]} 🏆\n"
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\nTotal: {len(ach)} achievements"
    await update.message.reply_text(msg)

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    keyboard = [
        [InlineKeyboardButton("🇮🇳 India", callback_data="shop_India")],
        [InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 England", callback_data="shop_England")],
        [InlineKeyboardButton("🇦🇺 Australia", callback_data="shop_Australia")],
        [InlineKeyboardButton("🇳🇿 New Zealand", callback_data="shop_New Zealand")],
        [InlineKeyboardButton("👩 Women Players", callback_data="shop_women")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛒 CRICKETER SHOP\n\nSelect country:", reply_markup=reply_markup)

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "shop_women":
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id, name, price FROM shop_women ORDER BY id")
        players = c.fetchall()
        conn.close()

        if not players:
            await query.edit_message_text("👩 WOMEN CRICKETERS\n\nNo players yet!")
            return

        msg = "👩 WOMEN CRICKETERS\n\n"
        for p in players:
            msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💡 /buyw <number> to purchase"
        await query.edit_message_text(msg)
        return

    parts = data.split('_')
    if len(parts) < 2:
        await query.edit_message_text("❌ Invalid selection")
        return

    country = parts[1]
    
    # Fix for "New Zealand" (has space)
    if len(parts) > 2:
        country = parts[1] + " " + parts[2]

    conn = get_db()
    c = conn.cursor()
    
    # 🔥 SIRF CATEGORY SE SEARCH KARO (Current + Legends dono)
    c.execute("SELECT id, name, price, type FROM shop WHERE category=?", (country,))
    players = c.fetchall()
    conn.close()

    if not players:
        await query.edit_message_text(f"❌ No players found for {country}")
        return

    # Separate Current and Legends for display
    current_players = [p for p in players if p[3] == 'current']
    legend_players = [p for p in players if p[3] == 'legend']
    
    msg = f"🛒 {country} PLAYERS\n\n"
    
    if current_players:
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n🔵 CURRENT PLAYERS ({len(current_players)}):\n"
        for p in current_players:
            msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
    
    if legend_players:
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n🌟 LEGENDS ({len(legend_players)}):\n"
        for p in legend_players:
            msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💡 /buy <number> to purchase"
    await query.edit_message_text(msg)


# ============ BUY MENS ============
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /buy <player_id>\nExample: /buy 1')
        return
    
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid ID')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, price FROM shop WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < player[1]:
        await update.message.reply_text(f'❌ Need {player[1]:,}, have {balance:,}')
        conn.close()
        return
    
    c.execute("SELECT * FROM user_players WHERE user_id=? AND player_id=? AND type='mens'", (user_id, player_id))
    if c.fetchone():
        await update.message.reply_text(f'❌ You already own {player[0]}!')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (player[1], user_id))
    c.execute("INSERT INTO user_players (user_id, player_id, type) VALUES (?, ?, 'mens')", (user_id, player_id))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"✅ PURCHASED!\n\n🏏 {player[0]}\n💰 Price: {player[1]:,} 💰\n📊 New balance: {new_bal:,} 💰")


# ============ BUY WOMEN ============
async def buyw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /buyw <player_id>\nExample: /buyw 1')
        return
    
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid ID')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, price FROM shop_women WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < player[1]:
        await update.message.reply_text(f'❌ Need {player[1]:,}, have {balance:,}')
        conn.close()
        return
    
    c.execute("SELECT * FROM user_players WHERE user_id=? AND player_id=? AND type='women'", (user_id, player_id))
    if c.fetchone():
        await update.message.reply_text(f'❌ You already own {player[0]}!')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (player[1], user_id))
    c.execute("INSERT INTO user_players (user_id, player_id, type) VALUES (?, ?, 'women')", (user_id, player_id))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"✅ PURCHASED!\n\n👩 {player[0]}\n💰 Price: {player[1]:,} 💰\n📊 New balance: {new_bal:,} 💰")


# ============ MY TEAM ============
async def myteam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT p.name, p.price FROM user_players u JOIN shop p ON u.player_id=p.id WHERE u.user_id=? AND u.type='mens'", (user_id,))
    mens = c.fetchall()
    
    c.execute("SELECT w.name, w.price FROM user_players u JOIN shop_women w ON u.player_id=w.id WHERE u.user_id=? AND u.type='women'", (user_id,))
    women = c.fetchall()
    
    c.execute("SELECT s.name, s.price FROM user_players2 u JOIN shop2 s ON u.player_id=s.id WHERE u.user_id=?", (user_id,))
    affordable = c.fetchall()
    
    c.execute("SELECT s.name, s.price FROM user_players3 u JOIN shop3 s ON u.player_id=s.id WHERE u.user_id=?", (user_id,))
    shop3 = c.fetchall()
    
    conn.close()
    
    mens_total = sum(p[1] for p in mens)
    women_total = sum(w[1] for w in women)
    affordable_total = sum(a[1] for a in affordable)
    shop3_total = sum(s[1] for s in shop3)
    
    msg = "🏏 MY CRICKET TEAM\n\n━━━━━━━━━━━━━━━━━━━━━━\n👨 MENS"
    if mens:
        msg += f" ({len(mens)})\n\n"
        for i, p in enumerate(mens, 1):
            msg += f"{i}. {p[0]} - {p[1]:,} 💰\n"
        msg += f"\nTotal: {mens_total:,} 💰"
    else:
        msg += "\n\nNo mens players. /shop to buy!"
    
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🛍️ AFFORDABLE"
    if affordable:
        msg += f" ({len(affordable)})\n\n"
        for i, a in enumerate(affordable, 1):
            msg += f"{i}. {a[0]} - {a[1]:,} 💰\n"
        msg += f"\nTotal: {affordable_total:,} 💰"
    else:
        msg += "\n\nNo affordable players. /shop2 to buy!"
    
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n💎 SHOP3"
    if shop3:
        msg += f" ({len(shop3)})\n\n"
        for i, s in enumerate(shop3, 1):
            msg += f"{i}. {s[0]} - {s[1]:,} 💰\n"
        msg += f"\nTotal: {shop3_total:,} 💰"
    else:
        msg += "\n\nNo shop3 players. /shop3 to buy!"
    
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n👩 WOMEN"
    if women:
        msg += f" ({len(women)})\n\n"
        for i, w in enumerate(women, 1):
            msg += f"{i}. {w[0]} - {w[1]:,} 💰\n"
        msg += f"\nTotal: {women_total:,} 💰"
    else:
        msg += "\n\nNo women players. /shop women section"
    
    grand_total = mens_total + affordable_total + shop3_total + women_total
    total_players = len(mens) + len(affordable) + len(shop3) + len(women)
    msg += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n💰 GRAND TOTAL: {grand_total:,} 💰\n🏆 TOTAL PLAYERS: {total_players}"
    
    await update.message.reply_text(msg)


# ============ TOP COLLECTORS ============
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(p.price), 0) as total FROM users u JOIN user_players up ON u.user_id=up.user_id JOIN shop p ON up.player_id=p.id WHERE up.type='mens' GROUP BY u.user_id ORDER BY total DESC LIMIT 10")
    tops = c.fetchall()
    
    if not tops:
        await update.message.reply_text('🏆 TOP COLLECTORS\n\nNo one owns any players yet!')
        conn.close()
        return
    
    msg = "🏆 TOP COLLECTORS\n\n"
    for i, t in enumerate(tops, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {t[0]} - {t[1]} players ({t[2]:,} 💰)\n"
    
    c.execute("SELECT COUNT(up.player_id), COALESCE(SUM(p.price), 0) FROM user_players up JOIN shop p ON up.player_id=p.id WHERE up.user_id=? AND up.type='mens'", (user_id,))
    user_data = c.fetchone()
    player_count = user_data[0] if user_data else 0
    total_value = user_data[1] if user_data else 0
    
    rank = 1
    for i, t in enumerate(tops, 1):
        if t[0] == update.effective_user.first_name:
            rank = i
            break
    else:
        rank = len(tops) + 1
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{rank}\n💰 Collection value: {total_value:,} 💰\n🏆 Players: {player_count}"
    await update.message.reply_text(msg)
    conn.close()

# ============ RPS GAME ============
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
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    args = context.args
    bet = 0
    if args:
        try:
            bet = int(args[0])
            if bet < 100:
                await update.message.reply_text("❌ Minimum bet is 100 credits!")
                return
        except:
            await update.message.reply_text("❌ Invalid bet amount!")
            return
    if bet > 0:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = c.fetchone()[0]
        conn.close()
        if balance < bet:
            await update.message.reply_text(f"❌ You need {bet:,} credits to play!")
            return
    global rps_next_id
    game_id = rps_next_id
    rps_next_id += 1
    rps_lobby[game_id] = {"creator_id": user_id, "creator_name": user_name, "bet": bet, "chat_id": chat_id}
    keyboard = [[InlineKeyboardButton("🔵 JOIN GAME", callback_data=f"rps_join_{game_id}")]]
    bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Free Play"
    await update.message.reply_text(f"✊ ROCK PAPER SCISSORS\n\n👑 Host: {user_name}\n{bet_text}\n\n━━━━━━━━━━━━━━━━━━━━\n⚡ Waiting for opponent...", reply_markup=InlineKeyboardMarkup(keyboard))

async def rps_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = query.data
    if data.startswith("rps_join_"):
        game_id = int(data.split("_")[2])
        if game_id not in rps_lobby:
            await query.edit_message_text("❌ Game lobby expired!")
            return
        lobby = rps_lobby[game_id]
        creator_id = lobby["creator_id"]
        creator_name = lobby["creator_name"]
        bet = lobby["bet"]
        chat_id = lobby["chat_id"]
        if creator_id == user_id:
            await query.answer("You cannot join your own game!", show_alert=True)
            return
        if bet > 0:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            result = c.fetchone()
            if not result:
                await query.edit_message_text("❌ You are not registered! Send /start first.")
                conn.close()
                return
            balance = result[0]
            conn.close()
            if balance < bet:
                await query.answer(f"❌ {user_name}, you need {bet:,} credits to join!", show_alert=True)
                return
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, creator_id))
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, user_id))
            conn.commit()
            conn.close()
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
        await query.edit_message_text(f"✊ ROCK PAPER SCISSORS\n\n{creator_name} vs {user_name}\n{bet_text}\n\n━━━━━━━━━━━━━━━━━━━━\n🎯 {creator_name}'s turn!", reply_markup=InlineKeyboardMarkup(keyboard))

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
        await query.edit_message_text(f"✊ ROCK PAPER SCISSORS\n\n{game.player1_name} vs {game.player2_name}\n{bet_text}\n\n━━━━━━━━━━━━━━━━━━━━\n✅ {game.player1_name} made their choice!\n\n🎯 {game.player2_name}'s turn!", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        game.player2_choice = choice
        game.waiting_for = None
        game.game_active = False
        result_text = game.get_result_text()
        winner = game.check_winner()
        if game.bet > 0 and winner != "draw":
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet*2, winner))
            conn.commit()
            conn.close()
            winner_name = game.player1_name if winner == game.player1_id else game.player2_name
            loser_name = game.player2_name if winner == game.player1_id else game.player1_name
            result_text += f"\n\n💰 Prize: {game.bet*2:,} credits\n💳 {winner_name}: +{game.bet*2:,}\n💳 {loser_name}: -{game.bet:,}"
        elif game.bet > 0 and winner == "draw":
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet, game.player1_id))
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet, game.player2_id))
            conn.commit()
            conn.close()
            result_text += f"\n\n💰 Money returned: {game.bet:,} each"
        await query.edit_message_text(f"✊ ROCK PAPER SCISSORS\n\n{result_text}")
        del rps_games[game_id]

async def rps_none_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Game Over!", show_alert=True)


# ============ NUMPUZ GAME ============

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
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Add columns if not exists
    try:
        c.execute("ALTER TABLE numpuz_progress ADD COLUMN chat_id INTEGER")
        conn.commit()
    except:
        pass
    try:
        c.execute("ALTER TABLE numpuz_progress ADD COLUMN owner_id INTEGER")
        conn.commit()
    except:
        pass
    
    # Check if game exists for this chat
    c.execute("SELECT level, board, moves, owner_id FROM numpuz_progress WHERE chat_id = ?", (chat_id,))
    saved = c.fetchone()
    
    if saved and saved[1]:
        level = saved[0]
        board = json.loads(saved[1])
        owner_id = saved[3]
        
        # Show who owns the game
        owner_name = "Someone"
        c.execute("SELECT name FROM users WHERE user_id = ?", (owner_id,))
        owner = c.fetchone()
        if owner:
            owner_name = owner[0]
        
        keyboard = get_board_keyboard(board, level)
        size = len(board)
        
        await update.message.reply_text(
            f"🧩 NUMBER PUZZLE - LEVEL {level}\n"
            f"🎮 Game started by: {owner_name}\n"
            f"📊 Only {owner_name} can play this game!\n"
            f"Arrange numbers from 1 to {size*size - 1}\n"
            f"⬜ is the empty space.",
            reply_markup=keyboard
        )
        conn.close()
        return
    
    # Create new game for this chat
    level = 1
    size = get_size_for_level(level)
    while True:
        board = get_shuffled_board(size)
        if is_solvable(board):
            break
    
    c.execute("INSERT OR REPLACE INTO numpuz_progress (user_id, level, board, moves, chat_id, owner_id) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, level, json.dumps(board), 0, chat_id, user_id))
    conn.commit()
    conn.close()
    
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
    
    conn = get_db()
    c = conn.cursor()
    
    # Get game for this chat
    c.execute("SELECT level, board, moves, owner_id FROM numpuz_progress WHERE chat_id = ?", (chat_id,))
    saved = c.fetchone()
    
    if not saved:
        await query.answer("No active game in this chat!", show_alert=True)
        await query.edit_message_text("❌ No active puzzle. Use /numpuz to start a new game.")
        conn.close()
        return
    
    db_level, board_json, moves, owner_id = saved
    
    # 🔥 CRITICAL: Only owner can play
    if owner_id != user_id:
        await query.answer("❌ This is not your game! Only the person who started /numpuz can play.", show_alert=True)
        conn.close()
        return
    
    board = json.loads(board_json)
    
    if db_level != level:
        await query.answer("Invalid move!", show_alert=True)
        conn.close()
        return
    
    if move_tile(board, row, col):
        moves += 1
        
        # Check win
        if is_win(board):
            next_level = db_level + 1
            next_size = get_size_for_level(next_level)
            
            while True:
                new_board = get_shuffled_board(next_size)
                if is_solvable(new_board):
                    break
            
            c.execute("UPDATE numpuz_progress SET level = ?, board = ?, moves = ?, owner_id = ? WHERE chat_id = ?",
                      (next_level, json.dumps(new_board), 0, user_id, chat_id))
            conn.commit()
            conn.close()
            
            keyboard = get_board_keyboard(new_board, next_level)
            await query.edit_message_text(
                f"🎉 LEVEL {db_level} COMPLETE! 🎉\n\n"
                f"📊 Moves taken: {moves}\n"
                f"✨ Moving to LEVEL {next_level}!\n\n"
                f"Arrange numbers from 1 to {next_size*next_size - 1}",
                reply_markup=keyboard
            )
            return
        
        # Update board
        c.execute("UPDATE numpuz_progress SET board = ?, moves = ? WHERE chat_id = ?",
                  (json.dumps(board), moves, chat_id))
        conn.commit()
        conn.close()
        
        keyboard = get_board_keyboard(board, db_level)
        size = len(board)
        await query.edit_message_text(
            f"🧩 NUMBER PUZZLE - LEVEL {db_level}\n"
            f"📊 Moves: {moves}",
            reply_markup=keyboard
        )
    else:
        conn.close()
        await query.answer("Invalid move! Click tile adjacent to ⬜", show_alert=True)


# ============ HALL OF FAME ============
async def hof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, winner FROM hall_of_fame ORDER BY id ASC")
    winners = c.fetchall()
    conn.close()
    if not winners:
        await update.message.reply_text("🏆 HALL OF FAME 🏆\n\nNo winners yet!")
        return
    msg = "🏆 HALL OF FAME 🏆\n\n"
    for i, (wid, winner) in enumerate(winners, 1):
        msg += f"{i}. {winner}\n"
        if i < len(winners):
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
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
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO hall_of_fame (winner, added_by, added_at) VALUES (?, ?, ?)", (winner, update.effective_user.id, datetime.now().isoformat()))
    conn.commit()
    c.execute("SELECT COUNT(*) FROM hall_of_fame")
    count = c.fetchone()[0]
    conn.close()
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
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, winner FROM hall_of_fame ORDER BY id ASC")
    winners = c.fetchall()
    if num < 1 or num > len(winners):
        await update.message.reply_text(f"❌ Invalid! Choose 1-{len(winners)}")
        conn.close()
        return
    winner_id = winners[num-1][0]
    winner_text = winners[num-1][1]
    c.execute("DELETE FROM hall_of_fame WHERE id = ?", (winner_id,))
    conn.commit()
    c.execute("SELECT COUNT(*) FROM hall_of_fame")
    count = c.fetchone()[0]
    conn.close()
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
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, winner FROM hall_of_fame ORDER BY id ASC")
    winners = c.fetchall()
    if num < 1 or num > len(winners):
        await update.message.reply_text(f"❌ Invalid! Choose 1-{len(winners)}")
        conn.close()
        return
    winner_id = winners[num-1][0]
    old_text = winners[num-1][1]
    c.execute("UPDATE hall_of_fame SET winner = ? WHERE id = ?", (new_text, winner_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✏️ EDITED HALL OF FAME!\n\n❌ Old: {old_text}\n✅ New: {new_text}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    msg = update.effective_message
    if not msg:
        return
    try:
        import time
        start_time = time.time()
        temp_msg = await msg.reply_text("🏓 Pinging...")
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        await temp_msg.edit_text(f"🏓 Pong!\n⏱️ Latency: {latency:.2f}ms\n🤖 Bot is alive!", parse_mode='Markdown')
    except Exception as e:
        await msg.reply_text("🏓 Pong!")


# ============ SHOP2 ============
async def shop2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM shop2 ORDER BY price ASC")
    players = c.fetchall()
    conn.close()
    if not players:
        await update.message.reply_text('🛒 AFFORDABLE SHOP\n\nNo players yet.\n👑 Admin: /addplayer2 <name> <price>')
        return
    msg = "🛒 AFFORDABLE PLAYERS SHOP\n\n"
    for p in players:
        msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n💡 /buy2 <id> to purchase"
    await update.message.reply_text(msg)

async def buy2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /buy2 <player_id>\nExample: /buy2 1')
        return
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid ID')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, price FROM shop2 WHERE id=?", (player_id,))
    player = c.fetchone()
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    if balance < player[1]:
        await update.message.reply_text(f'❌ Need {player[1]:,}, have {balance:,}')
        conn.close()
        return
    c.execute("SELECT * FROM user_players2 WHERE user_id=? AND player_id=?", (user_id, player_id))
    if c.fetchone():
        await update.message.reply_text(f'❌ You already own {player[0]}!')
        conn.close()
        return
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (player[1], user_id))
    c.execute("INSERT INTO user_players2 (user_id, player_id) VALUES (?, ?)", (user_id, player_id))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"✅ PURCHASED!\n\n🏏 {player[0]}\n💰 Price: {player[1]:,} 💰\n📊 New balance: {new_bal:,} 💰")

async def myteam2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT s.name, s.price FROM user_players2 u JOIN shop2 s ON u.player_id=s.id WHERE u.user_id=?", (user_id,))
    players = c.fetchall()
    conn.close()
    if not players:
        await update.message.reply_text('📭 No affordable players owned.\nUse /shop2 to buy!')
        return
    total = sum(p[1] for p in players)
    msg = "🛍️ MY AFFORDABLE PLAYERS\n\n"
    for i, p in enumerate(players, 1):
        msg += f"{i}. {p[0]} - {p[1]:,} 💰\n"
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💰 Total spent: {total:,} 💰"
    await update.message.reply_text(msg)

async def top2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(s.price), 0) as total FROM users u JOIN user_players2 up ON u.user_id=up.user_id JOIN shop2 s ON up.player_id=s.id GROUP BY u.user_id ORDER BY total DESC LIMIT 10")
    tops = c.fetchall()
    if not tops:
        await update.message.reply_text('🏆 AFFORDABLE PLAYERS TOP\n\nNo one owns any yet!')
        conn.close()
        return
    msg = "🏆 AFFORDABLE PLAYERS TOP\n\n"
    for i, t in enumerate(tops, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {t[0]} - {t[1]} players ({t[2]:,} 💰)\n"
    c.execute("SELECT COUNT(*) FROM user_players2 WHERE user_id=?", (user_id,))
    my_count = c.fetchone()[0]
    msg += f"\n📊 You own: {my_count} players"
    await update.message.reply_text(msg)
    conn.close()

async def addplayer2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /addplayer2 <name> <price>')
        return
    name = ' '.join(args[:-1])
    try:
        price = int(args[-1])
    except:
        await update.message.reply_text('❌ Invalid price!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO shop2 (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    player_id = c.lastrowid
    conn.close()
    await update.message.reply_text(f"✅ PLAYER ADDED!\n\nID: {player_id} | {name}\n💰 Price: {price:,} 💰")

async def setprice2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /setprice2 <id> <new_price>')
        return
    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid input!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM shop2 WHERE id=?", (player_id,))
    player = c.fetchone()
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    c.execute("UPDATE shop2 SET price = ? WHERE id=?", (new_price, player_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ PRICE UPDATED!\n{player[0]}\n💰 New Price: {new_price:,} 💰")

async def removeplayer2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /removeplayer2 <id>')
        return
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid ID!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM shop2 WHERE id=?", (player_id,))
    player = c.fetchone()
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    c.execute("DELETE FROM shop2 WHERE id=?", (player_id,))
    c.execute("DELETE FROM user_players2 WHERE player_id=?", (player_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ PLAYER REMOVED!\n{player[0]}")


# ============ BANK SYSTEM ==========
async def bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bank (user_id, balance, last_interest) VALUES (?, 0, ?)", (user_id, datetime.now().isoformat()))
    c.execute("SELECT balance, last_interest FROM bank WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if row:
        bank_bal, last_interest = row
    else:
        bank_bal, last_interest = 0, None
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    wallet_bal = c.fetchone()[0]
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
    conn.close()
    await update.message.reply_text(f"🏦 MY BANK ACCOUNT\n\n💰 Bank Balance: {bank_bal:,} 💰\n👛 Wallet Balance: {wallet_bal:,} 💰\n📈 Interest Rate: 5% daily\n⏰ Next interest: {next_time_str}\n\n━━━━━━━━━━━━━━━━━━━━━━\n💡 /deposit <amount>\n💡 /withdraw <amount>\n💡 /claim_interest")

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
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
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bank (user_id, balance, last_interest) VALUES (?, 0, ?)", (user_id, datetime.now().isoformat()))
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    wallet_bal = c.fetchone()[0]
    if wallet_bal < amount:
        await update.message.reply_text(f'❌ Insufficient wallet balance!\n\nNeed: {amount:,} 💰\nHave: {wallet_bal:,} 💰')
        conn.close()
        return
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id))
    c.execute("UPDATE bank SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_wallet = c.fetchone()[0]
    c.execute("SELECT balance FROM bank WHERE user_id=?", (user_id,))
    new_bank = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"✅ DEPOSITED!\n\nAmount: +{amount:,} 💰\nWallet: {wallet_bal:,} → {new_wallet:,} 💰\nBank: {new_bank - amount:,} → {new_bank:,} 💰")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
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
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bank (user_id, balance, last_interest) VALUES (?, 0, ?)", (user_id, datetime.now().isoformat()))
    c.execute("SELECT balance FROM bank WHERE user_id=?", (user_id,))
    bank_bal = c.fetchone()[0]
    if bank_bal < amount:
        await update.message.reply_text(f'❌ Insufficient bank balance!\n\nNeed: {amount:,} 💰\nHave: {bank_bal:,} 💰')
        conn.close()
        return
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    c.execute("UPDATE bank SET balance = balance - ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    c.execute("SELECT balance FROM bank WHERE user_id=?", (user_id,))
    new_bank = c.fetchone()[0]
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_wallet = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"✅ WITHDRAWN!\n\nAmount: -{amount:,} 💰\nBank: {bank_bal:,} → {new_bank:,} 💰\nWallet: {new_wallet - amount:,} → {new_wallet:,} 💰")

async def claim_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO bank (user_id, balance, last_interest) VALUES (?, 0, ?)", (user_id, datetime.now().isoformat()))
    c.execute("SELECT balance, last_interest FROM bank WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        await update.message.reply_text('❌ No bank account found! Use /bank first.')
        conn.close()
        return
    bank_bal, last_interest = row
    now = datetime.now()
    if last_interest:
        last = datetime.fromisoformat(last_interest)
        next_time = last + timedelta(hours=24)
        if now < next_time:
            remaining = next_time - now
            hours = remaining.seconds // 3600
            mins = (remaining.seconds % 3600) // 60
            await update.message.reply_text(f"⏰ Interest not ready yet!\n\nCome back in {hours}h {mins}m")
            conn.close()
            return
    interest = int(bank_bal * 0.05)
    new_bank = bank_bal + interest
    c.execute("UPDATE bank SET balance = ?, last_interest = ? WHERE user_id=?", (new_bank, now.isoformat(), user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"💰 INTEREST CLAIMED!\n\nRate: 5%\nInterest: +{interest:,} 💰\nNew Bank Balance: {new_bank:,} 💰\n\n⏰ Next interest: 24h")
# ============ ADMIN CRICKET COMMANDS ============
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
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO matches (team1, team2, date, status, locked) VALUES (?, ?, ?, 'upcoming', 0)", (team1, team2, date))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ MATCH ADDED!\n\n🏏 {team1} vs {team2}\n📅 {date}\n🔓 Status: OPEN")

async def deletematch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('❌ /deletematch TEAM1 vs TEAM2 [refund]')
        return
    team1 = args[0].upper()
    team2 = args[2].upper()
    do_refund = len(args) > 3 and args[3].lower() == 'refund'
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2 FROM matches WHERE (team1=? AND team2=?)", (team1, team2))
    match = c.fetchone()
    if not match:
        await update.message.reply_text(f'❌ Match not found!')
        conn.close()
        return
    c.execute("SELECT user_id, amount FROM bets WHERE match_id=?", (match[0],))
    bets = c.fetchall()
    refund_count = 0
    refund_total = 0
    if do_refund and bets:
        for bet in bets:
            user_id, amount = bet
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
            refund_count += 1
            refund_total += amount
        c.execute("UPDATE users SET total = total - ? WHERE user_id IN (SELECT user_id FROM bets WHERE match_id=?)", (refund_count, match[0]))
        conn.commit()
    c.execute("DELETE FROM bets WHERE match_id=?", (match[0],))
    c.execute("DELETE FROM matches WHERE id=?", (match[0],))
    conn.commit()
    conn.close()
    if do_refund and refund_count > 0:
        await update.message.reply_text(f"🗑️ MATCH DELETED + REFUNDED!\n\n🏏 {match[1]} vs {match[2]}\n💰 Refunded: {refund_count} users\n💰 Total refund: {refund_total:,} credits")
    elif do_refund and refund_count == 0:
        await update.message.reply_text(f"🗑️ MATCH DELETED!\n\n🏏 {match[1]} vs {match[2]}\nℹ️ No bets to refund")
    else:
        await update.message.reply_text(f"🗑️ MATCH DELETED WITHOUT REFUND!\n\n🏏 {match[1]} vs {match[2]}\n⚠️ {len(bets)} users lost their bets!")

async def lockmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('❌ /lockmatch TEAM1 vs TEAM2')
        return
    team1 = args[0].upper()
    team2 = args[2].upper()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2 FROM matches WHERE (team1=? AND team2=?)", (team1, team2))
    match = c.fetchone()
    if not match:
        await update.message.reply_text(f'❌ Match not found!')
        conn.close()
        return
    c.execute("UPDATE matches SET locked=1 WHERE id=?", (match[0],))
    c.execute("SELECT COUNT(*), SUM(amount) FROM bets WHERE match_id=?", (match[0],))
    result = c.fetchone()
    count = result[0] or 0
    total = result[1] or 0
    conn.commit()
    conn.close()
    await update.message.reply_text(f"🔒 MATCH LOCKED!\n\n🏏 {match[1]} vs {match[2]}\n📊 Bets: {count}\n💰 Pool: {total:,} 💰\n❌ No more bets accepted!")

async def result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text('❌ /result TEAM1 vs TEAM2 WINNER')
        return
    team1 = args[0].upper()
    team2 = args[2].upper()
    winner = args[3].upper()
    if winner not in [team1, team2]:
        await update.message.reply_text(f'❌ Winner must be {team1} or {team2}!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2 FROM matches WHERE (team1=? AND team2=?)", (team1, team2))
    match = c.fetchone()
    if not match:
        await update.message.reply_text(f'❌ Match not found!')
        conn.close()
        return
    c.execute("SELECT user_id, amount, team FROM bets WHERE match_id=?", (match[0],))
    bets = c.fetchall()
    winners = 0
    losers = 0
    total_paid = 0
    winner_list = []
    loser_list = []
    points_given = {}
    points_deducted = {}
    for bet in bets:
        user_id = bet[0]
        amount = bet[1]
        bet_team = bet[2].upper()
        c.execute("SELECT balance, won, points, name FROM users WHERE user_id=?", (user_id,))
        u = c.fetchone()
        if bet_team == winner:
            win_amount = amount * 2
            new_balance = u[0] + win_amount
            new_won = u[1] + 1
            if user_id not in points_given:
                new_points = u[2] + 10
                points_given[user_id] = True
            else:
                new_points = u[2]
            c.execute("UPDATE users SET balance = ?, won = ?, points = ? WHERE user_id=?", (new_balance, new_won, new_points, user_id))
            total_paid += win_amount
            winners += 1
            winner_list.append(f"{u[3]} - {amount} → {win_amount} (+{amount})")
        else:
            if user_id not in points_deducted:
                new_points = u[2] - 5
                points_deducted[user_id] = True
            else:
                new_points = u[2]
            c.execute("UPDATE users SET points = ? WHERE user_id=?", (new_points, user_id))
            losers += 1
            loser_list.append(f"{u[3]} - {amount} → 0 (-{amount})")
    c.execute("DELETE FROM bets WHERE match_id=?", (match[0],))
    c.execute("DELETE FROM matches WHERE id=?", (match[0],))
    conn.commit()
    conn.close()
    msg = f"📢 MATCH RESULT!\n\n🏏 {match[1]} vs {match[2]}\n🏆 WINNER: {winner}\n\n"
    msg += f"✅ WINNERS (+10 pts): {winners} users\n"
    for w in winner_list[:5]:
        msg += f"   • {w}\n"
    if len(winner_list) > 5:
        msg += f"   • +{len(winner_list)-5} more\n"
    msg += f"\n❌ LOSERS (-5 pts): {losers} users\n"
    for l in loser_list[:5]:
        msg += f"   • {l}\n"
    if len(loser_list) > 5:
        msg += f"   • +{len(loser_list)-5} more\n"
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💰 TOTAL PAYOUT: {total_paid:,} 💰"
    await update.message.reply_text(msg)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    if not update.message.reply_to_message:
        await update.message.reply_text('❌ Reply to user with /add AMOUNT')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /add AMOUNT')
        return
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid amount')
        return
    target = update.message.reply_to_message.from_user
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, name FROM users WHERE user_id=?", (target.id,))
    old = c.fetchone()
    if not old:
        await update.message.reply_text('❌ User not found!')
        conn.close()
        return
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, target.id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ ADDED {amount:,} to {old[1]}\n💰 Balance: {old[0]:,} → {old[0]+amount:,} 💰")

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    if not update.message.reply_to_message:
        await update.message.reply_text('❌ Reply to user with /remove AMOUNT')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /remove AMOUNT')
        return
    try:
        amount = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid amount')
        return
    target = update.message.reply_to_message.from_user
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, name FROM users WHERE user_id=?", (target.id,))
    old = c.fetchone()
    if not old:
        await update.message.reply_text('❌ User not found!')
        conn.close()
        return
    if old[0] < amount:
        await update.message.reply_text(f'❌ Insufficient! Balance: {old[0]:,} 💰')
        conn.close()
        return
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, target.id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"❌ REMOVED {amount:,} from {old[1]}\n💰 Balance: {old[0]:,} → {old[0]-amount:,} 💰")

async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /setprice <player_id> <new_price>')
        return
    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid input!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM shop WHERE id=?", (player_id,))
    player = c.fetchone()
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    c.execute("UPDATE shop SET price = ? WHERE id=?", (new_price, player_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ PRICE UPDATED!\n\n{player[0]}\n💰 New Price: {new_price:,} 💰")

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
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO achievements (user_id, achievement) VALUES (?, ?)", (target.id, achievement))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ ACHIEVEMENT GIVEN!\n\nUser: {target.first_name}\nAchievement: {achievement} 🏆")

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
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT rowid, achievement FROM achievements WHERE user_id=?", (target_id,))
    ach = c.fetchall()
    if num < 1 or num > len(ach):
        await update.message.reply_text(f'❌ Choose 1-{len(ach)}')
        conn.close()
        return
    removed = ach[num-1]
    c.execute("DELETE FROM achievements WHERE rowid=?", (removed[0],))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ ACHIEVEMENT REMOVED!\n\nRemoved: {removed[1]} 🏆")

async def unlockmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('❌ /unlockmatch TEAM1 vs TEAM2')
        return
    team1 = args[0].upper()
    team2 = args[2].upper()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2, locked FROM matches WHERE (team1=? AND team2=?)", (team1, team2))
    match = c.fetchone()
    if not match:
        await update.message.reply_text(f'❌ Match not found!')
        conn.close()
        return
    if match[3] == 0:
        await update.message.reply_text(f'⚠️ Match is already UNLOCKED!')
        conn.close()
        return
    c.execute("UPDATE matches SET locked=0 WHERE id=?", (match[0],))
    conn.commit()
    c.execute("SELECT COUNT(*), SUM(amount) FROM bets WHERE match_id=?", (match[0],))
    result = c.fetchone()
    count = result[0] or 0
    total = result[1] or 0
    conn.close()
    await update.message.reply_text(f"🔓 MATCH UNLOCKED!\n\n🏏 {match[1]} vs {match[2]}\n📊 Current Bets: {count}\n💰 Current Pool: {total:,} 💰\n✅ New bets are now accepted again!")


# ============ CLCRICKET (COMPLETE WITH STATS) ============
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

def update_cricket_stats_realtime(user_id, name, runs_added=0, wickets_added=0, current_match_runs=0):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM cricket_stats WHERE user_id=?", (user_id,))
    stats = c.fetchone()
    if stats:
        new_runs = stats[2] + runs_added
        new_wickets = stats[3] + wickets_added
        new_highest = stats[6]
        if current_match_runs > new_highest:
            new_highest = current_match_runs
        c.execute("UPDATE cricket_stats SET runs=?, wickets=?, highest_score=? WHERE user_id=?", (new_runs, new_wickets, new_highest, user_id))
    else:
        c.execute("INSERT INTO cricket_stats (user_id, name, runs, wickets, highest_score) VALUES (?, ?, ?, ?, ?)", (user_id, name, runs_added, wickets_added, current_match_runs))
    conn.commit()
    conn.close()

def update_wins_losses_realtime(user_id, name, won):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM cricket_stats WHERE user_id=?", (user_id,))
    stats = c.fetchone()
    if stats:
        if won:
            c.execute("UPDATE cricket_stats SET wins = wins + 1 WHERE user_id=?", (user_id,))
        else:
            c.execute("UPDATE cricket_stats SET losses = losses + 1 WHERE user_id=?", (user_id,))
    else:
        c.execute("INSERT INTO cricket_stats (user_id, name, wins, losses) VALUES (?, ?, ?, ?)", (user_id, name, 1 if won else 0, 0 if won else 1))
    conn.commit()
    conn.close()

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
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    args = context.args
    bet = 0
    if args:
        try:
            bet = int(args[0])
            if bet < 100:
                await update.message.reply_text("❌ Minimum bet is 100 credits!")
                return
        except:
            await update.message.reply_text("❌ Invalid bet amount!")
            return
    if bet > 0:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = c.fetchone()[0]
        conn.close()
        if balance < bet:
            await update.message.reply_text(f"❌ You need {bet:,} credits to play!")
            return
    global cricket_next_id
    game_id = cricket_next_id
    cricket_next_id += 1
    cricket_lobby[game_id] = {"creator_id": user_id, "creator_name": user_name, "bet": bet, "chat_id": chat_id}
    bet_text = f"💰 Bet: {bet} | Prize: {bet*2}" if bet > 0 else "🎮 Normal Game"
    await update.message.reply_text(f"🏏 CRICKET GAME\n\n👑 Host: {user_name}\n{bet_text}\n\n━━━━━━━━━━━━━━━━━━━━\n⚡ Select Mode:", reply_markup=InlineKeyboardMarkup([
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
        await query.edit_message_text("❌ Game expired!")
        return
    
    lobby = cricket_lobby[game_id]
    if update.effective_user.id != lobby["creator_id"]:
        await query.answer("Only host can select mode!", show_alert=True)
        return
    
    lobby["mode"] = mode
    bet_text = f"💰 Bet: {lobby['bet']} | Prize: {lobby['bet']*2}" if lobby['bet'] > 0 else "🎮 Normal Game"
    
    await query.edit_message_text(
        f"🏏 CRICKET GAME\n\n👑 Host: {lobby['creator_name']}\n{bet_text}\n\n━━━━━━━━━━━━━━━━━━━━\n⚡ Waiting for opponent...",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔵 JOIN GAME", callback_data=f"cricket_join_{game_id}")]])
    )


async def cricket_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = query.data
    game_id = int(data.split("_")[2])
    
    if game_id not in cricket_lobby:
        await query.edit_message_text("❌ Game expired!")
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
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        result = c.fetchone()
        if not result:
            await query.edit_message_text("❌ Send /start first!")
            conn.close()
            return
        balance = result[0]
        conn.close()
        if balance < bet:
            await query.answer(f"❌ Need {bet} credits!", show_alert=True)
            return
        
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, creator_id))
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, user_id))
        conn.commit()
        conn.close()
    
    game = CricketGame(game_id, creator_id, creator_name, bet, chat_id, mode)
    game.player2_id = user_id
    game.player2_name = user_name
    game.game_active = True
    cricket_games[game_id] = game
    del cricket_lobby[game_id]
    
    await query.edit_message_text(
        f"🏏 CRICKET GAME\n\n{creator_name} vs {user_name}\n" + (f"💰 Bet: {bet} | Prize: {bet*2}\n" if bet > 0 else "") + f"\n🪙 TOSS TIME!\n\n{creator_name}, choose:",
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
        f"🏏 CRICKET GAME\n\n🪙 TOSS: {toss.upper()}!\n🏆 {winner_name} won the toss!\n\nChoose:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏏 BAT", callback_data=f"cricket_choice_{game_id}_bat")],
            [InlineKeyboardButton("🎯 BOWL", callback_data=f"cricket_choice_{game_id}_bowl")]
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
        f"🏏 CRICKET GAME\n\n{batsman} Batting | {bowler} Bowling\n" + 
        (f"💰 Bet: {game.bet}\n" if game.bet > 0 else "") + 
        f"📊 {game.score}/{game.wickets}\n\n🎯 {bowler}'s turn:",
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
        f"🏏 CRICKET GAME\n\n{batsman_name}, choose your shot:\n📊 {game.score}/{game.wickets} | {game.get_overs()} overs",
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
        # UPDATE WICKET STATS
        if game.current_bowler == game.player1_id:
            game.player1_wickets_taken += 1
            update_cricket_stats_realtime(game.player1_id, game.player1_name, 0, 1, 0)
        else:
            game.player2_wickets_taken += 1
            update_cricket_stats_realtime(game.player2_id, game.player2_name, 0, 1, 0)
        
        game.wickets += 1
        game.balls += 1
        
        # First innings (target not set yet)
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
                f"🏏 CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\n❌ OUT!\n\n"
                f"📊 First Innings Score: {game.target - 1}\n🎯 Target: {game.target}\n\n"
                f"{batsman_name} Batting | {bowler_name} Bowling\n"
                f"📊 {game.score}/{game.wickets} | {game.get_overs()} overs\n\n"
                f"🎯 {bowler_name}'s turn:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Second innings - Check for DRAW
        else:
            if game.score == game.target - 1:
                game.game_active = False
                
                if game.bet > 0:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet, game.player1_id))
                    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet, game.player2_id))
                    conn.commit()
                    conn.close()
                
                await query.edit_message_text(
                    f"🏏 CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\n❌ OUT!\n\n"
                    f"📊 Final: {game.score}/{game.wickets}\n🎯 Target: {game.target}\n\n"
                    f"🤝 DRAW! 🤝" + (f"\n💰 Money returned: {game.bet} each" if game.bet > 0 else "")
                )
                del cricket_games[game_id]
                return
            
            # Normal loss
            else:
                game.game_active = False
                game.winner = game.player2_id if game.current_batsman == game.player1_id else game.player1_id
                loser_id = game.player2_id if game.winner == game.player1_id else game.player1_id
                loser_name = game.player2_name if game.winner == game.player1_id else game.player1_name
                
                # UPDATE WINS/LOSSES
                update_wins_losses_realtime(game.winner, game.player1_name if game.winner == game.player1_id else game.player2_name, True)
                update_wins_losses_realtime(loser_id, loser_name, False)
                
                if game.bet > 0:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet*2, game.winner))
                    conn.commit()
                    conn.close()
                
                winner_name = game.player1_name if game.winner == game.player1_id else game.player2_name
                
                await query.edit_message_text(
                    f"🏏 CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\n❌ OUT!\n\n"
                    f"📊 Final: {game.score}/{game.wickets}\n🎯 Target: {game.target}\n\n"
                    f"🏆 WINNER: {winner_name} 🏆" + (f"\n💰 Prize: {game.bet*2}" if game.bet > 0 else "")
                )
                del cricket_games[game_id]
                return
    
    # SAFE - Add runs
    else:
        # UPDATE RUNS STATS
        if game.current_batsman == game.player1_id:
            game.player1_match_runs += shot
            update_cricket_stats_realtime(game.player1_id, game.player1_name, shot, 0, game.player1_match_runs)
        else:
            game.player2_match_runs += shot
            update_cricket_stats_realtime(game.player2_id, game.player2_name, shot, 0, game.player2_match_runs)
        
        game.score += shot
        game.balls += 1
        
        # Check if target reached (second innings win)
        if game.target and game.score >= game.target:
            game.game_active = False
            game.winner = game.current_batsman
            loser_id = game.player2_id if game.winner == game.player1_id else game.player1_id
            loser_name = game.player2_name if game.winner == game.player1_id else game.player1_name
            
            # UPDATE WINS/LOSSES
            update_wins_losses_realtime(game.winner, game.player1_name if game.winner == game.player1_id else game.player2_name, True)
            update_wins_losses_realtime(loser_id, loser_name, False)
            
            if game.bet > 0:
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet*2, game.winner))
                conn.commit()
                conn.close()
            
            winner_name = game.player1_name if game.winner == game.player1_id else game.player2_name
            
            await query.edit_message_text(
                f"🏏 CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\n✅ {shot} runs!\n\n"
                f"📊 Final: {game.score}/{game.wickets}\n🎯 Target: {game.target}\n\n"
                f"🏆 WINNER: {winner_name} 🏆" + (f"\n💰 Prize: {game.bet*2}" if game.bet > 0 else "")
            )
            del cricket_games[game_id]
            return
        
        # Continue game
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
            f"🏏 CRICKET GAME\n\n{bowler} bowled: {delivery_name}\n{batsman} played: {shot}\n\n✅ {shot} runs!\n\n"
            f"{batsman_name} Batting | {bowler_name} Bowling\n"
            f"📊 {game.score}/{game.wickets} | {game.get_overs()} overs\n\n"
            f"🎯 {bowler_name}'s turn:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ============ MINES GAME (Fixed - Only owner can play) ============

active_mines = {}      # game_id -> game data
mines_owner = {}       # game_id -> owner user_id  
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
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "💣 MINES\n"
            "/mines <amount> <bombs>\n"
            "Example: /mines 1000 3\n\n"
            "Min:100 | Max:10,000\n"
            "Bombs:1-24\n"
            "More bombs = bigger reward!"
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
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    conn.close()
    
    if balance < bet:
        await update.message.reply_text(f"❌ Need {bet:,} credits, you have {balance:,}")
        return
    
    # Deduct bet amount
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, user_id))
    conn.commit()
    conn.close()
    
    # Create game with unique ID
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
    
    # Create keyboard with game_id in callback
    keyboard = []
    for i in range(5):
        row = []
        for j in range(5):
            pos = i * 5 + j
            row.append(InlineKeyboardButton("❓", callback_data=f"mine_{game_id}_{pos}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("💰 CASHOUT", callback_data=f"mine_cashout_{game_id}")])
    
    await update.message.reply_text(
        f"💣 MINES GAME STARTED\n\n"
        f"💰 Bet: {bet:,} credits\n"
        f"💣 Bombs: {bombs}\n"
        f"🎯 Max Multiplier: {max_mult}x\n"
        f"💎 Current: 1.00x | {bet:,} credits\n\n"
        f"Click tiles to reveal safe spots. Don't hit a bomb!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def mine_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    # Extract game_id from callback data
    parts = data.split("_")
    if parts[1] == "cashout":
        game_id = int(parts[2])
    else:
        game_id = int(parts[1])
    
    # 🔥 CRITICAL CHECK 1: Does game exist?
    if game_id not in active_mines:
        await query.answer("Game not found or expired!", show_alert=True)
        await query.edit_message_text("❌ No active game found. Use /mines to start a new game.")
        return
    
    game = active_mines[game_id]
    
    # 🔥 CRITICAL CHECK 2: Only game owner can play
    if game['owner_id'] != user_id:
        await query.answer("This is not your game!", show_alert=True)
        return
    
    # Handle cashout
    if data.startswith("mine_cashout_"):
        safe_count = len([t for t in game['revealed'] if t not in game['bombs']])
        multiplier = calc_multiplier(game['bomb_count'], safe_count)
        win_amount = int(game['bet'] * multiplier)
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        current_balance = c.fetchone()[0]
        new_balance = current_balance + win_amount
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_balance, user_id))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"💰 CASHOUT SUCCESSFUL!\n\n"
            f"💎 Multiplier: {multiplier}x\n"
            f"✅ Safe tiles: {safe_count}/{25 - game['bomb_count']}\n"
            f"💰 Won: {win_amount:,} credits\n"
            f"💳 New balance: {new_balance:,} credits"
        )
        
        del active_mines[game_id]
        del mines_owner[game_id]
        return
    
    # Handle tile click
    position = int(parts[2])
    
    if position in game['revealed']:
        await query.answer("You already revealed this tile!", show_alert=True)
        return
    
    game['revealed'].append(position)
    
    # Check if bomb
    if position in game['bombs']:
        await query.edit_message_text(
            f"💣 BOOM! YOU HIT A BOMB!\n\n"
            f"💰 Lost: {game['bet']:,} credits\n"
            f"😵 Game Over!\n\n"
            f"Use /mines to play again."
        )
        del active_mines[game_id]
        del mines_owner[game_id]
        return
    
    # Safe tile
    safe_count = len([t for t in game['revealed'] if t not in game['bombs']])
    total_safe = 25 - game['bomb_count']
    multiplier = calc_multiplier(game['bomb_count'], safe_count)
    current_win = int(game['bet'] * multiplier)
    
    # Check if all safe tiles revealed (win)
    if safe_count >= total_safe:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        current_balance = c.fetchone()[0]
        new_balance = current_balance + current_win
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_balance, user_id))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"🎉 PERFECT WIN! 🎉\n\n"
            f"✅ All {total_safe} safe tiles revealed!\n"
            f"💎 Multiplier: {multiplier}x\n"
            f"💰 Won: {current_win:,} credits\n"
            f"💳 New balance: {new_balance:,} credits"
        )
        del active_mines[game_id]
        del mines_owner[game_id]
        return
    
    # Update keyboard
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
    
    remaining = total_safe - safe_count
    max_mult = game['max_mult']
    
    await query.edit_message_text(
        f"💎 SAFE TILE!\n\n"
        f"💰 Bet: {game['bet']:,}\n"
        f"✅ Safe found: {safe_count}/{total_safe}\n"
        f"💎 Current multiplier: {multiplier}x\n"
        f"💰 Cashout value: {current_win:,}\n"
        f"🎯 Max multiplier: {max_mult}x\n"
        f"💚 Remaining safe tiles: {remaining}\n\n"
        f"Click another tile or CASHOUT!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ============ SHOP3 ============
async def shop3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM shop3 ORDER BY price ASC")
    players = c.fetchall()
    conn.close()
    
    if not players:
        await update.message.reply_text('🛒 SHOP3\n\nNo players yet.\n👑 Admin: /addplayer3 <name> <price>')
        return
    
    msg = "🛒 SHOP3\n\n"
    for p in players:
        msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n💡 /buy3 <id> to purchase"
    await update.message.reply_text(msg)

async def buy3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /buy3 <player_id>\nExample: /buy3 1')
        return
    
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid ID')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, price FROM shop3 WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < player[1]:
        await update.message.reply_text(f'❌ Need {player[1]:,}, have {balance:,}')
        conn.close()
        return
    
    c.execute("SELECT * FROM user_players3 WHERE user_id=? AND player_id=?", (user_id, player_id))
    if c.fetchone():
        await update.message.reply_text(f'❌ You already own {player[0]}!')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (player[1], user_id))
    c.execute("INSERT INTO user_players3 (user_id, player_id) VALUES (?, ?)", (user_id, player_id))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"✅ PURCHASED!\n\n🏏 {player[0]}\n💰 Price: {player[1]:,} 💰\n📊 New balance: {new_bal:,} 💰")

async def myteam3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT s.name, s.price FROM user_players3 u JOIN shop3 s ON u.player_id=s.id WHERE u.user_id=?", (user_id,))
    players = c.fetchall()
    conn.close()
    
    if not players:
        await update.message.reply_text('📭 No shop3 players owned.\nUse /shop3 to buy!')
        return
    
    total = sum(p[1] for p in players)
    msg = "💎 MY SHOP3 PLAYERS\n\n"
    for i, p in enumerate(players, 1):
        msg += f"{i}. {p[0]} - {p[1]:,} 💰\n"
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💰 Total spent: {total:,} 💰"
    await update.message.reply_text(msg)

async def top3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(s.price), 0) as total FROM users u JOIN user_players3 up ON u.user_id=up.user_id JOIN shop3 s ON up.player_id=s.id GROUP BY u.user_id ORDER BY total DESC LIMIT 10")
    tops = c.fetchall()
    
    if not tops:
        await update.message.reply_text('🏆 SHOP3 TOP COLLECTORS\n\nNo one owns any yet!')
        conn.close()
        return
    
    msg = "🏆 SHOP3 TOP COLLECTORS\n\n"
    for i, t in enumerate(tops, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {t[0]} - {t[1]} players ({t[2]:,} 💰)\n"
    
    c.execute("SELECT COUNT(*) FROM user_players3 WHERE user_id=?", (user_id,))
    my_count = c.fetchone()[0]
    msg += f"\n📊 You own: {my_count} players"
    await update.message.reply_text(msg)
    conn.close()

async def addplayer3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /addplayer3 <name> <price>')
        return
    
    name = ' '.join(args[:-1])
    try:
        price = int(args[-1])
    except:
        await update.message.reply_text('❌ Invalid price!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO shop3 (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    player_id = c.lastrowid
    conn.close()
    
    await update.message.reply_text(f"✅ PLAYER ADDED TO SHOP3!\n\nID: {player_id} | {name}\n💰 Price: {price:,} 💰")

async def setprice3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /setprice3 <id> <new_price>')
        return
    
    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid input!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM shop3 WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("UPDATE shop3 SET price = ? WHERE id=?", (new_price, player_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ SHOP3 PRICE UPDATED!\n{player[0]}\nNew Price: {new_price:,} 💰")

async def removeplayer3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /removeplayer3 <id>')
        return
    
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid ID!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM shop3 WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("DELETE FROM shop3 WHERE id=?", (player_id,))
    c.execute("DELETE FROM user_players3 WHERE player_id=?", (player_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ PLAYER REMOVED FROM SHOP3!\n{player[0]}")

# ============ CLAIM CODE SYSTEM ============

def init_claimcode_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS claim_codes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  code TEXT UNIQUE,
                  amount INTEGER,
                  max_claims INTEGER,
                  claimed_count INTEGER DEFAULT 0,
                  created_by INTEGER,
                  created_at TEXT,
                  expires_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS code_claims 
                 (code TEXT, user_id INTEGER, claimed_at TEXT,
                  PRIMARY KEY (code, user_id))''')
    conn.commit()
    conn.close()

init_claimcode_db()

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
        max_claims = 5
    except:
        await update.message.reply_text("❌ Invalid!")
        return
    
    if amount < 100:
        await update.message.reply_text("❌ Minimum amount 100 credits!")
        return
    
    if len(code) > 20:
        await update.message.reply_text("❌ Code too long! Max 20 chars")
        return
    
    now = datetime.now()
    expires_at = now + timedelta(hours=24)
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT code FROM claim_codes WHERE code = ?", (code,))
    if c.fetchone():
        await update.message.reply_text(f"❌ Code '{code}' already exists!")
        conn.close()
        return
    
    c.execute("INSERT INTO claim_codes (code, amount, max_claims, created_by, created_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
              (code, amount, max_claims, update.effective_user.id, now.isoformat(), expires_at.isoformat()))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ CODE CREATED!\n\n🔑 Code: {code}\n💰 Amount: {amount:,} credits\n👥 Max claims: {max_claims} users\n⏰ Expires: 24 hours\n\nUsers can claim with: /claimcode {code}")

async def claimcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: /claimcode <code>\nExample: /claimcode FESTIVAL10")
        return
    
    code = args[0].upper()
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT code, amount, max_claims, claimed_count, expires_at FROM claim_codes WHERE code = ?", (code,))
    result = c.fetchone()
    
    if not result:
        await update.message.reply_text(f"❌ Code '{code}' not found!\n💡 Try /activecodes")
        conn.close()
        return
    
    code_name, amount, max_claims, claimed_count, expires_at = result
    
    expires = datetime.fromisoformat(expires_at)
    if datetime.now() > expires:
        await update.message.reply_text(f"❌ Code '{code}' has expired!")
        conn.close()
        return
    
    c.execute("SELECT * FROM code_claims WHERE code = ? AND user_id = ?", (code, user_id))
    if c.fetchone():
        await update.message.reply_text(f"❌ You already claimed code '{code}'!")
        conn.close()
        return
    
    if claimed_count >= max_claims:
        await update.message.reply_text(f"❌ Code '{code}' has reached max claims!")
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    c.execute("UPDATE claim_codes SET claimed_count = claimed_count + 1 WHERE code = ?", (code,))
    c.execute("INSERT INTO code_claims (code, user_id, claimed_at) VALUES (?, ?, ?)",
              (code, user_id, datetime.now().isoformat()))
    conn.commit()
    
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    new_bal = c.fetchone()[0]
    remaining = max_claims - (claimed_count + 1)
    conn.close()
    
    await update.message.reply_text(f"🎉 CODE CLAIMED!\n\n🔑 Code: {code}\n💰 +{amount:,} credits\n💳 New balance: {new_bal:,}\n📊 Remaining: {remaining}/{max_claims}")

async def activecodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    now = datetime.now().isoformat()
    c.execute("SELECT code, amount, max_claims, claimed_count, expires_at FROM claim_codes WHERE expires_at > ? AND claimed_count < max_claims ORDER BY created_at DESC LIMIT 10", (now,))
    codes = c.fetchall()
    conn.close()
    
    if not codes:
        await update.message.reply_text("📭 NO ACTIVE CODES\n\nNo codes available right now!\nCheck back later for rewards! 🎁")
        return
    
    msg = "🎁 ACTIVE CLAIM CODES\n\n"
    for code, amount, max_c, claimed, expires in codes:
        remaining = max_c - claimed
        msg += f"🔑 {code}\n💰 {amount:,} credits\n👥 {remaining}/{max_c} left\n💡 /claimcode {code}\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━\nUse /claimcode <code> to claim!"
    await update.message.reply_text(msg)

async def deletecode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: /deletecode CODE123")
        return
    
    code = args[0].upper()
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT code FROM claim_codes WHERE code = ?", (code,))
    if not c.fetchone():
        await update.message.reply_text(f"❌ Code '{code}' not found!")
        conn.close()
        return
    
    c.execute("DELETE FROM claim_codes WHERE code = ?", (code,))
    c.execute("DELETE FROM code_claims WHERE code = ?", (code,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Code '{code}' deleted!")

async def codestats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM claim_codes")
    total_codes = c.fetchone()[0]
    
    now = datetime.now().isoformat()
    c.execute("SELECT COUNT(*) FROM claim_codes WHERE expires_at > ? AND claimed_count < max_claims", (now,))
    active_codes = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM code_claims")
    total_claims = c.fetchone()[0]
    
    c.execute("SELECT SUM(amount) FROM code_claims cc JOIN claim_codes c ON cc.code = c.code")
    total_given = c.fetchone()[0] or 0
    
    c.execute("SELECT COUNT(DISTINCT user_id) FROM code_claims")
    unique_users = c.fetchone()[0] or 0
    
    conn.close()
    
    await update.message.reply_text(f"📊 CODE STATS\n\n📝 Total codes: {total_codes}\n🟢 Active codes: {active_codes}\n🎯 Total claims: {total_claims}\n💰 Credits given: {total_given:,}\n👥 Unique users: {unique_users}")

# ============ TIC TAC TOE ============
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
            return False, "Position already taken!"
        
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
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    bet = 0
    if args:
        try:
            bet = int(args[0])
            if bet < 100:
                await update.message.reply_text("❌ Minimum bet is 100 credits!")
                return
        except:
            await update.message.reply_text("❌ Invalid bet amount!")
            return
    
    if bet > 0:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        balance = c.fetchone()[0]
        conn.close()
        if balance < bet:
            await update.message.reply_text(f"❌ You need {bet:,} credits!")
            return
    
    global ttt_next_id
    game_id = ttt_next_id
    ttt_next_id += 1
    
    ttt_lobby[game_id] = {
        "creator_id": user_id,
        "creator_name": user_name,
        "bet": bet,
        "chat_id": chat_id
    }
    
    keyboard = [[InlineKeyboardButton("🔵 JOIN GAME", callback_data=f"ttt_join_{game_id}")]]
    bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Normal Game"
    
    await update.message.reply_text(
        f"🎯 TIC TAC TOE\n\n"
        f"👑 {user_name} (❌)\n"
        f"{bet_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Waiting for opponent...",
        reply_markup=InlineKeyboardMarkup(keyboard),
        
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
            await query.edit_message_text("❌ Game lobby expired!")
            return
        
        lobby = ttt_lobby[game_id]
        creator_id = lobby["creator_id"]
        creator_name = lobby["creator_name"]
        bet = lobby["bet"]
        chat_id = lobby["chat_id"]
        
        if creator_id == user_id:
            await query.answer("You cannot join your own game!", show_alert=True)
            return
        
        if bet > 0:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            balance = c.fetchone()[0]
            conn.close()
            if balance < bet:
                await query.edit_message_text(f"❌ You need {bet:,} credits to join!")
                return
            
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, creator_id))
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, user_id))
            conn.commit()
            conn.close()
        
        game = TicTacToe(game_id, creator_id, creator_name, user_name, bet, chat_id)
        game.player2_id = user_id
        game.game_active = True
        ttt_games[game_id] = game
        del ttt_lobby[game_id]
        
        bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Normal Game"
        
        await query.edit_message_text(
            f"🎯 TIC TAC TOE\n\n"
            f"❌ {creator_name} vs ⭕ {user_name}\n"
            f"{bet_text}\n\n"
            f"🎯 {creator_name}'s Turn",
            reply_markup=game.get_keyboard(),
            
        )
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
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT balance FROM users WHERE user_id=?", (winner_id,))
                current_bal = c.fetchone()[0]
                new_bal = current_bal + (game.bet * 2)
                c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, winner_id))
                conn.commit()
                conn.close()
                result_text = f"🏆 WINNER: {winner_name.upper()} 🏆\n💰 +{game.bet*2:,} credits\n💳 New Balance: {new_bal:,}"
            else:
                result_text = f"🏆 WINNER: {winner_name.upper()} 🏆"
            
            await query.edit_message_text(
                f"🎯 TIC TAC TOE\n\n"
                f"❌ {game.player1_name} vs ⭕ {game.player2_name}\n\n"
                f"{result_text}",
                reply_markup=game.get_keyboard(),
                
            )
            del ttt_games[game_id]
            return
        
        elif msg == "draw":
            if game.bet > 0:
                conn = get_db()
                c = conn.cursor()
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet, game.player1_id))
                c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet, game.player2_id))
                conn.commit()
                conn.close()
            
            await query.edit_message_text(
                f"🎯 TIC TAC TOE\n\n"
                f"❌ {game.player1_name} vs ⭕ {game.player2_name}\n\n"
                f"🤝 DRAW 🤝",
                reply_markup=game.get_keyboard(),
                
            )
            del ttt_games[game_id]
            return
        
        else:
            turn_name = game.player1_name if game.current_turn == game.player1_id else game.player2_name
            turn_symbol = "❌" if game.current_turn == game.player1_id else "⭕"
            bet_text = f"💰 Bet: {game.bet:,} | Prize: {game.bet*2:,}" if game.bet > 0 else "🎮 Normal Game"
            
            await query.edit_message_text(
                f"🎯 TIC TAC TOE\n\n"
                f"❌ {game.player1_name} vs ⭕ {game.player2_name}\n"
                f"{bet_text}\n\n"
                f"🎯 {turn_name}'s Turn ({turn_symbol})",
                reply_markup=game.get_keyboard(),
                
            )
            return

# ============ BROADCAST SYSTEM ============

def get_known_users():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_known_groups():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT group_id FROM groups")
    groups = [row[0] for row in c.fetchall()]
    conn.close()
    return groups

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ ONLY ADMIN CAN USE THIS COMMAND!")
        return
    
    msg = update.message
    known_users = get_known_users()
    known_groups = get_known_groups()
    sent_users = 0
    sent_groups = 0
    failed = 0
    
    if msg.reply_to_message and msg.reply_to_message.photo:
        photo = msg.reply_to_message.photo[-1].file_id
        caption = msg.reply_to_message.caption or ""
        for uid in known_users:
            try:
                await context.bot.send_photo(uid, photo, caption=caption)
                sent_users += 1
            except:
                failed += 1
        for gid in known_groups:
            try:
                await context.bot.send_photo(gid, photo, caption=caption)
                sent_groups += 1
            except:
                pass
        await update.message.reply_text(f"📸 PHOTO BROADCAST SENT!\n\n👤 Users: {sent_users}\n👥 Groups: {sent_groups}\n❌ Failed: {failed}\n📊 Total: {sent_users + sent_groups}")
        return
    
    if msg.reply_to_message and msg.reply_to_message.video:
        video = msg.reply_to_message.video.file_id
        caption = msg.reply_to_message.caption or ""
        for uid in known_users:
            try:
                await context.bot.send_video(uid, video, caption=caption)
                sent_users += 1
            except:
                failed += 1
        for gid in known_groups:
            try:
                await context.bot.send_video(gid, video, caption=caption)
                sent_groups += 1
            except:
                pass
        await update.message.reply_text(f"🎥 VIDEO BROADCAST SENT!\n\n👤 Users: {sent_users}\n👥 Groups: {sent_groups}\n❌ Failed: {failed}")
        return
    
    if msg.reply_to_message:
        content = msg.reply_to_message.text or msg.reply_to_message.caption
    else:
        if not context.args:
            await msg.reply_text("📢 BROADCAST USAGE (ADMIN ONLY):\n\n📝 TEXT: /broadcast Hello\n🖼️ PHOTO: Reply to a photo\n🎥 VIDEO: Reply to a video\n📊 STATS: /broadcast_stats")
            return
        content = " ".join(context.args)
    
    for uid in known_users:
        try:
            await context.bot.send_message(uid, content)
            sent_users += 1
        except:
            failed += 1
    
    for gid in known_groups:
        try:
            await context.bot.send_message(gid, content)
            sent_groups += 1
        except:
            pass
    
    await msg.reply_text(f"📢 BROADCAST SENT!\n\n👤 Users: {sent_users}\n👥 Groups: {sent_groups}\n❌ Failed: {failed}\n📊 Total reached: {sent_users + sent_groups}")

async def broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ ONLY ADMIN CAN USE THIS COMMAND!")
        return
    
    known_users = get_known_users()
    known_groups = get_known_groups()
    
    await update.message.reply_text(f"📊 BROADCAST REACH STATS\n\n👤 Total Users: {len(known_users)}\n👥 Total Groups: {len(known_groups)}\n📡 Total Reach: {len(known_users) + len(known_groups)}\n\n👑 Admin IDs: {ADMIN_IDS}\n\n💡 Use /broadcast to send message to everyone!")


# ============ STATS COMMANDS ============

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    keyboard = [
        [InlineKeyboardButton("🏏 MOST RUNS", callback_data="stats_runs")],
        [InlineKeyboardButton("🎯 MOST WICKETS", callback_data="stats_wickets")],
        [InlineKeyboardButton("⭐ HIGHEST SCORE", callback_data="stats_highest")],
        [InlineKeyboardButton("✅ MOST WINS", callback_data="stats_wins")],
        [InlineKeyboardButton("❌ MOST LOSSES", callback_data="stats_losses")],
    ]
    await update.message.reply_text("🏏 CRICKET STATS LEADERBOARD\n\nSelect stat to view:", reply_markup=InlineKeyboardMarkup(keyboard))

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id
    conn = get_db()
    c = conn.cursor()
    
    if data == "stats_runs":
        c.execute("SELECT name, runs FROM cricket_stats ORDER BY runs DESC LIMIT 5")
        top = c.fetchall()
        c.execute("SELECT user_id FROM cricket_stats WHERE user_id=?", (user_id,))
        user_exists = c.fetchone()
        user_rank = None
        user_runs = 0
        if user_exists:
            c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE runs > (SELECT runs FROM cricket_stats WHERE user_id=?)", (user_id,))
            user_rank = c.fetchone()[0]
            c.execute("SELECT runs FROM cricket_stats WHERE user_id=?", (user_id,))
            user_runs = c.fetchone()[0]
        conn.close()
        msg = "🏏 MOST RUNS LEADERBOARD\n\n"
        medals = ["👑", "🥈", "🥉", "", ""]
        for i, (name, runs) in enumerate(top):
            medal = medals[i] if i < 3 else f"{i+1}."
            msg += f"{medal} {name} - {runs} runs\n"
        if user_rank:
            msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{user_rank}\n🏏 Your runs: {user_runs}"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "stats_wickets":
        c.execute("SELECT name, wickets FROM cricket_stats ORDER BY wickets DESC LIMIT 5")
        top = c.fetchall()
        c.execute("SELECT user_id FROM cricket_stats WHERE user_id=?", (user_id,))
        user_exists = c.fetchone()
        user_rank = None
        user_wickets = 0
        if user_exists:
            c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE wickets > (SELECT wickets FROM cricket_stats WHERE user_id=?)", (user_id,))
            user_rank = c.fetchone()[0]
            c.execute("SELECT wickets FROM cricket_stats WHERE user_id=?", (user_id,))
            user_wickets = c.fetchone()[0]
        conn.close()
        msg = "🎯 MOST WICKETS LEADERBOARD\n\n"
        medals = ["👑", "🥈", "🥉", "", ""]
        for i, (name, wickets) in enumerate(top):
            medal = medals[i] if i < 3 else f"{i+1}."
            msg += f"{medal} {name} - {wickets} wickets\n"
        if user_rank:
            msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{user_rank}\n🎯 Your wickets: {user_wickets}"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "stats_highest":
        c.execute("SELECT name, highest_score FROM cricket_stats ORDER BY highest_score DESC LIMIT 5")
        top = c.fetchall()
        c.execute("SELECT user_id FROM cricket_stats WHERE user_id=?", (user_id,))
        user_exists = c.fetchone()
        user_rank = None
        user_highest = 0
        if user_exists:
            c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE highest_score > (SELECT highest_score FROM cricket_stats WHERE user_id=?)", (user_id,))
            user_rank = c.fetchone()[0]
            c.execute("SELECT highest_score FROM cricket_stats WHERE user_id=?", (user_id,))
            user_highest = c.fetchone()[0]
        conn.close()
        msg = "⭐ HIGHEST SCORE LEADERBOARD\n\n"
        medals = ["👑", "🥈", "🥉", "", ""]
        for i, (name, score) in enumerate(top):
            medal = medals[i] if i < 3 else f"{i+1}."
            msg += f"{medal} {name} - {score} runs\n"
        if user_rank:
            msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{user_rank}\n⭐ Your highest: {user_highest}"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "stats_wins":
        c.execute("SELECT name, wins FROM cricket_stats ORDER BY wins DESC LIMIT 5")
        top = c.fetchall()
        c.execute("SELECT user_id FROM cricket_stats WHERE user_id=?", (user_id,))
        user_exists = c.fetchone()
        user_rank = None
        user_wins = 0
        if user_exists:
            c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE wins > (SELECT wins FROM cricket_stats WHERE user_id=?)", (user_id,))
            user_rank = c.fetchone()[0]
            c.execute("SELECT wins FROM cricket_stats WHERE user_id=?", (user_id,))
            user_wins = c.fetchone()[0]
        conn.close()
        msg = "✅ MOST WINS LEADERBOARD\n\n"
        medals = ["👑", "🥈", "🥉", "", ""]
        for i, (name, wins) in enumerate(top):
            medal = medals[i] if i < 3 else f"{i+1}."
            msg += f"{medal} {name} - {wins} wins\n"
        if user_rank:
            msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{user_rank}\n✅ Your wins: {user_wins}"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "stats_losses":
        c.execute("SELECT name, losses FROM cricket_stats ORDER BY losses DESC LIMIT 5")
        top = c.fetchall()
        c.execute("SELECT user_id FROM cricket_stats WHERE user_id=?", (user_id,))
        user_exists = c.fetchone()
        user_rank = None
        user_losses = 0
        if user_exists:
            c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE losses > (SELECT losses FROM cricket_stats WHERE user_id=?)", (user_id,))
            user_rank = c.fetchone()[0]
            c.execute("SELECT losses FROM cricket_stats WHERE user_id=?", (user_id,))
            user_losses = c.fetchone()[0]
        conn.close()
        msg = "❌ MOST LOSSES LEADERBOARD\n\n"
        medals = ["👑", "🥈", "🥉", "", ""]
        for i, (name, losses) in enumerate(top):
            medal = medals[i] if i < 3 else f"{i+1}."
            msg += f"{medal} {name} - {losses} losses\n"
        if user_rank:
            msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{user_rank}\n❌ Your losses: {user_losses}"
        keyboard = [[InlineKeyboardButton("◀️ BACK TO MENU", callback_data="stats_back")]]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == "stats_back":
        keyboard = [
            [InlineKeyboardButton("🏏 MOST RUNS", callback_data="stats_runs")],
            [InlineKeyboardButton("🎯 MOST WICKETS", callback_data="stats_wickets")],
            [InlineKeyboardButton("⭐ HIGHEST SCORE", callback_data="stats_highest")],
            [InlineKeyboardButton("✅ MOST WINS", callback_data="stats_wins")],
            [InlineKeyboardButton("❌ MOST LOSSES", callback_data="stats_losses")],
        ]
        await query.edit_message_text("🏏 CRICKET STATS LEADERBOARD\n\nSelect stat to view:", reply_markup=InlineKeyboardMarkup(keyboard))

async def mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user
    name = user.first_name if user.first_name else (user.username or "User")
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT runs, wickets, highest_score, wins, losses FROM cricket_stats WHERE user_id=?", (user_id,))
    stats = c.fetchone()
    
    if not stats:
        conn.close()
        await update.message.reply_text(
            f"🏏 YOUR CRICKET STATS\n\n"
            f"👤 {name}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🏏 Runs: 0 (Rank: N/A)\n"
            f"🎯 Wickets: 0 (Rank: N/A)\n"
            f"⭐ Highest Score: 0 (Rank: N/A)\n"
            f"✅ Wins: 0 (Rank: N/A)\n"
            f"❌ Losses: 0 (Rank: N/A)\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 Play /CLcricket to start!",
            
        )
        return
    
    runs, wickets, highest_score, wins, losses = stats
    
    c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE runs > ?", (runs,))
    runs_rank = c.fetchone()[0] if runs > 0 else None
    c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE wickets > ?", (wickets,))
    wickets_rank = c.fetchone()[0] if wickets > 0 else None
    c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE highest_score > ?", (highest_score,))
    highest_rank = c.fetchone()[0] if highest_score > 0 else None
    c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE wins > ?", (wins,))
    wins_rank = c.fetchone()[0] if wins > 0 else None
    c.execute("SELECT COUNT(*) + 1 FROM cricket_stats WHERE losses > ?", (losses,))
    losses_rank = c.fetchone()[0] if losses > 0 else None
    conn.close()
    
    msg = f"🏏 YOUR CRICKET STATS\n\n"
    msg += f"👤 {name}\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🏏 Runs: {runs} (Rank: #{runs_rank if runs_rank else 'N/A'})\n"
    msg += f"🎯 Wickets: {wickets} (Rank: #{wickets_rank if wickets_rank else 'N/A'})\n"
    msg += f"⭐ Highest Score: {highest_score} (Rank: #{highest_rank if highest_rank else 'N/A'})\n"
    msg += f"✅ Wins: {wins} (Rank: #{wins_rank if wins_rank else 'N/A'})\n"
    msg += f"❌ Losses: {losses} (Rank: #{losses_rank if losses_rank else 'N/A'})\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━"
    
    await update.message.reply_text(msg)


# ============ SHOP4 ============

async def shop4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM shop4 ORDER BY price ASC")
    players = c.fetchall()
    conn.close()
    
    if not players:
        await update.message.reply_text('🛒 SHOP4\n\nNo players yet.\n👑 Admin: /addplayer4 <name> <price>')
        return
    
    msg = "🛒 SHOP4\n\n"
    for p in players:
        msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n💡 /buy4 <id> to purchase"
    await update.message.reply_text(msg)

async def buy4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /buy4 <player_id>\nExample: /buy4 1')
        return
    
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid ID')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, price FROM shop4 WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < player[1]:
        await update.message.reply_text(f'❌ Need {player[1]:,}, have {balance:,}')
        conn.close()
        return
    
    c.execute("SELECT * FROM user_players4 WHERE user_id=? AND player_id=?", (user_id, player_id))
    if c.fetchone():
        await update.message.reply_text(f'❌ You already own {player[0]}!')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (player[1], user_id))
    c.execute("INSERT INTO user_players4 (user_id, player_id) VALUES (?, ?)", (user_id, player_id))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"✅ PURCHASED!\n\n🏏 {player[0]}\n💰 Price: {player[1]:,} 💰\n📊 New balance: {new_bal:,} 💰")

async def myteam4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT s.name, s.price FROM user_players4 u JOIN shop4 s ON u.player_id=s.id WHERE u.user_id=?", (user_id,))
    players = c.fetchall()
    conn.close()
    
    if not players:
        await update.message.reply_text('📭 No shop4 players owned.\nUse /shop4 to buy!')
        return
    
    total = sum(p[1] for p in players)
    msg = "🤑 MY SHOP4 PLAYERS\n\n"
    for i, p in enumerate(players, 1):
        msg += f"{i}. {p[0]} - {p[1]:,} 💰\n"
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💰 Total spent: {total:,} 💰"
    await update.message.reply_text(msg)

async def top4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(s.price), 0) as total FROM users u JOIN user_players4 up ON u.user_id=up.user_id JOIN shop4 s ON up.player_id=s.id GROUP BY u.user_id ORDER BY total DESC LIMIT 10")
    tops = c.fetchall()
    
    if not tops:
        await update.message.reply_text('🏆 SHOP4 TOP COLLECTORS\n\nNo one owns any yet!')
        conn.close()
        return
    
    msg = "🏆 SHOP4 TOP COLLECTORS\n\n"
    for i, t in enumerate(tops, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {t[0]} - {t[1]} players ({t[2]:,} 💰)\n"
    
    c.execute("SELECT COUNT(*) FROM user_players4 WHERE user_id=?", (user_id,))
    my_count = c.fetchone()[0]
    msg += f"\n📊 You own: {my_count} players"
    await update.message.reply_text(msg)
    conn.close()

async def addplayer4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /addplayer4 <name> <price>')
        return
    
    name = ' '.join(args[:-1])
    try:
        price = int(args[-1])
    except:
        await update.message.reply_text('❌ Invalid price!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO shop4 (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    player_id = c.lastrowid
    conn.close()
    
    await update.message.reply_text(f"✅ PLAYER ADDED TO SHOP4!\n\nID: {player_id} | {name}\n💰 Price: {price:,} 💰")

async def setprice4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /setprice4 <id> <new_price>')
        return
    
    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid input!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM shop4 WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("UPDATE shop4 SET price = ? WHERE id=?", (new_price, player_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ SHOP4 PRICE UPDATED!\n{player[0]}\nNew Price: {new_price:,} 💰")

async def removeplayer4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /removeplayer4 <id>')
        return
    
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid ID!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM shop4 WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("DELETE FROM shop4 WHERE id=?", (player_id,))
    c.execute("DELETE FROM user_players4 WHERE player_id=?", (player_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ PLAYER REMOVED FROM SHOP4!\n{player[0]}")


# ============ GROUP TRACKING ============

async def track_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        group_id = update.message.chat.id
        group_name = update.message.chat.title or "Unknown Group"
        conn = get_db()
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS groups (group_id INTEGER PRIMARY KEY, group_name TEXT, added_at TEXT)")
        c.execute("INSERT OR IGNORE INTO groups (group_id, group_name, added_at) VALUES (?, ?, ?)", (group_id, group_name, datetime.now().isoformat()))
        conn.commit()
        conn.close()


# ============ NUMBER GUESSING GAME (DM + GROUP) ==========

game_data = {}  # {chat_id: {"number": x, "attempts": y, "player_id": z, "player_name": w}}

async def numguess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a new number guessing game"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    # Check if game already active in this chat
    if chat_id in game_data:
        await update.message.reply_text(
            f"❌ A game is already active!\n"
            f"Started by: {game_data[chat_id]['player_name']}\n"
            f"Use /ngstop to stop it."
        )
        return
    
    # Create new game
    number = random.randint(1, 100)
    game_data[chat_id] = {
        "number": number,
        "attempts": 0,
        "player_id": user_id,
        "player_name": user_name,
        "chat_id": chat_id
    }
    
    msg = f"🎲 Number Guessing Game Started!\n\n"
    msg += f"👤 Host: {user_name}\n"
    msg += f"📊 I'm thinking of a number between 1-100\n"
    msg += f"💡 Use `/ng <number>` to guess!\n"
    
    if chat_type in ['group', 'supergroup']:
        msg += f"🛑 Admin: `/ngstop` to end game"
    
    await update.message.reply_text(msg)


async def ng(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Make a guess"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    # Check if game exists
    if chat_id not in game_data:
        await update.message.reply_text("❌ No active game! Use /numguess to start.")
        return
    
    game = game_data[chat_id]
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: /ng <number>\nExample: /ng 50")
        return
    
    try:
        guess = int(args[0])
    except:
        await update.message.reply_text("❌ Please enter a valid number!")
        return
    
    if guess < 1 or guess > 100:
        await update.message.reply_text("❌ Number must be between 1 and 100!")
        return
    
    game["attempts"] += 1
    target = game["number"]
    
    if guess == target:
        # Game won - reward based on attempts
        attempts = game["attempts"]
        winner_id = user_id
        winner_name = user_name
        
        # Reward system: fewer attempts = more coins
        if attempts == 1:
            reward = 5000
            msg = f"🎉 PERFECT! {winner_name} guessed {target} in FIRST attempt! 👑 LEGEND! +{reward} coins!"
        elif attempts <= 3:
            reward = 2000
            msg = f"🎉 AMAZING! {winner_name} guessed {target} in {attempts} attempts! 🌟 INCREDIBLE! +{reward} coins!"
        elif attempts <= 5:
            reward = 1000
            msg = f"🎉 EXCELLENT! {winner_name} guessed {target} in {attempts} attempts! 🎯 GREAT! +{reward} coins!"
        elif attempts <= 7:
            reward = 500
            msg = f"🎉 GOOD JOB! {winner_name} guessed {target} in {attempts} attempts! 👍 NICE! +{reward} coins!"
        elif attempts <= 10:
            reward = 300
            msg = f"🎉 NOT BAD! {winner_name} guessed {target} in {attempts} attempts! 💪 GOOD! +{reward} coins!"
        elif attempts <= 15:
            reward = 150
            msg = f"🎉 OKAY! {winner_name} guessed {target} in {attempts} attempts! 📊 KEEP TRYING! +{reward} coins!"
        else:
            reward = 50
            msg = f"🎉 FINALLY! {winner_name} guessed {target} in {attempts} attempts! 💪 PRACTICE MORE! +{reward} coins!"
        
        # Add reward
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?", (winner_id,))
        current_bal = c.fetchone()[0]
        new_bal = current_bal + reward
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, winner_id))
        conn.commit()
        conn.close()
        
        # Delete game
        del game_data[chat_id]
        
        await update.message.reply_text(msg)
        
    elif guess < target:
        await update.message.reply_text(f"📈 Too low! Attempts: {game['attempts']}")
    else:
        await update.message.reply_text(f"📉 Too high! Attempts: {game['attempts']}")


async def ngstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop current game - Host, Group Admin, or Bot Admin"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    # Check if game exists
    if chat_id not in game_data:
        await update.message.reply_text("❌ No active game to stop!")
        return
    
    game = game_data[chat_id]
    
    # Check permissions
    can_stop = False
    
    # Bot admin
    if user_id in ADMIN_IDS:
        can_stop = True
    
    # Game host
    if game["player_id"] == user_id:
        can_stop = True
    
    # Group admin (only in groups)
    if not can_stop and chat_type in ['group', 'supergroup']:
        try:
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            if chat_member.status in ['administrator', 'creator']:
                can_stop = True
        except:
            pass
    
    if not can_stop:
        await update.message.reply_text("❌ Only game host, group admin, or bot admin can stop the game!")
        return
    
    target = game["number"]
    attempts = game["attempts"]
    host_name = game["player_name"]
    
    del game_data[chat_id]
    
    await update.message.reply_text(
        f"🛑 Game Stopped!\n\n"
        f"👤 Host: {host_name}\n"
        f"🔢 The number was: {target}\n"
        f"📊 Total attempts: {attempts}\n\n"
        f"💡 Use /numguess to start a new game!",
        
    )


async def add_all_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Clear existing
    c.execute("DELETE FROM shop")
    
    # ========== INDIA CURRENT (20) ==========
    india_current = [
        ("Virat Kohli", 2000000, "India", "current"),
        ("Rohit Sharma", 1900000, "India", "current"),
        ("Shubman Gill", 1700000, "India", "current"),
        ("Hardik Pandya", 1800000, "India", "current"),
        ("Jasprit Bumrah", 2000000, "India", "current"),
        ("Ravindra Jadeja", 1600000, "India", "current"),
        ("KL Rahul", 1500000, "India", "current"),
        ("Suryakumar Yadav", 1750000, "India", "current"),
        ("Mohammed Shami", 1650000, "India", "current"),
        ("Rishabh Pant", 1550000, "India", "current"),
        ("Mohammed Siraj", 1450000, "India", "current"),
        ("Axar Patel", 1400000, "India", "current"),
        ("Shreyas Iyer", 1480000, "India", "current"),
        ("Ishan Kishan", 1380000, "India", "current"),
        ("Deepak Chahar", 1350000, "India", "current"),
        ("Sanju Samson", 1420000, "India", "current"),
        ("Yuzvendra Chahal", 1390000, "India", "current"),
        ("Bhuvneshwar Kumar", 1370000, "India", "current"),
        ("Shardul Thakur", 1320000, "India", "current"),
        ("Washington Sundar", 1300000, "India", "current")
    ]
    
    # ========== INDIA LEGENDS (20) ==========
    india_legends = [
        ("Sachin Tendulkar", 5000000, "India", "legend"),
        ("MS Dhoni", 4500000, "India", "legend"),
        ("Rahul Dravid", 4000000, "India", "legend"),
        ("Sourav Ganguly", 3800000, "India", "legend"),
        ("Virender Sehwag", 4200000, "India", "legend"),
        ("VVS Laxman", 3500000, "India", "legend"),
        ("Anil Kumble", 3600000, "India", "legend"),
        ("Kapil Dev", 4800000, "India", "legend"),
        ("Sunil Gavaskar", 4400000, "India", "legend"),
        ("Zaheer Khan", 3200000, "India", "legend"),
        ("Harbhajan Singh", 3100000, "India", "legend"),
        ("Yuvraj Singh", 4300000, "India", "legend"),
        ("Gautam Gambhir", 3400000, "India", "legend"),
        ("Mohammad Azharuddin", 3300000, "India", "legend"),
        ("Navjot Sidhu", 2800000, "India", "legend"),
        ("Kris Srikkanth", 2700000, "India", "legend"),
        ("Erapalli Prasanna", 2500000, "India", "legend"),
        ("Bishan Bedi", 2600000, "India", "legend"),
        ("Bhagwat Chandrasekhar", 2400000, "India", "legend"),
        ("Venkatesh Prasad", 2300000, "India", "legend")
    ]
    
    # ========== ENGLAND CURRENT (20) ==========
    england_current = [
        ("Joe Root", 1800000, "England", "current"),
        ("Ben Stokes", 1900000, "England", "current"),
        ("Jos Buttler", 1700000, "England", "current"),
        ("Jonny Bairstow", 1600000, "England", "current"),
        ("Jofra Archer", 1750000, "England", "current"),
        ("Moeen Ali", 1500000, "England", "current"),
        ("Sam Curran", 1550000, "England", "current"),
        ("Chris Woakes", 1400000, "England", "current"),
        ("Mark Wood", 1450000, "England", "current"),
        ("Adil Rashid", 1350000, "England", "current"),
        ("Dawid Malan", 1300000, "England", "current"),
        ("Jason Roy", 1250000, "England", "current"),
        ("Liam Livingstone", 1450000, "England", "current"),
        ("Harry Brook", 1500000, "England", "current"),
        ("Reece Topley", 1200000, "England", "current"),
        ("David Willey", 1150000, "England", "current"),
        ("Phil Salt", 1100000, "England", "current"),
        ("Will Jacks", 1050000, "England", "current"),
        ("Gus Atkinson", 1000000, "England", "current"),
        ("Tom Curran", 1080000, "England", "current")
    ]
    
    # ========== ENGLAND LEGENDS (20) ==========
    england_legends = [
        ("Ian Botham", 4800000, "England", "legend"),
        ("Alastair Cook", 4000000, "England", "legend"),
        ("Andrew Flintoff", 4500000, "England", "legend"),
        ("Kevin Pietersen", 4200000, "England", "legend"),
        ("James Anderson", 5000000, "England", "legend"),
        ("Stuart Broad", 4500000, "England", "legend"),
        ("Graeme Swann", 3800000, "England", "legend"),
        ("Michael Vaughan", 3500000, "England", "legend"),
        ("Alec Stewart", 3400000, "England", "legend"),
        ("Marcus Trescothick", 3300000, "England", "legend"),
        ("Paul Collingwood", 3200000, "England", "legend"),
        ("Monty Panesar", 2800000, "England", "legend"),
        ("Matthew Hoggard", 2700000, "England", "legend"),
        ("Steve Harmison", 3000000, "England", "legend"),
        ("Darren Gough", 2900000, "England", "legend"),
        ("Graeme Hick", 3100000, "England", "legend"),
        ("David Gower", 3500000, "England", "legend"),
        ("Geoffrey Boycott", 3800000, "England", "legend"),
        ("Fred Trueman", 4000000, "England", "legend"),
        ("WG Grace", 5000000, "England", "legend")
    ]
    
    # ========== AUSTRALIA CURRENT (20) ==========
    australia_current = [
        ("Pat Cummins", 1900000, "Australia", "current"),
        ("Steve Smith", 2000000, "Australia", "current"),
        ("David Warner", 1800000, "Australia", "current"),
        ("Mitchell Starc", 1850000, "Australia", "current"),
        ("Glenn Maxwell", 1750000, "Australia", "current"),
        ("Travis Head", 1650000, "Australia", "current"),
        ("Marnus Labuschagne", 1700000, "Australia", "current"),
        ("Josh Hazlewood", 1600000, "Australia", "current"),
        ("Adam Zampa", 1500000, "Australia", "current"),
        ("Marcus Stoinis", 1450000, "Australia", "current"),
        ("Cameron Green", 1550000, "Australia", "current"),
        ("Alex Carey", 1350000, "Australia", "current"),
        ("Mitchell Marsh", 1400000, "Australia", "current"),
        ("Nathan Lyon", 1480000, "Australia", "current"),
        ("Matthew Wade", 1300000, "Australia", "current"),
        ("Tim David", 1380000, "Australia", "current"),
        ("Ashton Agar", 1250000, "Australia", "current"),
        ("Sean Abbott", 1200000, "Australia", "current"),
        ("Ben McDermott", 1150000, "Australia", "current"),
        ("Kane Richardson", 1100000, "Australia", "current")
    ]
    
    # ========== AUSTRALIA LEGENDS (20) ==========
    australia_legends = [
        ("Don Bradman", 10000000, "Australia", "legend"),
        ("Ricky Ponting", 5500000, "Australia", "legend"),
        ("Shane Warne", 6000000, "Australia", "legend"),
        ("Glenn McGrath", 5500000, "Australia", "legend"),
        ("Adam Gilchrist", 5000000, "Australia", "legend"),
        ("Matthew Hayden", 4500000, "Australia", "legend"),
        ("Michael Clarke", 4200000, "Australia", "legend"),
        ("Steve Waugh", 4800000, "Australia", "legend"),
        ("Mark Waugh", 4000000, "Australia", "legend"),
        ("Brett Lee", 4500000, "Australia", "legend"),
        ("Dennis Lillee", 5000000, "Australia", "legend"),
        ("Jeff Thomson", 4200000, "Australia", "legend"),
        ("Allan Border", 4600000, "Australia", "legend"),
        ("Greg Chappell", 4400000, "Australia", "legend"),
        ("Ian Chappell", 4200000, "Australia", "legend"),
        ("David Boon", 3800000, "Australia", "legend"),
        ("Dean Jones", 3900000, "Australia", "legend"),
        ("Damien Martyn", 3700000, "Australia", "legend"),
        ("Jason Gillespie", 3600000, "Australia", "legend"),
        ("Michael Hussey", 4300000, "Australia", "legend")
    ]
    
    # ========== NEW ZEALAND CURRENT (20) ==========
    nz_current = [
        ("Kane Williamson", 1900000, "New Zealand", "current"),
        ("Trent Boult", 1800000, "New Zealand", "current"),
        ("Devon Conway", 1600000, "New Zealand", "current"),
        ("Daryl Mitchell", 1550000, "New Zealand", "current"),
        ("Mitchell Santner", 1450000, "New Zealand", "current"),
        ("Lockie Ferguson", 1500000, "New Zealand", "current"),
        ("Tim Southee", 1400000, "New Zealand", "current"),
        ("Glenn Phillips", 1350000, "New Zealand", "current"),
        ("Michael Bracewell", 1250000, "New Zealand", "current"),
        ("Finn Allen", 1300000, "New Zealand", "current"),
        ("Adam Milne", 1200000, "New Zealand", "current"),
        ("Ish Sodhi", 1150000, "New Zealand", "current"),
        ("James Neesham", 1250000, "New Zealand", "current"),
        ("Tom Latham", 1300000, "New Zealand", "current"),
        ("Martin Guptill", 1400000, "New Zealand", "current"),
        ("Matt Henry", 1200000, "New Zealand", "current"),
        ("Kyle Jamieson", 1350000, "New Zealand", "current"),
        ("Henry Nicholls", 1100000, "New Zealand", "current"),
        ("Will Young", 1050000, "New Zealand", "current"),
        ("Ben Sears", 1000000, "New Zealand", "current")
    ]
    
    # ========== NEW ZEALAND LEGENDS (20) ==========
    nz_legends = [
        ("Richard Hadlee", 5500000, "New Zealand", "legend"),
        ("Martin Crowe", 4800000, "New Zealand", "legend"),
        ("Brendon McCullum", 4500000, "New Zealand", "legend"),
        ("Daniel Vettori", 4200000, "New Zealand", "legend"),
        ("Stephen Fleming", 4000000, "New Zealand", "legend"),
        ("Chris Cairns", 3800000, "New Zealand", "legend"),
        ("Nathan Astle", 3600000, "New Zealand", "legend"),
        ("Craig McMillan", 3400000, "New Zealand", "legend"),
        ("Scott Styris", 3300000, "New Zealand", "legend"),
        ("Jacob Oram", 3200000, "New Zealand", "legend"),
        ("Shane Bond", 4500000, "New Zealand", "legend"),
        ("Geoff Allott", 2800000, "New Zealand", "legend"),
        ("Dion Nash", 2900000, "New Zealand", "legend"),
        ("John Wright", 3100000, "New Zealand", "legend"),
        ("Mark Greatbatch", 3000000, "New Zealand", "legend"),
        ("Ian Smith", 2900000, "New Zealand", "legend"),
        ("Lance Cairns", 3500000, "New Zealand", "legend"),
        ("Ewen Chatfield", 2800000, "New Zealand", "legend"),
        ("Bruce Taylor", 3000000, "New Zealand", "legend"),
        ("Bert Sutcliffe", 3200000, "New Zealand", "legend")
    ]
    
    # ========== INSERT ALL ==========
    
    # India
    for name, price, country, ptype in india_current:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    for name, price, country, ptype in india_legends:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # England
    for name, price, country, ptype in england_current:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    for name, price, country, ptype in england_legends:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # Australia
    for name, price, country, ptype in australia_current:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    for name, price, country, ptype in australia_legends:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # New Zealand
    for name, price, country, ptype in nz_current:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    for name, price, country, ptype in nz_legends:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM shop")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM shop WHERE type='current'")
    current_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM shop WHERE type='legend'")
    legend_count = c.fetchone()[0]
    
    conn.close()
    
    await update.message.reply_text(
        f"✅ ALL PLAYERS ADDED!\n\n"
        f"🏏 TOTAL: {total} players\n"
        f"📊 Current: {current_count} players\n"
        f"📊 Legends: {legend_count} players\n\n"
        f"🇮🇳 India: 20 Current + 20 Legends\n"
        f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 England: 20 Current + 20 Legends\n"
        f"🇦🇺 Australia: 20 Current + 20 Legends\n"
        f"🇳🇿 New Zealand: 20 Current + 20 Legends\n\n"
        f"💡 /shop - Now buy players!"
    )


# ============ LOTTERY SYSTEM ============

import random
import string
from datetime import datetime

# Global variables
lottery_active = False
lottery_tickets = {}
lottery_total_tickets = 0
lottery_participants = []
lottery_winner = None
lottery_start_time = None

def generate_ticket_number():
    """Generate unique ticket number"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

async def lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main lottery menu"""
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    conn.close()
    
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
    """Buy lottery tickets"""
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: /buy_ticket <quantity>\nExample: /buy_ticket 5")
        return
    
    try:
        quantity = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid quantity!")
        return
    
    if quantity < 1 or quantity > 100:
        await update.message.reply_text("❌ Quantity must be 1-100")
        return
    
    if not lottery_active:
        await update.message.reply_text("❌ Lottery not active! Wait for admin to start.")
        return
    
    cost = quantity * 20000
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < cost:
        await update.message.reply_text(f"❌ Need {cost:,} credits! You have {balance:,}")
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (cost, user_id))
    conn.commit()
    conn.close()
    
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
    
    ticket_list = "\n".join([f"🎫 {t}" for t in new_tickets[:5]])
    if quantity > 5:
        ticket_list += f"\n... and {quantity-5} more"
    
    await update.message.reply_text(
        f"✅ BOUGHT {quantity} TICKETS!\n\n"
        f"💰 Cost: {cost:,} credits\n"
        f"🎫 Your tickets:\n{ticket_list}\n\n"
        f"💡 /mytickets - Check all tickets"
    )

async def mytickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's tickets"""
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    user_tickets = lottery_tickets.get(user_id, [])
    
    if not user_tickets:
        await update.message.reply_text("🎫 You don't have any tickets!\nUse /buy_ticket to buy.")
        return
    
    ticket_list = "\n".join([f"🎫 {t}" for t in user_tickets[:10]])
    if len(user_tickets) > 10:
        ticket_list += f"\n... and {len(user_tickets)-10} more"
    
    await update.message.reply_text(
        f"🎫 MY TICKETS\n\n"
        f"Total: {len(user_tickets)}\n"
        f"Spent: {len(user_tickets) * 20000:,}\n\n"
        f"{ticket_list}"
    )

async def lottery_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show lottery info"""
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    user_tickets = lottery_tickets.get(user_id, [])
    prize_pool = lottery_total_tickets * 20000
    win_chance = (len(user_tickets) / lottery_total_tickets * 100) if lottery_total_tickets > 0 else 0
    status_text = "🟢 ACTIVE" if lottery_active else "🔴 NOT ACTIVE"
    
    msg = f"🎰 LOTTERY INFO\n\n"
    msg += f"Status: {status_text}\n"
    msg += f"Total tickets: {lottery_total_tickets}\n"
    msg += f"Participants: {len(lottery_participants)}\n"
    msg += f"Prize pool: {prize_pool:,}\n\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 YOUR STATS:\n"
    msg += f"Your tickets: {len(user_tickets)}\n"
    msg += f"Contribution: {len(user_tickets) * 20000:,}\n"
    msg += f"Win chance: {win_chance:.1f}%"
    
    await update.message.reply_text(msg)

async def start_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Start lottery"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    global lottery_active, lottery_tickets, lottery_total_tickets, lottery_participants, lottery_start_time
    
    if lottery_active:
        await update.message.reply_text("❌ Lottery already active!")
        return
    
    lottery_active = True
    lottery_tickets = {}
    lottery_total_tickets = 0
    lottery_participants = []
    lottery_start_time = datetime.now()
    
    await update.message.reply_text(
        "✅ LOTTERY STARTED!\n\n"
        "🎟️ Ticket price: 20,000 credits\n"
        "🏆 Winner gets: ALL prize pool\n"
        "📢 Users can buy tickets:\n"
        "/buy_ticket <quantity>\n\n"
        "💡 /draw_winner - Draw winner"
    )

async def draw_winner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Draw lottery winner"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    global lottery_active, lottery_winner
    
    if not lottery_active:
        await update.message.reply_text("❌ Lottery not active!")
        return
    
    if lottery_total_tickets == 0:
        await update.message.reply_text("❌ No tickets sold!")
        return
    
    all_tickets = []
    for uid, tickets in lottery_tickets.items():
        for ticket in tickets:
            all_tickets.append((uid, ticket))
    
    winner_id, winner_ticket = random.choice(all_tickets)
    lottery_winner = winner_id
    prize_pool = lottery_total_tickets * 20000
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM users WHERE user_id=?", (winner_id,))
    winner_name = c.fetchone()[0]
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (winner_id,))
    current_bal = c.fetchone()[0]
    c.execute("UPDATE users SET balance = ? WHERE user_id=?", (current_bal + prize_pool, winner_id))
    conn.commit()
    conn.close()
    
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
    
    lottery_active = False

async def reset_lottery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: Reset lottery"""
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
    """Admin: Generate coupon code"""
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
    
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS lottery_coupons (code TEXT PRIMARY KEY, quantity INTEGER, used INTEGER DEFAULT 0)")
    c.execute("INSERT INTO lottery_coupons (code, quantity) VALUES (?, ?)", (coupon_code, quantity))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ COUPON GENERATED!\n\n"
        f"🔑 Code: {coupon_code}\n"
        f"🎫 Free tickets: {quantity}\n\n"
        f"Claim: /claim_coupon {coupon_code}"
    )

async def claim_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User: Claim coupon code"""
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ /claim_coupon <code>")
        return
    
    coupon_code = args[0].upper()
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT quantity, used FROM lottery_coupons WHERE code=?", (coupon_code,))
    coupon = c.fetchone()
    
    if not coupon:
        await update.message.reply_text("❌ Invalid coupon code!")
        conn.close()
        return
    
    quantity, used = coupon
    
    if used >= quantity:
        await update.message.reply_text("❌ This coupon has been fully used!")
        conn.close()
        return
    
    c.execute("CREATE TABLE IF NOT EXISTS coupon_used (code TEXT, user_id INTEGER, PRIMARY KEY (code, user_id))")
    c.execute("SELECT * FROM coupon_used WHERE code=? AND user_id=?", (coupon_code, user_id))
    if c.fetchone():
        await update.message.reply_text("❌ You already used this coupon!")
        conn.close()
        return
    
    c.execute("INSERT INTO coupon_used (code, user_id) VALUES (?, ?)", (coupon_code, user_id))
    c.execute("UPDATE lottery_coupons SET used = used + 1 WHERE code=?", (coupon_code,))
    conn.commit()
    conn.close()
    
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

# ============ HILO GAME ==========

import random

hilo_games = {}

CARD_VALUES = {
    'A': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
    'J': 11, 'Q': 12, 'K': 13
}

SUITS = ['♠️', '♥️', '♣️', '♦️']

def get_random_card():
    value = random.choice(list(CARD_VALUES.keys()))
    suit = random.choice(SUITS)
    return {'value': value, 'suit': suit, 'rank': CARD_VALUES[value]}

def get_multiplier_increase(diff):
    if diff == 0:
        return 0.50
    elif diff == 1:
        return 0.05
    elif diff <= 3:
        return 0.08
    elif diff <= 6:
        return 0.12
    elif diff <= 9:
        return 0.18
    else:
        return 0.25

async def hilo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "📈 HiLo Game\n\n"
            "Usage: /hilo <bet>\n"
            "Example: /hilo 500\n\n"
            "💰 Min bet: 100\n"
            "💰 Max bet: 10,000"
        )
        return
    
    try:
        bet = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid bet amount!")
        return
    
    if bet < 100 or bet > 10000:
        await update.message.reply_text("❌ Bet must be between 100 and 10,000!")
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    conn.close()
    
    if balance < bet:
        await update.message.reply_text(f"❌ Need {bet:,} credits! You have {balance:,}")
        return
    
    # Deduct bet
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, user_id))
    conn.commit()
    conn.close()
    
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
            InlineKeyboardButton("🔼 HIGH", callback_data=f"hilo_high_{user_id}"),
            InlineKeyboardButton("🔽 LOW", callback_data=f"hilo_low_{user_id}")
        ],
        [InlineKeyboardButton("💰 CASHOUT", callback_data=f"hilo_cashout_{user_id}")]
    ]
    
    msg = f"📈 HiLo Game 📉\n\n"
    msg += f"Bet amount: {bet:,} 💰\n"
    msg += f"Multiplier: None\n\n"
    msg += f"Your card: {first_card['suit']}{first_card['value']}\n"
    
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))

async def hilo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if user_id not in hilo_games:
        await query.edit_message_text("❌ No active game! Use /hilo")
        return
    
    game = hilo_games[user_id]
    
    if data == f"hilo_cashout_{user_id}":
        win_amount = int(game['bet'] * game['multiplier'])
        
        if win_amount > 0:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            balance = c.fetchone()[0]
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (win_amount, user_id))
            conn.commit()
            conn.close()
        
        log_str = "".join([f"|{c['suit']}{c['value']}" for c in game['logs']])
        
        msg = f"📈 HiLo Game 📉\n\n"
        msg += f"Bet amount: {game['bet']:,} 💰\n"
        msg += f"Final Multiplier: {game['multiplier']:.3f}x\n"
        msg += f"You won: {win_amount:,} 💰\n\n"
        msg += f"Logs: {log_str}|"
        
        await query.edit_message_text(msg)
        del hilo_games[user_id]
        return
    
    # HIGH or LOW
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
        
        msg = f"📈 HiLo Game 📉\n\n"
        msg += f"Bet amount: {game['bet']:,} 💰\n"
        msg += f"Multiplier: {game['multiplier']:.3f}x\n"
        msg += f"Winning: {win_amount:,} 💰\n\n"
        msg += f"✅ Card: {new_card['suit']}{new_card['value']} ({guess.upper()} won!)\n"
        msg += f"Your card: {game['current_card']['suit']}{game['current_card']['value']}\n\n"
        msg += f"Logs: {log_str}|\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🔼 HIGH", callback_data=f"hilo_high_{user_id}"),
                InlineKeyboardButton("🔽 LOW", callback_data=f"hilo_low_{user_id}")
            ],
            [InlineKeyboardButton("💰 CASHOUT", callback_data=f"hilo_cashout_{user_id}")]
        ]
        
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        log_str = "".join([f"|{c['suit']}{c['value']}" for c in game['logs']])
        
        msg = f"📈 HiLo Game 📉\n\n"
        msg += f"Bet amount: {game['bet']:,} 💰\n"
        msg += f"Multiplier: 0x\n\n"
        msg += f"❌ Game Over!\n"
        msg += f"You bet {guess.upper()} on {new_card['suit']}{new_card['value']} and lost!\n\n"
        msg += f"Logs: {log_str}|"
        
        await query.edit_message_text(msg)
        del hilo_games[user_id]

# ============ MAIN ============

def main():
    threading.Thread(target=run_flask, daemon=True).start()
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

    # ============ LOTTERY COMMANDS ============
    app.add_handler(CommandHandler("lottery", lottery))
    app.add_handler(CommandHandler("buy_ticket", buy_ticket))
    app.add_handler(CommandHandler("mytickets", mytickets_command))
    app.add_handler(CommandHandler("lottery_info", lottery_info_command))

# ============ LOTTERY ADMIN COMMANDS ============
    app.add_handler(CommandHandler("start_lottery", start_lottery))
    app.add_handler(CommandHandler("draw_winner", draw_winner))
    app.add_handler(CommandHandler("reset_lottery", reset_lottery))
    app.add_handler(CommandHandler("lottery_coupon", lottery_coupon))
    app.add_handler(CommandHandler("claim_coupon", claim_coupon))

    # Numpuz Game
    app.add_handler(CommandHandler("numpuz", numpuz))
    app.add_handler(CallbackQueryHandler(numpuz_callback, pattern="^numpuz_"))

    # Hall of Fame
    app.add_handler(CommandHandler("hof", hof))
    app.add_handler(CommandHandler("addhof", addhof))
    app.add_handler(CommandHandler("rmhof", rmhof))
    app.add_handler(CommandHandler("edithof", edithof))
    app.add_handler(CommandHandler("ping", ping))

    # Shop2
    app.add_handler(CommandHandler("shop2", shop2))
    app.add_handler(CommandHandler("buy2", buy2))
    app.add_handler(CommandHandler("myteam2", myteam2))
    app.add_handler(CommandHandler("top2", top2))
    app.add_handler(CommandHandler("addplayer2", addplayer2))
    app.add_handler(CommandHandler("setprice2", setprice2))
    app.add_handler(CommandHandler("removeplayer2", removeplayer2))

    # Bank
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("claim_interest", claim_interest))

    # Admin
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

    # Shop3
    app.add_handler(CommandHandler("shop3", shop3))
    app.add_handler(CommandHandler("buy3", buy3))
    app.add_handler(CommandHandler("myteam3", myteam3))
    app.add_handler(CommandHandler("top3", top3))
    app.add_handler(CommandHandler("addplayer3", addplayer3))
    app.add_handler(CommandHandler("setprice3", setprice3))
    app.add_handler(CommandHandler("removeplayer3", removeplayer3))

    # Claim codes
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
    app.add_handler(CommandHandler("add_all_players", add_all_players))
    # Shop4
    app.add_handler(CommandHandler("shop4", shop4))
    app.add_handler(CommandHandler("buy4", buy4))
    app.add_handler(CommandHandler("myteam4", myteam4))
    app.add_handler(CommandHandler("top4", top4))
    app.add_handler(CommandHandler("addplayer4", addplayer4))
    app.add_handler(CommandHandler("setprice4", setprice4))
    app.add_handler(CommandHandler("removeplayer4", removeplayer4))

    # Group tracking
    app.add_handler(MessageHandler(filters.ChatType.GROUP | filters.ChatType.SUPERGROUP, track_group))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
