import asyncio
from telegram.ext import filters
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
import sqlite3
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
import os
import threading
from flask import Flask

TOKEN = "8533156744:AAE2Fesm35bggPg47V2UBjJolJnRsJ-pjVA"
ADMIN_IDS = [7687078555, 1315564307]

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is running!"

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 9090))  # 10000 → 9090
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
                 (user_id INTEGER PRIMARY KEY, name TEXT, balance INTEGER, points INTEGER, won INTEGER, total INTEGER, photo TEXT)''')
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
    c.execute('''CREATE TABLE IF NOT EXISTS farms
             (user_id INTEGER PRIMARY KEY,
              crops TEXT DEFAULT '[]',
              harvested TEXT DEFAULT '[]',
              total_grown INTEGER DEFAULT 0,
              total_earned INTEGER DEFAULT 0,
              total_profit INTEGER DEFAULT 0,
              chat_id INTEGER)''')

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

# ============ START (CL ZONE VIP Style) ============
# ============ START (CL ZONE VIP Style with Referral) ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.first_name if user.first_name else user.username or "User"
    user_id = user.id
    
    # Check for referral
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
        # Insert new user
        c.execute("INSERT INTO users (user_id, name, balance, points, won, total) VALUES (?, ?, 1000, 0, 0, 0)", (user_id, name))
        
        # Process referral if valid
        if referred_by and referred_by != user_id:
            c.execute("SELECT user_id FROM users WHERE user_id=?", (referred_by,))
            if c.fetchone():
                # Check if already referred
                c.execute("SELECT * FROM referrals WHERE user_id=?", (user_id,))
                if not c.fetchone():
                    # Add referral record
                    c.execute("INSERT INTO referrals (user_id, referred_by, referred_at) VALUES (?, ?, ?)",
                              (user_id, referred_by, datetime.now().isoformat()))
                    
                    # Add 1000 credits to referrer
                    c.execute("UPDATE users SET balance = balance + 1000 WHERE user_id=?", (referred_by,))
                    
                    # Add 500 bonus to new user
                    c.execute("UPDATE users SET balance = balance + 500 WHERE user_id=?", (user_id,))
                    
                    conn.commit()
                    
                    # Notify referrer
                    try:
                        await context.bot.send_message(referred_by, f"🎉 **REFERRAL REWARD!**\n\n@{name} joined using your link!\n💰 +1,000 credits!", parse_mode="Markdown")
                    except:
                        pass
                    
                    await update.message.reply_text(
                        f"🎉 **WELCOME!** 🎉\n\n"
                        f"You joined with a referral!\n"
                        f"💰 +500 bonus credits!\n\n"
                        f"✨ WELCOME TO CL ZONE ✨",
                        parse_mode="Markdown"
                    )
        
        conn.commit()
        
        # Keyboard buttons
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
        conn.close()
        
        # Keyboard buttons for existing users
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
            f"🏆 /leaderboard - Top players\n\n"
            f"📌 Stay connected with our community!",
            reply_markup=reply_markup
        )
    conn.close()

# ============ HELP ============
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
        "• /shop - Buy players (India, Aus, Eng, NZ, SL)\n"
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
        
        "🌾 FARM\n"
        "• /farm - Your farm\n"
        "• /crops - Crop prices\n"
        "• /grow <crop> <qty> - Grow crops\n"
        "• /harvest - Collect ready\n"
        "• /sell <crop> <qty> - Sell\n"
        "• /farm_stats - Your stats\n"
        "• /farm_leaderboard - Top farmers\n\n"
        
        "📦 STORAGE\n"
        "• /storage - Check space\n"
        "• /upgrade_storage - More slots\n\n"
        
        "👨‍🌾 WORKERS\n"
        "• /hire - Hire workers\n"
        "• /workers - Your workers\n\n"
        
        "🎮 GAMES\n"
        "• /ttt [amount] - Tic Tac Toe\n"
        "• /mines <amount> <bombs> - Mines game\n"
        "• /CLcricket [amount] - Cricket game\n"
        "• /rps [amount] - Rock Paper Scissors\n"
        "• /claimcode <code> - Claim rewards\n"
        "• /activecodes - Active codes\n"
        "• /numpuz - Number puzzle\n\n"
        "🎁 REFERRAL\n"
        "• /refer - Get your link (1k per refer)\n\n"
        
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Need help? @clbothelp"
    )
    
    # 🔥 NO parse_mode 🔥
    await update.message.reply_text(msg)

# ============ BIO FEATURE ============

async def setbio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "📝 **SET BIO**\n\n"
            "Usage: `/setbio <your bio>`\n"
            "Example: `/setbio Cricket lover 🏏`\n\n"
            "💡 Max 100 characters",
            parse_mode="Markdown"
        )
        return
    
    bio = " ".join(args)
    if len(bio) > 100:
        await update.message.reply_text("❌ Bio too long! Max 100 characters.")
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Add bio column if not exists
    try:
        c.execute("ALTER TABLE users ADD COLUMN bio TEXT")
    except:
        pass
    
    c.execute("UPDATE users SET bio = ? WHERE user_id = ?", (bio, user_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(f"✅ Bio updated!\n\n📝 {bio}")


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


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    user = update.effective_user
    name = user.first_name if user.first_name else user.username or "User"
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, points, won, total, photo, bio FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    
    # Get bank balance
    c.execute("SELECT balance FROM bank WHERE user_id=?", (user_id,))
    bank_row = c.fetchone()
    bank_bal = bank_row[0] if bank_row else 0
    
    conn.close()
    
    wallet_bal, points, won, total, photo, bio = data
    total_wealth = wallet_bal + bank_bal
    win_rate = int(won/total*100) if total > 0 else 0
    
    # Profile text with bio
    profile_text = f"👤 **PROFILE**\n\n**Name:** {name}\n"
    
    if bio:
        profile_text += f"**Bio:** {bio}\n\n"
    else:
        profile_text += f"\n"
    
    profile_text += (
        f"💰 Wallet: {wallet_bal:,} | 🏦 Bank: {bank_bal:,}\n"
        f"💰 Total: {total_wealth:,}\n"
        f"🏆 Points: {points}\n"
        f"📊 Bets: {won}/{total} ({win_rate}%)\n\n"
        f"🔄 /setpfp | ❌ /rmpfp | 📝 /setbio | ❌ /rmbio"
    )
    
    if photo:
        await update.message.reply_photo(photo=photo, caption=profile_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(profile_text, parse_mode="Markdown")


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
    conn = get_db()
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
    
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET photo=NULL WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text('❌ Profile photo removed!')

# ============ CLAIM ============
# ============ CLAIM ============
async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.message.chat.id
    chat_type = update.message.chat.type

    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    # 🔥 CL ZONE GROUP ID 🔥
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

    # 🔥 GROUP CHECK 🔥
    if chat_type in ['group', 'supergroup'] and chat_id == CL_GROUP_ID:
        reward = 1000
        extra_note = "\n\n✨ **BONUS:** You get 1000 credits in CL Zone Group!"
    else:
        reward = 500
        if chat_type in ['group', 'supergroup']:
            extra_note = f"\n\n💡 **Tip:** Use /claim in [CL Zone Group]({CL_GROUP_LINK}) to get 1000 credits!"
        else:
            extra_note = f"\n\n💡 **Tip:** Use /claim in [CL Zone Group]({CL_GROUP_LINK}) to get 1000 credits!"

    c.execute("INSERT OR REPLACE INTO claim (user_id, last_claim) VALUES (?, ?)", (user_id, today.isoformat()))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (reward, user_id))
    conn.commit()

    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()

    await update.message.reply_text(
        f"✅ **Claimed Daily Rewards!**\n\n"
        f"💰 +{reward} credits\n"
        f"📅 {today_str}\n"
        f"💳 New balance: {new_bal:,}{extra_note}\n\n"
        f"🔄 Next claim: tomorrow",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# ============ SPIN ============
# ============ SPIN (Updated - Claim Style) ============
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
            await update.message.reply_text(
                f"⚠️ Already spin today!\n"
                f"at {last.strftime('%m/%d/%y')}\n\n"
                f"🎡 Next spin: tomorrow"
            )
            conn.close()
            return
    
    amount = random.randint(1000, 10000)
    c.execute("INSERT OR REPLACE INTO spin (user_id, last_claim) VALUES (?, ?)", (user_id, now.isoformat()))
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    new_bal = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"✅ Claimed Daily Spin Rewards of {amount:,} Credits\n"
        f"at {today_str}\n\n"
        f"💰 New balance: {new_bal:,} 💰\n"
        f"🎡 Next spin: tomorrow"
    )

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

# ============ MYBETS ============
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
    c.execute("""
        SELECT b.id, b.amount, m.team1, m.team2, m.locked
        FROM bets b JOIN matches m ON b.match_id = m.id WHERE b.user_id = ? AND m.locked = 0
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

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Total wealth = wallet + bank
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
    
    # Current user total wealth
    c.execute("""
        SELECT u.balance + COALESCE(b.balance, 0)
        FROM users u
        LEFT JOIN bank b ON u.user_id = b.user_id
        WHERE u.user_id = ?
    """, (user_id,))
    user_total = c.fetchone()[0]
    
    rank = c.execute("""
        SELECT COUNT(*) + 1 FROM (
            SELECT u.balance + COALESCE(b.balance, 0) as total
            FROM users u
            LEFT JOIN bank b ON u.user_id = b.user_id
        ) WHERE total > ?
    """, (user_total,)).fetchone()[0]
    
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

# ============ HISTORY ============
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    user = get_user(user_id)
    win_rate = int(user[4]/user[5]*100) if user[5] > 0 else 0
    await update.message.reply_text(f'📜 BET HISTORY\n\n✅ Won: {user[4]}\n❌ Lost: {user[5]-user[4]}\n📊 Win Rate: {win_rate}%\n\n🏆 Fantasy Points: {user[3]}')

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

# ============ ADD DEFAULT PLAYERS (20 per category) ============
async def add_default_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add default players to shop - Admin only"""
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Clear existing
    c.execute("DELETE FROM shop")
    c.execute("DELETE FROM shop_women")
    
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
        ("Washington Sundar", 1300000, "India", "current"),
    ]
    
    # ========== INDIA LEGENDS (20) ==========
    india_legends = [
        ("Sachin Tendulkar", 2000000, "India", "legend"),
        ("MS Dhoni", 2000000, "India", "legend"),
        ("Rahul Dravid", 1800000, "India", "legend"),
        ("Sourav Ganguly", 1700000, "India", "legend"),
        ("Anil Kumble", 1600000, "India", "legend"),
        ("Kapil Dev", 1900000, "India", "legend"),
        ("Yuvraj Singh", 1750000, "India", "legend"),
        ("Virender Sehwag", 1650000, "India", "legend"),
        ("Zaheer Khan", 1500000, "India", "legend"),
        ("Harbhajan Singh", 1400000, "India", "legend"),
        ("Gautam Gambhir", 1350000, "India", "legend"),
        ("VVS Laxman", 1300000, "India", "legend"),
        ("Navjot Sidhu", 1000000, "India", "legend"),
        ("Kris Srikkanth", 950000, "India", "legend"),
        ("Venkatesh Prasad", 900000, "India", "legend"),
        ("Javagal Srinath", 1200000, "India", "legend"),
        ("Robin Singh", 850000, "India", "legend"),
        ("Ajay Jadeja", 880000, "India", "legend"),
        ("Nayan Mongia", 800000, "India", "legend"),
        ("Chetan Sharma", 780000, "India", "legend"),
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
        ("Tom Curran", 1080000, "England", "current"),
    ]
    
    # ========== ENGLAND LEGENDS (20) ==========
    england_legends = [
        ("Ian Botham", 2000000, "England", "legend"),
        ("Andrew Flintoff", 1900000, "England", "legend"),
        ("Kevin Pietersen", 1850000, "England", "legend"),
        ("Alastair Cook", 1700000, "England", "legend"),
        ("James Anderson", 1750000, "England", "legend"),
        ("Stuart Broad", 1650000, "England", "legend"),
        ("Graeme Swann", 1600000, "England", "legend"),
        ("Michael Vaughan", 1550000, "England", "legend"),
        ("Marcus Trescothick", 1500000, "England", "legend"),
        ("Paul Collingwood", 1450000, "England", "legend"),
        ("Alec Stewart", 1400000, "England", "legend"),
        ("Darren Gough", 1350000, "England", "legend"),
        ("Steve Harmison", 1300000, "England", "legend"),
        ("Matthew Hoggard", 1250000, "England", "legend"),
        ("Monty Panesar", 1200000, "England", "legend"),
        ("Nasser Hussain", 1400000, "England", "legend"),
        ("Graham Gooch", 1500000, "England", "legend"),
        ("David Gower", 1450000, "England", "legend"),
        ("Allan Lamb", 1300000, "England", "legend"),
        ("Derek Underwood", 1250000, "England", "legend"),
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
        ("Ben Sears", 1000000, "New Zealand", "current"),
    ]
    
    # ========== NEW ZEALAND LEGENDS (20) ==========
    nz_legends = [
        ("Brendon McCullum", 2000000, "New Zealand", "legend"),
        ("Richard Hadlee", 2000000, "New Zealand", "legend"),
        ("Martin Crowe", 1900000, "New Zealand", "legend"),
        ("Stephen Fleming", 1700000, "New Zealand", "legend"),
        ("Daniel Vettori", 1800000, "New Zealand", "legend"),
        ("Chris Cairns", 1650000, "New Zealand", "legend"),
        ("Nathan Astle", 1550000, "New Zealand", "legend"),
        ("Scott Styris", 1450000, "New Zealand", "legend"),
        ("Craig McMillan", 1400000, "New Zealand", "legend"),
        ("Jacob Oram", 1350000, "New Zealand", "legend"),
        ("Kyle Mills", 1300000, "New Zealand", "legend"),
        ("Tim Southee", 1400000, "New Zealand", "legend"),
        ("Ross Taylor", 1600000, "New Zealand", "legend"),
        ("John Wright", 1300000, "New Zealand", "legend"),
        ("Geoff Allott", 1100000, "New Zealand", "legend"),
        ("Shane Bond", 1500000, "New Zealand", "legend"),
        ("Dion Nash", 1200000, "New Zealand", "legend"),
        ("Mark Greatbatch", 1150000, "New Zealand", "legend"),
        ("Adam Parore", 1100000, "New Zealand", "legend"),
        ("Chris Harris", 1250000, "New Zealand", "legend"),
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
        ("Kane Richardson", 1100000, "Australia", "current"),
    ]
    
    # ========== AUSTRALIA LEGENDS (20) ==========
    australia_legends = [
        ("Ricky Ponting", 2000000, "Australia", "legend"),
        ("Adam Gilchrist", 2000000, "Australia", "legend"),
        ("Shane Warne", 2000000, "Australia", "legend"),
        ("Glenn McGrath", 1950000, "Australia", "legend"),
        ("Matthew Hayden", 1850000, "Australia", "legend"),
        ("Brett Lee", 1800000, "Australia", "legend"),
        ("Michael Clarke", 1750000, "Australia", "legend"),
        ("Andrew Symonds", 1700000, "Australia", "legend"),
        ("Steve Waugh", 1950000, "Australia", "legend"),
        ("Mark Waugh", 1600000, "Australia", "legend"),
        ("Ian Healy", 1500000, "Australia", "legend"),
        ("Craig McDermott", 1450000, "Australia", "legend"),
        ("Jason Gillespie", 1550000, "Australia", "legend"),
        ("Damien Martyn", 1400000, "Australia", "legend"),
        ("Justin Langer", 1350000, "Australia", "legend"),
        ("Michael Hussey", 1650000, "Australia", "legend"),
        ("Shane Watson", 1550000, "Australia", "legend"),
        ("Brad Haddin", 1300000, "Australia", "legend"),
        ("Stuart Clark", 1250000, "Australia", "legend"),
        ("Nathan Bracken", 1200000, "Australia", "legend"),
    ]
    
    # ========== WOMEN (20) ==========
    women_players = [
        ("Smriti Mandhana", 1500000, "Women", "women"),
        ("Harmanpreet Kaur", 1400000, "Women", "women"),
        ("Jemimah Rodrigues", 1300000, "Women", "women"),
        ("Shafali Verma", 1350000, "Women", "women"),
        ("Deepti Sharma", 1250000, "Women", "women"),
        ("Poonam Yadav", 1150000, "Women", "women"),
        ("Richa Ghosh", 1200000, "Women", "women"),
        ("Shefali Verma", 1100000, "Women", "women"),
        ("Meg Lanning", 1600000, "Women", "women"),
        ("Ellyse Perry", 1800000, "Women", "women"),
        ("Alyssa Healy", 1550000, "Women", "women"),
        ("Sophie Devine", 1650000, "Women", "women"),
        ("Amelia Kerr", 1450000, "Women", "women"),
        ("Suzy Bates", 1500000, "Women", "women"),
        ("Natalie Sciver", 1550000, "Women", "women"),
        ("Heather Knight", 1500000, "Women", "women"),
        ("Tammy Beaumont", 1400000, "Women", "women"),
        ("Marizanne Kapp", 1450000, "Women", "women"),
        ("Laura Wolvaardt", 1350000, "Women", "women"),
        ("Tahlia McGrath", 1400000, "Women", "women"),
    ]
    
    # Insert India Current
    for name, price, country, ptype in india_current:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # Insert India Legends
    for name, price, country, ptype in india_legends:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # Insert England Current
    for name, price, country, ptype in england_current:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # Insert England Legends
    for name, price, country, ptype in england_legends:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # Insert New Zealand Current
    for name, price, country, ptype in nz_current:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # Insert New Zealand Legends
    for name, price, country, ptype in nz_legends:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # Insert Australia Current
    for name, price, country, ptype in australia_current:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # Insert Australia Legends
    for name, price, country, ptype in australia_legends:
        c.execute("INSERT INTO shop (name, price, category, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    # Insert Women
    for name, price, country, ptype in women_players:
        c.execute("INSERT INTO shop_women (name, price, country, type) VALUES (?, ?, ?, ?)", (name, price, country, ptype))
    
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM shop")
    shop_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM shop_women")
    women_count = c.fetchone()[0]
    
    conn.close()
    
    await update.message.reply_text(
        f"✅ **20 PLAYERS ADDED PER CATEGORY!**\n\n"
        f"🏏 Total Men: {shop_count}\n"
        f"👩 Total Women: {women_count}\n\n"
        f"🇮🇳 India: 40 (20 Current + 20 Legends)\n"
        f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 England: 40 (20 Current + 20 Legends)\n"
        f"🇳🇿 New Zealand: 40 (20 Current + 20 Legends)\n"
        f"🇦🇺 Australia: 40 (20 Current + 20 Legends)\n"
        f"👩 Women: 20\n\n"
        f"💰 Prices: 780,000 - 2,000,000",
        parse_mode="Markdown"
    )



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
# ============ ADMIN: SET PRICE FOR SHOP1 ============
async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set price for any player - Admin only"""
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "📝 **SET PRICE**\n\n"
            "Usage: `/setprice <player_id> <new_price>`\n"
            "Example: `/setprice 1 2500000`\n\n"
            "Use `/shop` to see player IDs",
            parse_mode="Markdown"
        )
        return
    
    try:
        player_id = int(args[0])
        new_price = int(args[1])
    except:
        await update.message.reply_text('❌ Invalid input!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Check in shop1
    c.execute("SELECT name FROM shop WHERE id=?", (player_id,))
    player = c.fetchone()
    
    if not player:
        await update.message.reply_text(f'❌ Player ID {player_id} not found!')
        conn.close()
        return
    
    c.execute("UPDATE shop SET price = ? WHERE id=?", (new_price, player_id))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ **PRICE UPDATED!**\n\n"
        f"🏏 {player[0]}\n"
        f"💰 Old: {old_price:,} → New: {new_price:,}",
        parse_mode="Markdown"
    )

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
            await query.edit_message_text("👩 WOMEN CRICKETEBNC\n\nNo players yet!")
            return
        
        msg = "👩 WOMEN CRICKETEBNC\n\n"
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

async def myteam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    # Mens players (shop)
    c.execute("SELECT p.name, p.price FROM user_players u JOIN shop p ON u.player_id=p.id WHERE u.user_id=? AND u.type='mens'", (user_id,))
    mens = c.fetchall()
    
    # Women players
    c.execute("SELECT w.name, w.price FROM user_players u JOIN shop_women w ON u.player_id=w.id WHERE u.user_id=? AND u.type='women'", (user_id,))
    women = c.fetchall()
    
    # Shop2 (affordable)
    c.execute("SELECT s.name, s.price FROM user_players2 u JOIN shop2 s ON u.player_id=s.id WHERE u.user_id=?", (user_id,))
    affordable = c.fetchall()
    
    # 🔥 SHOP3 ADD KARO 🔥
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
    
    # 🔥 SHOP3 SECTION 🔥
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
    
    await update.message.reply_text(msg, parse_mode="Markdown")

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
    msg = "🛍️ **MY AFFORDABLE PLAYERS**\n\n"
    for i, p in enumerate(players, 1):
        msg += f"{i}. {p[0]} - {p[1]:,} 💰\n"
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💰 Total spent: {total:,} 💰"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


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
    
    await update.message.reply_text(msg, parse_mode="Markdown")


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

    for i, p in enumerate(mens, 1):
            msg += f"{i}. {p[0]} - {p[1]:,} 💰\n"
    msg += f"\nTotal: {mens_total:,} 💰"
    msg += "\n\nNo mens players. /shop to buy!"
    
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n🤑 AFFORDABLE"
    if shop2:
        msg += f" ({len(shop2)})\n\n"
        for i, c in enumerate(shop2, 1):
            msg += f"{i}. {c[0]} - {c[1]:,} 💰\n"
        msg += f"\nTotal: {shop2_total:,} 💰"
    else:
        msg += "\n\nNo shop2 players. /shop2 to buy!"
    
    msg += "\n\n━━━━━━━━━━━━━━━━━━━━━━\n👩 WOMEN"
    if women:
        msg += f" ({len(women)})\n\n"
        for i, w in enumerate(women, 1):
            msg += f"{i}. {w[0]} - {w[1]:,} 💰\n"
        msg += f"\nTotal: {women_total:,} 💰"
    else:
        msg += "\n\nNo women players. /shop women section"
    
    grand_total = mens_total + shop2_total + women_total
    total_players = len(mens) + len(shop2) + len(women)
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
        if t[0] == update.effective_user.first_name:  # ← COLON YAHAN HONA CHAHIYE
            rank = i
            break
    else:
        rank = len(tops) + 1
    
    msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Your rank: #{rank}\n💰 Collection value: {total_value:,} 💰\n🏆 Players: {player_count}"
    await update.message.reply_text(msg)
    conn.close()

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

# ============ ADMIN: DELETE MATCH WITH REFUND ============
async def deletematch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete match and optionally refund all bets - Admin only"""
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "❌ USAGE:\n"
            "/deletematch TEAM1 vs TEAM2\n"
            "/deletematch TEAM1 vs TEAM2 refund\n\n"
            "💡 Add 'refund' to return credits to all bettors"
        )
        return
    
    team1 = args[0].upper()
    team2 = args[2].upper()
    do_refund = len(args) > 3 and args[3].lower() == 'refund'
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2 FROM matches WHERE (team1=? AND team2=?)", (team1, team2))
    match = c.fetchone()
    
    if not match:
        await update.message.reply_text(f'❌ Match not found: {team1} vs {team2}')
        conn.close()
        return
    
    # Get all bets for refund calculation
    c.execute("SELECT user_id, amount FROM bets WHERE match_id=?", (match[0],))
    bets = c.fetchall()
    
    refund_count = 0
    refund_total = 0
    
    # Process refund if requested
    if do_refund and bets:
        for bet in bets:
            user_id, amount = bet
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
            refund_count += 1
            refund_total += amount
        
        # Also update total bets count for users
        c.execute("UPDATE users SET total = total - ? WHERE user_id IN (SELECT user_id FROM bets WHERE match_id=?)", (refund_count, match[0]))
        conn.commit()
    
    # Delete bets and match
    c.execute("DELETE FROM bets WHERE match_id=?", (match[0],))
    c.execute("DELETE FROM matches WHERE id=?", (match[0],))
    conn.commit()
    conn.close()
    
    # Response message
    if do_refund and refund_count > 0:
        await update.message.reply_text(
            f"🗑️ MATCH DELETED + REFUNDED!\n\n"
            f"🏏 {match[1]} vs {match[2]}\n"
            f"💰 Refunded: {refund_count} users\n"
            f"💰 Total refund: {refund_total:,} credits\n\n"
            f"✅ All bettors got their money back!"
        )
    elif do_refund and refund_count == 0:
        await update.message.reply_text(
            f"🗑️ MATCH DELETED!\n\n"
            f"🏏 {match[1]} vs {match[2]}\n"
            f"ℹ️ No bets to refund"
        )
    else:
        await update.message.reply_text(
            f"🗑️ MATCH DELETED WITHOUT REFUND!\n\n"
            f"🏏 {match[1]} vs {match[2]}\n"
            f"⚠️ {len(bets)} users lost their bets!\n\n"
            f"💡 Next time use: /deletematch {team1} vs {team2} refund"
        )

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
            
            c.execute("UPDATE users SET balance = ?, won = ?, points = ? WHERE user_id=?", 
                     (new_balance, new_won, new_points, user_id))
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
    msg += f"✅ WINNEBNC (+10 pts max): {winners} users\n"
    for w in winner_list[:5]:
        msg += f"   • {w}\n"
    if len(winner_list) > 5:
        msg += f"   • +{len(winner_list)-5} more\n"
    
    msg += f"\n❌ LOSEBNC (-5 pts max): {losers} users\n"
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
        await update.message.reply_text('❌ /setprice <player_id> <new_price>\nExample: /setprice 1 1500000')
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

# ============ ACHIEVEMENTS ============
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

# ============ ADMIN SHOP2 ============
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
        await update.message.reply_text('❌ /setprice2 <id> <new_price>\nExample: /setprice2 1 15000')
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
        await update.message.reply_text('❌ /removeplayer2 <id>\nExample: /removeplayer2 1')
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

# ============ SHOP3 (AFFORDABLEEST PLAYERS) ==========

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

    await update.message.reply_text(msg)

async def top3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(s.price), 0) as total
        FROM users u
        JOIN user_players3 up ON u.user_id = up.user_id
        JOIN shop3 s ON up.player_id = s.id
        GROUP BY u.user_id
        ORDER BY total DESC LIMIT 10
    """)
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

# ============ ADMIN SHOP3 ============
async def addplayer3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /addplayer3 <name> <price>\nExample: /addplayer3 "Player Name" 5000')
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
        await update.message.reply_text('❌ /setprice3 <id> <new_price>\nExample: /setprice3 1 8000')
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
        await update.message.reply_text('❌ /removeplayer3 <id>\nExample: /removeplayer3 1')
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

# ============ BROADCAST SYSTEM (Admin Only) ============

def get_known_users():
    """Get all users who have started the bot"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_known_groups():
    """Get all groups where bot has been added"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS groups 
                 (group_id INTEGER PRIMARY KEY, group_name TEXT, added_at TEXT)''')
    c.execute("SELECT group_id FROM groups")
    groups = [row[0] for row in c.fetchall()]
    conn.close()
    return groups

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send broadcast to all users and groups - ADMIN ONLY"""
    
    user = update.effective_user
    
    # 🔥 ADMIN CHECK 🔥
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ ONLY ADMIN CAN USE THIS COMMAND!\n\n👑 Admin ID: 7687078555")
        return
    
    msg = update.message
    
    known_users = get_known_users()
    known_groups = get_known_groups()
    
    sent_users = 0
    sent_groups = 0
    failed = 0
    
    # ========== PHOTO BROADCAST ==========
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
        
        await update.message.reply_text(
            f"📸 PHOTO BROADCAST SENT!\n\n"
            f"👤 Users: {sent_users}\n"
            f"👥 Groups: {sent_groups}\n"
            f"❌ Failed: {failed}\n"
            f"📊 Total: {sent_users + sent_groups}"
        )
        return
    
    # ========== VIDEO BROADCAST ==========
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
        
        await update.message.reply_text(
            f"🎥 VIDEO BROADCAST SENT!\n\n"
            f"👤 Users: {sent_users}\n"
            f"👥 Groups: {sent_groups}\n"
            f"❌ Failed: {failed}"
        )
        return
    
    # ========== TEXT BROADCAST ==========
    if msg.reply_to_message:
        content = msg.reply_to_message.text or msg.reply_to_message.caption
    else:
        if not context.args:
            await msg.reply_text(
                "📢 BROADCAST USAGE (ADMIN ONLY):\n\n"
                "📝 TEXT:\n"
                "   /broadcast Hello everyone!\n\n"
                "🖼️ PHOTO:\n"
                "   Reply to a photo with /broadcast\n\n"
                "🎥 VIDEO:\n"
                "   Reply to a video with /broadcast\n\n"
                "📊 STATS:\n"
                "   /broadcast_stats"
            )
            return
        content = " ".join(context.args)
    
    # Send to USEBNC
    for uid in known_users:
        try:
            await context.bot.send_message(uid, content)
            sent_users += 1
        except:
            failed += 1
    
    # Send to GROUPS
    for gid in known_groups:
        try:
            await context.bot.send_message(gid, content)
            sent_groups += 1
        except:
            pass
    
    await msg.reply_text(
        f"📢 BROADCAST SENT!\n\n"
        f"👤 Users: {sent_users}\n"
        f"👥 Groups: {sent_groups}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total reached: {sent_users + sent_groups}"
    )


# ============ BROADCAST STATS ============
async def broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check broadcast reach - ADMIN ONLY"""
    
    user = update.effective_user
    
    # 🔥 ADMIN CHECK 🔥
    if user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ ONLY ADMIN CAN USE THIS COMMAND!")
        return
    
    known_users = get_known_users()
    known_groups = get_known_groups()
    
    await update.message.reply_text(
        f"📊 BROADCAST REACH STATS\n\n"
        f"👤 Total Users: {len(known_users)}\n"
        f"👥 Total Groups: {len(known_groups)}\n"
        f"📡 Total Reach: {len(known_users) + len(known_groups)}\n\n"
        f"👑 Admin IDs: {ADMIN_IDS}\n\n"
        f"💡 Use /broadcast to send message to everyone!"
    )

# ============ ADMIN: UNLOCK MATCH ============
async def unlockmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unlock a locked match - Admin only"""
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 3:
        await update.message.reply_text('❌ /unlockmatch TEAM1 vs TEAM2\nExample: /unlockmatch IND vs AUS')
        return
    
    team1 = args[0].upper()
    team2 = args[2].upper()
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, team1, team2, locked FROM matches WHERE (team1=? AND team2=?)", (team1, team2))
    match = c.fetchone()
    
    if not match:
        await update.message.reply_text(f'❌ Match not found: {team1} vs {team2}')
        conn.close()
        return
    
    if match[3] == 0:
        await update.message.reply_text(f'⚠️ Match is already UNLOCKED!\n\n🏏 {match[1]} vs {match[2]}')
        conn.close()
        return
    
    # Unlock the match
    c.execute("UPDATE matches SET locked=0 WHERE id=?", (match[0],))
    conn.commit()
    
    # Get bet count
    c.execute("SELECT COUNT(*), SUM(amount) FROM bets WHERE match_id=?", (match[0],))
    result = c.fetchone()
    count = result[0] or 0
    total = result[1] or 0
    
    conn.close()
    
    await update.message.reply_text(
        f"🔓 MATCH UNLOCKED!\n\n"
        f"🏏 {match[1]} vs {match[2]}\n"
        f"📊 Current Bets: {count}\n"
        f"💰 Current Pool: {total:,} 💰\n\n"
        f"✅ New bets are now accepted again!"
    )

# ============ CLAIM CODE SYSTEM (COMPLETE) ============

# ============ GROUP TRACKING FUNCTIONS (Add these before main()) ============

async def track_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-track groups where bot is added"""
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        group_id = update.message.chat.id
        group_name = update.message.chat.title or "Unknown Group"
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS groups 
                     (group_id INTEGER PRIMARY KEY, 
                      group_name TEXT, 
                      added_at TEXT)''')
        c.execute("INSERT OR IGNORE INTO groups (group_id, group_name, added_at) VALUES (?, ?, ?)",
                  (group_id, group_name, datetime.now().isoformat()))
        conn.commit()
        conn.close()

async def new_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-add group when bot is added"""
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                group_id = update.message.chat.id
                group_name = update.message.chat.title or "Unknown Group"
                
                conn = get_db()
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS groups 
                             (group_id INTEGER PRIMARY KEY, 
                              group_name TEXT, 
                              added_at TEXT)''')
                c.execute("INSERT OR IGNORE INTO groups (group_id, group_name, added_at) VALUES (?, ?, ?)",
                          (group_id, group_name, datetime.now().isoformat()))
                conn.commit()
                conn.close()
                break

async def left_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-remove group when bot is removed"""
    if update.message.left_chat_member and update.message.left_chat_member.id == context.bot.id:
        group_id = update.message.chat.id
        
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
        conn.commit()
        conn.close()

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
    print("✅ Claim code tables ready!")

# Call this after init_db()
init_claimcode_db()


# ============ ADMIN: CREATE CODE ============
async def createcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "📝 **CREATE CODE**\n\n"
            "Usage: `/createcode <amount> <code>`\n"
            "Example: `/createcode 1000 FESTIVAL10`\n\n"
            "💰 Amount: 100-10000 credits\n"
            "🔑 Code: Any word/number\n"
            "👥 Max: 5 claims\n"
            "⏰ Expires: 24 hours",
            parse_mode="Markdown"
        )
        return
    
    try:
        amount = int(args[0])
        code = args[1].upper()
        max_claims = 5
    except:
        await update.message.reply_text("❌ Invalid! Use: /createcode 1000 CODE123")
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
    
    c.execute("""INSERT INTO claim_codes 
                 (code, amount, max_claims, created_by, created_at, expires_at)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (code, amount, max_claims, user_id, now.isoformat(), expires_at.isoformat()))
    
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ **CODE CREATED!**\n\n"
        f"🔑 Code: `{code}`\n"
        f"💰 Amount: {amount:,} credits\n"
        f"👥 Max claims: {max_claims} users\n"
        f"⏰ Expires: 24 hours\n\n"
        f"Users can claim with: `/claimcode {code}`",
        parse_mode="Markdown"
    )


# ============ USER: CLAIM CODE ============
async def claimcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "❌ **Usage:** `/claimcode <code>`\n"
            "Example: `/claimcode FESTIVAL10`",
            parse_mode="Markdown"
        )
        return
    
    code = args[0].upper()
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT code, amount, max_claims, claimed_count, expires_at FROM claim_codes WHERE code = ?", (code,))
    result = c.fetchone()
    
    if not result:
        await update.message.reply_text(f"❌ Code `{code}` not found!\n💡 Try `/activecodes`", parse_mode="Markdown")
        conn.close()
        return
    
    code_name, amount, max_claims, claimed_count, expires_at = result
    
    expires = datetime.fromisoformat(expires_at)
    if datetime.now() > expires:
        await update.message.reply_text(f"❌ Code `{code}` has expired!", parse_mode="Markdown")
        conn.close()
        return
    
    c.execute("SELECT * FROM code_claims WHERE code = ? AND user_id = ?", (code, user_id))
    if c.fetchone():
        await update.message.reply_text(f"❌ You already claimed code `{code}`!", parse_mode="Markdown")
        conn.close()
        return
    
    if claimed_count >= max_claims:
        await update.message.reply_text(f"❌ Code `{code}` has reached max claims!", parse_mode="Markdown")
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
    
    await update.message.reply_text(
        f"🎉 **CODE CLAIMED!**\n\n"
        f"🔑 Code: `{code}`\n"
        f"💰 +{amount:,} credits\n"
        f"💳 New balance: {new_bal:,}\n"
        f"📊 Remaining: {remaining}/{max_claims}",
        parse_mode="Markdown"
    )


# ============ VIEW ACTIVE CODES ============
async def activecodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    
    now = datetime.now().isoformat()
    c.execute("""SELECT code, amount, max_claims, claimed_count, expires_at 
                 FROM claim_codes 
                 WHERE expires_at > ? AND claimed_count < max_claims
                 ORDER BY created_at DESC LIMIT 10""", (now,))
    
    codes = c.fetchall()
    conn.close()
    
    if not codes:
        await update.message.reply_text(
            "📭 **NO ACTIVE CODES**\n\n"
            "No codes available right now!\n"
            "Check back later for rewards! 🎁",
            parse_mode="Markdown"
        )
        return
    
    msg = "🎁 **ACTIVE CLAIM CODES**\n\n"
    for code, amount, max_c, claimed, expires in codes:
        remaining = max_c - claimed
        msg += f"🔑 `{code}`\n"
        msg += f"💰 {amount:,} credits\n"
        msg += f"👥 {remaining}/{max_c} left\n"
        msg += f"💡 `/claimcode {code}`\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Use `/claimcode <code>` to claim!"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


# ============ ADMIN: DELETE CODE ============
async def deletecode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
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


# ============ ADMIN: CODE STATS ============
async def codestats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
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
    
    await update.message.reply_text(
        f"📊 **CODE STATS**\n\n"
        f"📝 Total codes: {total_codes}\n"
        f"🟢 Active codes: {active_codes}\n"
        f"🎯 Total claims: {total_claims}\n"
        f"💰 Credits given: {total_given:,}\n"
        f"👥 Unique users: {unique_users}",
        parse_mode="Markdown"
    )

# ============ FARM LAND GAME ============

import json
import random
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ContextTypes

# ============ CROP DATA ============
CROPS = {
    "potato": {"name": "🥔 Potato", "price": 1000, "sell": 1500, "time": 30, "emoji": "🥔"},
    "carrot": {"name": "🥕 Carrot", "price": 2000, "sell": 3000, "time": 60, "emoji": "🥕"},
    "tomato": {"name": "🍅 Tomato", "price": 3000, "sell": 4500, "time": 120, "emoji": "🍅"},
    "corn": {"name": "🌽 Corn", "price": 5000, "sell": 7500, "time": 240, "emoji": "🌽"},
    "wheat": {"name": "🌾 Wheat", "price": 7000, "sell": 10500, "time": 360, "emoji": "🌾"},
    "strawberry": {"name": "🍓 Strawberry", "price": 8000, "sell": 12000, "time": 480, "emoji": "🍓"},
    "watermelon": {"name": "🍉 Watermelon", "price": 10000, "sell": 15000, "time": 720, "emoji": "🍉"},
}

# ============ GLOBAL VARIABLES ============
rain_percentage = 0

# ============ DATABASE INIT ============
def init_farm_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS farms
                 (user_id INTEGER PRIMARY KEY,
                  crops TEXT DEFAULT '[]',
                  harvested TEXT DEFAULT '[]',
                  total_grown INTEGER DEFAULT 0,
                  total_earned INTEGER DEFAULT 0,
                  total_profit INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_farm_db()

# ============ HELPER FUNCTIONS ============
def format_time(minutes):
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins}m"

def get_grow_time(crop_time):
    global rain_percentage
    if rain_percentage > 0:
        # Direct percentage discount
        discount = (crop_time * rain_percentage) / 100
        reduced = crop_time - discount
        return int(max(1, reduced))  # Minimum 1 minute
    return crop_time

# ============ COMMANDS ============
# ============ CROPS DATA ============
CROPS = {
    "potato": {"name": "🥔 Potato", "price": 1000, "sell": 1500, "time": 30, "emoji": "🥔"},
    "carrot": {"name": "🥕 Carrot", "price": 2000, "sell": 3000, "time": 60, "emoji": "🥕"},
    "tomato": {"name": "🍅 Tomato", "price": 3000, "sell": 4500, "time": 120, "emoji": "🍅"},
    "corn": {"name": "🌽 Corn", "price": 5000, "sell": 7500, "time": 240, "emoji": "🌽"},
    "wheat": {"name": "🌾 Wheat", "price": 7000, "sell": 10500, "time": 360, "emoji": "🌾"},
    "strawberry": {"name": "🍓 Strawberry", "price": 8000, "sell": 12000, "time": 480, "emoji": "🍓"},
    "watermelon": {"name": "🍉 Watermelon", "price": 10000, "sell": 15000, "time": 720, "emoji": "🍉"},
    "orange": {"name": "🍊 Orange", "price": 12000, "sell": 18000, "time": 960, "emoji": "🍊"},
    "mango": {"name": "🥭 Mango", "price": 20000, "sell": 30000, "time": 1440, "emoji": "🥭"},
    "ganja": {"name": "🌿 Ganja", "price": 14000, "sell": 21000, "time": 720, "emoji": "🌿"},
}

# ============ CROPS COMMAND ============
async def crops(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    msg = "🌾 *CROP MARKET*\n\n```\n"
    msg += "🥔 Potato      💰1,000  →  💰1,500  (30m)\n"
    msg += "🥕 Carrot      💰2,000  →  💰3,000  (1h)\n"
    msg += "🍅 Tomato      💰3,000  →  💰4,500  (2h)\n"
    msg += "🌽 Corn        💰5,000  →  💰7,500  (4h)\n"
    msg += "🌾 Wheat       💰7,000  →  💰10,500 (6h)\n"
    msg += "🍓 Strawberry  💰8,000  →  💰12,000 (8h)\n"
    msg += "🍉 Watermelon  💰10,000 →  💰15,000 (12h)\n"
    msg += "🍊 Orange      💰12,000 →  💰18,000 (16h)\n"
    msg += "🥭 Mango       💰20,000 →  💰30,000 (24h)\n"
    msg += "🌿 Ganja       💰14,000 →  💰21,000 (12h)\n"
    msg += "```\n💡 /grow <crop> <quantity>"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def grow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Usage: /grow <crop> <quantity>\nExample: /grow watermelon 5")
        return

    crop_name = args[0].lower()
    try:
        quantity = int(args[1])
    except:
        await update.message.reply_text("❌ Invalid quantity!")
        return

    if crop_name not in CROPS:
        await update.message.reply_text(f"❌ Unknown crop! Use /crops to see available crops.")
        return

    if quantity < 1 or quantity > 100:
        await update.message.reply_text("❌ Quantity must be between 1 and 100!")
        return

    crop = CROPS[crop_name]
    total_cost = crop['price'] * quantity

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]

    if balance < total_cost:
        await update.message.reply_text(f"❌ Need {total_cost:,} credits!\n💰 Have: {balance:,}\n💡 /claim or /spin to earn more!")
        conn.close()
        return

    # 🔥 STORAGE CHECK 🔥
    c.execute("SELECT level, crops FROM user_storage WHERE user_id = ?", (user_id,))
    storage_result = c.fetchone()
    
    if storage_result:
        level = storage_result[0]
        crops_stored = json.loads(storage_result[1]) if storage_result[1] else {}
    else:
        level = 1
        crops_stored = {}
    
    total_slots = get_total_slots(level)
    used_slots = sum(crops_stored.values())
    free_slots = total_slots - used_slots
    
    if quantity > free_slots:
        await update.message.reply_text(
            f"❌ NOT ENOUGH STORAGE!\n\n"
            f"Need: {quantity} slots\n"
            f"Free: {free_slots} slots\n"
            f"Total: {used_slots}/{total_slots}\n\n"
            f"💡 /upgrade_storage to increase capacity\n"
            f"💡 /sell to free up space"
        )
        conn.close()
        return

    # Deduct cost
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (total_cost, user_id))

    # Get farm data
    c.execute("SELECT crops, harvested, total_grown, total_earned, total_profit FROM farms WHERE user_id=?", (user_id,))
    farm = c.fetchone()

    if farm:
        crops_data = json.loads(farm[0]) if farm[0] else []
        harvested_data = json.loads(farm[1]) if farm[1] else []
        total_grown = farm[2] or 0
        total_earned = farm[3] or 0
        total_profit = farm[4] or 0
    else:
        crops_data = []
        harvested_data = []
        total_grown = 0
        total_earned = 0
        total_profit = 0

    # Add new crops with rain effect
    now = datetime.now()
    grow_time = get_grow_time(crop['time'])

    for i in range(quantity):
        crops_data.append({
            "crop": crop_name,
            "planted": now.isoformat(),
            "ready_time": (now + timedelta(minutes=grow_time)).isoformat()
        })

    c.execute("INSERT OR REPLACE INTO farms (user_id, crops, harvested, total_grown, total_earned, total_profit) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, json.dumps(crops_data), json.dumps(harvested_data), total_grown + quantity, total_earned, total_profit))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"🌱 **GROWING {crop['emoji']} {crop['name']} x{quantity}**\n\n"
        f"💰 Cost: {total_cost:,} credits deducted\n"
        f"⏰ Ready in: {format_time(grow_time)}\n"
        f"📦 Storage: {used_slots}/{total_slots} → {used_slots + quantity}/{total_slots}\n"
        f"💡 /farm - Check status\n"
        f"💡 /harvest - When ready",
        parse_mode="Markdown"
    )

async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    balance = c.fetchone()[0]

    # Get farm data (manually grown)
    c.execute("SELECT crops, harvested FROM farms WHERE user_id=?", (user_id,))
    farm = c.fetchone()

    # Get storage data (auto-grown by workers)
    c.execute("SELECT crops FROM user_storage WHERE user_id=?", (user_id,))
    storage = c.fetchone()
    conn.close()

    # Manual growing crops
    crops_data = json.loads(farm[0]) if farm and farm[0] else []
    harvested_data = json.loads(farm[1]) if farm and farm[1] else []

    # Auto-grown crops from workers
    storage_crops = json.loads(storage[0]) if storage and storage[0] else {}

    now = datetime.now()
    growing = []
    ready = []

    # Check manually grown crops
    for crop in crops_data:
        ready_time = datetime.fromisoformat(crop['ready_time'])
        crop_info = CROPS[crop['crop']]
        if now >= ready_time:
            ready.append(crop)
        else:
            remaining = (ready_time - now).total_seconds() / 60
            growing.append((crop_info, remaining, crop))

    msg = f"🌾 **YOUR FARM**\n\n💰 Wallet: {balance:,} credits\n"

    global rain_percentage
    if rain_percentage > 0:
        msg += f"🌧️ Rain: {rain_percentage}% faster\n"

    msg += "\n"

    # 🔥 SHOW AUTO-GROWN CROPS FROM WORKEBNC 🔥
    if storage_crops:
        msg += "🤖 **WORKER CROPS (Auto-Grown - Ready to Sell):**\n"
        for crop_name, count in storage_crops.items():
            crop = CROPS.get(crop_name)
            if crop:
                msg += f"   {crop['emoji']} {crop['name']} x{count}\n"
        msg += "\n💡 /sell <crop> <quantity> to sell\n\n"

    if growing:
        msg += "🌿 **GROWING (Manual):**\n"
        for crop_info, remaining, _ in growing[:5]:
            msg += f"   {crop_info['emoji']} {crop_info['name']} → Ready in: {format_time(int(remaining))}\n"
        if len(growing) > 5:
            msg += f"   +{len(growing)-5} more\n"
        msg += "\n"

    if ready:
        msg += "🌾 **READY TO HARVEST (Manual):**\n"
        ready_count = {}
        for crop in ready:
            crop_name = crop['crop']
            ready_count[crop_name] = ready_count.get(crop_name, 0) + 1

        for crop_name, count in ready_count.items():
            crop_info = CROPS[crop_name]
            msg += f"   {crop_info['emoji']} {crop_info['name']} x{count} → READY!\n"
        msg += "\n💡 /harvest - Collect ready crops\n"

    if harvested_data:
        msg += "📦 **HARVESTED (Manual):**\n"
        harvest_count = {}
        for crop in harvested_data:
            crop_name = crop['crop']
            harvest_count[crop_name] = harvest_count.get(crop_name, 0) + 1

        for crop_name, count in list(harvest_count.items())[:5]:
            crop_info = CROPS[crop_name]
            msg += f"   {crop_info['emoji']} {crop_info['name']} x{count}\n"
        if len(harvest_count) > 5:
            msg += f"   +{len(harvest_count)-5} more\n"
        msg += "\n💡 /sell <crop> <quantity> to sell\n"

    if not growing and not ready and not harvested_data and not storage_crops:
        msg += "🌱 Empty farm!\n💡 /grow <crop> <quantity> to start!\n💡 /hire to hire workers for auto-growing!"

    await update.message.reply_text(msg, parse_mode="Markdown")


async def harvest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT crops, harvested FROM farms WHERE user_id=?", (user_id,))
    farm = c.fetchone()
    
    if not farm:
        await update.message.reply_text("🌱 No crops to harvest!")
        conn.close()
        return
    
    crops_data = json.loads(farm[0]) if farm[0] else []
    harvested_data = json.loads(farm[1]) if farm[1] else []
    
    now = datetime.now()
    ready_crops = []
    still_growing = []
    
    for crop in crops_data:
        ready_time = datetime.fromisoformat(crop['ready_time'])
        if now >= ready_time:
            ready_crops.append(crop)
        else:
            still_growing.append(crop)
    
    if not ready_crops:
        await update.message.reply_text("🌱 No crops ready to harvest yet!\n💡 /farm to check status")
        conn.close()
        return
    
    harvested_data.extend(ready_crops)
    
    c.execute("UPDATE farms SET crops = ?, harvested = ? WHERE user_id=?", 
              (json.dumps(still_growing), json.dumps(harvested_data), user_id))
    conn.commit()
    conn.close()
    
    harvest_count = {}
    for crop in ready_crops:
        crop_name = crop['crop']
        harvest_count[crop_name] = harvest_count.get(crop_name, 0) + 1
    
    msg = "🌾 **HARVESTED!**\n\n"
    for crop_name, count in harvest_count.items():
        crop_info = CROPS[crop_name]
        msg += f"✅ {crop_info['emoji']} {crop_info['name']} x{count}\n"
    msg += f"\n📦 Added to inventory!\n💡 /sell <crop> <quantity> to sell"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Usage: /sell <crop> <quantity>\nExample: /sell watermelon 5")
        return

    crop_name = args[0].lower()
    try:
        quantity = int(args[1])
    except:
        await update.message.reply_text("❌ Invalid quantity!")
        return

    if crop_name not in CROPS:
        await update.message.reply_text(f"❌ Unknown crop!")
        return

    if quantity < 1:
        await update.message.reply_text("❌ Quantity must be at least 1!")
        return

    conn = get_db()
    c = conn.cursor()
    
    crop_info = CROPS[crop_name]
    sell_price = crop_info['sell'] * quantity
    sold = False
    
    # 🔥 FIBNCT CHECK STORAGE (auto-grown by workers) 🔥
    c.execute("SELECT crops FROM user_storage WHERE user_id = ?", (user_id,))
    storage_result = c.fetchone()
    
    if storage_result:
        storage_crops = json.loads(storage_result[0]) if storage_result[0] else {}
        available_in_storage = storage_crops.get(crop_name, 0)
        
        if available_in_storage >= quantity:
            # Sell from storage
            storage_crops[crop_name] = storage_crops.get(crop_name, 0) - quantity
            if storage_crops[crop_name] <= 0:
                del storage_crops[crop_name]
            
            c.execute("UPDATE user_storage SET crops = ? WHERE user_id = ?", 
                     (json.dumps(storage_crops), user_id))
            
            c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            current_bal = c.fetchone()[0]
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (sell_price, user_id))
            
            # Update farm stats
            c.execute("SELECT total_earned, total_profit FROM farms WHERE user_id=?", (user_id,))
            stats = c.fetchone()
            if stats:
                total_earned = (stats[0] or 0) + sell_price
                total_profit = (stats[1] or 0) + (sell_price - (crop_info['price'] * quantity))
                c.execute("UPDATE farms SET total_earned = ?, total_profit = ? WHERE user_id=?", 
                         (total_earned, total_profit, user_id))
            else:
                c.execute("INSERT INTO farms (user_id, total_earned, total_profit) VALUES (?, ?, ?)", 
                         (user_id, sell_price, sell_price - (crop_info['price'] * quantity)))
            
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                f"💰 **SOLD FROM STORAGE!**\n\n"
                f"{crop_info['emoji']} {crop_info['name']} x{quantity}\n"
                f"💵 Price: {crop_info['sell']:,} each\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 Total: {sell_price:,} credits\n"
                f"💳 New balance: {current_bal + sell_price:,}",
                parse_mode="Markdown"
            )
            return
    
    # 🔥 IF NOT IN STORAGE, CHECK HARVESTED (manual) 🔥
    c.execute("SELECT harvested FROM farms WHERE user_id=?", (user_id,))
    farm = c.fetchone()

    if not farm:
        await update.message.reply_text("📦 No crops to sell!")
        conn.close()
        return

    harvested_data = json.loads(farm[0]) if farm[0] else []

    available = 0
    for crop in harvested_data:
        if crop['crop'] == crop_name:
            available += 1

    if available < quantity:
        await update.message.reply_text(f"❌ You have only {available} {crop_info['emoji']} {crop_info['name']}!\n💡 Check /farm to see what you have!")
        conn.close()
        return

    sold_count = 0
    new_harvested = []
    for crop in harvested_data:
        if crop['crop'] == crop_name and sold_count < quantity:
            sold_count += 1
        else:
            new_harvested.append(crop)

    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    current_bal = c.fetchone()[0]
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (sell_price, user_id))

    c.execute("SELECT total_earned, total_profit FROM farms WHERE user_id=?", (user_id,))
    stats = c.fetchone()
    if stats:
        total_earned = (stats[0] or 0) + sell_price
        total_profit = (stats[1] or 0) + (sell_price - (crop_info['price'] * quantity))
    else:
        total_earned = sell_price
        total_profit = sell_price - (crop_info['price'] * quantity)

    c.execute("UPDATE farms SET harvested = ?, total_earned = ?, total_profit = ? WHERE user_id=?",
              (json.dumps(new_harvested), total_earned, total_profit, user_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"💰 **SOLD FROM HARVEST!**\n\n"
        f"{crop_info['emoji']} {crop_info['name']} x{quantity}\n"
        f"💵 Price: {crop_info['sell']:,} each\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Total: {sell_price:,} credits\n"
        f"💎 Profit: {(sell_price - (crop_info['price'] * quantity)):,} credits\n\n"
        f"💳 New balance: {current_bal + sell_price:,}",
        parse_mode="Markdown"
    )

async def farm_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT total_grown, total_earned, total_profit FROM farms WHERE user_id=?", (user_id,))
    farm = c.fetchone()
    
    if not farm or not farm[0]:
        await update.message.reply_text("📊 No farm statistics yet!\n💡 /grow to start farming!")
        conn.close()
        return
    
    total_grown = farm[0] or 0
    total_earned = farm[1] or 0
    total_profit = farm[2] or 0
    
    await update.message.reply_text(
        f"📊 **FARM STATISTICS**\n\n"
        f"🌱 Total crops grown: {total_grown}\n"
        f"💰 Total earned: {total_earned:,}\n"
        f"💎 Total profit: {total_profit:,}\n\n"
        f"🏆 Keep farming to grow more!",
        parse_mode="Markdown"
    )

async def farm_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT u.name, f.total_grown, f.total_earned, f.total_profit 
        FROM farms f 
        JOIN users u ON f.user_id = u.user_id 
        WHERE f.total_grown > 0 
        ORDER BY f.total_grown DESC 
        LIMIT 5
    """)
    top_farmers = c.fetchall()
    
    c.execute("""
        SELECT COUNT(*) + 1 FROM farms WHERE total_grown > (SELECT total_grown FROM farms WHERE user_id=?)
    """, (user_id,))
    rank = c.fetchone()[0]
    
    c.execute("SELECT total_grown, total_profit FROM farms WHERE user_id=?", (user_id,))
    user_stats = c.fetchone()
    conn.close()
    
    msg = "🏆 **TOP FARMERS** 🏆\n\n"
    
    medals = ["👑", "🥈", "🥉", "", ""]
    for i, farmer in enumerate(top_farmers):
        name, grown, earned, profit = farmer
        medal = medals[i] if i < 3 else f"{i+1}."
        msg += f"{medal} {name}\n"
        msg += f"   🌱 Crops grown: {grown:,}\n"
        msg += f"   💰 Total earned: {earned:,}\n"
        msg += f"   💎 Total profit: {profit:,}\n"
        if i < len(top_farmers) - 1:
            msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    if user_stats and user_stats[0]:
        msg += f"\n📊 **Your Rank:** #{rank}\n"
        msg += f"🌱 Your crops: {user_stats[0]:,}\n"
        msg += f"💎 Your profit: {user_stats[1]:,}"
    else:
        msg += f"\n📊 Your Rank: Not ranked yet!\n💡 /grow to start farming!"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

# ============ ADMIN RAIN COMMAND (FULLY WORKING) ============

# ============ ADMIN RAIN COMMAND (FULLY WORKING - INSTANT READY AT 100%) ============

# ============ ADMIN RAIN COMMAND ============

async def rain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command - X% discount on grow time"""
    
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "🌧️ **RAIN COMMAND**\n\n"
            "Usage: `/rain <percentage>`\n"
            "Example: `/rain 50` - 50% less time\n"
            "Example: `/rain 100` - 100% less time (1 min)\n"
            "Example: `/rain 0` - Normal\n\n"
            "📊 Potato 30m → 50% = 15m\n"
            "📊 Watermelon 720m → 50% = 360m",
            parse_mode="Markdown"
        )
        return
    
    try:
        percentage = int(args[0])
    except:
        await update.message.reply_text("❌ Invalid percentage!")
        return
    
    if percentage < 0 or percentage > 100:
        await update.message.reply_text("❌ Percentage must be between 0 and 100!")
        return
    
    global rain_percentage
    rain_percentage = percentage
    
    if percentage == 0:
        await update.message.reply_text(
            f"🌤️ **RAIN STOPPED**\n\n"
            f"⏰ Grow time back to normal!",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"🌧️ **RAIN BONUS!**\n\n"
            f"⏰ Grow time reduced by {percentage}%\n"
            f"📉 Example: 60m crop → {int(60 - (60*percentage/100))}m\n\n"
            f"⚠️ Only affects NEW crops!",
            parse_mode="Markdown"
        )

# ============ TIC TAC TOE - FULLY FIXED ============

import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler

# Store active games
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
        
        if self.check_win(symbol):
            self.winner = user_id
            self.game_active = False
            return True, "win"
        
        if self.check_draw():
            self.game_active = False
            return True, "draw"
        
        self.current_turn = self.player2_id if user_id == self.player1_id else self.player1_id
        return True, "continue"
    
    def check_win(self, symbol):
        wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a,b,c in wins:
            if self.board[a] == symbol and self.board[b] == symbol and self.board[c] == symbol:
                return True
        return False
    
    def check_draw(self):
        return all(cell != '⬜' for cell in self.board)
    
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Normal Game"
    
    await update.message.reply_text(
        f"🎯 **TIC TAC TOE**\n\n"
        f"👑 {user_name} (❌)\n"
        f"{bet_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Waiting for opponent...\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def ttt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    data = query.data
    
    # Handle join game
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
        
        # Check balance for joiner
        if bet > 0:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
            balance = c.fetchone()[0]
            conn.close()
            
            if balance < bet:
                await query.edit_message_text(f"❌ You need {bet:,} credits to join!")
                return
        
        # Create game
        game = TicTacToe(game_id, creator_id, creator_name, user_name, bet, chat_id)
        game.player2_id = user_id
        game.game_active = True
        
        # Deduct bets if any
        if bet > 0:
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, creator_id))
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, user_id))
            conn.commit()
            conn.close()
        
        ttt_games[game_id] = game
        del ttt_lobby[game_id]
        
        bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Normal Game"
        
        await query.edit_message_text(
            f"🎯 **TIC TAC TOE**\n\n"
            f"❌ {creator_name} vs ⭕ {user_name}\n"
            f"{bet_text}\n\n"
            f"🎯 {creator_name}'s Turn",
            reply_markup=game.get_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    # Handle move
    if data.startswith("ttt_"):
        parts = data.split("_")
        if len(parts) < 3:
            return
        
        try:
            game_id = int(parts[1])
            pos = int(parts[2])
        except:
            return
        
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
            loser_name = game.player2_name if winner_id == game.player1_id else game.player1_name
            
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
            
            # Final message with board and result
            await query.edit_message_text(
                f"🎯 **TIC TAC TOE**\n\n"
                f"❌ {game.player1_name} vs ⭕ {game.player2_name}\n\n"
                f"{result_text}",
                reply_markup=game.get_keyboard(),
                parse_mode="Markdown"
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
                parse_mode="Markdown"
            )
            
            del ttt_games[game_id]
            return
        
        else:  # continue
            turn_name = game.player1_name if game.current_turn == game.player1_id else game.player2_name
            turn_symbol = "❌" if game.current_turn == game.player1_id else "⭕"
            
            bet_text = f"💰 Bet: {game.bet:,} | Prize: {game.bet*2:,}" if game.bet > 0 else "🎮 Normal Game"
            
            await query.edit_message_text(
                f"🎯 **TIC TAC TOE**\n\n"
                f"❌ {game.player1_name} vs ⭕ {game.player2_name}\n"
                f"{bet_text}\n\n"
                f"🎯 {turn_name}'s Turn ({turn_symbol})",
                reply_markup=game.get_keyboard(),
                parse_mode="Markdown"
            )
            return

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    bot_username = context.bot.username
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM referrals WHERE referred_by = ?", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"👥 REFERRAL SYSTEM\n\n"
        f"Invite friends and earn 1,000 credits each!\n\n"
        f"Your Link: {ref_link}\n\n"
        f"Referred: {count} users\n"
        f"Earned: {count * 1000} credits\n\n"
        f"Share this link with your friends!\n"
        f"New users get +500 bonus!"
    )

# ============ STORAGE & HIRE SYSTEM ============

# ============ STORAGE & HIRE SYSTEM ============

import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler

# Storage upgrade data
STORAGE_LEVELS = {
    1: {"slots": 50, "next_cost": 10000, "next_slots": 70},
    2: {"slots": 70, "next_cost": 15000, "next_slots": 95},
    3: {"slots": 95, "next_cost": 22500, "next_slots": 125},
    4: {"slots": 125, "next_cost": 33750, "next_slots": 160},
    5: {"slots": 160, "next_cost": 50625, "next_slots": 200},
    6: {"slots": 200, "next_cost": 75937, "next_slots": 245},
    7: {"slots": 245, "next_cost": 113905, "next_slots": 295},
    8: {"slots": 295, "next_cost": 170857, "next_slots": 350},
    9: {"slots": 350, "next_cost": 256285, "next_slots": 410},
    10: {"slots": 410, "next_cost": 0, "next_slots": 410},
}

# Worker data (Price = Crop Price × 8)
WORKEBNC = {
    "potato": {"name": "🥔 Potato", "price": 8000, "crop_price": 1000, "sell": 1500, "time": 30, "emoji": "🥔"},
    "carrot": {"name": "🥕 Carrot", "price": 16000, "crop_price": 2000, "sell": 3000, "time": 60, "emoji": "🥕"},
    "tomato": {"name": "🍅 Tomato", "price": 24000, "crop_price": 3000, "sell": 4500, "time": 120, "emoji": "🍅"},
    "corn": {"name": "🌽 Corn", "price": 40000, "crop_price": 5000, "sell": 7500, "time": 240, "emoji": "🌽"},
    "wheat": {"name": "🌾 Wheat", "price": 56000, "crop_price": 7000, "sell": 10500, "time": 360, "emoji": "🌾"},
    "strawberry": {"name": "🍓 Strawberry", "price": 64000, "crop_price": 8000, "sell": 12000, "time": 480, "emoji": "🍓"},
    "watermelon": {"name": "🍉 Watermelon", "price": 80000, "crop_price": 10000, "sell": 15000, "time": 720, "emoji": "🍉"},
    "ganja": {"name": "🌿 Ganja", "price": 112000, "crop_price": 14000, "sell": 21000, "time": 720, "emoji": "🌿"},
}

def init_storage_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_storage
                 (user_id INTEGER PRIMARY KEY,
                  level INTEGER DEFAULT 1,
                  crops TEXT DEFAULT '{}',
                  workers TEXT DEFAULT '[]')''')
    conn.commit()
    conn.close()

init_storage_db()

def get_user_storage(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT level, crops, workers FROM user_storage WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {"level": result[0], "crops": json.loads(result[1]), "workers": json.loads(result[2])}
    else:
        return {"level": 1, "crops": {}, "workers": []}

def save_user_storage(user_id, level, crops, workers):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO user_storage (user_id, level, crops, workers) VALUES (?, ?, ?, ?)",
              (user_id, level, json.dumps(crops), json.dumps(workers)))
    conn.commit()
    conn.close()

def get_total_slots(level):
    return STORAGE_LEVELS.get(level, {"slots": 50})["slots"]

def get_used_slots(crops):
    return sum(crops.values())

# ============ STORAGE COMMANDS ============
# ============ STORAGE SYSTEM ============

async def storage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    storage_data = get_user_storage(user_id)
    level = storage_data["level"]
    crops = storage_data["crops"]
    
    total_slots = get_total_slots(level)
    used_slots = get_used_slots(crops)
    free_slots = total_slots - used_slots
    
    next_level = level + 1
    if next_level in STORAGE_LEVELS:
        next_slots = STORAGE_LEVELS[next_level]["next_slots"]
        next_cost = STORAGE_LEVELS[level]["next_cost"]
        upgrade_text = f"📈 NEXT UPGRADE:\nLevel {next_level} → {next_slots} slots (+{next_slots - total_slots})\n💰 Cost: {next_cost:,} credits"
    else:
        upgrade_text = "🏆 MAX LEVEL REACHED!"
    
    crops_text = ""
    for crop_name, count in crops.items():
        crop = WORKEBNC.get(crop_name, CROPS.get(crop_name))
        if crop:
            crops_text += f"{crop['emoji']} {crop['name']} x{count}\n"
    
    if not crops_text:
        crops_text = "🌱 No crops stored\n"
    
    status = "🟢 FREE" if free_slots > 0 else "🔴 FULL"
    
    await update.message.reply_text(
        f"📦 YOUR STORAGE\n\n"
        f"Level: {level}\n"
        f"Slots: {used_slots}/{total_slots} ({status})\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"{upgrade_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🌾 Crops stored:\n{crops_text}\n"
        f"💡 /upgrade_storage - To upgrade"
    )

async def upgrade_storage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    storage_data = get_user_storage(user_id)
    level = storage_data["level"]
    
    if level not in STORAGE_LEVELS or STORAGE_LEVELS[level]["next_cost"] == 0:
        await update.message.reply_text("🏆 You have reached MAX storage level!")
        return
    
    next_cost = STORAGE_LEVELS[level]["next_cost"]
    next_slots = STORAGE_LEVELS[level]["next_slots"]
    current_slots = get_total_slots(level)
    
    keyboard = [
        [InlineKeyboardButton("✅ CONFIRM", callback_data=f"storage_confirm_{user_id}")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="storage_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📦 UPGRADE STORAGE\n\n"
        f"Current Level: {level} ({current_slots} slots)\n"
        f"Next Level: {level + 1} ({next_slots} slots)\n"
        f"💰 Cost: {next_cost:,} credits\n\n"
        f"⚠️ Confirm upgrade?",
        reply_markup=reply_markup
    )

async def storage_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "storage_cancel":
        await query.edit_message_text("❌ Upgrade cancelled!")
        return
    
    if data.startswith("storage_confirm_"):
        target_id = int(data.split("_")[2])
        
        if user_id != target_id:
            await query.answer("Not your upgrade!", show_alert=True)
            return
        
        storage_data = get_user_storage(user_id)
        level = storage_data["level"]
        
        if level not in STORAGE_LEVELS or STORAGE_LEVELS[level]["next_cost"] == 0:
            await query.edit_message_text("🏆 Max level already reached!")
            return
        
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = c.fetchone()[0]
        conn.close()
        
        cost = STORAGE_LEVELS[level]["next_cost"]
        
        if balance < cost:
            await query.edit_message_text(f"❌ Need {cost:,} credits to upgrade!")
            return
        
        conn = get_db()
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (cost, user_id))
        
        new_level = level + 1
        c.execute("INSERT OR REPLACE INTO user_storage (user_id, level, crops, workers) VALUES (?, ?, ?, ?)",
                  (user_id, new_level, json.dumps(storage_data["crops"]), json.dumps(storage_data["workers"])))
        conn.commit()
        conn.close()
        
        new_slots = get_total_slots(new_level)
        
        await query.edit_message_text(
            f"✅ STORAGE UPGRADED!\n\n"
            f"Level: {level} → {new_level}\n"
            f"Slots: {get_total_slots(level)} → {new_slots}\n"
            f"💰 Cost: {cost:,} credits\n\n"
            f"📦 Free slots: {new_slots - get_used_slots(storage_data['crops'])}"
        )

# ============ HIRE COMMANDS ============
async def hire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return

    keyboard = []
    for key, worker in WORKEBNC.items():
        keyboard.append([InlineKeyboardButton(
            f"{worker['emoji']} {worker['name']} - {worker['price']:,} credits",
            callback_data=f"hire_{key}"
        )])

    await update.message.reply_text(
        "👨‍🌾 **HIRE WORKER**\n\nClick on any worker to hire instantly:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def hire_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    data = query.data

    if not data.startswith("hire_"):
        return

    crop_key = data[5:]  # "hire_potato" -> "potato"
    worker = WORKEBNC.get(crop_key)

    if not worker:
        await query.edit_message_text("❌ Invalid worker!")
        return

    conn = get_db()
    c = conn.cursor()

    # get current workers
    c.execute("SELECT workers FROM user_storage WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    workers = json.loads(row[0]) if row and row[0] else []

    # balance check
    c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = c.fetchone()[0]

    if balance < worker["price"]:
        await query.edit_message_text(f"❌ Need {worker['price']:,} credits!")
        conn.close()
        return

    # deduct & add worker
    c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (worker["price"], user_id))
    workers.append(crop_key)
    c.execute("INSERT OR REPLACE INTO user_storage (user_id, level, crops, workers) VALUES (?, 1, '{}', ?)",
              (user_id, json.dumps(workers)))
    conn.commit()
    conn.close()

    await query.edit_message_text(f"✅ **{worker['name']} worker hired successfully!**", parse_mode="Markdown")



async def hire_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    print(f"Confirm data: {data}")  # Debug
    
    if data == "hire_cancel":
        await query.edit_message_text("❌ Hire cancelled!")
        return
    
    if data.startswith("hire_confirm_"):
        crop_key = data.replace("hire_confirm_", "")
        
        # Remove any extra parts
        if "_" in crop_key:
            crop_key = crop_key.split("_")[0]
        
        worker = WORKEBNC.get(crop_key)
        
        if not worker:
            await query.edit_message_text(f"❌ Invalid worker!")
            return
        
        # Process hire...
        conn = get_db()
        c = conn.cursor()
        
        c.execute("SELECT workers FROM user_storage WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        workers_list = json.loads(result[0]) if result and result[0] else []
        
        c.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = c.fetchone()[0]
        
        if balance < worker["price"]:
            await query.edit_message_text(f"❌ Need {worker['price']:,} credits!")
            conn.close()
            return
        
        c.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (worker["price"], user_id))
        workers_list.append(crop_key)
        
        c.execute("INSERT OR REPLACE INTO user_storage (user_id, level, crops, workers) VALUES (?, ?, ?, ?)",
                  (user_id, 1, "{}", json.dumps(workers_list)))
        
        conn.commit()
        conn.close()
        
        await query.edit_message_text(f"✅ HIRED! {worker['name']} worker added!")


async def workers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_registered(user_id):
        await update.message.reply_text('❌ Send /start first!')
        return
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT workers FROM user_storage WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        await update.message.reply_text("👨‍🌾 YOUR WORKEBNC\n\nNo workers hired yet!\n\n💡 /hire - Hire workers")
        return
    
    workers_list = json.loads(result[0]) if result[0] else []
    
    if not workers_list:
        await update.message.reply_text("👨‍🌾 YOUR WORKEBNC\n\nNo workers hired yet!\n\n💡 /hire - Hire workers")
        return
    
    now = time.time()
    total_cost = 0
    msg = "👨‍🌾 YOUR WORKEBNC\n\n"
    
    # Count workers
    from collections import Counter
    worker_counts = Counter(workers_list)
    
    for worker_key, count in worker_counts.items():
        worker = WORKEBNC.get(worker_key)
        if worker:
            # Get last grow time for this worker type
            key = f"{user_id}_{worker_key}"
            last = last_grow.get(key, 0)
            time_passed = now - last
            time_needed = worker["time"] * 60
            remaining = time_needed - time_passed
            
            if remaining <= 0:
                remaining_text = "✅ READY!"
            else:
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                remaining_text = f"⏰ {minutes}m {seconds}s"
            
            msg += f"{worker['emoji']} {worker['name']} Worker x{count}\n"
            msg += f"   - Auto-grows: {worker['name']}\n"
            msg += f"   - {remaining_text}\n\n"
            total_cost += worker["price"] * count
    
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"💰 Total spent: {total_cost:,} credits\n\n"
    msg += f"💡 /hire - Hire more workers\n"
    msg += f"📦 Storage full = auto-grow paused"
    
    await update.message.reply_text(msg)

# ============ WORKER AUTO-GROW WITH STORAGE CHECK ============

import threading
import time

last_grow = {}

def auto_grow_worker():
    while True:
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT user_id, workers FROM user_storage")
            users = c.fetchall()
            conn.close()
            
            now = time.time()
            
            for user_id, workers_json in users:
                workers = json.loads(workers_json) if workers_json else []
                
                # Get storage info
                conn2 = get_db()
                c2 = conn2.cursor()
                c2.execute("SELECT level, crops FROM user_storage WHERE user_id = ?", (user_id,))
                storage_result = c2.fetchone()
                conn2.close()
                
                if storage_result:
                    level = storage_result[0]
                    stored_crops = json.loads(storage_result[1]) if storage_result[1] else {}
                    total_slots = get_total_slots(level)
                    used_slots = sum(stored_crops.values())
                    free_slots = total_slots - used_slots
                else:
                    free_slots = 50
                
                for w in workers:
                    worker = WORKEBNC.get(w)
                    if not worker:
                        continue
                    
                    key = f"{user_id}_{w}"
                    last = last_grow.get(key, 0)
                    time_passed = now - last
                    time_needed = worker["time"] * 60
                    
                    if time_passed >= time_needed:
                        # 🔥 STORAGE CHECK - AGAR JAGAH NAHI TO MAT GROW KARO 🔥
                        if free_slots <= 0:
                            print(f"User {user_id} storage full, cannot auto-grow {w}")
                            continue
                        
                        # Grow crop
                        conn3 = get_db()
                        c3 = conn3.cursor()
                        c3.execute("SELECT crops FROM user_storage WHERE user_id = ?", (user_id,))
                        result = c3.fetchone()
                        
                        crops = json.loads(result[0]) if result and result[0] else {}
                        crops[w] = crops.get(w, 0) + 1
                        
                        c3.execute("UPDATE user_storage SET crops = ? WHERE user_id = ?", 
                                   (json.dumps(crops), user_id))
                        conn3.commit()
                        conn3.close()
                        
                        last_grow[key] = now
                        free_slots -= 1
                        
            time.sleep(60)
        except Exception as e:
            print(f"Worker error: {e}")
            time.sleep(60)


# Start background thread
threading.Thread(target=auto_grow_worker, daemon=True).start()

# ============ CLCRICKET CLEAN ============

import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler

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
    await update.message.reply_text(
        f"🏏 CRICKET GAME\n\n👑 Host: {user_name}\n{bet_text}\n\n━━━━━━━━━━━━━━━━━━━━\n⚡ Select Mode:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("1-3 MODE", callback_data=f"cricket_mode_{game_id}_1-3")],
            [InlineKeyboardButton("1-5 MODE", callback_data=f"cricket_mode_{game_id}_1-5")],
            [InlineKeyboardButton("1-9 MODE", callback_data=f"cricket_mode_{game_id}_1-9")],
            [InlineKeyboardButton("DEFAULT", callback_data=f"cricket_mode_{game_id}_default")]
        ])
    )


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
    
    # 🔥 RESET ALL COUNTERS FOR NEW GAME 🔥
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

    # Store delivery choice
    game.pending_delivery = delivery_key
    game.waiting_for = "bat"

    bowler_name = game.player1_name if game.current_bowler == game.player1_id else game.player2_name
    batsman_name = game.player1_name if game.current_batsman == game.player1_id else game.player2_name

    # Show batting buttons to batsman
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

    # EDIT THE SAME MESSAGE - don't send new one
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
        game.wickets += 1
        game.balls += 1
        
        # First innings (target not set yet)
        if game.target is None:
            game.target = game.score + 1
            
            # Switch sides for second innings
            game.current_batsman = game.player2_id if game.current_batsman == game.player1_id else game.player1_id
            game.current_bowler = game.player2_id if game.current_bowler == game.player1_id else game.player1_id
            game.score = 0
            game.wickets = 0
            game.balls = 0  # 🔥 RESET BALLS FOR SECOND INNINGS 🔥
            game.waiting_for = "bowl"
            game.pending_delivery = None
            
            # Create bowling keyboard for second innings
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
        game.score += shot
        game.balls += 1
        
        # Check if target reached (second innings win)
        if game.target and game.score >= game.target:
            game.game_active = False
            game.winner = game.current_batsman
            
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
        
        # Create bowling keyboard for next ball
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



# ============ MINES GAME (High Multiplier) ============

import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler

active_mines = {}

# Max multiplier based on bombs
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
            parse_mode="Markdown"
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
        parse_mode="Markdown"
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
            parse_mode="Markdown"
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
                parse_mode="Markdown"
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
                parse_mode="Markdown"
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
            parse_mode="Markdown"
        )

# ============ SHOP4 (Similar to Shop2/Shop3) ============

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
        await update.message.reply_text('🛒 **SHOP4**\n\nNo players yet.\n👑 Admin: /addplayer4 <name> <price>', parse_mode="Markdown")
        return
    
    msg = "🛒 **SHOP4**\n\n"
    for p in players:
        msg += f"{p[0]}. {p[1]} - {p[2]:,} 💰\n"
    msg += "\n━━━━━━━━━━━━━━━━━━━━━━\n💡 /buy4 <id> to purchase"
    
    await update.message.reply_text(msg, parse_mode="Markdown")


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
    c.execute("""
        SELECT s.name, s.price FROM user_players4 u 
        JOIN shop4 s ON u.player_id = s.id 
        WHERE u.user_id = ?
    """, (user_id,))
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
    c.execute("""
        SELECT u.name, COUNT(up.player_id) as count, COALESCE(SUM(s.price), 0) as total
        FROM users u
        JOIN user_players4 up ON u.user_id = up.user_id
        JOIN shop4 s ON up.player_id = s.id
        GROUP BY u.user_id
        ORDER BY total DESC LIMIT 10
    """)
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


# Admin commands for shop4
async def addplayer4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text('❌ Admin only!')
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text('❌ /addplayer4 <name> <price>\nExample: /addplayer4 "Player Name" 5000')
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
        await update.message.reply_text('❌ /setprice4 <id> <new_price>\nExample: /setprice4 1 8000')
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
        await update.message.reply_text('❌ /removeplayer4 <id>\nExample: /removeplayer4 1')
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

# ============ GROUP TRACKING HANDLER ============

async def track_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Auto-track groups where bot is added"""
    if update.message and update.message.chat.type in ['group', 'supergroup']:
        group_id = update.message.chat.id
        group_name = update.message.chat.title or "Unknown Group"
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS groups 
                     (group_id INTEGER PRIMARY KEY, group_name TEXT, added_at TEXT)''')
        c.execute("INSERT OR IGNORE INTO groups (group_id, group_name, added_at) VALUES (?, ?, ?)",
                  (group_id, group_name, datetime.now().isoformat()))
        conn.commit()
        conn.close()

# ============ HALL OF FAME SYSTEM ============
# ============ HALL OF FAME SYSTEM (CLEAN) ============

import json
from telegram import Update
from telegram.ext import CommandHandler

def init_hof_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hall_of_fame
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  winner TEXT,
                  added_by INTEGER,
                  added_at TEXT)''')
    conn.commit()
    conn.close()

init_hof_db()

# ============ VIEW HALL OF FAME ============
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
    
    # 🔥 NO PARSE_MODE 🔥
    await update.message.reply_text(msg)


# ============ ADMIN: ADD WINNER ============
async def addhof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "📝 **ADD TO HALL OF FAME**\n\n"
            "Usage: `/addhof <winner_name>`\n"
            "Example: `/addhof 🔅 IPL S1: CSK 💛 (@user)`",
            parse_mode="Markdown"
        )
        return
    
    winner = " ".join(args)
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO hall_of_fame (winner, added_by, added_at) VALUES (?, ?, ?)",
              (winner, update.effective_user.id, datetime.now().isoformat()))
    conn.commit()
    
    c.execute("SELECT COUNT(*) FROM hall_of_fame")
    count = c.fetchone()[0]
    conn.close()
    
    await update.message.reply_text(
        f"✅ **Added to Hall of Fame!**\n\n"
        f"🏆 {winner}\n\n"
        f"📊 Total Winners: {count}",
        parse_mode="Markdown"
    )


# ============ ADMIN: REMOVE WINNER ============
async def rmhof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 1:
        await update.message.reply_text(
            "🗑️ **REMOVE FROM HALL OF FAME**\n\n"
            "Usage: `/rmhof <number>`\n"
            "Example: `/rmhof 5`",
            parse_mode="Markdown"
        )
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
    
    await update.message.reply_text(
        f"🗑️ **Removed from Hall of Fame!**\n\n"
        f"❌ Removed: {winner_text}\n\n"
        f"📊 Total Winners: {count}",
        parse_mode="Markdown"
    )

# ============ ADMIN: EDIT WINNER ============
async def edithof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin only!")
        return
    
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "✏️ EDIT HALL OF FAME\n\n"
            "Usage: /edithof <number> <new_text>\n"
            "Example: /edithof 5 🔅 IPL S2: MI 💙 (@user)\n\n"
            "Use /hof to see numbers"
        )
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
    
    await update.message.reply_text(
        f"✏️ EDITED HALL OF FAME!\n\n"
        f"❌ Old: {old_text}\n"
        f"✅ New: {new_text}"
    )

# ============ CRICKET STATS SYSTEM ============

def init_cricket_stats_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cricket_stats
                 (user_id INTEGER PRIMARY KEY,
                  name TEXT,
                  runs INTEGER DEFAULT 0,
                  wickets INTEGER DEFAULT 0,
                  wins INTEGER DEFAULT 0,
                  losses INTEGER DEFAULT 0,
                  highest_score INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_cricket_stats_db()

def update_cricket_stats(user_id, name, runs, wickets, won):
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM cricket_stats WHERE user_id = ?", (user_id,))
    stats = c.fetchone()
    
    if stats:
        new_runs = stats[2] + runs
        new_wickets = stats[3] + wickets
        new_wins = stats[4] + (1 if won else 0)
        new_losses = stats[5] + (0 if won else 1)
        new_highest = stats[6]
        if runs > new_highest:
            new_highest = runs
        
        c.execute("UPDATE cricket_stats SET runs = ?, wickets = ?, wins = ?, losses = ?, highest_score = ? WHERE user_id = ?",
                  (new_runs, new_wickets, new_wins, new_losses, new_highest, user_id))
    else:
        c.execute("INSERT INTO cricket_stats (user_id, name, runs, wickets, wins, losses, highest_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_id, name, runs, wickets, (1 if won else 0), (0 if won else 1), runs))
    
    conn.commit()
    conn.close()

def get_user_rank(user_id, stat_type):
    """Get user rank for a specific stat"""
    conn = get_db()
    c = conn.cursor()
    
    stat_column = {
        "runs": "runs",
        "wickets": "wickets", 
        "highest_score": "highest_score",
        "wins": "wins",
        "losses": "losses"
    }.get(stat_type, "runs")
    
    c.execute(f"SELECT COUNT(*) + 1 FROM cricket_stats WHERE {stat_column} > (SELECT {stat_column} FROM cricket_stats WHERE user_id = ?)", (user_id,))
    rank = c.fetchone()[0]
    conn.close()
    return rank

def get_top_5(stat_type):
    """Get top 5 players for a stat"""
    conn = get_db()
    c = conn.cursor()
    
    stat_column = {
        "runs": "runs",
        "wickets": "wickets",
        "highest_score": "highest_score", 
        "wins": "wins",
        "losses": "losses"
    }.get(stat_type, "runs")
    
    c.execute(f"SELECT name, {stat_column} FROM cricket_stats ORDER BY {stat_column} DESC LIMIT 5")
    top = c.fetchall()
    conn.close()
    return top

# ============ ROCK PAPER SCISSORS GAME ============

import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler

# Store active games
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
        choices = {"rock": "✊", "paper": "📄", "scissors": "✂️"}
        p1 = self.player1_choice
        p2 = self.player2_choice
        
        if p1 == p2:
            return "draw"
        
        if (p1 == "rock" and p2 == "scissors") or \
           (p1 == "paper" and p2 == "rock") or \
           (p1 == "scissors" and p2 == "paper"):
            return self.player1_id
        else:
            return self.player2_id
    
    def get_result_text(self):
        p1_emoji = {"rock": "✊", "paper": "📄", "scissors": "✂️"}[self.player1_choice]
        p2_emoji = {"rock": "✊", "paper": "📄", "scissors": "✂️"}[self.player2_choice]
        
        winner = self.check_winner()
        
        if winner == "draw":
            return f"{p1_emoji} {self.player1_name}: {self.player1_choice.upper()}\n{p2_emoji} {self.player2_name}: {self.player2_choice.upper()}\n\n🤝 **DRAW!** 🤝"
        else:
            winner_name = self.player1_name if winner == self.player1_id else self.player2_name
            return f"{p1_emoji} {self.player1_name}: {self.player1_choice.upper()}\n{p2_emoji} {self.player2_name}: {self.player2_choice.upper()}\n\n🏆 **WINNER: {winner_name.upper()}** 🏆"


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
    
    rps_lobby[game_id] = {
        "creator_id": user_id,
        "creator_name": user_name,
        "bet": bet,
        "chat_id": chat_id
    }
    
    keyboard = [[InlineKeyboardButton("🔵 JOIN GAME", callback_data=f"rps_join_{game_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Free Play"
    
    await update.message.reply_text(
        f"✊ **ROCK PAPER SCISSORS**\n\n"
        f"👑 Host: {user_name}\n"
        f"{bet_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ Waiting for opponent...\n"
        f"━━━━━━━━━━━━━━━━━━━━",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


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
            
            # Deduct bets
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, creator_id))
            c.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (bet, user_id))
            conn.commit()
            conn.close()
        
        # Create game
        game = RPSGame(game_id, creator_id, creator_name, bet, chat_id)
        game.player2_id = user_id
        game.player2_name = user_name
        game.game_active = True
        
        rps_games[game_id] = game
        del rps_lobby[game_id]
        
        # Show move buttons
        keyboard = [
            [InlineKeyboardButton("✊ ROCK", callback_data=f"rps_move_{game_id}_rock")],
            [InlineKeyboardButton("📄 PAPER", callback_data=f"rps_move_{game_id}_paper")],
            [InlineKeyboardButton("✂️ SCISSORS", callback_data=f"rps_move_{game_id}_scissors")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        bet_text = f"💰 Bet: {bet:,} | Prize: {bet*2:,}" if bet > 0 else "🎮 Free Play"
        
        await query.edit_message_text(
            f"✊ **ROCK PAPER SCISSORS**\n\n"
            f"{creator_name} vs {user_name}\n"
            f"{bet_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 {creator_name}'s turn!\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )


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
        
        # 🔥 OPPONENT KO CHOICE MAT DIKHA 🔥
        keyboard = [
            [InlineKeyboardButton("✊ ROCK", callback_data=f"rps_move_{game_id}_rock")],
            [InlineKeyboardButton("📄 PAPER", callback_data=f"rps_move_{game_id}_paper")],
            [InlineKeyboardButton("✂️ SCISSORS", callback_data=f"rps_move_{game_id}_scissors")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        bet_text = f"💰 Bet: {game.bet:,} | Prize: {game.bet*2:,}" if game.bet > 0 else "🎮 Free Play"
        
        # 🔥 SIRF TURN BATAYO, CHOICE NAHI 🔥
        await query.edit_message_text(
            f"✊ **ROCK PAPER SCISSORS**\n\n"
            f"{game.player1_name} vs {game.player2_name}\n"
            f"{bet_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ {game.player1_name} made their choice!\n\n"
            f"🎯 {game.player2_name}'s turn!\n"
            f"━━━━━━━━━━━━━━━━━━━━",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return
    
    else:
        game.player2_choice = choice
        game.waiting_for = None
        game.game_active = False
        
        result_text = game.get_result_text()
        winner = game.check_winner()
        
        # Transfer credits if bet and winner
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
            # Return money to both
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet, game.player1_id))
            c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (game.bet, game.player2_id))
            conn.commit()
            conn.close()
            
            result_text += f"\n\n💰 Money returned: {game.bet:,} each"
        
        # 🔥 RESULT KE BAAD BUTTONS HATAO 🔥
        await query.edit_message_text(
            f"✊ **ROCK PAPER SCISSORS**\n\n"
            f"{result_text}",
            parse_mode="Markdown"
        )
        
        del rps_games[game_id]
        return

async def rps_none_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Game Over!", show_alert=True)

# ============ NUMPUZ GAME (Size increases every level) ============

import random
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler

def init_numpuz_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS numpuz_progress
                 (user_id INTEGER PRIMARY KEY,
                  level INTEGER DEFAULT 1,
                  board TEXT,
                  moves INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

init_numpuz_db()

def get_size_for_level(level):
    """Return grid size based on level"""
    if level == 1:
        return 3
    elif level == 2:
        return 4
    elif level == 3:
        return 5
    elif level == 4:
        return 6
    elif level == 5:
        return 7
    elif level == 6:
        return 8
    else:
        return 9  # Max 9x9 (Telegram limit)

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

def get_board_display(board):
    size = len(board)
    msg = ""
    for row in board:
        row_parts = []
        for num in row:
            if num == 0:
                row_parts.append("⬜")
            else:
                row_parts.append(str(num))
        msg += " ".join(row_parts) + "\n"
    return msg

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
            if num == 0:
                text = "⬜"
            else:
                text = str(num)
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
    
    if saved:
        level = saved[0]
        board = json.loads(saved[1])
        
        if board:
            keyboard = get_board_keyboard(board, level)
            await update.message.reply_text(
                f"NUMPUZ - LEVEL {level}",
                reply_markup=keyboard
            )
            return
    
    # New game - level 1
    level = 1
    size = get_size_for_level(level)
    
    while True:
        board = get_shuffled_board(size)
        if is_solvable(board):
            break
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO numpuz_progress (user_id, level, board, moves) VALUES (?, ?, ?, ?)",
              (user_id, level, json.dumps(board), 0))
    conn.commit()
    conn.close()
    
    keyboard = get_board_keyboard(board, level)
    await update.message.reply_text(
        f"NUMPUZ - LEVEL {level}",
        reply_markup=keyboard
    )


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
                
                # Create new board for next level with bigger size
                while True:
                    new_board = get_shuffled_board(next_size)
                    if is_solvable(new_board):
                        break
                
                # Save new board
                c.execute("UPDATE numpuz_progress SET level = ?, board = ?, moves = ? WHERE user_id = ?",
                          (next_level, json.dumps(new_board), 0, user_id))
                conn.commit()
                conn.close()
                
                keyboard = get_board_keyboard(new_board, next_level)
                
                await query.edit_message_text(
                    f"LEVEL {current_level} COMPLETE!\n\nMoves: {moves}\n\nNUMPUZ - LEVEL {next_level} ({next_size}x{next_size})",
                    reply_markup=keyboard
                )
                return
            
            # Update board
            c.execute("UPDATE numpuz_progress SET board = ?, moves = ? WHERE user_id = ?",
                      (json.dumps(board), moves, user_id))
            conn.commit()
            conn.close()
            
            keyboard = get_board_keyboard(board, current_level)
            await query.edit_message_text(
                f"NUMPUZ - LEVEL {current_level}",
                reply_markup=keyboard
            )
        else:
            conn.close()

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot's response time"""
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
            f"🏓 **Pong!**\n"
            f"⏱️ Latency: `{latency:.2f}ms`\n"
            f"🤖 Bot is alive!",
            parse_mode='Markdown'
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



def main():
#    threading.Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    threading.Thread(target=auto_grow_worker, daemon=True).start()

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
    app.add_handler(CommandHandler("rps", rps))
    app.add_handler(CallbackQueryHandler(rps_join_callback, pattern="^rps_join_"))  
    app.add_handler(CallbackQueryHandler(rps_move_callback, pattern="^rps_move_"))
    app.add_handler(CallbackQueryHandler(rps_none_callback, pattern="^rps_none"))
    app.add_handler(CommandHandler("numpuz", numpuz))
    # Handler mein pattern "numpuz_" hona chahiye, "numpuz_next_" nahi
    app.add_handler(CallbackQueryHandler(numpuz_callback, pattern="^numpuz_"))

    # Hall of Fame commands (sahi naam se)
    app.add_handler(CommandHandler("hof", hof))
    app.add_handler(CommandHandler("addhof", addhof))
    app.add_handler(CommandHandler("rmhof", rmhof))
    app.add_handler(CommandHandler("edithof", edithof))
    app.add_handler(CommandHandler("ping", ping))
    # Shop2 commands
    app.add_handler(CommandHandler("shop2", shop2))
    app.add_handler(CommandHandler("buy2", buy2))
    app.add_handler(CommandHandler("myteam2", myteam2))
    app.add_handler(CommandHandler("top2", top2))
    app.add_handler(CommandHandler("addplayer2", addplayer2))
    app.add_handler(CommandHandler("setprice2", setprice2))
    app.add_handler(CommandHandler("removeplayer2", removeplayer2))

    # Bank commands
    app.add_handler(CommandHandler("bank", bank))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("withdraw", withdraw))
    app.add_handler(CommandHandler("claim_interest", claim_interest))

    # Admin commands
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
# ============ CLCRICKET HANDLERS ============

    app.add_handler(CommandHandler("CLcricket", clcricket))
    app.add_handler(CallbackQueryHandler(cricket_mode_callback, pattern="^cricket_mode_"))
    app.add_handler(CallbackQueryHandler(cricket_join_callback, pattern="^cricket_join_"))
    app.add_handler(CallbackQueryHandler(cricket_toss_callback, pattern="^cricket_toss_"))
    app.add_handler(CallbackQueryHandler(cricket_choice_callback, pattern="^cricket_choice_"))
    app.add_handler(CallbackQueryHandler(cricket_bowl_callback, pattern="^cricket_bowl_"))
    app.add_handler(CallbackQueryHandler(cricket_bat_callback, pattern="^cricket_bat_"))
    app.add_handler(CommandHandler("mines", mines))
    app.add_handler(CallbackQueryHandler(mine_callback, pattern="^mine_"))


    # Shop3 commands
    app.add_handler(CommandHandler("shop3", shop3))
    app.add_handler(CommandHandler("buy3", buy3))
    app.add_handler(CommandHandler("myteam3", myteam3))
    app.add_handler(CommandHandler("top3", top3))
    app.add_handler(CommandHandler("addplayer3", addplayer3))
    app.add_handler(CommandHandler("setprice3", setprice3))
    app.add_handler(CommandHandler("removeplayer3", removeplayer3))

    # Broadcast commands
    app.add_handler(CommandHandler("farm", farm))
    app.add_handler(CommandHandler("grow", grow))
    app.add_handler(CommandHandler("harvest", harvest))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("crops", crops))
    app.add_handler(CommandHandler("farm_stats", farm_stats))
    app.add_handler(CommandHandler("farm_leaderboard", farm_leaderboard))
    app.add_handler(CommandHandler("rain", rain))
    app.add_handler(CommandHandler("claimcode", claimcode))
    app.add_handler(CommandHandler("activecodes", activecodes))
    app.add_handler(CommandHandler("createcode", createcode))
    app.add_handler(CommandHandler("deletecode", deletecode))
    app.add_handler(CommandHandler("codestats", codestats))
    app.add_handler(CommandHandler("add_default_players", add_default_players))
    app.add_handler(CommandHandler("ttt", ttt))
    app.add_handler(CallbackQueryHandler(ttt_callback, pattern="^ttt_"))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("broadcast_stats", broadcast_stats))
    app.add_handler(CommandHandler("storage", storage))
    app.add_handler(CommandHandler("upgrade_storage", upgrade_storage))
    app.add_handler(CallbackQueryHandler(storage_callback, pattern="^storage_"))
    # Hire commands
    app.add_handler(CommandHandler("hire", hire))
    app.add_handler(CallbackQueryHandler(hire_callback, pattern="^hire_"))
    app.add_handler(CommandHandler("workers", workers))
    app.add_handler(CallbackQueryHandler(hire_callback, pattern="^hire_now_"))
    # ============ SHOP4 HANDLERS ============

    app.add_handler(CommandHandler("shop4", shop4))
    app.add_handler(CommandHandler("buy4", buy4))
    app.add_handler(CommandHandler("myteam4", myteam4))
    app.add_handler(CommandHandler("top4", top4))
    app.add_handler(CommandHandler("addplayer4", addplayer4))
    app.add_handler(CommandHandler("setprice4", setprice4))
    app.add_handler(CommandHandler("removeplayer4", removeplayer4))
    app.add_handler(MessageHandler(filters.ChatType.GROUP | filters.ChatType.SUPERGROUP, track_group))


    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
