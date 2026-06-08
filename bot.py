#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
777 BigWin Auto Bet Bot - Fixed Stop Loss Logic & Fast Loop
"""

import requests
import json
import time
import hashlib
import random
import threading
from datetime import datetime
from collections import deque, Counter

# ==================== CONFIG ====================
BOT_TOKEN = "8978079117:AAE7CPRk01NAh4eqn-g0CWYwNa0CFJBIdfc"
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
API_BASE = "https://api.bigwinqaz.com/api/webapi/"

http_session = requests.Session()

GAME_TYPES = {
    "1": {"name": "🎲 Wingo 30s",      "typeId": 30, "wait_sec": 28, "is_trx": False},
    "2": {"name": "⏱️ Wingo 1 Minute", "typeId": 1,  "wait_sec": 58, "is_trx": False},
    "3": {"name": "⚡ TRX Wingo 1 Minute", "typeId": 13, "wait_sec": 58, "is_trx": True},
}
DEFAULT_GAME_TYPE = "1"

BASE_AMOUNT = 10
DEFAULT_BETTING_SEQUENCE = [1, 3, 9, 27, 81, 243, 729, 2187] 

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://777bigwingame.vip",
    "Referer": "https://777bigwingame.vip/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ==================== API CLASS ====================
class LotteryAPI:
    def __init__(self):
        self.headers = HEADERS.copy()
        self.token = ""

    def sign_md5(self, data_dict):
        sign_data = data_dict.copy()
        for k in ['signature','timestamp']:
            if k in sign_data: del sign_data[k]
        sorted_data = dict(sorted(sign_data.items()))
        hash_string = json.dumps(sorted_data, separators=(',', ':')).replace(' ', '')
        return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    def random_key(self):
        xxxx = "xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx"
        return ''.join(random.choice('0123456789abcdef') if c=='x' else random.choice('89a') if c=='y' else c for c in xxxx)

    def login(self, phone, password):
        try:
            clean_phone = phone.replace("95", "") if phone.startswith("95") else phone
            username = f"95{clean_phone}"
            body = {
                "phonetype": -1, "language": 0, "logintype": "mobile",
                "random": "9078efc98754430e92e51da59eb2563c",
                "username": username, "pwd": password, "timestamp": int(time.time())
            }
            body["signature"] = self.sign_md5(body).upper()
            resp = http_session.post(f"{API_BASE}Login", headers=self.headers, json=body, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if data.get('msgCode') == 0:
                    tok = data.get('data', {})
                    self.token = f"{tok.get('tokenHeader','')}{tok.get('token','')}"
                    self.headers["Authorization"] = self.token
                    return True, "✅ Login Successful! (777 BigWin)"
                return False, data.get('msg', 'Login Failed')
            return False, f"API Error {resp.status_code}"
        except Exception as e:
            return False, f"Login Error: {e}"

    def get_balance(self):
        try:
            body = {"language":0,"random":"9078efc98754430e92e51da59eb2563c","timestamp":int(time.time())}
            body["signature"] = self.sign_md5(body).upper()
            resp = http_session.post(f"{API_BASE}GetBalance", headers=self.headers, json=body, timeout=4)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('msgCode') == 0:
                    return float(d.get('data',{}).get('amount', 0))
            return 0.0
        except:
            return 0.0

    def get_current_issue(self, type_id):
        try:
            body = {"typeId": type_id, "language":0, "random":"b05034ba4a2642009350ee863f29e2e9", "timestamp":int(time.time())}
            body["signature"] = self.sign_md5(body).upper()
            resp = http_session.post(f"{API_BASE}GetGameIssue", headers=self.headers, json=body, timeout=4)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('msgCode') == 0:
                    return d.get('data',{}).get('issueNumber','')
            return ""
        except:
            return ""

    def place_bet(self, issue, base_amount, bet_count, bet_type, type_id):
        try:
            body = {
                "typeId": type_id, "issuenumber": issue, "language": 0, "gameType": 2,
                "amount": base_amount, "betCount": bet_count, "selectType": bet_type,
                "random": self.random_key(), "timestamp": int(time.time())
            }
            body["signature"] = self.sign_md5(body).upper()
            resp = http_session.post(f"{API_BASE}GameBetting", headers=self.headers, json=body, timeout=4)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('code') == 0 or d.get('msgCode') == 0:
                    total_bet = base_amount * bet_count
                    profit = int(total_bet * 0.96)
                    return True, "Bet placed", profit
                return False, d.get('msg','Bet failed'), 0
            return False, f"API error {resp.status_code}", 0
        except Exception as e:
            return False, f"Bet error: {e}", 0

    def get_recent_results(self, count, type_id, is_trx=False):
        try:
            if is_trx:
                endpoint = f"{API_BASE}GetTRXNoaverageEmerdList"
            else:
                endpoint = f"{API_BASE}GetNoaverageEmerdList"
            body = {
                "pageNo": 1, "pageSize": count, "language": 0, "typeId": type_id,
                "random": "6DEB0766860C42151A193692ED16D65A", "timestamp": int(time.time())
            }
            body["signature"] = self.sign_md5(body).upper()
            resp = http_session.post(endpoint, headers=self.headers, json=body, timeout=4)
            if resp.status_code == 200:
                d = resp.json()
                if d.get('msgCode') == 0:
                    if is_trx:
                        games = d.get('data', {}).get('data', {}).get('gameslist', [])
                    else:
                        games = d.get('data', {}).get('list', [])
                    return games
            return []
        except:
            return []

# ==================== SESSION STORAGE ====================
user_sessions = {}

# ==================== TELEGRAM HELPERS ====================
def send_message(chat_id, text, reply_markup=None, **kwargs):
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup: payload["reply_markup"] = json.dumps(reply_markup)
    try: http_session.post(url, json=payload, timeout=4)
    except: pass

def get_updates(offset=None):
    url = f"{TELEGRAM_API}/getUpdates"
    params = {"timeout": 10}
    if offset: params["offset"] = offset
    try:
        resp = http_session.get(url, params=params, timeout=12)
        if resp.status_code == 200: return resp.json().get("result", [])
    except: pass
    return []

# ==================== KEYBOARDS ====================
def get_login_keyboard():
    return {"keyboard": [["🔐 Login"]], "resize_keyboard": True}

def get_main_keyboard():
    return {"keyboard": [
        ["🎮 Game Type", "🧧 Bet Amount"],
        ["📚 Strategy", "🧧 Profit Target"],
        ["🛑 Stop Loss", "🔁 Layer"],
        ["🔄 Test Mode", "ℹ️ Info"],
        ["▶️ Start", "⏹️ Stop"],
        ["🚪 Logout"]
    ], "resize_keyboard": True}

def get_game_type_keyboard():
    buttons = [[gt["name"]] for gt in GAME_TYPES.values()]
    buttons.append(["◀️ Back"])
    return {"keyboard": buttons, "resize_keyboard": True}

def get_strategy_keyboard():
    return {"keyboard": [
        ["📊 Pattern Analyzer", "🥇 Menus 1.6 Ultra"],
        ["🧠 Manus AI", "📈 Trend Follow"],
        ["🎨 Custom BS Pattern", "✨ Wingo Advanced"],
        ["◀️ Back"]
    ], "resize_keyboard": True}

# ==================== STRATEGY CLASSES ====================
class PatternAnalyzerStrategy:
    def __init__(self):
        self.recent_history = []
    def add_result(self, result):
        self.recent_history.append(result)
        if len(self.recent_history) > 50: self.recent_history.pop(0)
    def predict(self):
        if len(self.recent_history) < 3: return random.choice(['B', 'S']), 0.5
        return ('B' if self.recent_history[-1] == 'S' else 'S'), 0.6

class MenusUltraStrategy:
    def __init__(self):
        self.history = []
    def add_result(self, result):
        self.history.append(result)
        if len(self.history) > 50: self.history.pop(0)
    def predict(self):
        if len(self.history) < 5: return random.choice(['B', 'S']), 50
        scores = {'B': 0, 'S': 0}
        if self.history[0] == self.history[1] == self.history[2]: scores[self.history[0]] += 35
        pred = 'B' if scores['B'] > scores['S'] else 'S'
        return pred, 75

class ManusAIStrategy:
    def __init__(self): self.last_result = 'B'
    def add_result(self, result): self.last_result = result
    def predict(self): return ('B' if self.last_result == 'S' else 'S'), 70

class TrendFollowStrategy:
    def __init__(self):
        self.history = []
        self.cycle_count = 0
    def add_result(self, result):
        self.history.append(result)
        self.cycle_count = len(self.history) % 6
    def predict(self):
        if not self.history: return random.choice(['B', 'S']), 50
        return (self.history[-1] if self.cycle_count < 3 else ('B' if self.history[-1] == 'S' else 'S')), 60

class CustomBSStrategy:
    def __init__(self, pattern_str):
        self.pattern = [c for c in pattern_str.upper() if c in 'BS']
        self.index = 0
        if not self.pattern: self.pattern = ['B', 'S']
    def add_result(self, result): pass
    def predict(self):
        val = self.pattern[self.index % len(self.pattern)]
        self.index += 1
        return val, 80

class WingoAdvancedStrategy:
    def __init__(self):
        self.history = []
        self.patterns = {
            "BBBBB": "SMALL", "SSSSS": "BIG", "BBBB": "BIG", "SSSS": "SMALL",
            "BBB": "BIG", "SSS": "SMALL", "BSBSB": "SMALL", "SBSBS": "BIG"
        }
    def add_result(self, result):
        self.history.append(result)
        if len(self.history) > 50: self.history.pop(0)
    def predict(self):
        if len(self.history) < 3: return random.choice(['B', 'S']), 50
        history_str = ''.join(self.history)
        for p in sorted(self.patterns.keys(), key=len, reverse=True):
            if history_str.endswith(p):
                return ('B' if self.patterns[p] == "BIG" else 'S'), 85
        return random.choice(['B', 'S']), 50

# ==================== UI MESSAGES ====================
def format_stylish_info(sess):
    api = sess['api']
    bal = api.get_balance() if api and api.token else 0.0
    game_name = GAME_TYPES[sess.get('game_key', DEFAULT_GAME_TYPE)]['name']
    strategy_display = sess.get('strategy', 'None').upper()
    bet_seq = sess.get('betting_sequence', DEFAULT_BETTING_SEQUENCE)
    profit_target = sess.get('profit_target', 0.0)
    stop_loss = sess.get('stop_loss', 0.0)
    mode = "🧪 TEST MODE" if sess.get('test_mode', False) else "💰 REAL MODE"
    
    return f"""
🔋 *777 BIGWIN BOT ACTIVE*
🔄 *Mode:* {mode}
🎲 *Game:* {game_name}
💳 *Balance:* `{bal:.2f} Ks`
🎯 *Sequence:* `{bet_seq}`
📚 *Strategy:* {strategy_display}
🧧 *Profit Target:* `{profit_target:.2f} Ks`
🌡️ *Stop Loss:* `{stop_loss:.2f} Ks`
"""

def send_info(chat_id, user_id):
    sess = user_sessions.get(user_id)
    if not sess or not sess.get('api') or not sess['api'].token:
        send_message(chat_id, "❌ Not logged in. Please /start.", reply_markup=get_login_keyboard())
        return
    send_message(chat_id, format_stylish_info(sess), reply_markup=get_main_keyboard())

def send_bet_message(chat_id, amount, bet_name, issue, game_name, test_mode):
    prefix = "🧪 TEST MODE \n" if test_mode else ""
    send_message(chat_id, f"{prefix}🎮 🃏 777 BIGWIN\n🎯 *𝑩𝒆𝒕:* {bet_name} `{amount:.2f} Ks`\n🧭 {game_name}: `{issue}`")

def send_result_message(chat_id, win, result_num, actual, profit, balance, total_profit, test_mode):
    header = f"🏆 *အနိုင်ရရှိသည်* `+{profit:.2f} Ks`" if win else f"⛔ *ပါသွားပါပြီ* `{profit:.2f} Ks`"
    if test_mode: header = "🧪 " + header
    msg = f"""{header}
════════════════════════
📊 *ရလဒ်:* {actual} (`{result_num}`)
🧩 *လက်ကျန်ငွေ:* `{balance:.2f} Ks`
📈 *𝑻𝒐𝒕𝒂𝒍 𝑷𝒓𝒐𝒇𝒊𝒕:* `{total_profit:+.2f} Ks`"""
    send_message(chat_id, msg)

# ==================== BETTING LOOP ====================
def betting_loop(user_id, chat_id):
    sess = user_sessions.get(user_id)
    if not sess: return
    api = sess['api']
    
    initial_balance = api.get_balance()
    while initial_balance <= 0:
        time.sleep(1.0)
        initial_balance = api.get_balance()
    sess['initial_balance'] = initial_balance

    seq = sess.get('betting_sequence', DEFAULT_BETTING_SEQUENCE)
    step = sess.get('current_step', 0)
    total = sess.get('total_profit', 0.0)
    loss_streak = sess.get('loss_streak', 0)
    stop_loss = sess.get('stop_loss', 0.0)
    profit_target = sess.get('profit_target', 0.0)
    loss_limit = sess.get('loss_streak_limit', 0)
    strategy_name = sess.get('strategy', 'manus_ai')
    game_key = sess.get('game_key', DEFAULT_GAME_TYPE)
    game_type = GAME_TYPES[game_key]
    game_type_id = game_type['typeId']
    wait_sec = game_type['wait_sec']
    is_trx = game_type['is_trx']
    game_name = game_type['name']
    test_mode = sess.get('test_mode', False)
    custom_pattern = sess.get('custom_pattern', '')
    
    if strategy_name == 'pattern_analyzer': strategy = PatternAnalyzerStrategy()
    elif strategy_name == 'menus_ultra': strategy = MenusUltraStrategy()
    elif strategy_name == 'manus_ai': strategy = ManusAIStrategy()
    elif strategy_name == 'trend_follow': strategy = TrendFollowStrategy()
    elif strategy_name == 'custom_bs': strategy = CustomBSStrategy(custom_pattern)
    elif strategy_name == 'wingo_advanced': strategy = WingoAdvancedStrategy()
    else: strategy = ManusAIStrategy()

    last_issue = None
    while sess.get('is_running') and not sess.get('stop_flag'):
        current_balance = api.get_balance()
        if current_balance <= 0:
            time.sleep(0.5)
            continue
            
        if stop_loss > 0:
            actual_loss = sess['initial_balance'] - current_balance
            if actual_loss > 0 and actual_loss >= stop_loss:
                send_message(chat_id, f"🛑 *Stop Loss reached!* Actual Loss: `{actual_loss:.2f} Ks`")
                break
                
        if profit_target > 0 and total >= profit_target:
            send_message(chat_id, f"🎯 *Profit Target reached!* Profit: `{total:.2f} Ks`")
            break

        issue = api.get_current_issue(game_type_id)
        if not issue or issue == last_issue:
            time.sleep(0.4) 
            continue

        pred_char, _ = strategy.predict()
        bet_type = 13 if pred_char == 'B' else 14
        bet_name = "BIG" if bet_type == 13 else "SMALL"
        
        bet_count = seq[step % len(seq)]
        total_amount = BASE_AMOUNT * bet_count
        
        if not test_mode and total_amount > current_balance:
            send_message(chat_id, f"❌ *Insufficient balance:* need `{total_amount}`, have `{current_balance}`")
            break

        if test_mode:
            send_bet_message(chat_id, total_amount, bet_name, issue, game_name, True)
            last_issue = issue
        else:
            ok, msg, _ = api.place_bet(issue, BASE_AMOUNT, bet_count, bet_type, game_type_id)
            if not ok:
                if "settled" in msg.lower(): last_issue = issue
                else: time.sleep(0.5)
                continue
            send_bet_message(chat_id, total_amount, bet_name, issue, game_name, False)
            last_issue = issue

        result_num = None
        start_time = time.time()
        max_wait = wait_sec + 15
        while (time.time() - start_time) < max_wait and sess.get('is_running') and not sess.get('stop_flag'):
            time.sleep(1.0)
            recents = api.get_recent_results(5, game_type_id, is_trx)
            for r in recents:
                if str(r.get('issueNumber')) == issue:
                    result_num = int(r.get('number', 0))
                    break
            if result_num is not None: break

        if result_num is not None:
            actual_char = 'B' if result_num >= 5 else 'S'
            actual_name = "BIG" if actual_char == 'B' else "SMALL"
            win = (pred_char == actual_char)
            
            if win:
                profit = total_amount * 0.96
                step = 0 
                loss_streak = 0
            else:
                profit = -total_amount
                step = (step + 1) % len(seq) 
                loss_streak += 1
                
            total += profit
            strategy.add_result(actual_char)
            sess['current_step'] = step
            sess['total_profit'] = total
            sess['loss_streak'] = loss_streak
            
            new_balance = api.get_balance()
            send_result_message(chat_id, win, result_num, actual_name, profit, new_balance, total, test_mode)
            if loss_limit > 0 and loss_streak >= loss_limit:
                send_message(chat_id, f"🛑 *Loss limit reached!* Stopped.")
                break
        else:
            time.sleep(1.0)

    sess['is_running'] = False
    send_message(chat_id, "🔴 Auto betting loop finished.")

# ==================== LOGIN WORKER THREAD ====================
def login_worker(chat_id, user_id, phone, pwd):
    sess = user_sessions[user_id]
    api = LotteryAPI()
    ok, msg = api.login(phone, pwd)
    if ok:
        sess['api'] = api
        sess['phone'] = phone
        sess['initial_balance'] = api.get_balance()
        sess['login_step'] = None
        send_message(chat_id, f"{msg}\n💰 Balance: `{sess['initial_balance']:.2f} Ks`", reply_markup=get_main_keyboard())
        send_info(chat_id, user_id)
    else:
        send_message(chat_id, f"❌ {msg}\nPlease /start again.", reply_markup=get_login_keyboard())
        sess['login_step'] = None

# ==================== MESSAGE HANDLER ====================
def process_message(chat_id, text, user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            'api': None, 'phone': None, 'betting_sequence': DEFAULT_BETTING_SEQUENCE.copy(),
            'current_step': 0, 'total_profit': 0.0, 'loss_streak': 0, 'win_streak': 0,
            'pattern_history': [], 'is_running': False, 'stop_flag': False,
            'initial_balance': 0.0, 'stop_loss': 0.0, 'profit_target': 0.0, 'strategy': 'none',
            'game_key': DEFAULT_GAME_TYPE, 'custom_pattern': '', 'test_mode': False,
            'loss_streak_limit': 0, 'login_step': None, 'login_phone': None
        }

    sess = user_sessions[user_id]

    if text == "🔐 Login":
        sess['login_step'] = 'phone'
        send_message(chat_id, "📱 Enter your *phone number* (without 95):")
        return
    if sess.get('login_step') == 'phone':
        sess['login_phone'] = text.strip()
        sess['login_step'] = 'password'
        send_message(chat_id, "🔑 Enter your *Password*:")
        return
    if sess.get('login_step') == 'password':
        phone = sess['login_phone']
        pwd = text.strip()
        send_message(chat_id, "⏳ Logging in... Please wait...")
        threading.Thread(target=login_worker, args=(chat_id, user_id, phone, pwd), daemon=True).start()
        return

    if not sess.get('api') or not sess['api'].token:
        send_message(chat_id, "Please login first.", reply_markup=get_login_keyboard())
        return

    if text == "🎮 Game Type":
        send_message(chat_id, "Select game type:", reply_markup=get_game_type_keyboard())
        return
    for key, gt in GAME_TYPES.items():
        if text == gt['name']:
            sess['game_key'] = key
            send_message(chat_id, f"✅ Game type set to: *{gt['name']}*", reply_markup=get_main_keyboard())
            return
    if text == "◀️ Back":
        send_message(chat_id, "Main menu:", reply_markup=get_main_keyboard())
        return

    if text == "🧧 Bet Amount":
        send_message(chat_id, "Enter your betCount sequence.\n*Example:* `1,3,9,27` \n(Base amount is 10)")
        sess['setting_seq'] = True
        return
    if sess.get('setting_seq'):
        try:
            seq = [int(x.strip()) for x in text.split(',')]
            if all(x > 0 for x in seq):
                sess['betting_sequence'] = seq
                sess['current_step'] = 0
                send_message(chat_id, f"✅ Updated: `{seq}`", reply_markup=get_main_keyboard())
            else: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        except: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        sess['setting_seq'] = False
        return

    if text == "🔁 Layer":
        send_message(chat_id, "Enter consecutive loss limit (0 = disabled):")
        sess['setting_loss_limit'] = True
        return
    if sess.get('setting_loss_limit'):
        try:
            sess['loss_streak_limit'] = int(text)
            send_message(chat_id, f"✅ Set to `{text}`", reply_markup=get_main_keyboard())
        except: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        sess['setting_loss_limit'] = False
        return

    if text == "📚 Strategy":
        send_message(chat_id, "Select strategy:", reply_markup=get_strategy_keyboard())
        return
    if text in ["📊 Pattern Analyzer", "🥇 Menus 1.6 Ultra", "🧠 Manus AI", "📈 Trend Follow", "🎨 Custom BS Pattern", "✨ Wingo Advanced"]:
        if text == "📊 Pattern Analyzer": sess['strategy'] = 'pattern_analyzer'
        elif text == "🥇 Menus 1.6 Ultra": sess['strategy'] = 'menus_ultra'
        elif text == "🧠 Manus AI": sess['strategy'] = 'manus_ai'
        elif text == "📈 Trend Follow": sess['strategy'] = 'trend_follow'
        elif text == "✨ Wingo Advanced": sess['strategy'] = 'wingo_advanced'
        elif text == "🎨 Custom BS Pattern":
            send_message(chat_id, "Enter pattern (e.g. BBSB):")
            sess['awaiting_custom_pattern'] = True
            return
        send_message(chat_id, f"✅ Strategy set", reply_markup=get_main_keyboard())
        return
        
    if sess.get('awaiting_custom_pattern'):
        pattern = text.upper().replace(' ', '')
        if all(c in 'BS' for c in pattern) and pattern:
            sess['custom_pattern'] = pattern
            sess['strategy'] = 'custom_bs'
            send_message(chat_id, f"✅ Custom Set: `{pattern}`", reply_markup=get_main_keyboard())
        else: send_message(chat_id, "❌ Error", reply_markup=get_strategy_keyboard())
        sess['awaiting_custom_pattern'] = False
        return

    if text == "🧧 Profit Target":
        send_message(chat_id, "Enter profit target (0 = disabled):")
        sess['setting_profit_target'] = True
        return
    if sess.get('setting_profit_target'):
        try:
            sess['profit_target'] = float(text)
            send_message(chat_id, "✅ Done", reply_markup=get_main_keyboard())
        except: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        sess['setting_profit_target'] = False
        return

    if text == "🛑 Stop Loss":
        send_message(chat_id, "Enter stop loss (0 = disabled):")
        sess['setting_stop_loss'] = True
        return
    if sess.get('setting_stop_loss'):
        try:
            sess['stop_loss'] = float(text)
            send_message(chat_id, "✅ Done", reply_markup=get_main_keyboard())
        except: send_message(chat_id, "❌ Error", reply_markup=get_main_keyboard())
        sess['setting_stop_loss'] = False
        return

    if text == "🔄 Test Mode":
        sess['test_mode'] = not sess.get('test_mode', False)
        send_message(chat_id, f"✅ Switched Mode", reply_markup=get_main_keyboard())
        return

    if text == "ℹ️ Info":
        threading.Thread(target=send_info, args=(chat_id, user_id), daemon=True).start()
        return

    if text == "▶️ Start":
        if sess.get('strategy') == 'none':
            send_message(chat_id, "⚠️ Set strategy first.")
            return
        if sess.get('is_running'):
            send_message(chat_id, "Already running.")
        else:
            sess['total_profit'] = 0.0
            sess['current_step'] = 0
            sess['loss_streak'] = 0
            sess['is_running'] = True
            sess['stop_flag'] = False
            threading.Thread(target=betting_loop, args=(user_id, chat_id), daemon=True).start()
        return

    if text == "⏹️ Stop":
        sess['stop_flag'] = True
        sess['is_running'] = False
        send_message(chat_id, "⏹️ Bot stopping...")
        return

    if text == "🚪 Logout":
        sess['stop_flag'] = True
        sess['is_running'] = False
        user_sessions[user_id] = {}
        send_message(chat_id, "✅ Logged out.", reply_markup=get_login_keyboard())
        return

# ==================== MAIN LOOP ====================
def main():
    print("🤖 Bot is starting (Fixed Stop Loss Logic)...")
    last_update_id = 0
    while True:
        updates = get_updates(offset=last_update_id + 1)
        for update in updates:
            last_update_id = update['update_id']
            if 'message' in update:
                msg = update['message']
                chat_id = msg['chat']['id']
                user_id = msg['from']['id']
                text = msg.get('text', '')
                if text == '/start':
                    send_message(chat_id, "* Joker 777 BIGWIN Bot *\n\nClick *Login* to start.", reply_markup=get_login_keyboard())
                else:
                    threading.Thread(target=process_message, args=(chat_id, text, user_id), daemon=True).start()
        time.sleep(0.2)

if __name__ == "__main__":
    main()
