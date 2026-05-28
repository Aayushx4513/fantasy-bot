from flask import Flask
from telegram.ext import MessageHandler
import asyncio
from telegram.ext import filters
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import sqlite3
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import os
import threading
import json
import time

TOKEN = "8817319745:AAF8ugFftViQgEoHb9n_GHfx58nUyNs52ks"
ADMIN_IDS = [7687078555, 1315564307]

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
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
        keyboard = [[InlineKeyboardButton("📢 UPDATES", url="https://t.me/clbotofficial")],
                    [InlineKeyboardButton("👥 MAIN GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"✨ WELCOME TO CL ZONE ✨\n\n👑 {name}\n💰 1000 credits\n🎯 /claim\n🎡 /spin\n👤 /profile\n🏆 /leaderboard\n🏏 /CLcricket\n📊 /stats", reply_markup=reply_markup)
    else:
        conn.close()
        keyboard = [[InlineKeyboardButton("📢 UPDATES", url="https://t.me/clbotofficial")],
                    [InlineKeyboardButton("👥 MAIN GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"✨ WELCOME BACK\n\n👑 {name}\n💰 {existing[2]:,} credits", reply_markup=reply_markup)
    conn.close()


# ============ REFER ============
async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    bot_username = context.bot.username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await update.message.reply_text(f"👥 REFERRAL SYSTEM\n\nInvite friends and earn 1,000 credits each!\n\nYour Link: {ref_link}\n\nNew users get +500 bonus!")


# ============ HELP ============
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    msg = "📋 CL ZONE - COMMAND LIST\n\n👤 PROFILE\n/start - Start bot\n/profile - Your stats\n/setbio <text> - Set bio\n/rmbio - Remove bio\n/setpfp - Set photo\n/rmpfp - Remove photo\n\n💰 EARN\n/claim - 500 daily\n/spin - 1,000-10,000 daily\n/dice <amount>\n/flip heads/tails <amount>\n/tip <amount>\n\n🏏 CRICKET BETTING\n/matches - Live matches\n/bet <team> <amount>\n/mybets - Your bets\n/cancel <number>\n/allbets - All bets\n/history - Win/loss\n/top_fantasy - Fantasy ranking\n\n🛒 SHOP\n/shop - Buy players\n/buy <id> - Mens\n/buyw <id> - Women\n/myteam - Your collection\n/top - Top collectors\n/shop2 - Budget\n/shop3 - TG players\n/shop4 - More\n\n🏦 BANK\n/bank - Check balance\n/deposit <amount>\n/withdraw <amount>\n/claim_interest - 5% daily\n\n🎮 GAMES\n/ttt [amount] - Tic Tac Toe\n/mines <amount> <bombs>\n/CLcricket [amount]\n/rps [amount]\n/numpuz - Number puzzle\n\n🏆 OTHER\n/leaderboard - Rich list\n/achievements - Your badges\n/refer - Get link\n/claimcode <code>\n/activecodes\n/hof - Hall of fame\n/stats - Cricket leaderboard\n/mystats - Your cricket stats\n\n━━━━━━━━━━━━━━━━━━━━\n💡 Need help? @clbothelp"
    await update.message.reply_text(msg)


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
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text('❌ Reply to a photo with /setpfp')
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

# ============ SHOP ============
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    keyboard = [
        [InlineKeyboardButton("🇮🇳 India (Current)", callback_data="shop_India_current")],
        [InlineKeyboardButton("🇮🇳 India (Legends)", callback_data="shop_India_legend")],
        [InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 England (Current)", callback_data="shop_England_current")],
        [InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 England (Legends)", callback_data="shop_England_legend")],
        [InlineKeyboardButton("🇳🇿 New Zealand (Current)", callback_data="shop_New Zealand_current")],
        [InlineKeyboardButton("🇳🇿 New Zealand (Legends)", callback_data="shop_New Zealand_legend")],
        [InlineKeyboardButton("🇦🇺 Australia (Current)", callback_data="shop_Australia_current")],
        [InlineKeyboardButton("🇦🇺 Australia (Legends)", callback_data="shop_Australia_legend")],
        [InlineKeyboardButton("👩 Women Players", callback_data="shop_women")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛒 CRICKETER SHOP\n\nSelect category:", reply_markup=reply_markup)


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
    if len(parts) < 3:
        await query.edit_message_text("❌ Invalid selection")
        return
    
    country = parts[1]
    ptype = parts[2]
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM shop WHERE category=? AND type=?", (country, ptype))
    players = c.fetchall()
    conn.close()
    
    if not players:
        await query.edit_message_text(f"❌ No players found")
        return
    
    msg = f"🛒 {country} {ptype.upper()} PLAYERS\n\n"
    for p in players:
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
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT level, board, moves FROM numpuz_progress WHERE user_id = ?", (user_id,))
    saved = c.fetchone()
    conn.close()
    if saved and saved[1]:
        level = saved[0]
        board = json.loads(saved[1])
        if board:
            keyboard = get_board_keyboard(board, level)
            await update.message.reply_text(f"🧩 NUMPUZ - LEVEL {level}", reply_markup=keyboard)
            return
    level = 1
    size = get_size_for_level(level)
    while True:
        board = get_shuffled_board(size)
        if is_solvable(board):
            break
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO numpuz_progress (user_id, level, board, moves) VALUES (?, ?, ?, ?)", (user_id, level, json.dumps(board), 0))
    conn.commit()
    conn.close()
    keyboard = get_board_keyboard(board, level)
    await update.message.reply_text(f"🧩 NUMPUZ - LEVEL {level}", reply_markup=keyboard)

async def numpuz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data
    if data.startswith("numpuz_"):
        parts = data.split("_")
        level = int(parts[1])
        row = int(parts[2])
        col = int(parts[3])
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT level, board, moves FROM numpuz_progress WHERE user_id = ?", (user_id,))
        saved = c.fetchone()
        if not saved:
            await query.edit_message_text("No game! Use /numpuz")
            conn.close()
            return
        current_level = saved[0]
        board = json.loads(saved[1])
        moves = saved[2]
        if current_level != level:
            await query.answer("Wrong level!", show_alert=True)
            conn.close()
            return
        if move_tile(board, row, col):
            moves += 1
            if is_win(board):
                next_level = current_level + 1
                next_size = get_size_for_level(next_level)
                while True:
                    new_board = get_shuffled_board(next_size)
                    if is_solvable(new_board):
                        break
                c.execute("UPDATE numpuz_progress SET level = ?, board = ?, moves = ? WHERE user_id = ?", (next_level, json.dumps(new_board), 0, user_id))
                conn.commit()
                conn.close()
                keyboard = get_board_keyboard(new_board, next_level)
                await query.edit_message_text(f"🎉 LEVEL {current_level} COMPLETE!\n\nMoves: {moves}\n\n🧩 NUMPUZ - LEVEL {next_level} ({next_size}x{next_size})", reply_markup=keyboard)
                return
            c.execute("UPDATE numpuz_progress SET board = ?, moves = ? WHERE user_id = ?", (json.dumps(board), moves, user_id))
            conn.commit()
            conn.close()
            keyboard = get_board_keyboard(board, current_level)
            await query.edit_message_text(f"🧩 NUMPUZ - LEVEL {current_level}", reply_markup=keyboard)
        else:
            conn.close()


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

# ============ MINES GAME ============
active_mines = {}

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
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "💣 **MINES**\n"
            "`/mines <amount> <bombs>`\n"
            "Example: `/mines 1000 3`\n\n"
            "⚡ Min:100 | Max:10,000\n"
            "💣 Bombs:1-24\n"
            "🎯 More bombs = bigger reward!",
            
        )
        return
    
    try:
        bet = int(args[0])
        bombs = int(args[1])
    except:
        await update.message.reply_text("❌ Invalid!")
        return
    
    if bet < 100 or bet > 10000:
        await update.message.reply_text("❌ Bet 100-10,000!")
        return
    
    if bombs < 1 or bombs > 24:
        await update.message.reply_text("❌ Bombs 1-24!")
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    conn.close()
    
    if balance < bet:
        await update.message.reply_text(f"❌ Need {bet:,}, have {balance:,}")
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, user_id))
    conn.commit()
    conn.close()
    
    bomb_pos = random.sample(range(25), bombs)
    max_mult = MAX_MULTIPLIER.get(bombs, 50.0)
    
    active_mines[user_id] = {
        'bet': bet,
        'bombs': bomb_pos,
        'revealed': [],
        'active': True,
        'bomb_count': bombs,
        'max_mult': max_mult
    }
    
    keyboard = []
    for i in range(5):
        row = []
        for j in range(5):
            row.append(InlineKeyboardButton("❓", callback_data=f"mine_{user_id}_{i*5+j}"))
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("💰 CASHOUT", callback_data=f"mine_cashout_{user_id}")])
    
    await update.message.reply_text(
        f"💣 **MINES**\n"
        f"💰 {bet:,} | 💣 {bombs}\n"
        f"🎯 Max: {max_mult}x\n"
        f"📈 1.00x | 💎 {bet:,}\n\n"
        f"⬇️ Click tiles ⬇️",
        reply_markup=InlineKeyboardMarkup(keyboard),
        
    )

async def mine_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if user_id not in active_mines:
        await query.edit_message_text("❌ No game! /mines")
        return
    
    game = active_mines[user_id]
    
    if data.startswith("mine_cashout_"):
        safe = len([t for t in game['revealed'] if t not in game['bombs']])
        mult = calc_multiplier(game['bomb_count'], safe)
        win = int(game['bet'] * mult)
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        bal = c.fetchone()[0]
        c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (win, user_id))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"💰 **CASHOUT**\n"
            f"✅ +{win:,}\n"
            f"📈 {mult}x\n"
            f"💳 {bal + win:,}",
            
        )
        del active_mines[user_id]
        return
    
    if data.startswith("mine_"):
        idx = int(data.split("_")[2])
        
        if idx in game['revealed']:
            await query.answer("Already opened!")
            return
        
        game['revealed'].append(idx)
        
        if idx in game['bombs']:
            await query.edit_message_text(
                f"💣 **BOMB!**\n"
                f"💰 Lost: {game['bet']:,}\n"
                f"😵 Game over!",
                
            )
            del active_mines[user_id]
            return
        
        safe = len([t for t in game['revealed'] if t not in game['bombs']])
        total_safe = 25 - game['bomb_count']
        mult = calc_multiplier(game['bomb_count'], safe)
        win = int(game['bet'] * mult)
        
        if safe >= total_safe:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            bal = c.fetchone()[0]
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (win, user_id))
            conn.commit()
            conn.close()
            
            await query.edit_message_text(
                f"🎉 **WIN!**\n"
                f"✅ All safe tiles!\n"
                f"💰 +{win:,}\n"
                f"📈 {mult}x\n"
                f"💳 {bal + win:,}",
                
            )
            del active_mines[user_id]
            return
        
        keyboard = []
        for i in range(5):
            row = []
            for j in range(5):
                pos = i*5+j
                if pos in game['revealed']:
                    row.append(InlineKeyboardButton("💎", callback_data=f"mine_{user_id}_{pos}"))
                else:
                    row.append(InlineKeyboardButton("❓", callback_data=f"mine_{user_id}_{pos}"))
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("💰 CASHOUT", callback_data=f"mine_cashout_{user_id}")])
        
        left = total_safe - safe
        max_mult = game['max_mult']
        
        await query.edit_message_text(
            f"💎 **SAFE**\n"
            f"💰 {game['bet']:,}\n"
            f"✅ {safe}/{total_safe}\n"
            f"📈 {mult}x (Max: {max_mult}x)\n"
            f"💎 {win:,}\n"
            f"💚 {left} left\n\n"
            f"⬇️ Click or CASHOUT",
            reply_markup=InlineKeyboardMarkup(keyboard),
            
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
    msg = "💎 **MY SHOP3 PLAYERS**\n\n"
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
        f"🎯 **TIC TAC TOE**\n\n"
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
            f"🎯 **TIC TAC TOE**\n\n"
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
                result_text = f"🏆 **WINNER: {winner_name.upper()}** 🏆\n💰 +{game.bet*2:,} credits\n💳 New Balance: {new_bal:,}"
            else:
                result_text = f"🏆 **WINNER: {winner_name.upper()}** 🏆"
            
            await query.edit_message_text(
                f"🎯 **TIC TAC TOE**\n\n"
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
                f"🎯 **TIC TAC TOE**\n\n"
                f"❌ {game.player1_name} vs ⭕ {game.player2_name}\n\n"
                f"🤝 **DRAW** 🤝",
                reply_markup=game.get_keyboard(),
                
            )
            del ttt_games[game_id]
            return
        
        else:
            turn_name = game.player1_name if game.current_turn == game.player1_id else game.player2_name
            turn_symbol = "❌" if game.current_turn == game.player1_id else "⭕"
            bet_text = f"💰 Bet: {game.bet:,} | Prize: {game.bet*2:,}" if game.bet > 0 else "🎮 Normal Game"
            
            await query.edit_message_text(
                f"🎯 **TIC TAC TOE**\n\n"
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
    await update.message.reply_text("🏏 **CRICKET STATS LEADERBOARD**\n\nSelect stat to view:", reply_markup=InlineKeyboardMarkup(keyboard))

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
        msg = "🏏 **MOST RUNS LEADERBOARD**\n\n"
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
        msg = "🎯 **MOST WICKETS LEADERBOARD**\n\n"
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
        msg = "⭐ **HIGHEST SCORE LEADERBOARD**\n\n"
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
        msg = "✅ **MOST WINS LEADERBOARD**\n\n"
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
        msg = "❌ **MOST LOSSES LEADERBOARD**\n\n"
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
        await query.edit_message_text("🏏 **CRICKET STATS LEADERBOARD**\n\nSelect stat to view:", reply_markup=InlineKeyboardMarkup(keyboard))

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
            f"🏏 **YOUR CRICKET STATS**\n\n"
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
    
    msg = f"🏏 **YOUR CRICKET STATS**\n\n"
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
        await update.message.reply_text('🛒 **SHOP4**\n\nNo players yet.\n👑 Admin: /addplayer4 <name> <price>')
        return
    
    msg = "🛒 **SHOP4**\n\n"
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
    msg = "🤑 **MY SHOP4 PLAYERS**\n\n"
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
    
    msg = "🏆 **SHOP4 TOP COLLECTORS**\n\n"
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

# ============ AUCTION SYSTEM - PART 1 (DATABASE & IMPORTS) ==========

import sqlite3
import random
import asyncio
import threading
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes

# ============ DATABASE INITIALIZATION ==========

def init_auction_db():
    conn = get_db()
    c = conn.cursor()
    
    # Players table
    c.execute('''CREATE TABLE IF NOT EXISTS auction_players
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  base_price INTEGER,
                  status TEXT DEFAULT 'pending',
                  sold_to TEXT,
                  sold_price INTEGER,
                  team TEXT)''')
    
    # Teams/Captains table
    c.execute('''CREATE TABLE IF NOT EXISTS auction_teams
                 (team_name TEXT PRIMARY KEY,
                  budget INTEGER,
                  captain_id INTEGER,
                  captain_name TEXT,
                  purse_used INTEGER DEFAULT 0)''')
    
    # Purchases table
    c.execute('''CREATE TABLE IF NOT EXISTS auction_purchases
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  team_name TEXT,
                  player_id INTEGER,
                  player_name TEXT,
                  price INTEGER,
                  purchased_at TEXT)''')
    
    # Auction session table
    c.execute('''CREATE TABLE IF NOT EXISTS auction_session
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  tournament_name TEXT,
                  total_teams INTEGER,
                  base_budget INTEGER,
                  current_player_id INTEGER,
                  current_bid INTEGER,
                  current_bidder TEXT,
                  current_bidder_team TEXT,
                  is_active INTEGER DEFAULT 0,
                  is_paused INTEGER DEFAULT 0,
                  created_at TEXT)''')
    
    # Captain requests table
    c.execute('''CREATE TABLE IF NOT EXISTS captain_requests
                 (user_id INTEGER PRIMARY KEY,
                  user_name TEXT,
                  requested_at TEXT,
                  status TEXT DEFAULT 'pending')''')
    
    # Player registration (simple)
    c.execute('''CREATE TABLE IF NOT EXISTS auction_players_registered
                 (user_id INTEGER PRIMARY KEY,
                  user_name TEXT,
                  registered_at TEXT)''')
    
    conn.commit()
    conn.close()

init_auction_db()

# ============ GLOBAL VARIABLES ==========

auction_active = False
auction_paused = False
current_player = None
current_bid = 0
current_bidder = None
current_bidder_team = None

# Available teams
AVAILABLE_TEAMS = ["CSK", "MI", "RCB", "KKR", "SRH", "DC", "PBKS", "LSG", "GT", "RR"]

# ============ HELPER FUNCTIONS ==========

def cr_to_number(cr_str):
    """Convert 1cr to 10000000"""
    try:
        if 'cr' in cr_str.lower():
            num = float(cr_str.lower().replace('cr', ''))
            return int(num * 10000000)
    except:
        pass
    return None

def number_to_cr(amount):
    """Convert 10000000 to 1cr"""
    cr = amount / 10000000
    if cr == int(cr):
        return f"{int(cr)}cr"
    return f"{cr}cr"

def get_auction_session():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT tournament_name, total_teams, base_budget, current_player_id, current_bid, current_bidder, current_bidder_team, is_active, is_paused FROM auction_session ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result

# ============ AUCTION SYSTEM - PART 2 (USER COMMANDS) ==========

# ============ REGISTER PLAYER ==========

# ============ REGISTER WITH BUTTONS ==========

# ============ REGISTER WITH TOURNAMENT SELECTION ==========

# ============ REGISTER WITH WORKING BUTTONS ==========

# ============ REGISTER WITH CONFIRM BUTTON ==========

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Add column if missing
    try:
        c.execute("ALTER TABLE auction_players_registered ADD COLUMN tournament_id INTEGER DEFAULT 1")
    except:
        pass
    
    # Check if already registered
    c.execute("SELECT * FROM auction_players_registered WHERE user_id=?", (user_id,))
    if c.fetchone():
        await update.message.reply_text("✅ You are already registered!")
        conn.close()
        return
    
    # Get tournament
    c.execute("SELECT id, tournament_name FROM auction_session ORDER BY id DESC LIMIT 1")
    tour = c.fetchone()
    conn.close()
    
    if not tour:
        await update.message.reply_text("❌ No tournament! Admin: /create_auc")
        return
    
    tour_id, tour_name = tour
    
    # Simple button - direct confirmation
    keyboard = [[InlineKeyboardButton("✅ CONFIRM REGISTRATION", callback_data=f"confirm_reg_{tour_id}_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🏏 **PLAYER REGISTRATION**\n\n"
        f"📛 Tournament: {tour_name}\n"
        f"👤 User: {user_name}\n\n"
        f"Click CONFIRM to register:",
        reply_markup=reply_markup
    )


async def confirm_reg_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if data.startswith("confirm_reg_"):
        parts = data.split("_")
        tour_id = int(parts[2])
        target_id = int(parts[3])
        
        if user_id != target_id:
            await query.answer("Not for you!", show_alert=True)
            return
        
        conn = get_db()
        c = conn.cursor()
        
        c.execute("SELECT * FROM auction_players_registered WHERE user_id=? AND tournament_id=?", (user_id, tour_id))
        if c.fetchone():
            await query.edit_message_text("✅ You are already registered!")
            conn.close()
            return
        
        c.execute("INSERT INTO auction_players_registered (user_id, user_name, tournament_id, registered_at) VALUES (?, ?, ?, ?)",
                  (user_id, user_name, tour_id, datetime.now().isoformat()))
        
        c.execute("SELECT tournament_name FROM auction_session WHERE id=?", (tour_id,))
        tour = c.fetchone()
        tour_name = tour[0] if tour else "Unknown"
        
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"✅ **REGISTERED!**\n\n"
            f"🏏 {user_name} in {tour_name}\n\n"
            f"💡 /req_captain - Request captaincy"
        )



async def register_tour_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if data.startswith("reg_tour_"):
        tour_id = int(data.split("_")[2])
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT tournament_name, base_budget FROM auction_session WHERE id=?", (tour_id,))
        tour = c.fetchone()
        
        if not tour:
            await query.edit_message_text("❌ Tournament not found!")
            conn.close()
            return
        
        tour_name, base_budget = tour
        budget_cr = int(base_budget / 10000000)
        
        keyboard = [
            [InlineKeyboardButton("✅ CONFIRM", callback_data=f"reg_confirm_{tour_id}_{user_id}")],
            [InlineKeyboardButton("❌ CANCEL", callback_data="reg_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🏏 **CONFIRM REGISTRATION**\n\n"
            f"📛 Tournament: {tour_name}\n"
            f"💰 Budget: {budget_cr}CR per team\n"
            f"👤 User: {user_name}\n\n"
            f"Click CONFIRM to register.",
            reply_markup=reply_markup
        )
        conn.close()


async def register_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if data == "reg_cancel":
        await query.edit_message_text("❌ Registration cancelled!")
        return
    
    if data.startswith("reg_confirm_"):
        parts = data.split("_")
        tour_id = int(parts[2])
        target_id = int(parts[3])
        
        if user_id != target_id:
            await query.answer("This is not for you!", show_alert=True)
            return
        
        conn = get_db()
        c = conn.cursor()
        
        # Add tournament_id column if not exists
        try:
            c.execute("ALTER TABLE auction_players_registered ADD COLUMN tournament_id INTEGER DEFAULT 1")
        except:
            pass
        
        c.execute("SELECT * FROM auction_players_registered WHERE user_id=? AND tournament_id=?", (user_id, tour_id))
        if c.fetchone():
            await query.edit_message_text("✅ You are already registered!")
            conn.close()
            return
        
        c.execute("INSERT INTO auction_players_registered (user_id, user_name, tournament_id, registered_at) VALUES (?, ?, ?, ?)",
                  (user_id, user_name, tour_id, datetime.now().isoformat()))
        
        c.execute("SELECT tournament_name FROM auction_session WHERE id=?", (tour_id,))
        tour = c.fetchone()
        tour_name = tour[0] if tour else "Unknown"
        
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"✅ **REGISTERED!**\n\n"
            f"🏏 {user_name}, you are now a PLAYER in {tour_name}!\n\n"
            f"💡 /req_captain - Request captaincy"
        )


async def my_tournament(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT r.tournament_id, s.tournament_name, r.registered_at 
                 FROM auction_players_registered r 
                 JOIN auction_session s ON r.tournament_id = s.id 
                 WHERE r.user_id=?""", (user_id,))
    reg = c.fetchone()
    conn.close()
    
    if not reg:
        await update.message.reply_text("❌ You are not registered!\n💡 /register to join")
        return
    
    tour_id, tour_name, registered_at = reg
    
    await update.message.reply_text(
        f"🏏 **MY TOURNAMENT**\n\n"
        f"📛 {tour_name}\n"
        f"📅 Registered: {registered_at[:19]}\n\n"
        f"💡 /req_captain - Request captaincy"
    )

async def register_tour_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if data.startswith("reg_tour_"):
        tour_id = int(data.split("_")[2])
        
        # Get tournament details
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT tournament_name, base_budget FROM auction_session WHERE id=?", (tour_id,))
        tour = c.fetchone()
        
        if not tour:
            await query.edit_message_text("❌ Tournament not found!")
            conn.close()
            return
        
        tour_name, base_budget = tour
        
        # Confirmation keyboard
        keyboard = [
            [InlineKeyboardButton("✅ CONFIRM REGISTRATION", callback_data=f"reg_confirm_{tour_id}_{user_id}")],
            [InlineKeyboardButton("❌ CANCEL", callback_data="reg_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🏏 **CONFIRM REGISTRATION**\n\n"
            f"📛 Tournament: {tour_name}\n"
            f"💰 Budget per team: {int(base_budget/10000000)}CR\n"
            f"👤 User: {user_name}\n\n"
            f"⚠️ Click CONFIRM to register as a player.\n"
            f"Registration is FREE!\n\n"
            f"💡 Want to be CAPTAIN? Register first, then use /req_captain",
            reply_markup=reply_markup,
            parse_mode=None
        )
        conn.close()


async def register_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if data == "reg_cancel":
        await query.edit_message_text("❌ Registration cancelled!")
        return
    
    if data.startswith("reg_confirm_"):
        parts = data.split("_")
        tour_id = int(parts[2])
        target_id = int(parts[3])
        
        if user_id != target_id:
            await query.answer("This is not for you!", show_alert=True)
            return
        
        conn = get_db()
        c = conn.cursor()
        
        # Check if already registered
        c.execute("SELECT * FROM auction_players_registered WHERE user_id=? AND tournament_id=?", (user_id, tour_id))
        if c.fetchone():
            await query.edit_message_text("✅ You are already registered in this tournament!")
            conn.close()
            return
        
        # Register user
        c.execute("INSERT INTO auction_players_registered (user_id, user_name, tournament_id, registered_at) VALUES (?, ?, ?, ?)",
                  (user_id, user_name, tour_id, datetime.now().isoformat()))
        
        # Get tournament name
        c.execute("SELECT tournament_name FROM auction_session WHERE id=?", (tour_id,))
        tour = c.fetchone()
        tour_name = tour[0] if tour else "Unknown"
        
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"✅ **REGISTERED SUCCESSFULLY!**\n\n"
            f"🏏 {user_name}, you are now a PLAYER in {tour_name}!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 Want to be a CAPTAIN?\n"
            f"Use /req_captain to request captaincy\n\n"
            f"💡 Admin will approve captain requests",
            parse_mode=None
        )


async def my_tournament(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check which tournament user is registered in"""
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT r.tournament_id, s.tournament_name, r.registered_at 
                 FROM auction_players_registered r 
                 JOIN auction_session s ON r.tournament_id = s.id 
                 WHERE r.user_id=?""", (user_id,))
    reg = c.fetchone()
    conn.close()
    
    if not reg:
        await update.message.reply_text("❌ You are not registered in any tournament!\n💡 /register to join")
        return
    
    tour_id, tour_name, registered_at = reg
    
    await update.message.reply_text(
        f"🏏 **MY TOURNAMENT**\n\n"
        f"📛 Tournament: {tour_name}\n"
        f"📅 Registered: {registered_at}\n\n"
        f"💡 /req_captain - Request to become captain",
        parse_mode=None
    )

async def register_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if data == "reg_cancel":
        await query.edit_message_text("❌ Registration cancelled!")
        return
    
    if data.startswith("reg_confirm_"):
        target_id = int(data.split("_")[2])
        
        if user_id != target_id:
            await query.answer("This is not for you!", show_alert=True)
            return
        
        conn = get_db()
        c = conn.cursor()
        
        c.execute("SELECT * FROM auction_players_registered WHERE user_id=?", (user_id,))
        if c.fetchone():
            await query.edit_message_text("✅ You are already registered!")
            conn.close()
            return
        
        c.execute("INSERT INTO auction_players_registered (user_id, user_name, registered_at) VALUES (?, ?, ?)",
                  (user_id, user_name, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"✅ **REGISTERED SUCCESSFULLY!**\n\n"
            f"🏏 {user_name}, you are now a PLAYER!\n\n"
            f"💡 Want to be a CAPTAIN?\n"
            f"Use /req_captain to request captaincy",
            
        )


# ============ REQUEST CAPTAIN ==========

async def req_captain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Check if already a captain
    c.execute("SELECT * FROM auction_teams WHERE captain_id=?", (user_id,))
    if c.fetchone():
        await update.message.reply_text("👑 You are already a CAPTAIN!")
        conn.close()
        return
    
    # Check if request already sent
    c.execute("SELECT status FROM captain_requests WHERE user_id=?", (user_id,))
    req = c.fetchone()
    
    if req:
        if req[0] == 'pending':
            await update.message.reply_text("⏳ Your captain request is already PENDING!\n💡 Wait for admin approval")
        elif req[0] == 'approved':
            await update.message.reply_text("✅ Your captain request was APPROVED! Check /myrequest")
        elif req[0] == 'rejected':
            await update.message.reply_text("❌ Your captain request was REJECTED.\n💡 Try next tournament")
        conn.close()
        return
    
    c.execute("INSERT INTO captain_requests (user_id, user_name, requested_at, status) VALUES (?, ?, ?, 'pending')",
              (user_id, user_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    # Notify admin
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"👑 **NEW CAPTAIN REQUEST!**\n\n"
                f"User: @{user_name} ({user_name})\n"
                f"ID: `{user_id}`\n\n"
                f"💡 /captain_requests to view and approve",
                
            )
        except:
            pass
    
    await update.message.reply_text(
        f"👑 **CAPTAIN REQUEST SENT!**\n\n"
        f"User: {user_name}\n"
        f"Status: ⏳ PENDING APPROVAL\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📢 Admin has been notified.\n"
        f"You will be notified when approved.\n\n"
        f"💡 /myrequest - Check status",
        
    )


# ============ MY REQUEST STATUS ==========

async def myrequest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Check if already captain
    c.execute("SELECT team_name, budget FROM auction_teams WHERE captain_id=?", (user_id,))
    captain = c.fetchone()
    
    if captain:
        await update.message.reply_text(
            f"👑 **CAPTAIN REQUEST STATUS**\n\n"
            f"Status: ✅ **APPROVED!**\n"
            f"Team: {captain[0]}\n"
            f"💰 Budget: {captain[1]:,}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 /mybudget - Check budget\n"
            f"💡 /myplayers - Your squad\n"
            f"💡 /bid <amount>cr - Place bids",
            
        )
        conn.close()
        return
    
    c.execute("SELECT status, requested_at FROM captain_requests WHERE user_id=?", (user_id,))
    req = c.fetchone()
    conn.close()
    
    if not req:
        await update.message.reply_text(
            f"👑 **CAPTAIN REQUEST STATUS**\n\n"
            f"Status: ❌ **NOT REQUESTED**\n\n"
            f"💡 Use /req_captain to request captaincy",
            
        )
        return
    
    status = req[0]
    requested_at = req[1]
    
    if status == 'pending':
        await update.message.reply_text(
            f"👑 **CAPTAIN REQUEST STATUS**\n\n"
            f"Status: ⏳ **PENDING**\n"
            f"Requested: {requested_at}\n\n"
            f"💡 Waiting for admin approval",
            
        )
    elif status == 'approved':
        await update.message.reply_text(
            f"👑 **CAPTAIN REQUEST STATUS**\n\n"
            f"Status: ✅ **APPROVED!**\n\n"
            f"💡 Contact admin for team assignment",
            
        )
    elif status == 'rejected':
        await update.message.reply_text(
            f"👑 **CAPTAIN REQUEST STATUS**\n\n"
            f"Status: ❌ **REJECTED**\n\n"
            f"Reason: All captain slots filled\n"
            f"💡 Try next tournament!",
            
        )

# ============ AUCTION SYSTEM - PART 3 (ADMIN CAPTAIN REQUESTS) ==========

# ============ VIEW CAPTAIN REQUESTS ==========

async def captain_requests(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT user_id, user_name, requested_at FROM captain_requests WHERE status='pending' ORDER BY requested_at")
    requests = c.fetchall()
    
    # Get already approved count
    c.execute("SELECT COUNT(*) FROM auction_teams")
    approved_count = c.fetchone()[0]
    
    conn.close()
    
    if not requests:
        await update.message.reply_text(
            f"👑 **CAPTAIN REQUESTS**\n\n"
            f"✅ Approved: {approved_count}/10\n"
            f"⏳ Pending: 0\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"No pending requests!",
            
        )
        return
    
    # Create keyboard with requests
    keyboard = []
    for req in requests:
        user_id, user_name, requested_at = req
        keyboard.append([InlineKeyboardButton(
            f"👑 {user_name} (ID: {user_id})",
            callback_data=f"approve_cap_{user_id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👑 **CAPTAIN REQUESTS**\n\n"
        f"✅ Approved: {approved_count}/10\n"
        f"⏳ Pending: {len(requests)}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Click on a user to approve:",
        reply_markup=reply_markup,
        
    )


# ============ APPROVE CAPTAIN CALLBACK ==========

async def approve_captain_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id not in ADMIN_IDS:
        await query.edit_message_text("❌ Admin only!")
        return
    
    data = query.data
    user_id = int(data.split("_")[2])
    
    conn = get_db()
    c = conn.cursor()
    
    # Get user details
    c.execute("SELECT user_name FROM captain_requests WHERE user_id=?", (user_id,))
    req = c.fetchone()
    
    if not req:
        await query.edit_message_text("❌ Request not found!")
        conn.close()
        return
    
    user_name = req[0]
    
    # Get available teams
    c.execute("SELECT team_name FROM auction_teams")
    taken_teams = [row[0] for row in c.fetchall()]
    available_teams = [t for t in AVAILABLE_TEAMS if t not in taken_teams]
    
    if not available_teams:
        # Reject if no teams left
        c.execute("UPDATE captain_requests SET status='rejected' WHERE user_id=?", (user_id,))
        conn.commit()
        conn.close()
        
        await query.edit_message_text(
            f"❌ **CANNOT APPROVE!**\n\n"
            f"User: {user_name}\n"
            f"Reason: All 10 captain slots are filled!\n\n"
            f"Request marked as REJECTED.",
            
        )
        
        # Notify user
        try:
            await context.bot.send_message(
                user_id,
                f"❌ **CAPTAIN REQUEST REJECTED**\n\n"
                f"All captain slots for this tournament are filled.\n"
                f"💡 Try next tournament!",
                
            )
        except:
            pass
        return
    
    # Create team selection keyboard
    keyboard = []
    for team in available_teams:
        keyboard.append([InlineKeyboardButton(
            f"🏏 {team}",
            callback_data=f"assign_team_{user_id}_{team}"
        )])
    
    await query.edit_message_text(
        f"✅ **APPROVE CAPTAIN REQUEST**\n\n"
        f"User: {user_name} (ID: {user_id})\n\n"
        f"Select team for this captain:\n\n"
        f"Available Teams: {len(available_teams)}/10",
        reply_markup=InlineKeyboardMarkup(keyboard),
        
    )
    conn.close()


# ============ ASSIGN TEAM CALLBACK ==========

async def assign_team_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id not in ADMIN_IDS:
        await query.edit_message_text("❌ Admin only!")
        return
    
    data = query.data
    parts = data.split("_")
    user_id = int(parts[2])
    team = parts[3]
    
    conn = get_db()
    c = conn.cursor()
    
    # Get user name
    c.execute("SELECT user_name FROM captain_requests WHERE user_id=?", (user_id,))
    req = c.fetchone()
    
    if not req:
        await query.edit_message_text("❌ User not found!")
        conn.close()
        return
    
    user_name = req[0]
    
    # Get session budget
    session = get_auction_session()
    base_budget = session[2] if session else 10000000
    
    # Add to teams
    c.execute("INSERT INTO auction_teams (team_name, budget, captain_id, captain_name, purse_used) VALUES (?, ?, ?, ?, 0)",
              (team, base_budget, user_id, user_name))
    
    # Update request status
    c.execute("UPDATE captain_requests SET status='approved' WHERE user_id=?", (user_id,))
    
    conn.commit()
    conn.close()
    
    # Notify user
    try:
        await context.bot.send_message(
            user_id,
            f"🎉 **CONGRATULATIONS!**\n\n"
            f"Your captain request has been **APPROVED**!\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏏 Team: {team}\n"
            f"💰 Budget: {base_budget:,} ({number_to_cr(base_budget)})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 /mybudget - Check budget\n"
            f"💡 /myplayers - Your squad\n"
            f"💡 /bid <amount>cr - Place bids (when auction starts)\n\n"
            f"🏆 Good luck!",
            
        )
    except:
        pass
    
    await query.edit_message_text(
        f"✅ **CAPTAIN APPROVED!**\n\n"
        f"User: {user_name}\n"
        f"Team: {team}\n"
        f"💰 Budget: {base_budget:,} ({number_to_cr(base_budget)})\n\n"
        f"📢 User notified!\n"
        f"✅ Approved: {len(AVAILABLE_TEAMS) - len([t for t in AVAILABLE_TEAMS if t != team])}/10",
        
    )

# ============ AUCTION SYSTEM - PART 4 (ADMIN AUCTION SETUP) ==========

# ============ CREATE AUCTION ==========

async def create_auc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "📝 **CREATE AUCTION**\n\n"
            "Usage: `/create_auc <name> <teams> <budget>`\n"
            "Example: `/create_auc \"IPL 2024\" 10 10000000`\n\n"
            "💰 Budget in credits (e.g., 10000000 = 1cr)\n"
            "👥 Teams: Number of teams (max 10)\n"
            "🏏 Name: Tournament name in quotes",
            
        )
        return
    
    # Parse name with quotes
    if args[0].startswith('"'):
        name_parts = []
        for i, arg in enumerate(args):
            name_parts.append(arg)
            if arg.endswith('"'):
                name = " ".join(name_parts).strip('"')
                remaining = args[i+1:]
                break
        else:
            await update.message.reply_text("❌ Invalid name format! Use quotes for names with spaces.")
            return
    else:
        name = args[0]
        remaining = args[1:]
    
    if len(remaining) < 2:
        await update.message.reply_text("❌ Usage: /create_auc <name> <teams> <budget>")
        return
    
    try:
        total_teams = int(remaining[0])
        base_budget = int(remaining[1])
    except:
        await update.message.reply_text("❌ Invalid teams or budget!")
        return
    
    if total_teams > 10:
        await update.message.reply_text("❌ Maximum 10 teams allowed!")
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Clear previous session
    c.execute("DELETE FROM auction_session")
    c.execute("DELETE FROM auction_players")
    c.execute("DELETE FROM auction_purchases")
    
    # Create new session
    c.execute("""INSERT INTO auction_session 
                 (tournament_name, total_teams, base_budget, is_active, is_paused, created_at) 
                 VALUES (?, ?, ?, 0, 0, ?)""",
              (name, total_teams, base_budget, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    # Add default players
    default_players = [
        "Virat Kohli", "Rohit Sharma", "MS Dhoni", "Jasprit Bumrah", "Hardik Pandya",
        "Ravindra Jadeja", "KL Rahul", "Shubman Gill", "Suryakumar Yadav", "Rishabh Pant",
        "Mohammed Shami", "Ravichandran Ashwin", "Shreyas Iyer", "Ishan Kishan", "Yuzvendra Chahal",
        "Axar Patel", "Sanju Samson", "Deepak Chahar", "Mohammed Siraj", "Kuldeep Yadav"
    ]
    
    conn = get_db()
    c = conn.cursor()
    for player in default_players:
        c.execute("INSERT INTO auction_players (name, base_price, status) VALUES (?, 10000000, 'pending')", (player,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ **AUCTION CREATED!**\n\n"
        f"🏆 Tournament: {name}\n"
        f"👥 Total Teams: {total_teams}\n"
        f"💰 Base Budget: {base_budget:,} ({number_to_cr(base_budget)})\n"
        f"🏏 Players added: {len(default_players)}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 /players - View all players\n"
        f"💡 /add_player - Add more players\n"
        f"💡 /start_auc - Start auction when ready",
        
    )


# ============ ADD PLAYER ==========

async def add_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "📝 **ADD PLAYER**\n\n"
            "Usage: `/add_player <name> <base_price>`\n"
            "Example: `/add_player \"Virat Kohli\" 10000000`\n\n"
            "💰 Base price in credits (10000000 = 1cr)\n"
            "🏏 Use quotes for names with spaces",
            
        )
        return
    
    # Parse name with quotes
    if args[0].startswith('"'):
        name_parts = []
        for i, arg in enumerate(args):
            name_parts.append(arg)
            if arg.endswith('"'):
                name = " ".join(name_parts).strip('"')
                remaining = args[i+1:]
                break
        else:
            await update.message.reply_text("❌ Invalid name format! Use quotes for names with spaces.")
            return
    else:
        name = args[0]
        remaining = args[1:]
    
    if len(remaining) < 1:
        await update.message.reply_text("❌ Please provide base price!")
        return
    
    try:
        base_price = int(remaining[0])
    except:
        await update.message.reply_text("❌ Invalid base price!")
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO auction_players (name, base_price, status) VALUES (?, ?, 'pending')", (name, base_price))
    conn.commit()
    player_id = c.lastrowid
    conn.close()
    
    await update.message.reply_text(
        f"✅ **PLAYER ADDED!**\n\n"
        f"🏏 {name}\n"
        f"💰 Base Price: {base_price:,} ({number_to_cr(base_price)})\n"
        f"🆔 ID: {player_id}\n\n"
        f"💡 /players - View all players",
        
    )


# ============ VIEW PLAYERS LIST ==========
async def players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, base_price, status, team FROM auction_players ORDER BY id")
    players = c.fetchall()
    conn.close()
    
    if not players:
        await update.message.reply_text("📭 No players found! Use /add_player to add players.")
        return
    
    pending = [p for p in players if p[3] == 'pending']
    sold = [p for p in players if p[3] == 'sold']
    unsold = [p for p in players if p[3] == 'unsold']
    
    msg = f"🏏 AUCTION PLAYERS LIST\n\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 Total: {len(players)} | ✅ Sold: {len(sold)} | ❌ Unsold: {len(unsold)} | ⏳ Pending: {len(pending)}\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if pending:
        msg += f"⏳ PENDING PLAYERS:\n"
        for i, p in enumerate(pending[:10], 1):
            price = p[2] if isinstance(p[2], int) else int(p[2]) if p[2] else 0
            msg += f"{i}. {p[1]} - {number_to_cr(price)} 💰\n"
        if len(pending) > 10:
            msg += f"... and {len(pending)-10} more\n"
    
    if sold:
        msg += f"\n✅ SOLD PLAYERS:\n"
        for i, p in enumerate(sold[:5], 1):
            price = p[2] if isinstance(p[2], int) else int(p[2]) if p[2] else 0
            team = p[4] if p[4] else "Unknown"
            msg += f"{i}. {p[1]} → {team} - {number_to_cr(price)} 💰\n"
        if len(sold) > 5:
            msg += f"... and {len(sold)-5} more\n"
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"💡 /rmplayer <number> - Remove player by number\n"
    msg += f"💡 /add_player - Add more players"
    
    await update.message.reply_text(msg)


# ============ REMOVE PLAYER ==========

async def rmplayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ /rmplayer <player_number>\nExample: /rmplayer 5\n\nUse /players to see numbers")
        return
    
    try:
        player_num = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid player number!")
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Get all pending players with numbers
    c.execute("SELECT id, name, base_price, status FROM auction_players WHERE status='pending' ORDER BY id")
    players = c.fetchall()
    
    if player_num < 1 or player_num > len(players):
        await update.message.reply_text(f"❌ Invalid! Choose 1-{len(players)}")
        conn.close()
        return
    
    player_id = players[player_num-1][0]
    player_name = players[player_num-1][1]
    player_price = players[player_num-1][2]
    
    c.execute("DELETE FROM auction_players WHERE id=?", (player_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"🗑️ **PLAYER REMOVED!**\n\n"
        f"❌ Removed: {player_name}\n"
        f"💰 Base Price: {player_price:,} ({number_to_cr(player_price)})\n\n"
        f"💡 /players - View updated list",
        
    )



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
