import random, time

MEDIA = {
    "fifty": [
        ("BAACAgUAAyEFAATqVpOyAAILOWr6lp3mlW_5iV68wa19mlW9tZgfAALlEQAC73HoVB-ASI7oVXD2PQQ",
         "CgACAgUAAyEFAATqVpOyAAILQWr6lxokaLEr4oBQDpHfOBe7XfwnAAKRIwACHpLYV-vIKh87M4LJPQQ"),
        ("BAACAgEAAyEFAATqVpOyAAILUWr6ncBzIbSrqzR1-q6Xz5DDljNJAAIECQAC1DvRRyKoLuLyz5kaPQQ",
         "CgACAgUAAyEFAATqVpOyAAILUmr6ncNMMFuwXQlfOQO-2BM_jxiWAAIFCQAC1DvRR2i16uMhioKhPQQ"),
        ("BAACAgEAAyEFAATqVpOyAAILTWr6nbjJ1UW9ts_I5ruV94bq54KdAAMJAALUO9FHTEKhce6v6xk9BA",
         "CgACAgEAAyEFAATqVpOyAAILUGr6nb4DDNnyasHsxaETBenhY7TgAAIDCQAC1DvRR34ySP2RsU5qPQQ"),
        ("BAACAgEAAyEFAATqVpOyAAILTGr6nbdl1WCwcurUmhHGSygLoYlsAAL-CAAC1DvRRxaal4FYUvCKPQQ",
         "CgACAgEAAyEFAATqVpOyAAILTmr6nbrErPDT_eUjbdvW4zr1CMOcAAIBCQAC1DvRR2qr1RGhzWkHPQQ"),
    ],
    "wicket": [
        ("BAACAgUAAyEFAATqVpOyAAILQmr6l0xDg_U49qKOjJ8w87vAbVubAAKSIwACHpLYV9dnsw1_PCgDPQQ",
         "CgACAgUAAyEFAATqVpOyAAILQ2r6l3FgkomB2l1ai1jl34Q7fODrAAKUIwACHpLYVxLIymCLY9HjPQQ"),
        ("BAACAgUAAyEFAATqVpOyAAILPGr6lp1HBbW3v4J9r1BvRPGgIKLwAALRCwACtHOJVoI5cpq8zSXnPQQ",
         "CgACAgUAAyEFAATqVpOyAAILPmr6lwLHhHf2FEuxMIxNZ4FnmpseAAKOIwACHpLYV_bFf4JRTDJyPQQ"),
        ("BAACAgEAAyEFAATqVpOyAAILWWr6oan0K2ZLPDMW06PLH5Ws0GH6AAITCQAC1DvRRyLatiYFlu6PPQQ",
         "CgACAgEAAyEFAATqVpOyAAILWmr6odP5cXW9ePx6GuaTs0Hv_njPAAIUCQAC1DvRR6Zd5EQZRWNmPQQ"),
    ],
    "wellplayed": [
        ("BAACAgEAAyEFAATqVpOyAAILO2r6lp3wMcQJtTRlfWfWc6v85tyrAAJrBQACwL04R4axI9UnrODXPQQ",
         "CgACAgUAAyEFAATqVpOyAAILP2r6lw2g0Y1UfOy3qW7J96kFC-EIAAKPIwACHpLYVwvMQpvE96dQPQQ"),
    ],
    "summary": [
        ("BAACAgQAAyEFAATqVpOyAAILOmr6lp0IQFICdEcUqs0go4tBdilYAAJeGwACTQ7gUVG4jxU7t6PIPQQ",
         "CgACAgUAAyEFAATqVpOyAAILQGr6lxkTkw6ER-m1VT0pJ7R4Vp2NAAKQIwACHpLYV-1L9PDn-bBKPQQ"),
    ],
    "century": [
        ("BAACAgUAAyEFAATqVpOyAAILSGr6nLuAQP6etaYHUWqEwQZuDDcTAAKiIwACHpLYV-TnykkwBcZuPQQ",
         "CgACAgEAAyEFAATqVpOyAAILWGr6oNxibBOSqmVt3yKVZ7euThM8AAIQCQAC1DvRR5sWhpY0TXPGPQQ"),
        ("BAACAgUAAyEFAATqVpOyAAILSWr6nQFOn0UBd3sZDaKNX--5pOa5AAKjIwACHpLYV5H0EhOkOpOMPQQ",
         "CgACAgEAAyEFAATqVpOyAAILWGr6oNxibBOSqmVt3yKVZ7euThM8AAIQCQAC1DvRR5sWhpY0TXPGPQQ"),
        ("BAACAgEAAyEFAATqVpOyAAILV2r6oGDu27A6KGen-52ogbzR1kmBAAIOCQAC1DvRR8HjFcjvEwABAz0E",
         "CgACAgEAAyEFAATqVpOyAAILWGr6oNxibBOSqmVt3yKVZ7euThM8AAIQCQAC1DvRR5sWhpY0TXPGPQQ"),
    ],
    "duck": [
        ("BAACAgEAAyEFAATqVpOyAAILVWr6nsKQpRdnImqhY43ny4cVfcR1AAIJCQAC1DvRR5YbvDIzHKu8PQQ",
         "CgACAgEAAyEFAATqVpOyAAILVmr6n_YE-CB9NTxC6-jQao51UnpVAAINCQAC1DvRR8ckJOYFpKnMPQQ"),
        ("BAACAgEAAyEFAATqVpOyAAILU2r6noki6co2BFJmChxt2XGjujglAAIHCQAC1DvRR0eGLpzbFnuEPQQ",
         "CgACAgEAAyEFAATqVpOyAAILVGr6noqZx1eHwT09RKGIQ26Q8cMwAAIICQAC1DvRR0g7CjOOyeZlPQQ"),
    ],
    "fifer": [
        ("BAACAgEAAyEFAATqVpOyAAILXGr6pCkAARlDkJKyhlcH36gw_o32rgACGwkAAtQ70Uccs7yw3n3rIz0E",
         "CgACAgEAAyEFAATqVpOyAAILXWr6pD1SIKDwSL5fWM0FVbjPECY4AAIcCQAC1DvRRzL6dewb_vcfPQQ"),
    ],
}

_admin_cache = {}

def mention(uid, name):
    if not uid:
        return name
    return f'<a href="tg://user?id={uid}">{name}</a>'

async def _can_video(bot, chat_id):
    if chat_id > 0:
        return True
    c = _admin_cache.get(chat_id)
    if c and time.time() - c[1] < 300:
        return c[0]
    try:
        me = await bot.get_me()
        cm = await bot.get_chat_member(chat_id, me.id)
        ok = cm.status in ("administrator", "creator")
        _admin_cache[chat_id] = (ok, time.time())
        return ok
    except Exception as e:
        print(f"media admin check error: {e}")
        return False

_milestone_pin = {}

async def _pin_it(bot, chat_id, msg):
    try:
        old = _milestone_pin.get(chat_id)
        if old:
            try:
                await bot.unpin_chat_message(chat_id, old)
            except Exception:
                pass
        await bot.pin_chat_message(chat_id, msg.message_id, disable_notification=True)
        _milestone_pin[chat_id] = msg.message_id
    except Exception as e:
        print(f"media pin error: {e}")

async def send_media(bot, chat_id, kind, caption=None, pin=False):
    items = MEDIA.get(kind)
    if not items:
        return False
    vid, gif = random.choice(items)
    pm = "HTML" if caption else None
    msg = None
    if vid and await _can_video(bot, chat_id):
        try:
            msg = await bot.send_video(chat_id, vid, caption=caption, parse_mode=pm)
        except Exception as e:
            print(f"media video error ({kind}): {e}")
    if msg is None and gif:
        try:
            msg = await bot.send_animation(chat_id, gif, caption=caption, parse_mode=pm)
        except Exception as e:
            print(f"media gif error ({kind}): {e}")
    if msg is None and caption:
        try:
            msg = await bot.send_message(chat_id, caption, parse_mode="HTML")
        except Exception as e:
            print(f"media text fallback error ({kind}): {e}")
    if msg is None:
        return False
    if pin and chat_id < 0:
        await _pin_it(bot, chat_id, msg)
    return msg
