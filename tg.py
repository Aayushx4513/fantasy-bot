# ============ PART 1: IMPORTS & DATABASE ============

from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import sqlite3
import random
from datetime import datetime, timedelta
import os
import threading
import time

TOKEN = "8533156744:AAE2Fesm35bggPg47V2UBjJolJnRsJ-pjVA"
ADMIN_IDS = [7687078555, 1315564307]

def get_db():
    return sqlite3.connect('fantasy.db')

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, name TEXT, balance INTEGER, 
                  points INTEGER, won INTEGER, total INTEGER, photo TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS matches 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, team1 TEXT, team2 TEXT, 
                  date TEXT, status TEXT, locked INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bets 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
                  match_id INTEGER, team TEXT, amount INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS claim 
                 (user_id INTEGER PRIMARY KEY, last_claim DATE)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS spin 
                 (user_id INTEGER PRIMARY KEY, last_claim TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS shop 
                 (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, 
                  country TEXT, type TEXT, category TEXT, photo TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS shop_women 
                 (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, 
                  country TEXT, type TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS shop2 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS shop3 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_players 
                 (user_id INTEGER, player_id INTEGER, type TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_players2 
                 (user_id INTEGER, player_id INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS user_players3 
                 (user_id INTEGER, player_id INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS achievements 
                 (user_id INTEGER, achievement TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS bank 
                 (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, 
                  last_interest TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS groups 
                 (group_id INTEGER PRIMARY KEY, group_name TEXT, added_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS claim_codes 
                 (code TEXT PRIMARY KEY, amount INTEGER, max_claims INTEGER DEFAULT 5,
                  claimed_count INTEGER DEFAULT 0, created_at TEXT, expires_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS code_claims 
                 (code TEXT, user_id INTEGER, claimed_at TEXT,
                  PRIMARY KEY (code, user_id))''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

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

# ============ PART 2: BASIC COMMANDS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name if user.first_name else user.username or "User"
    user_id = user.id
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing = c.fetchone()
    
    keyboard = [
        [InlineKeyboardButton("📢 UPDATES", url="https://t.me/clbotofficial")],
        [InlineKeyboardButton("👥 MAIN GROUP", url="https://t.me/+eTD1m8Cjc_wyOTNl")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if not existing:
        c.execute("INSERT INTO users (user_id, name, balance, points, won, total) VALUES (?, ?, 1000, 0, 0, 0)", (user_id, name))
        conn.commit()
        await update.message.reply_text(
            f"✨ WELCOME TO CL ZONE ✨\n\n👑 {name}, you've joined the elite club!\n💰 1000 credits | 🏆 0 pts\n\n🎯 /claim - Daily rewards\n🎡 /spin - Daily spin\n👤 /profile - Your stats\n🏆 /leaderboard - Top players",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            f"✨ WELCOME BACK TO CL ZONE ✨\n\n👑 {name}\n💰 {existing[2]:,} credits | 🏆 {existing[3]} pts\n\n🎯 /claim - Daily rewards\n🎡 /spin - Daily spin\n👤 /profile - Your stats\n🏆 /leaderboard - Top players",
            reply_markup=reply_markup
        )
    conn.close()

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 COMMANDS\n\n"
        "/start - Start bot\n/profile - Your profile\n/claim - 500 daily\n/spin - 1k-10k daily\n"
        "/dice - Dice game\n/flip - Heads/Tails\n/matches - Live matches\n/bet - Place bet\n"
        "/shop - Buy players\n/myteam - Your collection\n/leaderboard - Rich list\n/bank - Bank system\n"
        "/claimcode - Claim code\n/activecodes - Active codes"
    )

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
    
    c.execute("SELECT balance FROM bank WHERE user_id=?", (user_id,))
    bank_row = c.fetchone()
    bank_bal = bank_row[0] if bank_row else 0
    conn.close()
    
    wallet_bal, points, won, total, photo = data
    total_wealth = wallet_bal + bank_bal
    win_rate = int(won/total*100) if total > 0 else 0
    
    if photo:
        await update.message.reply_photo(photo=photo, 
            caption=f"👤 PROFILE\n\n{name}\n💰 Wallet: {wallet_bal:,} | 🏦 Bank: {bank_bal:,}\n💰 Total: {total_wealth:,}\n🏆 Points: {points}\n📊 Bets: {won}/{total} ({win_rate}%)")
    else:
        await update.message.reply_text(f"👤 PROFILE\n\n{name}\n💰 Wallet: {wallet_bal:,} | 🏦 Bank: {bank_bal:,}\n💰 Total: {total_wealth:,}\n🏆 Points: {points}\n📊 Bets: {won}/{total} ({win_rate}%)")

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

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT last_claim FROM claim WHERE user_id=?", (user_id,))
    row = c.fetchone()
    today = datetime.now().date()
    if row and row[0]:
        last = datetime.fromisoformat(row[0]).date()
        if last == today:
            await update.message.reply_text("⚠️ Already claimed today!")
            conn.close()
            return
    c.execute("INSERT OR REPLACE INTO claim (user_id, last_claim) VALUES (?, ?)", (user_id, today.isoformat()))
    c.execute("UPDATE users SET balance = balance + 500 WHERE user_id=?", (user_id,))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"✅ Claimed 500 credits!\n💰 New balance: {new_bal:,}")

async def spin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT last_claim FROM spin WHERE user_id=?", (user_id,))
    row = c.fetchone()
    now = datetime.now()
    if row and row[0]:
        last = datetime.fromisoformat(row[0])
        if last.date() == now.date():
            await update.message.reply_text("⚠️ Already spun today!")
            conn.close()
            return
    amount = random.randint(1000, 10000)
    c.execute("INSERT OR REPLACE INTO spin (user_id, last_claim) VALUES (?, ?)", (user_id, now.isoformat()))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"✅ Spin reward: {amount:,} credits!\n💰 New balance: {new_bal:,}")

# ============ PART 3: GAMES & BETTING ============

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
        await update.message.reply_text(f"🎲 DICE\n\n🎲 Rolled: {roll} {dice_emoji[roll]}\n✨ You won {win:,}💰 ({multi[roll]}x)\n💰 New balance: {new_bal:,}")
    else:
        await update.message.reply_text(f"🎲 DICE\n\n🎲 Rolled: {roll} {dice_emoji[roll]}\n💀 You lost {amount:,}💰\n💰 New balance: {new_bal:,}")

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
        await update.message.reply_text(f"🪙 {result.upper()}! You won {win:,}💰\n💰 New balance: {new_bal:,}")
    else:
        new_bal = balance - amount
        c.execute("UPDATE users SET balance = ? WHERE user_id=?", (new_bal, user_id))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"😞 {result.upper()}! You lost {amount:,}💰\n💰 New balance: {new_bal:,}")

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2, date, locked FROM matches WHERE locked=0")
    matches_data = c.fetchall()
    conn.close()
    
    if not matches_data:
        await update.message.reply_text('📭 No active matches')
        return
    
    msg = "🏏 LIVE MATCHES\n\n"
    for m in matches_data:
        status = "🔓 OPEN" if m[4] == 0 else "🔒 LOCKED"
        msg += f"🔥 {m[1]} vs {m[2]}\n📅 {m[3]} | {status}\n💰 /bet {m[1]} <amount>\n\n"
    await update.message.reply_text(msg)

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /bet TEAM AMOUNT\nExample: /bet IND 1000')
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
        await update.message.reply_text("❌ Max 2 bets per match!")
        conn.close()
        return
    
    c.execute("INSERT INTO bets (user_id, match_id, team, amount) VALUES (?, ?, ?, ?)", (user_id, match[0], team, amount))
    c.execute("UPDATE users SET balance = balance - ?, total = total + 1 WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ BET PLACED!\n🏏 {match[1]} vs {match[2]}\n🎯 {team}\n💰 {amount:,}💰\n📊 New balance: {user[2]-amount:,}")

async def mybets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT b.id, b.team, b.amount, m.team1, m.team2 FROM bets b JOIN matches m ON b.match_id = m.id WHERE b.user_id = ? AND m.locked = 0", (user_id,))
    bets = c.fetchall()
    conn.close()
    
    if not bets:
        await update.message.reply_text('📭 No active bets')
        return
    
    msg = "🎯 MY BETS\n\n"
    for i, bet in enumerate(bets, 1):
        msg += f"{i}. {bet[3]} vs {bet[4]}\n   🎯 {bet[1]} | 💰 {bet[2]:,}\n\n"
    msg += "💡 /cancel <number>"
    await update.message.reply_text(msg)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /cancel <bet_number>')
        return
    
    try:
        bet_num = int(args[0])
    except:
        await update.message.reply_text('❌ Invalid number')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT b.id, b.amount, m.team1, m.team2 FROM bets b JOIN matches m ON b.match_id = m.id WHERE b.user_id = ? AND m.locked = 0", (user_id,))
    bets = c.fetchall()
    
    if bet_num < 1 or bet_num > len(bets):
        await update.message.reply_text(f'❌ Choose 1-{len(bets)}')
        conn.close()
        return
    
    bet = bets[bet_num - 1]
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (bet[1], user_id))
    c.execute("DELETE FROM bets WHERE id=?", (bet[0],))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Bet cancelled! Refund: {bet[1]:,}💰")

# ============ PART 4: SHOP SYSTEM ============

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
        [InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 England (Current)", callback_data="shop_England_current")],
        [InlineKeyboardButton("🏴󠁧󠁢󠁥󠁮󠁧󠁿 England (Legends)", callback_data="shop_England_legend")],
        [InlineKeyboardButton("🇳🇿 New Zealand (Current)", callback_data="shop_New Zealand_current")],
        [InlineKeyboardButton("🇳🇿 New Zealand (Legends)", callback_data="shop_New Zealand_legend")],
        [InlineKeyboardButton("🇱🇰 Sri Lanka (Current)", callback_data="shop_Sri Lanka_current")],
        [InlineKeyboardButton("🇱🇰 Sri Lanka (Legends)", callback_data="shop_Sri Lanka_legend")],
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
            await query.edit_message_text("👩 No women players yet!")
            return
        
        msg = "👩 WOMEN CRICKETERS\n\n"
        for p in players:
            msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
        msg += "\n💡 /buyw <number>"
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
    
    msg = f"🛒 {country} {ptype.upper()}\n\n"
    for p in players:
        msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
    msg += "\n💡 /buy <number>"
    await query.edit_message_text(msg)

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /buy <player_id>')
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
    
    name, price = player
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < price:
        await update.message.reply_text(f'❌ Need {price:,}, have {balance:,}')
        conn.close()
        return
    
    c.execute("SELECT * FROM user_players WHERE user_id=? AND player_id=? AND type='mens'", (user_id, player_id))
    if c.fetchone():
        await update.message.reply_text(f'❌ You already own {name}!')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (price, user_id))
    c.execute("INSERT INTO user_players (user_id, player_id, type) VALUES (?, ?, 'mens')", (user_id, player_id))
    conn.commit()
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"✅ PURCHASED!\n🏏 {name}\n💰 Price: {price:,}💰\n📊 New balance: {new_bal:,}")

async def buyw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /buyw <player_id>')
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
    
    name, price = player
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]
    
    if balance < price:
        await update.message.reply_text(f'❌ Need {price:,}, have {balance:,}')
        conn.close()
        return
    
    c.execute("SELECT * FROM user_players WHERE user_id=? AND player_id=? AND type='women'", (user_id, player_id))
    if c.fetchone():
        await update.message.reply_text(f'❌ You already own {name}!')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (price, user_id))
    c.execute("INSERT INTO user_players (user_id, player_id, type) VALUES (?, ?, 'women')", (user_id, player_id))
    conn.commit()
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(f"✅ PURCHASED!\n👩 {name}\n💰 Price: {price:,}💰\n📊 New balance: {new_bal:,}")

async def myteam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT s.name, s.price FROM user_players u JOIN shop s ON u.player_id = s.id WHERE u.user_id = ? AND u.type = 'mens'", (user_id,))
    mens = c.fetchall()
    
    c.execute("SELECT w.name, w.price FROM user_players u JOIN shop_women w ON u.player_id = w.id WHERE u.user_id = ? AND u.type = 'women'", (user_id,))
    women = c.fetchall()
    
    conn.close()
    
    if not mens and not women:
        await update.message.reply_text("📭 No players owned. Use /shop to buy!")
        return
    
    msg = "🏏 MY CRICKET TEAM\n\n━━━━━━━━━━━━━━━━━━━━━━\n👨 MENS"
    if mens:
        msg += f" ({len(mens)})\n\n"
        for i, p in enumerate(mens, 1):
            msg += f"{i}. {p[0]} - {p[1]:,} 💰\n"
        msg += f"\nTotal: {sum(p[1] for p in mens):,} 💰"
    else:
        msg += "\n\nNo mens players."
    
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n👩 WOMEN"
    if women:
        msg += f" ({len(women)})\n\n"
        for i, w in enumerate(women, 1):
            msg += f"{i}. {w[0]} - {w[1]:,} 💰\n"
        msg += f"\nTotal: {sum(w[1] for w in women):,} 💰"
    else:
        msg += "\n\nNo women players."
    
    total = sum(p[1] for p in mens) + sum(w[1] for w in women)
    msg += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n💰 GRAND TOTAL: {total:,} 💰"
    await update.message.reply_text(msg)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, balance FROM users ORDER BY balance DESC LIMIT 10")
    users = c.fetchall()
    conn.close()
    
    msg = "🏆 TOP 10 RICHEST\n\n"
    for i, u in enumerate(users, 1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        msg += f"{medal} {u[0]} - {u[1]:,} 💰\n"
    await update.message.reply_text(msg)

# ============ PART 5: BANK SYSTEM ============

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
    bank_bal = row[0] if row else 0
    last_interest = row[1] if row else None
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    wallet_bal = c.fetchone()[0]
    conn.close()
    
    next_time = "Available now"
    if last_interest:
        last = datetime.fromisoformat(last_interest)
        next_t = last + timedelta(hours=24)
        if datetime.now() < next_t:
            remaining = next_t - datetime.now()
            next_time = f"{remaining.seconds//3600}h {(remaining.seconds%3600)//60}m"
    
    await update.message.reply_text(
        f"🏦 MY BANK\n\n💰 Bank: {bank_bal:,}\n👛 Wallet: {wallet_bal:,}\n📈 Interest: 5% daily\n⏰ Next: {next_time}\n\n💡 /deposit <amount>\n💡 /withdraw <amount>\n💡 /claim_interest")

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /deposit <amount>')
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
    wallet = c.fetchone()[0]
    
    if wallet < amount:
        await update.message.reply_text(f'❌ Need {amount:,}, have {wallet:,}')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (amount, user_id))
    c.execute("UPDATE bank SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Deposited {amount:,} credits!")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text('❌ /withdraw <amount>')
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
    c.execute("SELECT balance FROM bank WHERE user_id=?", (user_id,))
    bank_bal = c.fetchone()
    
    if not bank_bal or bank_bal[0] < amount:
        await update.message.reply_text(f'❌ Insufficient bank balance!')
        conn.close()
        return
    
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    c.execute("UPDATE bank SET balance = balance - ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Withdrawn {amount:,} credits!")

async def claim_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, last_interest FROM bank WHERE user_id=?", (user_id,))
    row = c.fetchone()
    
    if not row:
        await update.message.reply_text('❌ No bank account! Use /bank first')
        conn.close()
        return
    
    bank_bal, last_interest = row
    now = datetime.now()
    
    if last_interest:
        last = datetime.fromisoformat(last_interest)
        if now < last + timedelta(hours=24):
            remaining = (last + timedelta(hours=24) - now)
            await update.message.reply_text(f"⏰ Come back in {remaining.seconds//3600}h")
            conn.close()
            return
    
    interest = int(bank_bal * 0.05)
    new_bank = bank_bal + interest
    c.execute("UPDATE bank SET balance = ?, last_interest = ? WHERE user_id=?", (new_bank, now.isoformat(), user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"💰 Interest claimed! +{interest:,} credits!\n🏦 New balance: {new_bank:,}")

# ============ PART 6: CLAIM CODE SYSTEM ============

async def createcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Usage: /createcode <amount> <code>\nExample: /createcode 1000 FESTIVAL10")
        return
    
    try:
        amount = int(args[0])
        code = args[1].upper()
    except:
        await update.message.reply_text("❌ Invalid!")
        return
    
    if amount < 100:
        await update.message.reply_text("❌ Minimum 100 credits!")
        return
    
    now = datetime.now()
    expires = now + timedelta(hours=24)
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT code FROM claim_codes WHERE code = ?", (code,))
    if c.fetchone():
        await update.message.reply_text(f"❌ Code '{code}' already exists!")
        conn.close()
        return
    
    c.execute("INSERT INTO claim_codes (code, amount, created_at, expires_at) VALUES (?, ?, ?, ?)",
              (code, amount, now.isoformat(), expires.isoformat()))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ CODE CREATED!\n🔑 {code}\n💰 {amount:,} credits\n⏰ Expires: 24 hours\n\n/claimcode {code}")

async def claimcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Usage: /claimcode <code>")
        return
    
    code = args[0].upper()
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT code, amount, max_claims, claimed_count, expires_at FROM claim_codes WHERE code = ?", (code,))
    result = c.fetchone()
    
    if not result:
        await update.message.reply_text(f"❌ Code '{code}' not found!")
        conn.close()
        return
    
    code_name, amount, max_claims, claimed_count, expires_at = result
    
    expires = datetime.fromisoformat(expires_at)
    if datetime.now() > expires:
        await update.message.reply_text(f"❌ Code expired!")
        conn.close()
        return
    
    c.execute("SELECT * FROM code_claims WHERE code = ? AND user_id = ?", (code, user_id))
    if c.fetchone():
        await update.message.reply_text(f"❌ You already claimed this code!")
        conn.close()
        return
    
    if claimed_count >= max_claims:
        await update.message.reply_text(f"❌ Code fully claimed!")
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
    
    await update.message.reply_text(f"🎉 CODE CLAIMED!\n🔑 {code}\n💰 +{amount:,} credits\n💳 Balance: {new_bal:,}\n👥 {remaining} claims left")

async def activecodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    now = datetime.now().isoformat()
    c.execute("SELECT code, amount, max_claims, claimed_count FROM claim_codes WHERE expires_at > ? AND claimed_count < max_claims", (now,))
    codes = c.fetchall()
    conn.close()
    
    if not codes:
        await update.message.reply_text("📭 No active codes!")
        return
    
    msg = "🎁 ACTIVE CODES\n\n"
    for code, amount, max_c, claimed in codes:
        remaining = max_c - claimed
        msg += f"🔑 {code} → {amount:,} credits ({remaining} left)\n"
    msg += "\n💡 /claimcode <code>"
    await update.message.reply_text(msg)

async def deletecode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Usage: /deletecode CODE123")
        return
    
    code = args[0].upper()
    
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM claim_codes WHERE code = ?", (code,))
    c.execute("DELETE FROM code_claims WHERE code = ?", (code,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Code '{code}' deleted!")

# ============ PART 7: BROADCAST & MAIN ============

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
        await update.message.reply_text("❌ Admin only!")
        return
    
    msg = update.message
    
    known_users = get_known_users()
    known_groups = get_known_groups()
    
    sent = 0
    failed = 0
    
    if msg.reply_to_message and msg.reply_to_message.photo:
        photo = msg.reply_to_message.photo[-1].file_id
        caption = msg.reply_to_message.caption or ""
        for uid in known_users:
            try:
                await context.bot.send_photo(uid, photo, caption=caption)
                sent += 1
            except:
                failed += 1
        for gid in known_groups:
            try:
                await context.bot.send_photo(gid, photo, caption=caption)
                sent += 1
            except:
                pass
        await update.message.reply_text(f"📸 Broadcast sent!\n👤 {sent} chats\n❌ {failed} failed")
        return
    
    if msg.reply_to_message and msg.reply_to_message.video:
        video = msg.reply_to_message.video.file_id
        caption = msg.reply_to_message.caption or ""
        for uid in known_users:
            try:
                await context.bot.send_video(uid, video, caption=caption)
                sent += 1
            except:
                failed += 1
        for gid in known_groups:
            try:
                await context.bot.send_video(gid, video, caption=caption)
                sent += 1
            except:
                pass
        await update.message.reply_text(f"🎥 Broadcast sent!\n👤 {sent} chats\n❌ {failed} failed")
        return
    
    if msg.reply_to_message:
        content = msg.reply_to_message.text or msg.reply_to_message.caption
    else:
        if not context.args:
            await msg.reply_text("Usage: /broadcast <message> or reply to photo/video")
            return
        content = " ".join(context.args)
    
    for uid in known_users:
        try:
            await context.bot.send_message(uid, content)
            sent += 1
        except:
            failed += 1
    
    for gid in known_groups:
        try:
            await context.bot.send_message(gid, content)
            sent += 1
        except:
            pass
    
    await msg.reply_text(f"📢 Broadcast sent!\n👤 {sent} chats\n❌ {failed} failed")

async def broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    users = get_known_users()
    groups = get_known_groups()
    
    await update.message.reply_text(f"📊 BROADCAST STATS\n\n👤 Users: {len(users)}\n👥 Groups: {len(groups)}\n📡 Total: {len(users) + len(groups)}")

async def track_all_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        group_id = update.message.chat.id
        group_name = update.message.chat.title or "Unknown"
        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO groups (group_id, group_name, added_at) VALUES (?, ?, datetime('now'))", (group_id, group_name))
        conn.commit()
        conn.close()

async def add_default_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("DELETE FROM shop")
    
    players = [
        ("Virat Kohli", 2000000, "India", "current"),
        ("Rohit Sharma", 1900000, "India", "current"),
        ("Shubman Gill", 1700000, "India", "current"),
        ("Hardik Pandya", 1800000, "India", "current"),
        ("Jasprit Bumrah", 2000000, "India", "current"),
        ("Pat Cummins", 1900000, "Australia", "current"),
        ("Steve Smith", 2000000, "Australia", "current"),
        ("Joe Root", 1800000, "England", "current"),
        ("Ben Stokes", 1900000, "England", "current"),
        ("Kane Williamson", 1900000, "New Zealand", "current"),
        ("Wanindu Hasaranga", 1600000, "Sri Lanka", "current"),
    ]
    
    for name, price, country, ptype in players:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Added {len(players)} players to shop!")

# ============ MAIN ==========

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Basic commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("setpfp", setpfp))
    app.add_handler(CommandHandler("rmpfp", rmpfp))
    app.add_handler(CommandHandler("claim", claim))
    app.add_handler(CommandHandler("spin", spin))
    
    # Games
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("flip", flip))
    
    # Betting
    app.add_handler(CommandHandler("matches", matches))
    app.add_handler(CommandHandler("bet", bet))
    app.add_handler(CommandHandler("mybets", mybets))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Shop
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("buyw", buyw))
    app.add_handler(CommandHandler("myteam", myteam))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_"))
    
    # Leaderboard
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    
    # Bank
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("claim_interest", claim_interest))
    
    # Claim Codes
    app.add_handler(CommandHandler("createcode", createcode))
    app.add_handler(CommandHandler("claimcode", claimcode))
    app.add_handler(CommandHandler("activecodes", activecodes))
    app.add_handler(CommandHandler("deletecode", deletecode))
    
    # Broadcast
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("broadcast_stats", broadcast_stats))
    app.add_handler(MessageHandler(filters.ChatType.GROUP | filters.ChatType.SUPERGROUP, track_all_groups))
    
    # Admin
    app.add_handler(CommandHandler("add_default_players", add_default_players))
    
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
