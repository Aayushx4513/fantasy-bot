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

# Flask app for Render
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

# ============ DATABASE ============
def init_db():
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, name TEXT, balance INTEGER, points INTEGER, won INTEGER, total INTEGER, photo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS matches 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, team1 TEXT, team2 TEXT, date TEXT, status TEXT, locked INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bets 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, match_id INTEGER, team TEXT, amount INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily 
                 (user_id INTEGER, last_claim TEXT)''')
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
    conn.commit()
    conn.close()

init_db()

def is_registered(user_id):
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_user(user_id, name=""):
    conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing = c.fetchone()
    
    if not existing:
        c.execute("INSERT INTO users (user_id, name, balance, points, won, total) VALUES (?, ?, 1000, 0, 0, 0)", (user_id, name))
        conn.commit()
        await update.message.reply_text(
            f"╔══════════════════════════════════════╗\n"
            f"║      🏏 CRICKET FANTASY LEAGUE       ║\n"
            f"╚══════════════════════════════════════╝\n\n"
            f"Welcome {name}! 👋\n\n"
            f"💰 Credits: 1,000\n"
            f"🏆 Points: 0\n"
            f"📊 Win Rate: 0%\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✨ Quick Commands:\n"
            f"🎁 /daily → +500 credits\n"
            f"🎡 /spin → Win upto 10k\n"
            f"🎲 /dice → 0x to 2.5x\n"
            f"🏏 /matches → Live matches\n"
            f"🛒 /shop → Buy players\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 Type /help for all commands")
    else:
        await update.message.reply_text(
            f"╔══════════════════════════════════════╗\n"
            f"║      🏏 CRICKET FANTASY LEAGUE       ║\n"
            f"╚══════════════════════════════════════╝\n\n"
            f"Welcome back {name}! 👋\n\n"
            f"💰 Credits: {existing[2]:,}\n"
            f"🏆 Points: {existing[3]}\n"
            f"📊 Bets: {existing[4]}/{existing[5]}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 /matches | /shop | /leaderboard")
    conn.close()

# ============ PROFILE ============
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    user = update.effective_user
    name = user.first_name if user.first_name else user.username or "User"
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("SELECT balance, points, won, total, photo FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    
    balance, points, won, total, photo = data
    win_rate = int(won/total*100) if total > 0 else 0
    
    if photo:
        await update.message.reply_photo(photo=photo, 
            caption=f"👤 PROFILE\n\n━━━━━━━━━━━━━━━━━━━━━━\n📛 {name}\n🆔 ID: {user_id}\n\n💰 Credits: {balance:,}\n🏆 Points: {points}\n📊 Bets: {won}/{total} ({win_rate}%)\n\n━━━━━━━━━━━━━━━━━━━━━━\n🔄 /setpfp | ❌ /rmpfp")
    else:
        await update.message.reply_text(
            f"👤 PROFILE\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📛 {name}\n🆔 ID: {user_id}\n\n"
            f"💰 Credits: {balance:,}\n"
            f"🏆 Points: {points}\n"
            f"📊 Bets: {won}/{total} ({win_rate}%)\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n🔄 /setpfp | ❌ /rmpfp")

# ============ SETPFP ============
async def setpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text('❌ Reply to a photo with /setpfp')
        return
    
    photo = update.message.reply_to_message.photo[-1].file_id
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("UPDATE users SET photo=? WHERE user_id=?", (photo, user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text('✅ Profile photo updated!')

# ============ RMPFP ============
async def rmpfp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("UPDATE users SET photo=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text('❌ Profile photo removed!')

# ============ DAILY ============
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    
    # Ensure daily table exists
    c.execute("CREATE TABLE IF NOT EXISTS daily (user_id INTEGER PRIMARY KEY, last_claim TEXT)")
    
    c.execute("SELECT last_claim FROM daily WHERE user_id=?", (user_id,))
    row = c.fetchone()
    now = datetime.now()
    
    # Check if already claimed today (using date)
    if row and row[0]:
        last = datetime.fromisoformat(row[0])
        if last.date() == now.date():
            await update.message.reply_text('⚠️ You already claimed today\'s daily reward!')
            conn.close()
            return
    
    # Add 500 credits
    c.execute("INSERT OR REPLACE INTO daily (user_id, last_claim) VALUES (?, ?)", (user_id, now.isoformat()))
    c.execute("UPDATE users SET balance = balance + 500 WHERE user_id=?", (user_id,))
    conn.commit()
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f'🎁 DAILY REWARD\n✅ +500 credits\nNew balance: {new_bal} 💰\nCome back tomorrow!')


# ============ SPIN ============
async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS spin (user_id INTEGER PRIMARY KEY, last_claim TEXT)")
    c.execute("SELECT last_claim FROM spin WHERE user_id=?", (user_id,))
    row = c.fetchone()
    now = datetime.now()
    
    if row and row[0]:
        last = datetime.fromisoformat(row[0])
        diff = now - last
        if diff.total_seconds() < 86400:
            remaining = 24 - diff.seconds // 3600
            rem_min = (86400 - diff.total_seconds()) // 60
            await update.message.reply_text(f"⏰ ALREADY SPIN\n\nCome back in {remaining}h {int(rem_min%60)}m")
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
        await update.message.reply_text(f"🎡 DAILY SPIN\n\n🎉🔥 JACKPOT! 🔥🎉\n✨ You got {amount:,} 💰\n💰 Balance: {new_bal:,} 💰")
    else:
        await update.message.reply_text(f"🎡 DAILY SPIN\n\n✨ You got {amount:,} 💰\n💰 Balance: {new_bal:,} 💰")

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
    
    conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
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
        await update.message.reply_text(f"🪙 {result.upper()}! You won {win:,} 👾\n💰 Balance: {balance:,} → {new_bal:,} 👾")
    else:
        new_bal = balance - amount
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"😞 {result.upper()}! You lost {amount:,} 👾\n💰 Balance: {balance:,} → {new_bal:,} 👾")

# ============ MATCHES ============
async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("""
        SELECT b.id, b.team, b.amount, m.team1, m.team2, m.date
        FROM bets b 
        JOIN matches m ON b.match_id = m.id 
        WHERE b.user_id = ? AND m.locked = 0
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
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("""
        SELECT b.id, b.amount, m.team1, m.team2, m.locked, b.match_id
        FROM bets b 
        JOIN matches m ON b.match_id = m.id 
        WHERE b.user_id = ? AND m.locked = 0
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

# ============ LEADERBOARD ============
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("SELECT name, balance FROM users ORDER BY balance DESC LIMIT 10")
    users_data = c.fetchall()
    
    msg = "🏆 TOP 10 RICHEST\n\n"
    for i, u in enumerate(users_data, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {u[0]} - {u[1]:,} 💰\n"
    
    user = get_user(user_id)
    rank = c.execute("SELECT COUNT(*) FROM users WHERE balance > ?", (user[2],)).fetchone()[0] + 1
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{rank}\n💰 Your balance: {user[2]:,} 💰"
    
    await update.message.reply_text(msg)
    conn.close()

# ============ ALLBETS ============
async def allbets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
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

# ============ TOP FANTASY ============
async def top_fantasy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
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

# ============ SHOP ============
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛒 CRICKETER SHOP\n\nSelect category:", reply_markup=reply_markup)

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "shop_women":
        conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM shop WHERE category=? AND type=?", (country, ptype))
    players = c.fetchall()
    conn.close()
    
    if not players:
        await query.edit_message_text(f"❌ No players found for {country}")
        return
    
    msg = f"🛒 {country} {ptype.upper()} PLAYERS\n\n"
    for p in players:
        msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💡 /buy <number> to purchase\n🔙 Back to /shop"
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
    
    conn = sqlite3.connect('fantasy.db')
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
    
    await update.message.reply_text(f"✅ PURCHASED!\n\n🏏 {player[0]}\n💰 Price: {player[1]:,} 💰\n📊 New balance: {new_bal:,} 💰\n🏆 Players owned: Check /myteam")

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
    
    conn = sqlite3.connect('fantasy.db')
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

# ============ SHOP2 (CHEAP PLAYERS) ============
async def shop2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("""
        SELECT s.name, s.price FROM user_players2 u 
        JOIN shop2 s ON u.player_id = s.id 
        WHERE u.user_id = ?
    """, (user_id,))
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
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("""
        SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(s.price), 0) as total
        FROM users u
        JOIN user_players2 up ON u.user_id = up.user_id
        JOIN shop2 s ON up.player_id = s.id
        GROUP BY u.user_id
        ORDER BY total DESC LIMIT 10
    """)
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

# ============ ADMIN SHOP2 COMMANDS ============
async def addplayer2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /addplayer2 <name> <price>\nExample: /addplayer2 "Navdeep Saini" 8000')
        return
    
    name = ' '.join(args[:-1])
    try:
        price = int(args[-1])
    except:
        await update.message.reply_text('❌ Invalid price!')
        return
    
    conn = sqlite3.connect('fantasy.db')
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
        await update.message.reply_text('❌ /setprice2 <id> <new_price>\nExample: /setprice2 1 15000')
        return
    
    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid input!')
        return
    
    conn = sqlite3.connect('fantasy.db')
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
    
    await update.message.reply_text(f"✅ PRICE UPDATED!\n{player[0]}\nNew Price: {new_price:,} 💰")

async def removeplayer2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /removeplayer2 <id>\nExample: /removeplayer2 1')
        return
    
    try:
        player_id = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid ID!')
        return
    
    conn = sqlite3.connect('fantasy.db')
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

# ============ MYTEAM (FULL) ============
async def myteam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT p.name, p.price FROM user_players u 
        JOIN shop p ON u.player_id = p.id 
        WHERE u.user_id = ? AND u.type = 'mens'
    """, (user_id,))
    mens = c.fetchall()
    
    c.execute("""
        SELECT w.name, w.price FROM user_players u 
        JOIN shop_women w ON u.player_id = w.id 
        WHERE u.user_id = ? AND u.type = 'women'
    """, (user_id,))
    women = c.fetchall()
    
    c.execute("""
        SELECT s.name, s.price FROM user_players2 u 
        JOIN shop2 s ON u.player_id = s.id 
        WHERE u.user_id = ?
    """, (user_id,))
    cheap = c.fetchall()
    
    conn.close()
    
    mens_total = sum(p[1] for p in mens)
    women_total = sum(w[1] for w in women)
    cheap_total = sum(c[1] for c in cheap)
    
    msg = "🏏 MY CRICKET TEAM\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n👨 MENS"
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

# ============ TOP ============
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(p.price), 0) as total
        FROM users u
        JOIN user_players up ON u.user_id = up.user_id
        JOIN shop p ON up.player_id = p.id
        WHERE up.type = 'mens'
        GROUP BY u.user_id
        ORDER BY total DESC LIMIT 10
    """)
    tops = c.fetchall()
    
    if not tops:
        await update.message.reply_text('🏆 TOP COLLECTORS\n\nNo one owns any players yet!')
        conn.close()
        return
    
    msg = "🏆 TOP COLLECTORS\n\n"
    for i, t in enumerate(tops, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {t[0]} - {t[1]} players ({t[2]:,} 💰)\n"
    
    c.execute("""
        SELECT COUNT(up.player_id), COALESCE(SUM(p.price), 0)
        FROM user_players up
        JOIN shop p ON up.player_id = p.id
        WHERE up.user_id = ? AND up.type = 'mens'
    """, (user_id,))
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
    
    conn = sqlite3.connect('fantasy.db')
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
    
    await context.bot.send_message(receiver.id, f"💝 TIP RECEIVED!\n\n📥 From: {sender.first_name}\n💰 +{amount:,} 💰\n📊 New balance: {sender_bal + amount:,} 💰")

# ============ HISTORY ============
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    user = get_user(user_id)
    win_rate = int(user[4]/user[5]*100) if user[5] > 0 else 0
    await update.message.reply_text(
        f"📜 BET HISTORY\n\n"
        f"✅ Won: {user[4]}\n"
        f"❌ Lost: {user[5]-user[4]}\n"
        f"📊 Win Rate: {win_rate}%\n\n"
        f"🏆 Fantasy Points: {user[3]}")

# ============ ACHIEVEMENTS ============
async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
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

# ============ ADMIN COMMANDS ============
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
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("INSERT INTO matches (team1, team2, date, status, locked) VALUES (?, ?, ?, 'upcoming', 0)", (team1, team2, date))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ MATCH ADDED!\n\n🏏 {team1} vs {team2}\n📅 {date}\n🔓 Status: OPEN")

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
    
    conn = sqlite3.connect('fantasy.db')
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
    
    conn = sqlite3.connect('fantasy.db')
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
    
    for bet in bets:
        c.execute("SELECT balance, won, points, name FROM users WHERE user_id=?", (bet[0],))
        u = c.fetchone()
        
        if bet[2].upper() == winner:
            win_amount = bet[1] * 2
            c.execute("UPDATE users SET balance = ?, won = ?, points = points + 10 WHERE user_id=?", (u[0] + win_amount, u[1] + 1, bet[0]))
            total_paid += win_amount
            winners += 1
            winner_list.append(f"{u[3]} - {bet[1]:,} → {win_amount:,}")
        else:
            c.execute("UPDATE users SET points = points - 5 WHERE user_id=?", (bet[0],))
            losers += 1
            loser_list.append(f"{u[3]} - {bet[1]:,} → 0")
    
    c.execute("DELETE FROM bets WHERE match_id=?", (match[0],))
    c.execute("DELETE FROM matches WHERE id=?", (match[0],))
    conn.commit()
    conn.close()
    
    msg = f"📢 MATCH RESULT!\n\n🏏 {match[1]} vs {match[2]}\n🏆 WINNER: {winner}\n\n"
    msg += f"✅ WINNERS (+10 pts) - {winners} users\n"
    for w in winner_list[:5]:
        msg += f"   • {w}\n"
    if len(winner_list) > 5:
        msg += f"   • +{len(winner_list)-5} more\n"
    
    msg += f"\n❌ LOSERS (-5 pts) - {losers} users\n"
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
    conn = sqlite3.connect('fantasy.db')
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
    
    await update.message.reply_text(f"✅ CREDITS ADDED!\n\n👤 User: {old[1]}\n➕ Amount: +{amount:,} 💰\n💰 Balance: {old[0]:,} → {old[0]+amount:,} 💰\n\n👑 Added by Admin")

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
    conn = sqlite3.connect('fantasy.db')
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
    
    await update.message.reply_text(f"❌ CREDITS REMOVED!\n\n👤 User: {old[1]}\n➖ Amount: -{amount:,} 💰\n💰 Balance: {old[0]:,} → {old[0]-amount:,} 💰\n\n👑 Removed by Admin")

async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /setprice <player_id> <new_price>\nExample: /setprice 1 1500000')
        return
    
    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid input!')
        return
    
    conn = sqlite3.connect('fantasy.db')
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
    
    await update.message.reply_text(f'✅ PRICE UPDATED!\n{player[0]}\nNew Price: {new_price:,} 💰')



# ============ HELP ============
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    msg = (
        "📋 COMMAND LIST\n\n"
        "🎁 EARN CREDITS:\n"
        "   /daily - 500 credits daily\n"
        "   /spin - Win 1k-10k daily\n"
        "   /dice - Dice game (0x-2.5x)\n"
        "   /flip - Heads/Tails (2x)\n\n"
        "🏏 BETTING:\n"
        "   /matches - Live matches\n"
        "   /bet - Place bet\n"
        "   /mybets - Your bets\n"
        "   /cancel - Cancel bet\n"
        "   /allbets - All bets\n\n"
        "🛒 SHOP:\n"
        "   /shop - Buy players\n"
        "   /shop2 - Cheap players\n"
        "   /buy /buyw /buy2 - Purchase\n"
        "   /myteam - Your collection\n"
        "   /top - Top collectors\n\n"
        "📊 STATS:\n"
        "   /profile - Your profile\n"
        "   /leaderboard - Rich list\n"
        "   /top_fantasy - Points ranking\n"
        "   /history - Bet history\n\n"
        "💝 OTHER:\n"
        "   /tip - Send credits\n"
        "   /achievements - Your badges\n\n"
        "👑 ADMIN:\n"
        "   /addmatch /lockmatch /result\n"
        "   /add /remove /addplayer2 /setprice2"
    )
    await update.message.reply_text(msg)


# ============ MAIN ============
def main():
    # Start Flask thread for Render
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    app = Application.builder().token(TOKEN).build()
    
    # User commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("setpfp", setpfp))
    app.add_handler(CommandHandler("rmpfp", rmpfp))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("flip", flip))
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("bet", bet))
    app.add_handler(CommandHandler("mybets", mybets))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("allbets", allbets))
    app.add_handler(CommandHandler("tip", tip))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("top_fantasy", top_fantasy))

    # Shop commands
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("buyw", buyw))
    app.add_handler(CommandHandler("myteam", myteam))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_"))
    
    # Shop2 commands
    app.add_handler(CommandHandler("shop2", shop2))
    app.add_handler(CommandHandler("buy2", buy2))
    app.add_handler(CommandHandler("myteam2", myteam2))
    app.add_handler(CommandHandler("top2", top2))
    app.add_handler(CommandHandler("addplayer2", addplayer2))
    app.add_handler(CommandHandler("setprice2", setprice2))
    app.add_handler(CommandHandler("removeplayer2", removeplayer2))
    
    # Admin commands
    app.add_handler(CommandHandler("addmatch", addmatch))
    app.add_handler(CommandHandler("lockmatch", lockmatch))
    app.add_handler(CommandHandler("result", result))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("setprice", setprice))
 
    # Achievement commands
    app.add_handler(CommandHandler("achievements", achievements))
    app.add_handler(CommandHandler("achieve", achieve))
    app.add_handler(CommandHandler("rmachieve", rmachieve))
    
    # Clear webhook
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(app.bot.delete_webhook(drop_pending_updates=True))
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
