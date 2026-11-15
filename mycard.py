import io, os, re
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import ContextTypes

def _font(size, bold=True):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/system/fonts/Roboto-Bold.ttf" if bold else "/system/fonts/Roboto-Regular.ttf",
              "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()

_SC = dict(zip("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡʏᴢ", "ABCDEFGHIJKLMNOPQRSTUVWYZ"))

def _clean(name):
    import unicodedata
    n = unicodedata.normalize("NFKC", str(name or ""))
    n = "".join(_SC.get(c, c) for c in n)
    n = re.sub(r"[^A-Za-z0-9 _.\-]", "", n).strip()
    return (n or "PLAYER")[:16].upper()

def build_card(name, st, avatar_bytes=None):
    W, H = 900, 560
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(12 + 18 * t), int(16 + 22 * t), int(40 + 40 * t)))
    d.rounded_rectangle((12, 12, W - 12, H - 12), 28, outline=(255, 190, 60), width=4)
    d.text((40, 34), "CL BOT  |  PLAYER CARD", font=_font(26), fill=(255, 190, 60))
    cx, cy, r = 150, 200, 95
    av = None
    if avatar_bytes:
        try:
            av = Image.open(io.BytesIO(avatar_bytes)).convert("RGB").resize((r * 2, r * 2))
        except Exception:
            av = None
    if av is None:
        av = Image.new("RGB", (r * 2, r * 2), (40, 90, 170))
        ImageDraw.Draw(av).text((r, r), _clean(name)[0], font=_font(110), fill="white", anchor="mm")
    mask = Image.new("L", (r * 2, r * 2), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, r * 2 - 1, r * 2 - 1), fill=255)
    d.ellipse((cx - r - 6, cy - r - 6, cx + r + 6, cy + r + 6), outline=(255, 190, 60), width=5)
    img.paste(av, (cx - r, cy - r), mask)
    d.text((290, 150), _clean(name), font=_font(56), fill="white")
    d.text((292, 220), "Cricket Stats", font=_font(26, False), fill=(170, 180, 210))
    items = [("RUNS", st.get("runs", 0)), ("WICKETS", st.get("wickets", 0)), ("HIGHEST", st.get("highest_score", 0)),
             ("WINS", st.get("wins", 0)), ("LOSSES", st.get("losses", 0)), ("DUCKS", st.get("ducks", 0))]
    bw, bh = 260, 110
    for i, (k, v) in enumerate(items):
        x = 40 + (i % 3) * (bw + 20)
        y = 340 + (i // 3) * (bh + 20)
        d.rounded_rectangle((x, y, x + bw, y + bh), 18, fill=(28, 36, 72), outline=(70, 90, 150), width=2)
        d.text((x + bw // 2, y + 36), str(v), font=_font(42), fill="white", anchor="mm")
        d.text((x + bw // 2, y + 82), k, font=_font(20), fill=(255, 190, 60), anchor="mm")
    out = io.BytesIO()
    img.save(out, "PNG")
    out.seek(0)
    return out

def make_mycard(get_db, close_db):
    async def mycard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message:
            return
        u = update.effective_user
        wait_msg = None
        try:
            wait_msg = await update.message.reply_text("⏳ Generating your player card...\nPlease wait a moment.")
        except Exception:
            pass
        db = None
        st = {}
        try:
            db = await get_db()
            row = await db.fetchrow("SELECT * FROM cricket_stats WHERE user_id = $1", u.id)
            st = dict(row) if row else {}
        except Exception as e:
            print(f"mycard db error: {e}")
        finally:
            if db:
                await close_db(db)
        avatar = None
        try:
            ph = await context.bot.get_user_profile_photos(u.id, limit=1)
            if ph.total_count:
                f = await context.bot.get_file(ph.photos[0][-1].file_id)
                avatar = bytes(await f.download_as_bytearray())
        except Exception:
            pass
        try:
            buf = build_card(u.first_name, st, avatar)
            await update.message.reply_photo(buf, caption="Your CL Bot player card")
            if wait_msg:
                try:
                    await wait_msg.delete()
                except Exception:
                    pass
        except Exception as e:
            print(f"mycard error: {e}")
            await update.message.reply_text("Card banane me error aaya.")
    return mycard
