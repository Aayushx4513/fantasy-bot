import sqlite3
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

TOKEN = "8265192837:AAFjO4TNxGDArDiD1_cF4Y0W3W8UDKdm4XM"
ADMIN_IDS = [7687078555, 1315564307]

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
    c.execute('''CREATE TABLE IF NOT EXISTS achievements 
                 (user_id INTEGER, achievement TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS shop2 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_players2 
             (user_id INTEGER, player_id INTEGER)''')
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
        await update.message.reply_text(f'🏏 CRICKET FANTASY LEAGUE\n\nWelcome {name}! 👋\n💰 1000 credits | 🏆 0 pts\n\n📌 /daily | /matches | /profile | /leaderboard')
    else:
        await update.message.reply_text(f'🏏 CRICKET FANTASY LEAGUE\n\nWelcome back {name}! 👋\n💰 {existing[2]} credits | 🏆 {existing[3]} pts\n\n📌 /daily | /matches | /profile | /leaderboard')
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
    
    if photo:
        await update.message.reply_photo(photo=photo, caption=f'👤 PROFILE\n\n{name}\n💰 {balance} | 🏆 {points} | 📊 {won}/{total}\n\n🔄 /setpfp | ❌ /rmpfp')
    else:
        await update.message.reply_text(f'👤 PROFILE\n\n{name}\n💰 {balance} | 🏆 {points} | 📊 {won}/{total}\n\n🔄 /setpfp | ❌ /rmpfp')

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
    await update.message.reply_text('✅ Profile photo updated!\n/profile to view')

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
    await update.message.reply_text('❌ Profile photo removed!\n/profile to view')

# ============ DAILY ============
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS daily (user_id INTEGER PRIMARY KEY, last_claim TEXT)")
    c.execute("SELECT last_claim FROM daily WHERE user_id=?", (user_id,))
    row = c.fetchone()
    now = datetime.now()
    
    if row and row[0]:
        last = datetime.fromisoformat(row[0])
        diff = now - last
        if diff.total_seconds() < 86400:
            remaining = 24 - diff.seconds // 3600
            rem_min = (86400 - diff.total_seconds()) // 60
            await update.message.reply_text(f'⚠️ Already claimed!\n⏰ Come back in {remaining}h {int(rem_min%60)}m')
            conn.close()
            return
    
    c.execute("INSERT OR REPLACE INTO daily (user_id, last_claim) VALUES (?, ?)", (user_id, now.isoformat()))
    c.execute("UPDATE users SET balance = balance + 500 WHERE user_id=?", (user_id,))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f'🎁 DAILY REWARD\n✅ +500 credits\nNew balance: {new_bal} 💰')

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
            await update.message.reply_text(f'⏰ Already spin today!\nCome back after {remaining}h {int(rem_min%60)}m')
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
        await update.message.reply_text(f'🎡 DAILY SPIN\n\n🎉 JACKPOT! 10000 💰\nNew balance: {new_bal} 💰')
    else:
        await update.message.reply_text(f'🎡 DAILY SPIN\n\nYou got {amount} 💰\nNew balance: {new_bal} 💰')

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
        await update.message.reply_text(f'❌ Need {amount}, have {balance}')
        conn.close()
        return
    
    roll = random.randint(1, 6)
    multi = {1:0, 2:0.25, 3:0.5, 4:1.25, 5:1.5, 6:2.5}
    win = int(amount * multi[roll])
    new_bal = balance - amount + win
    c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f'🎲 Dice rolled on {roll}!\nYou won {win} 💰 ({multi[roll]}x)\nNew balance: {new_bal} 💰')

# ============ BET (Heads/Tails) ============
async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /bet heads/tails <amount>\nExample: /bet heads 1000')
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
        await update.message.reply_text(f'❌ Need {amount}, have {balance}')
        conn.close()
        return
    
    result = random.choice(['heads', 'tails'])
    
    if choice == result:
        win = amount * 2
        new_bal = balance - amount + win
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f'😃 Congratulations! It landed on {result}\nYou won {win} 👾\nBalance: {new_bal} 👾')
    else:
        new_bal = balance - amount
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f'😞 Unfortunately! It did not land on {choice}\nYou lost {amount} 👾\nBalance: {new_bal} 👾')

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
    
    msg = "🏏 IPL MATCHES\n\n"
    for m in matches_data:
        status = "🔓 OPEN" if m[4] == 0 else "🔒 LOCKED"
        msg += f'{m[1]} vs {m[2]}\n📅 {m[3]} | {status}\n/betmatch {m[1]} <amount> | /betmatch {m[2]} <amount>\n\n'
    
    user = get_user(user_id)
    msg += f'💰 Your balance: {user[2]} 💰'
    await update.message.reply_text(msg)
    conn.close()

# ============ BETMATCH ============
async def betmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /betmatch TEAM AMOUNT\nExample: /betmatch KKR 1000')
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
        await update.message.reply_text(f'❌ Need {amount}, have {user[2]}')
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
    
    await update.message.reply_text(f'✅ BET PLACED!\n{match[1]} vs {match[2]}\n🎯 {team} | {amount} 💰\nNew balance: {user[2]-amount} 💰')

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
    
    msg = f"🎯 MY BETS ({len(bets_data)})\n\n"
    for i, bet in enumerate(bets_data, 1):
        msg += f"{i}. {bet[3]} vs {bet[4]}\n   🎯 {bet[1]} | 💰 {bet[2]}\n   📅 {bet[5]}\n\n"
    msg += "💡 To cancel: /cancelbet TEAM1 vs TEAM2 [number]"
    await update.message.reply_text(msg)

# ============ CANCELBET ============
async def cancelbet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /cancelbet TEAM1 vs TEAM2 [bet_number]\nExample: /cancelbet KKR vs CSK 2')
        return
    
    team1 = args[0].upper()
    team2 = args[2].upper()
    bet_number = None
    if len(args) >= 4:
        try:
            bet_number = int(args[3])
        except:
            bet_number = None
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("SELECT id, team1, team2, locked FROM matches WHERE (team1=? AND team2=?) OR (team1=? AND team2=?)", (team1, team2, team2, team1))
    match = c.fetchone()
    
    if not match:
        await update.message.reply_text(f'❌ Match not found: {team1} vs {team2}')
        conn.close()
        return
    
    if match[3] == 1:
        await update.message.reply_text(f'🔒 Match locked! Cannot cancel now.')
        conn.close()
        return
    
    c.execute("SELECT id, amount FROM bets WHERE user_id=? AND match_id=?", (user_id, match[0]))
    bets_data = c.fetchall()
    
    if not bets_data:
        await update.message.reply_text(f'❌ No bets on {match[1]} vs {match[2]}')
        conn.close()
        return
    
    if len(bets_data) > 1 and bet_number is None:
        msg = f"🎯 Multiple bets on {match[1]} vs {match[2]}:\n\n"
        for i, bet in enumerate(bets_data, 1):
            msg += f"{i}. Amount: {bet[1]} 💰\n"
        msg += f"\n/cancelbet {match[1]} vs {match[2]} [number]"
        await update.message.reply_text(msg)
        conn.close()
        return
    
    if bet_number is not None:
        if bet_number < 1 or bet_number > len(bets_data):
            await update.message.reply_text(f'❌ Invalid! Choose 1-{len(bets_data)}')
            conn.close()
            return
        bet_to_cancel = bets_data[bet_number - 1]
    else:
        bet_to_cancel = bets_data[0]
    
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (bet_to_cancel[1], user_id))
    c.execute("DELETE FROM bets WHERE id=?", (bet_to_cancel[0],))
    c.execute("UPDATE users SET total = total - 1 WHERE user_id=?", (user_id,))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f'✅ BET CANCELLED!\n\n🏏 {match[1]} vs {match[2]}\n💰 Refund: {bet_to_cancel[1]} 💰\n📊 New balance: {new_bal} 💰')

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
        msg += f"{medal} {u[0]} - {u[1]} 💰\n"
    
    user = get_user(user_id)
    rank = c.execute("SELECT COUNT(*) FROM users WHERE balance > ?", (user[2],)).fetchone()[0] + 1
    msg += f"\n📊 Your rank: #{rank} | Balance: {user[2]} 💰"
    
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
                team1_users.append(f"{bet[2]} - {bet[1]}")
            else:
                team2_amount += bet[1]
                team2_users.append(f"{bet[2]} - {bet[1]}")
        
        full_msg += f'🏏 {match[1]} vs {match[2]}\n'
        full_msg += f'🎯 {match[1]} ({team1_amount}):\n'
        for i, u in enumerate(team1_users, 1):
            full_msg += f'   {i}. {u}\n'
        full_msg += f'\n🎯 {match[2]} ({team2_amount}):\n'
        for i, u in enumerate(team2_users, 1):
            full_msg += f'   {i}. {u}\n'
        full_msg += f'\n💣 Pool: {team1_amount + team2_amount} 💰\n\n'
    
    await update.message.reply_text(full_msg)
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
    
    if amount < 1:
        await update.message.reply_text('❌ Amount must be positive')
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
        await update.message.reply_text(f'❌ Need {amount}, have {sender_bal}')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, sender.id))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, receiver.id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f'💝 TIP SENT!\nTo: {receiver.first_name}\nAmount: {amount} 💰\nYour balance: {sender_bal - amount} 💰')

# ============ HISTORY ============
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    user = get_user(user_id)
    win_rate = int(user[4]/user[5]*100) if user[5] > 0 else 0
    await update.message.reply_text(f'📜 BET HISTORY\n\n✅ Won: {user[4]}\n❌ Lost: {user[5]-user[4]}\n📊 Win Rate: {win_rate}%\n\n🏆 Fantasy Points: {user[3]}')

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
    msg += f"\n📊 Your points: {user[3]} | Rank: #{rank}"
    
    await update.message.reply_text(msg)
    conn.close()

# ============ SHOP DATA INIT ============
def init_shop_data():
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    
    # Drop old tables
    c.execute("DROP TABLE IF EXISTS shop")
    c.execute("DROP TABLE IF EXISTS shop_women")
    
    c.execute('''CREATE TABLE shop 
                 (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, country TEXT, type TEXT, category TEXT)''')
    c.execute('''CREATE TABLE shop_women 
                 (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, country TEXT, type TEXT)''')
    
    # ============ INDIA CURRENT (40 players) ============
    players = [
        (1, 'Virat Kohli', 1000000, '🇮🇳', 'current', 'India'),
        (2, 'Rohit Sharma', 1000000, '🇮🇳', 'current', 'India'),
        (3, 'MS Dhoni', 1000000, '🇮🇳', 'current', 'India'),
        (4, 'Jasprit Bumrah', 900000, '🇮🇳', 'current', 'India'),
        (5, 'Hardik Pandya', 400000, '🇮🇳', 'current', 'India'),
        (6, 'Suryakumar Yadav', 350000, '🇮🇳', 'current', 'India'),
        (7, 'Ravindra Jadeja', 300000, '🇮🇳', 'current', 'India'),
        (8, 'KL Rahul', 280000, '🇮🇳', 'current', 'India'),
        (9, 'Rishabh Pant', 300000, '🇮🇳', 'current', 'India'),
        (10, 'Shubman Gill', 250000, '🇮🇳', 'current', 'India'),
        (11, 'Shreyas Iyer', 220000, '🇮🇳', 'current', 'India'),
        (12, 'Mohammed Shami', 250000, '🇮🇳', 'current', 'India'),
        (13, 'Kuldeep Yadav', 200000, '🇮🇳', 'current', 'India'),
        (14, 'Axar Patel', 200000, '🇮🇳', 'current', 'India'),
        (15, 'Ishan Kishan', 200000, '🇮🇳', 'current', 'India'),
        (16, 'Yuzvendra Chahal', 450000, '🇮🇳', 'current', 'India'),
        (17, 'Mohammed Siraj', 350000, '🇮🇳', 'current', 'India'),
        (18, 'Sanju Samson', 220000, '🇮🇳', 'current', 'India'),
        (19, 'Deepak Chahar', 180000, '🇮🇳', 'current', 'India'),
        (20, 'Prithvi Shaw', 150000, '🇮🇳', 'current', 'India'),
        (21, 'Shardul Thakur', 160000, '🇮🇳', 'current', 'India'),
        (22, 'Washington Sundar', 140000, '🇮🇳', 'current', 'India'),
        (23, 'Venkatesh Iyer', 130000, '🇮🇳', 'current', 'India'),
        (24, 'Ruturaj Gaikwad', 180000, '🇮🇳', 'current', 'India'),
        (25, 'Devdutt Padikkal', 120000, '🇮🇳', 'current', 'India'),
        (26, 'T Natarajan', 110000, '🇮🇳', 'current', 'India'),
        (27, 'Arshdeep Singh', 100000, '🇮🇳', 'current', 'India'),
        (28, 'Umran Malik', 90000, '🇮🇳', 'current', 'India'),
        (29, 'Ravi Bishnoi', 85000, '🇮🇳', 'current', 'India'),
        (30, 'Avesh Khan', 80000, '🇮🇳', 'current', 'India'),
        (31, 'Nitish Rana', 120000, '🇮🇳', 'current', 'India'),
        (32, 'Manish Pandey', 100000, '🇮🇳', 'current', 'India'),
        (33, 'Shivam Dube', 110000, '🇮🇳', 'current', 'India'),
        (34, 'Rahul Tripathi', 100000, '🇮🇳', 'current', 'India'),
        (35, 'Sarfaraz Khan', 80000, '🇮🇳', 'current', 'India'),
        (36, 'Krunal Pandya', 120000, '🇮🇳', 'current', 'India'),
        (37, 'Krishnappa Gowtham', 70000, '🇮🇳', 'current', 'India'),
        (38, 'Jaydev Unadkat', 75000, '🇮🇳', 'current', 'India'),
        (39, 'Umesh Yadav', 90000, '🇮🇳', 'current', 'India'),
        (40, 'Bhuvneshwar Kumar', 100000, '🇮🇳', 'current', 'India'),
        
        # India Legends (30 players)
        (41, 'Sachin Tendulkar', 2000000, '🇮🇳', 'legend', 'India'),
        (42, 'Rahul Dravid', 1500000, '🇮🇳', 'legend', 'India'),
        (43, 'Sourav Ganguly', 1400000, '🇮🇳', 'legend', 'India'),
        (44, 'VVS Laxman', 1300000, '🇮🇳', 'legend', 'India'),
        (45, 'Virender Sehwag', 1350000, '🇮🇳', 'legend', 'India'),
        (46, 'Zaheer Khan', 1200000, '🇮🇳', 'legend', 'India'),
        (47, 'Yuvraj Singh', 1450000, '🇮🇳', 'legend', 'India'),
        (48, 'Harbhajan Singh', 1100000, '🇮🇳', 'legend', 'India'),
        (49, 'Anil Kumble', 1250000, '🇮🇳', 'legend', 'India'),
        (50, 'Suresh Raina', 950000, '🇮🇳', 'legend', 'India'),
        (51, 'Gautam Gambhir', 1000000, '🇮🇳', 'legend', 'India'),
        (52, 'Mohammad Azharuddin', 800000, '🇮🇳', 'legend', 'India'),
        (53, 'Navjot Singh Sidhu', 700000, '🇮🇳', 'legend', 'India'),
        (54, 'Kapil Dev', 1800000, '🇮🇳', 'legend', 'India'),
        (55, 'Sunil Gavaskar', 1700000, '🇮🇳', 'legend', 'India'),
        (56, 'Bishan Singh Bedi', 900000, '🇮🇳', 'legend', 'India'),
        (57, 'Erapalli Prasanna', 850000, '🇮🇳', 'legend', 'India'),
        (58, 'BS Chandrasekhar', 820000, '🇮🇳', 'legend', 'India'),
        (59, 'Venkatesh Prasad', 600000, '🇮🇳', 'legend', 'India'),
        (60, 'Javagal Srinath', 750000, '🇮🇳', 'legend', 'India'),
        (61, 'Robin Singh', 500000, '🇮🇳', 'legend', 'India'),
        (62, 'Ajay Jadeja', 550000, '🇮🇳', 'legend', 'India'),
        (63, 'Vinod Kambli', 480000, '🇮🇳', 'legend', 'India'),
        (64, 'Dilip Vengsarkar', 650000, '🇮🇳', 'legend', 'India'),
        (65, 'Chandu Borde', 450000, '🇮🇳', 'legend', 'India'),
        (66, 'Madan Lal', 420000, '🇮🇳', 'legend', 'India'),
        (67, 'Roger Binny', 400000, '🇮🇳', 'legend', 'India'),
        (68, 'Syed Kirmani', 480000, '🇮🇳', 'legend', 'India'),
        (69, 'Farokh Engineer', 500000, '🇮🇳', 'legend', 'India'),
        (70, 'Salil Ankola', 350000, '🇮🇳', 'legend', 'India'),
        
        # Australia Current (30 players)
        (71, 'Steve Smith', 280000, '🇦🇺', 'current', 'Australia'),
        (72, 'David Warner', 260000, '🇦🇺', 'current', 'Australia'),
        (73, 'Pat Cummins', 220000, '🇦🇺', 'current', 'Australia'),
        (74, 'Glenn Maxwell', 240000, '🇦🇺', 'current', 'Australia'),
        (75, 'Mitchell Starc', 210000, '🇦🇺', 'current', 'Australia'),
        (76, 'Adam Zampa', 130000, '🇦🇺', 'current', 'Australia'),
        (77, 'Travis Head', 140000, '🇦🇺', 'current', 'Australia'),
        (78, 'Josh Hazlewood', 150000, '🇦🇺', 'current', 'Australia'),
        (79, 'Marcus Stoinis', 120000, '🇦🇺', 'current', 'Australia'),
        (80, 'Tim David', 100000, '🇦🇺', 'current', 'Australia'),
        (81, 'Cameron Green', 180000, '🇦🇺', 'current', 'Australia'),
        (82, 'Alex Carey', 90000, '🇦🇺', 'current', 'Australia'),
        (83, 'Sean Abbott', 80000, '🇦🇺', 'current', 'Australia'),
        (84, 'Nathan Lyon', 110000, '🇦🇺', 'current', 'Australia'),
        (85, 'Ashton Agar', 85000, '🇦🇺', 'current', 'Australia'),
        (86, 'Kane Richardson', 75000, '🇦🇺', 'current', 'Australia'),
        (87, 'Daniel Sams', 70000, '🇦🇺', 'current', 'Australia'),
        (88, 'Ben McDermott', 65000, '🇦🇺', 'current', 'Australia'),
        (89, 'Josh Inglis', 80000, '🇦🇺', 'current', 'Australia'),
        (90, 'Mitchell Marsh', 130000, '🇦🇺', 'current', 'Australia'),
        (91, 'Aaron Finch', 110000, '🇦🇺', 'current', 'Australia'),
        (92, 'Matthew Wade', 85000, '🇦🇺', 'current', 'Australia'),
        (93, 'Moises Henriques', 70000, '🇦🇺', 'current', 'Australia'),
        (94, 'Nathan Coulter-Nile', 68000, '🇦🇺', 'current', 'Australia'),
        (95, 'Andrew Tye', 62000, '🇦🇺', 'current', 'Australia'),
        (96, 'Jason Behrendorff', 60000, '🇦🇺', 'current', 'Australia'),
        (97, 'Riley Meredith', 55000, '🇦🇺', 'current', 'Australia'),
        (98, 'Jhye Richardson', 70000, '🇦🇺', 'current', 'Australia'),
        (99, 'Nic Maddinson', 50000, '🇦🇺', 'current', 'Australia'),
        (100, 'Usman Khawaja', 95000, '🇦🇺', 'current', 'Australia'),
        
        # Australia Legends (25 players)
        (101, 'Ricky Ponting', 1700000, '🇦🇺', 'legend', 'Australia'),
        (102, 'Adam Gilchrist', 1600000, '🇦🇺', 'legend', 'Australia'),
        (103, 'Shane Warne', 1500000, '🇦🇺', 'legend', 'Australia'),
        (104, 'Glenn McGrath', 1450000, '🇦🇺', 'legend', 'Australia'),
        (105, 'Brett Lee', 1400000, '🇦🇺', 'legend', 'Australia'),
        (106, 'Matthew Hayden', 1350000, '🇦🇺', 'legend', 'Australia'),
        (107, 'Michael Clarke', 1200000, '🇦🇺', 'legend', 'Australia'),
        (108, 'Mike Hussey', 1050000, '🇦🇺', 'legend', 'Australia'),
        (109, 'Andrew Symonds', 1100000, '🇦🇺', 'legend', 'Australia'),
        (110, 'Shane Watson', 1000000, '🇦🇺', 'legend', 'Australia'),
        (111, 'Brad Haddin', 700000, '🇦🇺', 'legend', 'Australia'),
        (112, 'David Boon', 600000, '🇦🇺', 'legend', 'Australia'),
        (113, 'Dean Jones', 750000, '🇦🇺', 'legend', 'Australia'),
        (114, 'Mark Waugh', 800000, '🇦🇺', 'legend', 'Australia'),
        (115, 'Steve Waugh', 850000, '🇦🇺', 'legend', 'Australia'),
        (116, 'Allan Border', 900000, '🇦🇺', 'legend', 'Australia'),
        (117, 'Dennis Lillee', 950000, '🇦🇺', 'legend', 'Australia'),
        (118, 'Jeff Thomson', 800000, '🇦🇺', 'legend', 'Australia'),
        (119, 'Greg Chappell', 750000, '🇦🇺', 'legend', 'Australia'),
        (120, 'Ian Chappell', 700000, '🇦🇺', 'legend', 'Australia'),
        (121, 'Doug Walters', 600000, '🇦🇺', 'legend', 'Australia'),
        (122, 'Rod Marsh', 550000, '🇦🇺', 'legend', 'Australia'),
        (123, 'Craig McDermott', 500000, '🇦🇺', 'legend', 'Australia'),
        (124, 'Damien Martyn', 650000, '🇦🇺', 'legend', 'Australia'),
        (125, 'Jason Gillespie', 550000, '🇦🇺', 'legend', 'Australia'),
        
        # Pakistan Current (25 players)
        (126, 'Babar Azam', 300000, '🇵🇰', 'current', 'Pakistan'),
        (127, 'Shaheen Afridi', 250000, '🇵🇰', 'current', 'Pakistan'),
        (128, 'Mohammad Rizwan', 200000, '🇵🇰', 'current', 'Pakistan'),
        (129, 'Shadab Khan', 150000, '🇵🇰', 'current', 'Pakistan'),
        (130, 'Haris Rauf', 130000, '🇵🇰', 'current', 'Pakistan'),
        (131, 'Fakhar Zaman', 120000, '🇵🇰', 'current', 'Pakistan'),
        (132, 'Imam-ul-Haq', 100000, '🇵🇰', 'current', 'Pakistan'),
        (133, 'Naseem Shah', 110000, '🇵🇰', 'current', 'Pakistan'),
        (134, 'Mohammad Nawaz', 90000, '🇵🇰', 'current', 'Pakistan'),
        (135, 'Hasan Ali', 85000, '🇵🇰', 'current', 'Pakistan'),
        (136, 'Iftikhar Ahmed', 70000, '🇵🇰', 'current', 'Pakistan'),
        (137, 'Khushdil Shah', 65000, '🇵🇰', 'current', 'Pakistan'),
        (138, 'Mohammad Wasim', 60000, '🇵🇰', 'current', 'Pakistan'),
        (139, 'Usman Qadir', 55000, '🇵🇰', 'current', 'Pakistan'),
        (140, 'Haider Ali', 50000, '🇵🇰', 'current', 'Pakistan'),
        (141, 'Sarfaraz Ahmed', 80000, '🇵🇰', 'current', 'Pakistan'),
        (142, 'Asif Ali', 60000, '🇵🇰', 'current', 'Pakistan'),
        (143, 'Mohammad Hasnain', 55000, '🇵🇰', 'current', 'Pakistan'),
        (144, 'Shan Masood', 70000, '🇵🇰', 'current', 'Pakistan'),
        (145, 'Saud Shakeel', 50000, '🇵🇰', 'current', 'Pakistan'),
        (146, 'Agha Salman', 48000, '🇵🇰', 'current', 'Pakistan'),
        (147, 'Mohammad Haris', 45000, '🇵🇰', 'current', 'Pakistan'),
        (148, 'Zaman Khan', 40000, '🇵🇰', 'current', 'Pakistan'),
        (149, 'Abrar Ahmed', 35000, '🇵🇰', 'current', 'Pakistan'),
        (150, 'Ihsanullah', 38000, '🇵🇰', 'current', 'Pakistan'),
        
        # Pakistan Legends (25 players)
        (151, 'Wasim Akram', 1400000, '🇵🇰', 'legend', 'Pakistan'),
        (152, 'Waqar Younis', 1300000, '🇵🇰', 'legend', 'Pakistan'),
        (153, 'Imran Khan', 1600000, '🇵🇰', 'legend', 'Pakistan'),
        (154, 'Shahid Afridi', 1000000, '🇵🇰', 'legend', 'Pakistan'),
        (155, 'Younis Khan', 900000, '🇵🇰', 'legend', 'Pakistan'),
        (156, 'Mohammad Hafeez', 600000, '🇵🇰', 'legend', 'Pakistan'),
        (157, 'Mohammad Amir', 500000, '🇵🇰', 'legend', 'Pakistan'),
        (158, 'Shoaib Akhtar', 1200000, '🇵🇰', 'legend', 'Pakistan'),
        (159, 'Inzamam-ul-Haq', 950000, '🇵🇰', 'legend', 'Pakistan'),
        (160, 'Javed Miandad', 850000, '🇵🇰', 'legend', 'Pakistan'),
        (161, 'Zaheer Abbas', 800000, '🇵🇰', 'legend', 'Pakistan'),
        (162, 'Saeed Anwar', 750000, '🇵🇰', 'legend', 'Pakistan'),
        (163, 'Saleem Malik', 600000, '🇵🇰', 'legend', 'Pakistan'),
        (164, 'Mushtaq Ahmed', 550000, '🇵🇰', 'legend', 'Pakistan'),
        (165, 'Saqlain Mushtaq', 500000, '🇵🇰', 'legend', 'Pakistan'),
        (166, 'Abdul Qadir', 480000, '🇵🇰', 'legend', 'Pakistan'),
        (167, 'Sarfraz Nawaz', 450000, '🇵🇰', 'legend', 'Pakistan'),
        (168, 'Misbah-ul-Haq', 550000, '🇵🇰', 'legend', 'Pakistan'),
        (169, 'Kamran Akmal', 400000, '🇵🇰', 'legend', 'Pakistan'),
        (170, 'Umar Gul', 420000, '🇵🇰', 'legend', 'Pakistan'),
        (171, 'Sohail Tanvir', 380000, '🇵🇰', 'legend', 'Pakistan'),
        (172, 'Abdul Razzaq', 450000, '🇵🇰', 'legend', 'Pakistan'),
        (173, 'Azhar Mahmood', 350000, '🇵🇰', 'legend', 'Pakistan'),
        (174, 'Mohammad Yousuf', 580000, '🇵🇰', 'legend', 'Pakistan'),
        (175, 'Taufeeq Umar', 300000, '🇵🇰', 'legend', 'Pakistan'),
    ]
    
    for p in players:
        c.execute("INSERT OR REPLACE INTO shop (id, name, price, country, type, category) VALUES (?, ?, ?, ?, ?, ?)", p)
    
    # ============ WOMEN PLAYERS (40 players) ============
    women = [
        (1, 'Smriti Mandhana', 750000, '🇮🇳', 'current'),
        (2, 'Harmanpreet Kaur', 750000, '🇮🇳', 'current'),
        (3, 'Mithali Raj', 700000, '🇮🇳', 'current'),
        (4, 'Jhulan Goswami', 650000, '🇮🇳', 'current'),
        (5, 'Shafali Verma', 300000, '🇮🇳', 'current'),
        (6, 'Deepti Sharma', 320000, '🇮🇳', 'current'),
        (7, 'Richa Ghosh', 250000, '🇮🇳', 'current'),
        (8, 'Renuka Singh', 220000, '🇮🇳', 'current'),
        (9, 'Shreyanka Patil', 150000, '🇮🇳', 'current'),
        (10, 'Pratika Rawal', 200000, '🇮🇳', 'current'),
        (11, 'Meg Lanning', 600000, '🇦🇺', 'current'),
        (12, 'Ellyse Perry', 700000, '🇦🇺', 'current'),
        (13, 'Alyssa Healy', 500000, '🇦🇺', 'current'),
        (14, 'Beth Mooney', 480000, '🇦🇺', 'current'),
        (15, 'Ashleigh Gardner', 400000, '🇦🇺', 'current'),
        (16, 'Jess Jonassen', 350000, '🇦🇺', 'current'),
        (17, 'Nat Sciver-Brunt', 550000, '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'current'),
        (18, 'Heather Knight', 420000, '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'current'),
        (19, 'Sophie Ecclestone', 450000, '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'current'),
        (20, 'Danni Wyatt', 300000, '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'current'),
        (21, 'Alice Capsey', 280000, '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'current'),
        (22, 'Sophie Devine', 500000, '🇳🇿', 'current'),
        (23, 'Suzie Bates', 480000, '🇳🇿', 'current'),
        (24, 'Amelia Kerr', 420000, '🇳🇿', 'current'),
        (25, 'Lea Tahuhu', 250000, '🇳🇿', 'current'),
        (26, 'Laura Wolvaardt', 400000, '🇿🇦', 'current'),
        (27, 'Marizanne Kapp', 420000, '🇿🇦', 'current'),
        (28, 'Shabnim Ismail', 350000, '🇿🇦', 'current'),
        (29, 'Chloe Tryon', 280000, '🇿🇦', 'current'),
        (30, 'Bismah Maroof', 250000, '🇵🇰', 'current'),
        (31, 'Nida Dar', 270000, '🇵🇰', 'current'),
        (32, 'Fatima Sana', 180000, '🇵🇰', 'current'),
        (33, 'Chamari Athapaththu', 350000, '🇱🇰', 'current'),
        (34, 'Harshitha Samarawickrama', 200000, '🇱🇰', 'current'),
        (35, 'Salma Khatun', 180000, '🇧🇩', 'current'),
        (36, 'Nigar Sultana', 200000, '🇧🇩', 'current'),
        (37, 'Nahida Sapan', 120000, '🇧🇩', 'current'),
        (38, 'Gaby Lewis', 220000, '🇮🇪', 'current'),
        (39, 'Laura Delany', 200000, '🇮🇪', 'current'),
        (40, 'Sana Mir', 350000, '🇵🇰', 'current'),
    ]
    
    for w in women:
        c.execute("INSERT OR REPLACE INTO shop_women (id, name, price, country, type) VALUES (?, ?, ?, ?, ?)", w)
    
    conn.commit()
    conn.close()

# Call this after init_db()
init_shop_data()

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
    await update.message.reply_text("🏏 CRICKETER SHOP\n\nSelect category:", reply_markup=reply_markup)

# ============ SHOP CALLBACK ============
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
        msg = "👩 WOMEN CRICKETERS\n\n"
        for p in players:
            msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
        msg += f"\n💡 Use /buyw <number> to purchase"
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
        await query.edit_message_text(f"❌ No players found")
        return
    
    msg = f"🏏 {country} {ptype.upper()} PLAYERS\n\n"
    for p in players:
        msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
    msg += f"\n💡 Use /buy <number> to purchase"
    await query.edit_message_text(msg)

# ============ BUY ============
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
    
    await update.message.reply_text(f'✅ PURCHASED!\n\n🏏 {player[0]}\n💰 Price: {player[1]:,} 💰\n📊 New balance: {new_bal:,} 💰')

# ============ BUYW ============
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
    
    await update.message.reply_text(f'✅ PURCHASED!\n\n👩 {player[0]}\n💰 Price: {player[1]:,} 💰\n📊 New balance: {new_bal:,} 💰')

# ============ MYTEAM ============
async def myteam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    
    # Shop (men) players
    c.execute("""
        SELECT p.name, p.price FROM user_players u 
        JOIN shop p ON u.player_id = p.id 
        WHERE u.user_id = ? AND u.type = 'mens'
    """, (user_id,))
    mens = c.fetchall()
    
    # Shop2 (cheap) players
    c.execute("""
        SELECT s.name, s.price FROM user_players2 u 
        JOIN shop2 s ON u.player_id = s.id 
        WHERE u.user_id = ?
    """, (user_id,))
    cheap = c.fetchall()
    
    # Women players (if any)
    c.execute("""
        SELECT w.name, w.price FROM user_players u 
        JOIN shop_women w ON u.player_id = w.id 
        WHERE u.user_id = ? AND u.type = 'women'
    """, (user_id,))
    women = c.fetchall()
    
    conn.close()
    
    mens_total = sum(p[1] for p in mens)
    cheap_total = sum(c[1] for c in cheap)
    women_total = sum(w[1] for w in women)
    
    msg = "🏏 MY CRICKET TEAM\n\n"
    
    # MEN PLAYERS
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n👨 MEN PLAYERS"
    if mens:
        msg += f" ({len(mens)})\n\n"
        for i, p in enumerate(mens, 1):
            msg += f"{i}. {p[0]} - {p[1]:,} 💰\n"
        msg += f"\nTotal Value: {mens_total:,} 💰"
    else:
        msg += "\n\nNo men players. Use /shop to buy!"
    
    # CHEAP PLAYERS (SHOP2)
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🤑 CHEAP PLAYERS"
    if cheap:
        msg += f" ({len(cheap)})\n\n"
        for i, c in enumerate(cheap, 1):
            msg += f"{i}. {c[0]} - {c[1]:,} 💰\n"
        msg += f"\nTotal Value: {cheap_total:,} 💰"
    else:
        msg += "\n\nNo cheap players. Use /shop2 to buy!"
    
    # WOMEN PLAYERS
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n👩 WOMEN PLAYERS"
    if women:
        msg += f" ({len(women)})\n\n"
        for i, w in enumerate(women, 1):
            msg += f"{i}. {w[0]} - {w[1]:,} 💰\n"
        msg += f"\nTotal Value: {women_total:,} 💰"
    else:
        msg += "\n\nNo women players. Use /shop to buy!"
    
    grand_total = mens_total + cheap_total + women_total
    total_players = len(mens) + len(cheap) + len(women)
    
    msg += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n💰 TOTAL VALUE: {grand_total:,} 💰\n🏆 PLAYERS: {total_players}"
    
    await update.message.reply_text(msg)

# ============ TOP COLLECTORS ============
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    
    # Sirf un users ko dikhao jinhone kuch kharida hai
    c.execute("""
        SELECT u.name, COUNT(up.player_id) as count, 
        COALESCE((SELECT SUM(p.price) FROM user_players up2 
                  JOIN shop p ON up2.player_id = p.id 
                  WHERE up2.user_id = u.user_id), 0) as total_value
        FROM users u
        JOIN user_players up ON u.user_id = up.user_id
        GROUP BY u.user_id
        ORDER BY total_value DESC
        LIMIT 10
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
    
    # Current user ka data
    c.execute("""
        SELECT COUNT(up.player_id), 
        COALESCE((SELECT SUM(p.price) FROM user_players up2 
                  JOIN shop p ON up2.player_id = p.id 
                  WHERE up2.user_id = ?), 0)
        FROM user_players up WHERE user_id = ?
    """, (user_id, user_id))
    user_data = c.fetchone()
    
    player_count = user_data[0] if user_data and user_data[0] else 0
    total_value = user_data[1] if user_data and user_data[1] else 0
    
    msg += f"\n📊 Your rank: #{len(tops)} | Players: {player_count} | Value: {total_value:,} 💰"
    
    await update.message.reply_text(msg)
    conn.close()

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
    msg += f"\nTotal: {len(ach)} achievements"
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
    
    await update.message.reply_text(f'✅ ACHIEVEMENT GIVEN!\n\nUser: {target.first_name}\nAchievement: {achievement} 🏆')

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
    
    await update.message.reply_text(f'✅ ACHIEVEMENT REMOVED!\n\nRemoved: {removed[1]} 🏆')

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
    
    await update.message.reply_text(f'✅ MATCH ADDED!\n{team1} vs {team2} | {date}')

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
    
    await update.message.reply_text(f'🔒 MATCH LOCKED!\n{match[1]} vs {match[2]}\nBets: {count}\nPool: {total} 💰')

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
            winner_list.append(f"{u[3]} - {bet[1]} → {win_amount}")
        else:
            c.execute("UPDATE users SET points = points - 5 WHERE user_id=?", (bet[0],))
            losers += 1
            loser_list.append(f"{u[3]} - {bet[1]} → 0")
    
    c.execute("DELETE FROM bets WHERE match_id=?", (match[0],))
    c.execute("DELETE FROM matches WHERE id=?", (match[0],))
    conn.commit()
    conn.close()
    
    msg = f"📢 RESULT!\n\n🏏 {match[1]} vs {match[2]}\n🏆 Winner: {winner}\n\n✅ WINNERS (+10 pts): {winners}\n"
    for w in winner_list[:5]:
        msg += f"   • {w}\n"
    if len(winner_list) > 5:
        msg += f"   • +{len(winner_list)-5} more\n"
    
    msg += f"\n❌ LOSERS (-5 pts): {losers}\n"
    for l in loser_list[:5]:
        msg += f"   • {l}\n"
    if len(loser_list) > 5:
        msg += f"   • +{len(loser_list)-5} more\n"
    
    msg += f"\n💰 Total Payout: {total_paid} 💰"
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
    
    await update.message.reply_text(f'✅ ADDED {amount} to {old[1]}\nBalance: {old[0]} → {old[0]+amount}')

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
        await update.message.reply_text(f'❌ Insufficient! Balance: {old[0]}')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, target.id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f'❌ REMOVED {amount} from {old[1]}\nBalance: {old[0]} → {old[0]-amount}')

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
        await update.message.reply_text('❌ Invalid input')
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

async def setprice2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /setprice2 <player_id> <new_price>\nExample: /setprice2 1 800000')
        return
    
    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid input')
        return
    
    conn = sqlite3.connect('fantasy.db')
    c = conn.cursor()
    c.execute("SELECT name FROM shop_women WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("UPDATE shop_women SET price = ? WHERE id=?", (new_price, player_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f'✅ WOMEN PRICE UPDATED!\n{player[0]}\nNew Price: {new_price:,} 💰')


# ============ CHEAP SHOP (SHOP2) ============

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
    
    await update.message.reply_text(f'✅ PURCHASED!\n\n🏏 {player[0]}\n💰 Price: {player[1]:,} 💰\n📊 New balance: {new_bal:,} 💰')

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
    msg = "👤 MY CHEAP PLAYERS\n\n"
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
        SELECT u.name, COUNT(up.player_id) as count, SUM(s.price) as total
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

# ============ ADMIN COMMANDS FOR SHOP2 ============

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
    
    await update.message.reply_text(f'✅ PLAYER ADDED!\n\nID: {player_id} | {name}\n💰 Price: {price:,} 💰')

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
    
    await update.message.reply_text(f'✅ PRICE UPDATED!\n{player[0]}\nNew Price: {new_price:,} 💰')

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
    
    await update.message.reply_text(f'✅ PLAYER REMOVED!\n{player[0]} (ID: {player_id})')


# ============ MAIN ============
def main():
    app = Application.builder().token(TOKEN).build()
    
    # User commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("setpfp", setpfp))
    app.add_handler(CommandHandler("rmpfp", rmpfp))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("spin", spin))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("bet", bet))
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("betmatch", betmatch))
    app.add_handler(CommandHandler("mybets", mybets))
    app.add_handler(CommandHandler("cancelbet", cancelbet))
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
    app.add_handler(CommandHandler("top", top_collectors))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_"))
    
    # Admin commands
    app.add_handler(CommandHandler("addmatch", addmatch))
    app.add_handler(CommandHandler("lockmatch", lockmatch))
    app.add_handler(CommandHandler("result", result))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("setprice", setprice))
    app.add_handler(CommandHandler("setprice2", setprice2))
    
    # Achievement commands
    app.add_handler(CommandHandler("achievements", achievements))
    app.add_handler(CommandHandler("achieve", achieve))
    app.add_handler(CommandHandler("rmachieve", rmachieve))

    # Cheap shop handlers
    app.add_handler(CommandHandler("shop2", shop2))
    app.add_handler(CommandHandler("buy2", buy2))
    app.add_handler(CommandHandler("myteam2", myteam2))
    app.add_handler(CommandHandler("top2", top2))
    app.add_handler(CommandHandler("addplayer2", addplayer2))
    app.add_handler(CommandHandler("setprice2", setprice2))
    app.add_handler(CommandHandler("removeplayer2", removeplayer2))

    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()


