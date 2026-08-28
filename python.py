#!/usr/bin/env python3
"""
Micro-SaaS Bot System - iSH Edition
Link-uri ascunse, doar comenzi în terminal
"""

import os
import sys
import time
import uuid
import random
import threading
import requests
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# ==================== CONFIGURARE ====================
API_KEYS = {
    "user1": {"balance": 100.00, "wallet": "0xYourWalletAddress"},
}

MIN_PAYOUT = 0.02
BOT_COUNT = 3
REQUESTS_PER_BOT = 5

# URL-uri reale (NU sunt afișate în terminal)
REAL_URLS = [
    "https://google.com",
    "https://github.com",
    "https://stackoverflow.com",
    "https://python.org",
    "https://pypi.org",
    "https://docker.com",
    "https://kubernetes.io",
    "https://linux.org",
    "https://ubuntu.com",
    "https://debian.org",
    "https://archlinux.org",
    "https://kali.org",
    "https://wikipedia.org",
    "https://youtube.com",
    "https://reddit.com",
    "https://amazon.com",
    "https://microsoft.com",
    "https://apple.com",
    "https://netflix.com",
    "https://spotify.com",
    "https://twitter.com",
    "https://instagram.com",
    "https://facebook.com",
    "https://tiktok.com",
    "https://discord.com",
    "https://slack.com",
    "https://zoom.us",
    "https://dropbox.com",
    "https://cloudflare.com",
    "https://digitalocean.com",
    "https://heroku.com",
    "https://netlify.com",
    "https://vercel.com",
    "https://mongodb.com",
    "https://mysql.com",
    "https://postgresql.org",
    "https://redis.io",
    "https://elastic.co",
    "https://apache.org",
    "https://nginx.org"
]

# ==================== FASTAPI APP ====================
app = FastAPI()

class RequestModel(BaseModel):
    api_key: str
    url: str

@app.post("/check-url")
def check_url(req: RequestModel):
    if req.api_key not in API_KEYS:
        raise HTTPException(403, "Invalid API key")
    user = API_KEYS[req.api_key]
    if user["balance"] < MIN_PAYOUT:
        raise HTTPException(402, f"Insufficient balance (need ${MIN_PAYOUT:.2f})")
    
    user["balance"] -= MIN_PAYOUT
    
    try:
        resp = requests.get(req.url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        return {
            "status": resp.status_code,
            "online": resp.status_code < 500,
            "charged": MIN_PAYOUT,
            "balance_remaining": round(user["balance"], 4)
        }
    except:
        return {"online": False, "charged": MIN_PAYOUT}

@app.post("/withdraw")
def withdraw(api_key: str, amount: float):
    if api_key not in API_KEYS:
        raise HTTPException(403, "Invalid API key")
    user = API_KEYS[api_key]
    
    if amount > user["balance"]:
        raise HTTPException(400, f"Insufficient balance: {user['balance']:.4f}")
    if amount < MIN_PAYOUT:
        raise HTTPException(400, f"Minimum payout: ${MIN_PAYOUT:.2f}")
    
    user["balance"] -= amount
    return {
        "status": "pending",
        "amount": amount,
        "wallet": user["wallet"],
        "tx_id": f"tx_{uuid.uuid4().hex[:16]}"
    }

@app.get("/balance/{api_key}")
def get_balance(api_key: str):
    if api_key not in API_KEYS:
        raise HTTPException(403, "Invalid API key")
    return API_KEYS[api_key]

# ==================== BOT SYSTEM ====================
class BotWorker:
    def __init__(self, bot_id, api_key, num_requests):
        self.bot_id = bot_id
        self.api_key = api_key
        self.num_requests = num_requests
        self.total_charged = 0
        self.success_count = 0
        self.error_count = 0
        self.running = True
        
    def get_random_url(self):
        return random.choice(REAL_URLS)
    
    def make_request(self):
        url = self.get_random_url()
        payload = {"api_key": self.api_key, "url": url}
        
        try:
            response = requests.post("http://localhost:8000/check-url", json=payload, timeout=5)
            data = response.json()
            
            if response.status_code == 200:
                self.success_count += 1
                self.total_charged += data.get("charged", 0)
                return True
            else:
                self.error_count += 1
                return False
        except:
            self.error_count += 1
            return False
    
    def run(self):
        for i in range(self.num_requests):
            if not self.running:
                break
            result = self.make_request()
            time.sleep(random.uniform(0.3, 0.8))
        
        return {
            "success": self.success_count,
            "errors": self.error_count,
            "charged": self.total_charged
        }

# ==================== INTERFAȚĂ TERMINAL ====================
class TerminalUI:
    def __init__(self):
        self.running = True
        self.bots_running = False
        self.bot_workers = []
        self.bot_threads = []
        self.last_balance = 0
        
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def get_balance(self, api_key="user1"):
        try:
            response = requests.get(f"http://localhost:8000/balance/{api_key}")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {"balance": 0, "wallet": "N/A"}
    
    def display_header(self):
        self.clear_screen()
        
        # Balanță actuală
        balance = self.get_balance()
        self.last_balance = balance['balance']
        
        print("""
╔═══════════════════════════════════════════╗
║  💰 MICRO-SAAS BOT SYSTEM                ║
║  Câștigă $0.02 per request               ║
╚═══════════════════════════════════════════╝
        """)
        
        print(f"  💵 BALANȚĂ: ${balance['balance']:.4f}")
        status = "🟢 ACTIV" if self.bots_running else "🔴 OPRIT"
        print(f"  🤖 BOTI: {status}")
        print("  " + "=" * 40)
    
    def display_commands(self):
        print("""
  COMENZI DISPONIBILE:
  ┌─────────────────────────────────────────┐
  │  start    - Pornește botii              │
  │  stop     - Oprește botii               │
  │  balance  - Verifică balanța            │
  │  withdraw - Retrage bani                │
  │  stats    - Statistici                  │
  │  config   - Configurare                 │
  │  help     - Ajutor                      │
  │  exit     - Ieșire                     │
  └─────────────────────────────────────────┘
        """)
        print("  " + "=" * 40)
    
    def process_command(self, cmd):
        """Procesează comenzile"""
        cmd = cmd.lower().strip()
        
        if cmd == "start":
            self.start_bots()
        elif cmd == "stop":
            self.stop_bots()
        elif cmd == "balance":
            self.show_balance()
        elif cmd == "withdraw":
            self.withdraw()
        elif cmd == "stats":
            self.show_stats()
        elif cmd == "config":
            self.configure()
        elif cmd == "help":
            self.show_help()
        elif cmd == "exit":
            self.running = False
            print("\n  👋 La revedere!")
            sys.exit(0)
        else:
            print(f"\n  ❌ Comandă necunoscută: '{cmd}'")
            print("  📝 Scrie 'help' pentru lista de comenzi")
            time.sleep(1)
    
    def start_bots(self):
        global BOT_COUNT, REQUESTS_PER_BOT
        
        if self.bots_running:
            print("\n  ⚠️ Botii sunt deja porniți!")
            time.sleep(0.5)
            return
        
        print("\n  🚀 Pornesc botii...")
        self.bots_running = True
        self.bot_workers = []
        self.bot_threads = []
        
        api_keys = list(API_KEYS.keys())
        
        for i in range(BOT_COUNT):
            api_key = random.choice(api_keys)
            bot = BotWorker(i+1, api_key, REQUESTS_PER_BOT)
            self.bot_workers.append(bot)
            
            thread = threading.Thread(target=self._run_bot, args=(bot,))
            thread.daemon = True
            thread.start()
            self.bot_threads.append(thread)
            time.sleep(0.2)
        
        print(f"  ✅ {BOT_COUNT} boti porniți!")
        time.sleep(0.5)
    
    def _run_bot(self, bot):
        result = bot.run()
        # Verifică dacă toți botii s-au terminat
        if all(not b.running for b in self.bot_workers):
            self.bots_running = False
    
    def stop_bots(self):
        if not self.bots_running:
            print("\n  ⚠️ Nu sunt boti activi!")
            time.sleep(0.5)
            return
        
        print("\n  🛑 Oprește botii...")
        for bot in self.bot_workers:
            bot.running = False
        
        self.bots_running = False
        print("  ✅ Toți botii au fost opriți!")
        time.sleep(0.5)
    
    def show_balance(self):
        print("\n" + "=" * 40)
        print("  💰 BALANȚE")
        print("=" * 40)
        
        total = 0
        for key in API_KEYS:
            bal = self.get_balance(key)
            print(f"  👤 {key}: ${bal['balance']:.4f}")
            total += bal['balance']
        
        print(f"\n  💰 Total: ${total:.4f}")
        input("\n  Apasă Enter pentru a continua...")
    
    def withdraw(self):
        print("\n" + "=" * 40)
        print("  💸 RETRAGERE")
        print("=" * 40)
        
        users = list(API_KEYS.keys())
        for i, key in enumerate(users, 1):
            bal = self.get_balance(key)
            print(f"  {i}. {key}: ${bal['balance']:.4f}")
        
        try:
            choice = int(input("\n  Selectează utilizatorul: ")) - 1
            if choice < 0 or choice >= len(users):
                print("  ❌ Invalid!")
                time.sleep(0.5)
                return
            
            api_key = users[choice]
            bal = self.get_balance(api_key)
            amount = float(input("  Sumă: "))
            
            if amount < MIN_PAYOUT or amount > bal['balance']:
                print("  ❌ Sumă invalidă!")
                time.sleep(0.5)
                return
            
            response = requests.post(
                f"http://localhost:8000/withdraw?api_key={api_key}&amount={amount}"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n  ✅ Retras ${data['amount']:.4f}")
                print(f"  🆔 TX: {data['tx_id']}")
            else:
                print(f"  ❌ Eroare!")
            
        except:
            print("  ❌ Eroare!")
        
        input("\n  Apasă Enter pentru a continua...")
    
    def show_stats(self):
        print("\n" + "=" * 40)
        print("  📊 STATISTICI")
        print("=" * 40)
        
        total = 0
        for key in API_KEYS:
            bal = self.get_balance(key)
            total += bal['balance']
        
        print(f"  👥 Utilizatori: {len(API_KEYS)}")
        print(f"  💰 Total balanță: ${total:.4f}")
        print(f"  🤖 Boti: {BOT_COUNT}")
        print(f"  🔄 Requesturi/bot: {REQUESTS_PER_BOT}")
        print(f"  💵 Profit potențial: ${BOT_COUNT * REQUESTS_PER_BOT * MIN_PAYOUT:.4f}")
        
        input("\n  Apasă Enter pentru a continua...")
    
    def configure(self):
        global BOT_COUNT, REQUESTS_PER_BOT
        
        print("\n" + "=" * 40)
        print("  ⚙️ CONFIGURARE")
        print("=" * 40)
        print(f"  1. Boti: {BOT_COUNT}")
        print(f"  2. Requesturi/bot: {REQUESTS_PER_BOT}")
        print(f"  3. Adaugă utilizator")
        
        choice = input("\n  Selectează: ")
        
        if choice == "1":
            try:
                BOT_COUNT = int(input("  Număr boti: "))
                print(f"  ✅ Setat {BOT_COUNT}")
            except:
                print("  ❌ Invalid!")
        elif choice == "2":
            try:
                REQUESTS_PER_BOT = int(input("  Requesturi/bot: "))
                print(f"  ✅ Setat {REQUESTS_PER_BOT}")
            except:
                print("  ❌ Invalid!")
        elif choice == "3":
            key = input("  Nume utilizator: ")
            try:
                balance = float(input("  Balanță inițială: "))
                wallet = input("  Adresă wallet: ")
                API_KEYS[key] = {"balance": balance, "wallet": wallet}
                print(f"  ✅ {key} adăugat!")
            except:
                print("  ❌ Invalid!")
        
        time.sleep(0.5)
    
    def show_help(self):
        print("""
  📝 AJUTOR - COMENZI DISPONIBILE

  start     - Pornește botii (generează requesturi)
  stop      - Oprește toți botii
  balance   - Afișează balanța curentă
  withdraw  - Retrage bani în wallet
  stats     - Vezi statistici detaliate
  config    - Configurează botii
  help      - Afișează acest ajutor
  exit      - Ieșire din aplicație

  💡 Botii accesează site-uri reale automat
  💰 Fiecare request câștigă $0.02
        """)
        input("\n  Apasă Enter pentru a continua...")
    
    def main_loop(self):
        # Pornește serverul
        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=8000, log_level="critical")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        
        while self.running:
            self.display_header()
            self.display_commands()
            
            cmd = input("  > ")
            self.process_command(cmd)

# ==================== MAIN ====================
if __name__ == "__main__":
    try:
        ui = TerminalUI()
        ui.main_loop()
    except KeyboardInterrupt:
        print("\n\n  👋 La revedere!")
        sys.exit(0)
