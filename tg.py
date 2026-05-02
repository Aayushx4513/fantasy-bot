import re
import sqlite3
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import os
import threading
from flask import Flask

TOKEN = "8265192837:AAEwM57vS_tTQU48iWK1u8c7mCih-5n423g"
ADMIN_IDS = [7687078555, 1315564307]

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    if DATABASE_URL:
        import psycopg2
        return psycopg2.connect(DATABASE_URL)
    return sqlite3.connect('fantasy.db')

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, name TEXT, balance INTEGER, points INTEGER, won INTEGER, total INTEGER, photo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS matches 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, team1 TEXT, team2 TEXT, date TEXT, status TEXT, locked INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bets 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, match_id INTEGER, team TEXT, amount INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS login_streak 
                 (user_id INTEGER PRIMARY KEY, streak INTEGER, last_login TEXT)''')
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
                 (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bank
                 (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, last_interest TEXT)''')


 
    # 🇮🇳 INDIA CURRENT (25)
    india_current = [
        (1, 'Virat Kohli', 1000000, '🇮🇳', 'current', 'India'),
        (2, 'Rohit Sharma', 980000, '🇮🇳', 'current', 'India'),
        (3, 'Shubman Gill', 950000, '🇮🇳', 'current', 'India'),
        (4, 'Hardik Pandya', 920000, '🇮🇳', 'current', 'India'),
        (5, 'Jasprit Bumrah', 900000, '🇮🇳', 'current', 'India'),
        (6, 'Ravindra Jadeja', 880000, '🇮🇳', 'current', 'India'),
        (7, 'KL Rahul', 860000, '🇮🇳', 'current', 'India'),
        (8, 'Suryakumar Yadav', 840000, '🇮🇳', 'current', 'India'),
        (9, 'Mohammed Shami', 820000, '🇮🇳', 'current', 'India'),
        (10, 'Rishabh Pant', 800000, '🇮🇳', 'current', 'India'),
        (11, 'Mohammed Siraj', 780000, '🇮🇳', 'current', 'India'),
        (12, 'Shreyas Iyer', 760000, '🇮🇳', 'current', 'India'),
        (13, 'Axar Patel', 740000, '🇮🇳', 'current', 'India'),
        (14, 'Kuldeep Yadav', 720000, '🇮🇳', 'current', 'India'),
        (15, 'Ishan Kishan', 700000, '🇮🇳', 'current', 'India'),
        (16, 'Sanju Samson', 680000, '🇮🇳', 'current', 'India'),
        (17, 'Yuzvendra Chahal', 660000, '🇮🇳', 'current', 'India'),
        (18, 'Deepak Chahar', 640000, '🇮🇳', 'current', 'India'),
        (19, 'Prithvi Shaw', 620000, '🇮🇳', 'current', 'India'),
        (20, 'Washington Sundar', 600000, '🇮🇳', 'current', 'India'),
        (21, 'Shardul Thakur', 580000, '🇮🇳', 'current', 'India'),
        (22, 'Arshdeep Singh', 560000, '🇮🇳', 'current', 'India'),
        (23, 'Ravi Bishnoi', 540000, '🇮🇳', 'current', 'India'),
        (24, 'Umran Malik', 520000, '🇮🇳', 'current', 'India'),
        (25, 'Avesh Khan', 500000, '🇮🇳', 'current', 'India'),
    ]
    for p in india_current:
        c.execute("INSERT OR IGNORE INTO shop (id, name, price, country, type, category) VALUES (?, ?, ?, ?, ?, ?)", p)
    
    # 🇮🇳 INDIA LEGENDS (25)
    india_legends = [
        (26, 'Sachin Tendulkar', 2000000, '🇮🇳', 'legend', 'India'),
        (27, 'MS Dhoni', 1900000, '🇮🇳', 'legend', 'India'),
        (28, 'Rahul Dravid', 1800000, '🇮🇳', 'legend', 'India'),
        (29, 'Sourav Ganguly', 1700000, '🇮🇳', 'legend', 'India'),
        (30, 'Virender Sehwag', 1600000, '🇮🇳', 'legend', 'India'),
        (31, 'Yuvraj Singh', 1550000, '🇮🇳', 'legend', 'India'),
        (32, 'Kapil Dev', 1500000, '🇮🇳', 'legend', 'India'),
        (33, 'Sunil Gavaskar', 1450000, '🇮🇳', 'legend', 'India'),
        (34, 'Anil Kumble', 1400000, '🇮🇳', 'legend', 'India'),
        (35, 'Zaheer Khan', 1350000, '🇮🇳', 'legend', 'India'),
        (36, 'Harbhajan Singh', 1300000, '🇮🇳', 'legend', 'India'),
        (37, 'Gautam Gambhir', 1250000, '🇮🇳', 'legend', 'India'),
        (38, 'VVS Laxman', 1200000, '🇮🇳', 'legend', 'India'),
        (39, 'Suresh Raina', 1150000, '🇮🇳', 'legend', 'India'),
        (40, 'Mohammad Kaif', 1100000, '🇮🇳', 'legend', 'India'),
        (41, 'Irfan Pathan', 1050000, '🇮🇳', 'legend', 'India'),
        (42, 'Ajit Agarkar', 1000000, '🇮🇳', 'legend', 'India'),
        (43, 'Javagal Srinath', 950000, '🇮🇳', 'legend', 'India'),
        (44, 'Dilip Vengsarkar', 900000, '🇮🇳', 'legend', 'India'),
        (45, 'Kris Srikkanth', 850000, '🇮🇳', 'legend', 'India'),
        (46, 'Nawab Pataudi', 800000, '🇮🇳', 'legend', 'India'),
        (47, 'Erapalli Prasanna', 750000, '🇮🇳', 'legend', 'India'),
        (48, 'Bishan Singh Bedi', 700000, '🇮🇳', 'legend', 'India'),
        (49, 'Chandu Borde', 650000, '🇮🇳', 'legend', 'India'),
        (50, 'Salil Ankola', 600000, '🇮🇳', 'legend', 'India'),
    ]
    for p in india_legends:
        c.execute("INSERT OR IGNORE INTO shop (id, name, price, country, type, category) VALUES (?, ?, ?, ?, ?, ?)", p)
    
    # 🇦🇺 AUSTRALIA CURRENT (25)
    aus_current = []
    for i in range(51, 76):
        aus_current.append((i, f'AUS Player {i-50}', 900000 - (i-51)*15000, '🇦🇺', 'current', 'Australia'))
    for p in aus_current:
        c.execute("INSERT OR IGNORE INTO shop (id, name, price, country, type, category) VALUES (?, ?, ?, ?, ?, ?)", p)
    
    # 🇦🇺 AUSTRALIA LEGENDS (25)
    aus_legends = []
    for i in range(76, 101):
        aus_legends.append((i, f'AUS Legend {i-75}', 1500000 - (i-76)*20000, '🇦🇺', 'legend', 'Australia'))
    for p in aus_legends:
        c.execute("INSERT OR IGNORE INTO shop (id, name, price, country, type, category) VALUES (?, ?, ?, ?, ?, ?)", p)
    
    # 🇵🇰 PAKISTAN CURRENT (25)
    pak_current = []
    for i in range(101, 126):
        pak_current.append((i, f'PAK Player {i-100}', 800000 - (i-101)*12000, '🇵🇰', 'current', 'Pakistan'))
    for p in pak_current:
        c.execute("INSERT OR IGNORE INTO shop (id, name, price, country, type, category) VALUES (?, ?, ?, ?, ?, ?)", p)
    
    # 🇵🇰 PAKISTAN LEGENDS (25)
    pak_legends = []
    for i in range(126, 151):
        pak_legends.append((i, f'PAK Legend {i-125}', 1300000 - (i-126)*18000, '🇵🇰', 'legend', 'Pakistan'))
    for p in pak_legends:
        c.execute("INSERT OR IGNORE INTO shop (id, name, price, country, type, category) VALUES (?, ?, ?, ?, ?, ?)", p)
    
    # 👩 WOMEN (25)
    women = []
    for i in range(1, 26):
        women.append((i, f'Women Player {i}', 600000 - (i-1)*10000, '🇮🇳', 'current'))
    for w in women:
        c.execute("INSERT OR IGNORE INTO shop_women (id, name, price, country, type) VALUES (?, ?, ?, ?, ?)", w)
    
    # SHOP2 (25 cheap players)
    cheap = []
    for i in range(1, 26):
        cheap.append((i, f'Cheap Player {i}', 50000 - (i-1)*1000))
    for c2 in cheap:
        c.execute("INSERT OR IGNORE INTO shop2 (id, name, price) VALUES (?, ?, ?)", c2)
    
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name if user.first_name else user.username or "User"
    user_id = user.id
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing = c.fetchone()
    if not existing:
        c.execute("INSERT INTO users (user_id, name, balance, points, won, total) VALUES (?, ?, 1000, 0, 0, 0)", (user_id, name))
        conn.commit()
        await update.message.reply_text(f'🏏 CRICKET FANTASY LEAGUE\n\nWelcome {name}! 👋\n💰 1000 credits | 🏆 0 pts\n\n📌 /login | /spin | /profile | /leaderboard')
    else:
        await update.message.reply_text(f'🏏 CRICKET FANTASY LEAGUE\n\nWelcome back {name}! 👋\n💰 {existing[2]} credits | 🏆 {existing[3]} pts\n\n📌 /login | /spin | /profile | /leaderboard')
    conn.close()

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Test command working! No reset!")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    msg = (
        "📋 COMMAND LIST\n\n"
        "👤 PROFILE:\n   /profile - Your profile\n   /setpfp - Set photo\n   /rmpfp - Remove photo\n\n"
        "🎁 EARN:\n   /claim - Daily credits\n   /spin - Daily spin (1k-10k)\n   /dice - Dice game\n   /flip - Heads/Tails\n\n"
        "🏏 CRICKET:\n   /matches - Live matches\n   /bet - Place bet\n   /mybets - Your bets\n   /cancel - Cancel bet\n   /allbets - All bets\n\n"
        "🛒 SHOP:\n   /shop - Buy players\n   /shop2 - Cheap players\n   /buy /buyw /buy2 - Purchase\n   /myteam - Your collection\n   /top - Top collectors\n\n"
        "📊 STATS:\n   /leaderboard - Rich list\n   /top_fantasy - Points ranking\n   /history - Bet history\n\n"
        "💝 OTHER:\n   /tip - Send credits\n   /achievements - Your badges"
    )
    await update.message.reply_text(msg)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    user = update.effective_user
    name = user.first_name if user.first_name else user.username or "User"
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, points, won, total, photo FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    balance, points, won, total, photo = data
    win_rate = int(won/total*100) if total > 0 else 0
    if photo:
        await update.message.reply_photo(photo=photo, caption=f'👤 PROFILE\n\n{name}\n💰 {balance:,} | 🏆 {points} | 📊 {won}/{total} ({win_rate}%)\n\n🔄 /setpfp | ❌ /rmpfp')
    else:
        await update.message.reply_text(f'👤 PROFILE\n\n{name}\n💰 {balance:,} | 🏆 {points} | 📊 {won}/{total} ({win_rate}%)\n\n🔄 /setpfp | ❌ /rmpfp')

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
    if row and row[0]:
        last = datetime.fromisoformat(row[0])
        if (now - last).total_seconds() < 86400:
            remaining = 24 - (now - last).seconds // 3600
            await update.message.reply_text(f'⏰ Already spin today!\nCome back in {remaining}h')
            conn.close()
            return
    amount = random.randint(1000, 10000)
    c.execute("INSERT OR REPLACE INTO spin (user_id, last_claim) VALUES (?, ?)", (user_id, now.isoformat()))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    if amount == 10000:
        await update.message.reply_text(f'🎡 SPIN\n\n🎉 JACKPOT! 10000 💰\n💰 New balance: {new_bal:,} 💰')
    else:
        await update.message.reply_text(f'🎡 SPIN\n\nYou got {amount} 💰\n💰 New balance: {new_bal:,} 💰')


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
        await update.message.reply_text(f'🎲 DICE\n\n🎲 Rolled: {roll} {dice_emoji[roll]}\n✨ You won {win:,} 💰 ({multi[roll]}x)\n💰 New balance: {new_bal:,} 💰')
    else:
        await update.message.reply_text(f'🎲 DICE\n\n🎲 Rolled: {roll} {dice_emoji[roll]}\n💀 You lost {amount:,} 💰\n💰 New balance: {new_bal:,} 💰')

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
        await update.message.reply_text(f'🪙 {result.upper()}! You won {win:,} 💰\n💰 Balance: {balance:,} → {new_bal:,} 💰')
    else:
        new_bal = balance - amount
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f'😞 {result.upper()}! You lost {amount:,} 💰\n💰 Balance: {balance:,} → {new_bal:,} 💰')

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
        msg += f'🔥 {m[1]} vs {m[2]}\n📅 {m[3]} | {status}\n💰 /bet {m[1]} <amount> | /bet {m[2]} <amount>\n\n'
    user = get_user(user_id)
    msg += f'━━━━━━━━━━━━━━━━━━━━━━\n💰 Your balance: {user[2]:,} 💰'
    await update.message.reply_text(msg)
    conn.close()

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
    
    # 🔥 MAX 2 BETS CHECK 🔥
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

async def mybets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT b.id, b.team, b.amount, m.team1, m.team2, m.date
        FROM bets b JOIN matches m ON b.match_id = m.id WHERE b.user_id = ? AND m.locked = 0
    """, (user_id,))
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
    c.execute("""
        SELECT b.id, b.amount, m.team1, m.team2, m.locked FROM bets b JOIN matches m ON b.match_id = m.id WHERE b.user_id = ? AND m.locked = 0
    """, (user_id,))
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

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""
        SELECT u.name, u.balance + COALESCE(b.balance, 0) as total_wealth
        FROM users u
        LEFT JOIN bank b ON u.user_id = b.user_id
        ORDER BY total_wealth DESC
        LIMIT 10
    """)
    users_data = c.fetchall()
    
    msg = "🏆 TOP 10 RICHEST (Wallet + Bank)\n\n"
    for i, u in enumerate(users_data, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {u[0]} - {u[1]:,} 💰\n"
    
    c.execute("SELECT u.balance + COALESCE(b.balance, 0) FROM users u LEFT JOIN bank b ON u.user_id = b.user_id WHERE u.user_id = ?", (user_id,))
    user_total = c.fetchone()[0]
    rank = c.execute("SELECT COUNT(*) + 1 FROM (SELECT u.balance + COALESCE(b.balance, 0) as total FROM users u LEFT JOIN bank b ON u.user_id = b.user_id) WHERE total > ?", (user_total,)).fetchone()[0]
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{rank}\n💰 Total wealth: {user_total:,} 💰"
    
    await update.message.reply_text(msg)
    conn.close()

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
            
            new_points = u[2]
            if user_id not in points_given:
                new_points = u[2] + 10
                points_given[user_id] = True
            
            c.execute("UPDATE users SET balance = ?, won = ?, points = ? WHERE user_id=?", 
                     (new_balance, new_won, new_points, user_id))
            total_paid += win_amount
            winners += 1
            winner_list.append(f"{u[3]} - {amount} → {win_amount} (+{amount})")
        else:
            new_points = u[2] - 5
            c.execute("UPDATE users SET points = ? WHERE user_id=?", (new_points, user_id))
            losers += 1
            loser_list.append(f"{u[3]} - {amount} → 0 (-{amount})")
    
    c.execute("DELETE FROM bets WHERE match_id=?", (match[0],))
    c.execute("DELETE FROM matches WHERE id=?", (match[0],))
    conn.commit()
    conn.close()
    
    msg = f"📢 MATCH RESULT!\n\n🏏 {match[1]} vs {match[2]}\n🏆 WINNER: {winner}\n\n"
    msg += f"✅ WINNERS (max +10 pts each): {winners} users\n"
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
    
    await update.message.reply_text(
        f"🏦 MY BANK ACCOUNT\n\n"
        f"💰 Bank Balance: {bank_bal:,} 💰\n"
        f"👛 Wallet Balance: {wallet_bal:,} 💰\n"
        f"📈 Interest Rate: 5% daily\n"
        f"⏰ Next interest: {next_time_str}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 /deposit <amount>\n"
        f"💡 /withdraw <amount>\n"
        f"💡 /claim_interest"
    )

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
    
    await update.message.reply_text(
        f"✅ DEPOSITED!\n\n"
        f"Amount: +{amount:,} 💰\n"
        f"Wallet: {wallet_bal:,} → {new_wallet:,} 💰\n"
        f"Bank: {new_bank - amount:,} → {new_bank:,} 💰"
    )

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
    
    await update.message.reply_text(
        f"✅ WITHDRAWN!\n\n"
        f"Amount: -{amount:,} 💰\n"
        f"Bank: {bank_bal:,} → {new_bank:,} 💰\n"
        f"Wallet: {new_wallet - amount:,} → {new_wallet:,} 💰"
    )

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
    
    await update.message.reply_text(
        f"💰 INTEREST CLAIMED!\n\n"
        f"Rate: 5%\n"
        f"Interest: +{interest:,} 💰\n"
        f"New Bank Balance: {new_bank:,} 💰\n\n"
        f"⏰ Next interest: 24h"
    )



async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    user = get_user(user_id)
    win_rate = int(user[4]/user[5]*100) if user[5] > 0 else 0
    await update.message.reply_text(f'📜 BET HISTORY\n\n✅ Won: {user[4]}\n❌ Lost: {user[5]-user[4]}\n📊 Win Rate: {win_rate}%\n\n🏆 Fantasy Points: {user[3]}')

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
        [InlineKeyboardButton("🇮🇳 India (Current)", callback_data="shop_India_current")],
        [InlineKeyboardButton("🇮🇳 India (Legends)", callback_data="shop_India_legend")],
        [InlineKeyboardButton("🇦🇺 Australia (Current)", callback_data="shop_Australia_current")],
        [InlineKeyboardButton("🇦🇺 Australia (Legends)", callback_data="shop_Australia_legend")],
        [InlineKeyboardButton("🇵🇰 Pakistan (Current)", callback_data="shop_Pakistan_current")],
        [InlineKeyboardButton("🇵🇰 Pakistan (Legends)", callback_data="shop_Pakistan_legend")],
        [InlineKeyboardButton("👩 Women Players", callback_data="shop_women")],
    ]
    await update.message.reply_text("🛒 CRICKETER SHOP\n\nSelect category:", reply_markup=InlineKeyboardMarkup(keyboard))

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
    cheap = c.fetchall()
    conn.close()
    mens_total = sum(p[1] for p in mens)
    women_total = sum(w[1] for w in women)
    cheap_total = sum(c[1] for c in cheap)
    msg = "🏏 MY CRICKET TEAM\n\n━━━━━━━━━━━━━━━━━━━━━━\n👨 MENS"
    if mens:
        msg += f" ({len(mens)})\n\n"
        for i, p in enumerate(mens, 1):
            msg += f"{i}. {p[0]} - {p[1]:,} 💰\n"
        msg += f"\nTotal: {mens_total:,} 💰"
    else:
        msg += "\n\nNo mens players. /shop to buy!"
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🤑 CHEAP"
    if cheap:
        msg += f" ({len(cheap)})\n\n"
        for i, c in enumerate(cheap, 1):
            msg += f"{i}. {c[0]} - {c[1]:,} 💰\n"
        msg += f"\nTotal: {cheap_total:,} 💰"
    else:
        msg += "\n\nNo cheap players. /shop2 to buy!"
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n👩 WOMEN"
    if women:
        msg += f" ({len(women)})\n\n"
        for i, w in enumerate(women, 1):
            msg += f"{i}. {w[0]} - {w[1]:,} 💰\n"
        msg += f"\nTotal: {women_total:,} 💰"
    else:
        msg += "\n\nNo women players. /shop women section"
    grand_total = mens_total + cheap_total + women_total
    total_players = len(mens) + len(cheap) + len(women)
    msg += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n💰 GRAND TOTAL: {grand_total:,} 💰\n🏆 TOTAL PLAYERS: {total_players}"
    await update.message.reply_text(msg)

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
        await update.message.reply_text('🛒 CHEAP SHOP\n\nNo players yet.\n👑 Admin: /addplayer2 <name> <price>')
        return
    msg = "🛒 CHEAP PLAYERS SHOP\n\n"
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
        await update.message.reply_text('📭 No cheap players owned.\nUse /shop2 to buy!')
        return
    total = sum(p[1] for p in players)
    msg = "🤑 MY CHEAP PLAYERS\n\n"
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
        await update.message.reply_text('🏆 CHEAP PLAYERS TOP\n\nNo one owns any yet!')
        conn.close()
        return
    msg = "🏆 CHEAP PLAYERS TOP\n\n"
    for i, t in enumerate(tops, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {t[0]} - {t[1]} players ({t[2]:,} 💰)\n"
    c.execute("SELECT COUNT(*) FROM user_players2 WHERE user_id=?", (user_id,))
    my_count = c.fetchone()[0]
    msg += f"\n📊 You own: {my_count} players"
    await update.message.reply_text(msg)
    conn.close()

async def addmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 4:
        await update.message.reply_text('❌ /addmatch TEAM1 vs TEAM2 YYYY-MM-DD')
        return
    team1, vs, team2, date = args[0], args[1], args[2], args[3]
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO matches (team1, team2, date, status, locked) VALUES (?, ?, ?, 'upcoming', 0)", (team1, team2, date))
    conn.commit()
    await update.message.reply_text(f'✅ MATCH ADDED!\n{team1} vs {team2} | {date}')
    conn.close()

async def lockmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('❌ /lockmatch TEAM1 vs TEAM2')
        return
    team1, vs, team2 = args[0], args[1], args[2]
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE matches SET locked=1 WHERE team1=? AND team2=?", (team1, team2))
    conn.commit()
    c.execute("SELECT COUNT(*), SUM(amount) FROM bets JOIN matches ON bets.match_id=matches.id WHERE team1=? AND team2=?", (team1, team2))
    result = c.fetchone()
    count = result[0] or 0
    total = result[1] or 0
    await update.message.reply_text(f'🔒 MATCH LOCKED!\n{team1} vs {team2}\nBets: {count}\nPool: {total} 💰')
    conn.close()


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
    amount = int(args[0])
    target = update.message.reply_to_message.from_user
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, name FROM users WHERE user_id=?", (target.id,))
    old = c.fetchone()
    if not old:
        await update.message.reply_text('❌ User not found')
        conn.close()
        return
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, target.id))
    conn.commit()
    await update.message.reply_text(f'✅ ADDED {amount} to {old[1]}\nBalance: {old[0]} → {old[0]+amount}')
    conn.close()

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
    amount = int(args[0])
    target = update.message.reply_to_message.from_user
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, name FROM users WHERE user_id=?", (target.id,))
    old = c.fetchone()
    if not old:
        await update.message.reply_text('❌ User not found')
        conn.close()
        return
    if old[0] < amount:
        await update.message.reply_text(f'❌ Insufficient! Balance: {old[0]}')
        conn.close()
        return
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, target.id))
    conn.commit()
    await update.message.reply_text(f'❌ REMOVED {amount} from {old[1]}\nBalance: {old[0]} → {old[0]-amount}')
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
    price = int(args[-1])
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO shop2 (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    await update.message.reply_text(f'✅ ADDED "{name}" for {price} 💰')
    conn.close()

async def setprice2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /setprice2 <id> <new_price>')
        return
    pid = int(args[0])
    price = int(args[1])
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE shop2 SET price = ? WHERE id = ?", (price, pid))
    conn.commit()
    await update.message.reply_text(f'✅ Player {pid} price updated to {price} 💰')
    conn.close()

async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            '❌ /setprice <player_id> <new_price>\n\n'
            'Example: /setprice 1 1500000'
        )
        return

    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid price or ID')
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name FROM shop WHERE id = ?", (player_id,))
    player = c.fetchone()

    if not player:
        await update.message.reply_text(f'❌ Player with ID {player_id} not found')
        conn.close()
        return

    c.execute("UPDATE shop SET price = ? WHERE id = ?", (new_price, player_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f'✅ PRICE UPDATED!\n\n'
        f'Player: {player[0]}\n'
        f'New Price: {new_price:,} 💰'
    )



async def removeplayer2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /removeplayer2 <id>')
        return
    pid = int(args[0])
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM shop2 WHERE id=?", (pid,))
    c.execute("DELETE FROM user_players2 WHERE player_id=?", (pid,))
    conn.commit()
    await update.message.reply_text(f'✅ Player {pid} removed')
    conn.close()

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
    name = ' '.join(args)
    target = update.message.reply_to_message.from_user
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO achievements (user_id, achievement) VALUES (?, ?)", (target.id, name))
    conn.commit()
    await update.message.reply_text(f'✅ Achievement "{name}" given to {target.first_name}')
    conn.close()

async def rmachieve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /rmachieve <number>')
        return
    num = int(args[0])
    target_id = update.effective_user.id
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT rowid, achievement FROM achievements WHERE user_id=?", (target_id,))
    ach = c.fetchall()
    if num < 1 or num > len(ach):
        await update.message.reply_text(f'❌ Invalid number! Choose 1-{len(ach)}')
        conn.close()
        return
    removed = ach[num-1]
    c.execute("DELETE FROM achievements WHERE rowid=?", (removed[0],))
    conn.commit()
    await update.message.reply_text(f'✅ Achievement removed: {removed[1]}')
    conn.close()

# ============ CLAIM DAILY REWARD ============
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS claims (user_id INTEGER PRIMARY KEY, last_claim DATE)")
    c.execute("SELECT last_claim FROM claims WHERE user_id=?", (user_id,))
    row = c.fetchone()
    
    today = datetime.now().date()
    today_str = today.strftime("%m/%d/%y")
    
    if row and row[0]:
        last = datetime.fromisoformat(row[0]).date()
        if last == today:
            await update.message.reply_text("⚠️ You already claimed today's reward!\nCome back tomorrow.")
            conn.close()
            return
    
    c.execute("INSERT OR REPLACE INTO claims (user_id, last_claim) VALUES (?, ?)", (user_id, today.isoformat()))
    c.execute("UPDATE users SET balance = balance + 500 WHERE user_id=?", (user_id,))
    conn.commit()
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"✅ Claimed Daily Rewards of 500 Credits\n"
        f"at {today_str}\n\n"
        f"💰 New balance: {new_bal:,} 💰\n"
        f"📅 Next claim: tomorrow"
    )


def main():
    threading.Thread(target=run_flask, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("setpfp", setpfp))
    app.add_handler(CommandHandler("rmpfp", rmpfp))
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
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("buyw", buyw))
    app.add_handler(CommandHandler("myteam", myteam))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("shop2", shop2))
    app.add_handler(CommandHandler("buy2", buy2))
    app.add_handler(CommandHandler("myteam2", myteam2))
    app.add_handler(CommandHandler("top2", top2))
    app.add_handler(CommandHandler("addmatch", addmatch))
    app.add_handler(CommandHandler("lockmatch", lockmatch))
    app.add_handler(CommandHandler("result", result))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("addplayer2", addplayer2))
    app.add_handler(CommandHandler("setprice2", setprice2))
    app.add_handler(CommandHandler("removeplayer2", removeplayer2))
    app.add_handler(CommandHandler("achieve", achieve))
    app.add_handler(CommandHandler("setprice", setprice))
    app.add_handler(CommandHandler("rmachieve", rmachieve))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_"))
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("claim_interest", claim_interest))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()


