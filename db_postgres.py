# ============ db_postgres.py ==========

import asyncpg
import os
from datetime import datetime

DATABASE_URL = "postgresql://fantasy_user:R8gn40MjuTwC0hfEuGOkCrOVSmja6G5k@dpg-d8ejhocm0tmc73etsa80-a/fantasy_bot"

conn = None

async def get_db():
    global conn
    if conn is None or conn.is_closed():
        conn = await asyncpg.connect(DATABASE_URL)
    return conn

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
    
    print("✅ PostgreSQL tables created!")
    
    await conn.close()

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
