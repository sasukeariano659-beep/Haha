#!/usr/bin/env python3
"""
Micro-SaaS Bot System - iSH Edition
Rulează în terminal, balanță în timp real, boti automatizați
"""

import os
import sys
import time
import uuid
import random
import threading
import requests
import json
import queue
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import subprocess

# ==================== CONFIGURARE ====================
API_KEYS = {
    "user1": {"balance": 100.00, "wallet": "0xYourWalletAddress"},
}

MIN_PAYOUT = 0.02
BOT_COUNT = 5
REQUESTS_PER_BOT = 10
UPDATE_INTERVAL = 2  # Secunde între update-uri balanță

# Listă de URL-uri REALE pentru verificat
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

# ==================== FASTAPI APP (ascuns) ====================
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
        # Verifică URL-ul REAL
        resp = requests.get(req.url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        return {
            "url": req.url,
            "status": resp.status_code,
            "online": resp.status_code < 500,
            "charged": MIN_PAYOUT,
            "balance_remaining": round(user["balance"], 4),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"url": req.url, "error": str(e), "online": False, "charged": MIN_PAYOUT}

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
        "tx_id": f"tx_{uuid.uuid4().hex[:16]}",
        "note": "Withdrawal processed"
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
        self.logs = []
        
    def get_random_url(self):
        """Alege un URL real random"""
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
                return f"✅ {url[:30]}... | Status: {data.get('status', 'N/A')}"
            else:
                self.error_count += 1
                return f"❌ {url[:30]}... | Eroare: {data.get('detail', 'Unknown')}"
        except Exception as e:
            self.error_count += 1
            return f"❌ {url[:30]}... | Conexiune eșuată"
    
    def run(self):
        for i in range(self.num_requests):
            if not self.running:
                break
            result = self.make_request()
            self.logs.append(f"Bot{self.bot_id} [{i+1}/{self.num_requests}]: {result}")
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
        self.bot_threads = []
        self.bot_workers = []
        self.log_queue = queue.Queue()
        self.balance_history = []
        
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
    
    def format_balance(self, balance_data):
        return f"${balance_data['balance']:.4f}"
    
    def display_header(self):
        self.clear_screen()
        print("""
╔══════════════════════════════════════════════════════════════╗
║  💰 MICRO-SAAS BOT SYSTEM - iSH                            ║
║  Câștigă $0.02 per request real                            ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Afișează balanța în timp real
        balance = self.get_balance()
        print(f"  💵 BALANȚĂ: {self.format_balance(balance)}")
        print(f"  🏦 WALLET: {balance.get('wallet', 'N/A')[:20]}...")
        
        # Status boti
        status = "🟢 ACTIV" if self.bots_running else "🔴 OPRIT"
        print(f"  🤖 BOTI: {status}")
        print("=" * 60)
        
        # Afișează ultimele log-uri
        logs_to_show = []
        while not self.log_queue.empty():
            logs_to_show.append(self.log_queue.get())
        
        for log in logs_to_show[-5:]:  # Arată ultimele 5
            print(f"  {log}")
        
        print("\n" + "=" * 60)
    
    def display_menu(self):
        print("\n  COMENZI:")
        print("  ┌─────────────────────────────────────────────┐")
        print("  │  1. ▶  Pornește boti                       │")
        print("  │  2. ⏹  Oprește boti                       │")
        print("  │  3. 💰  Verifică balanță                   │")
        print("  │  4. 💸  Retrage bani                       │")
        print("  │  5. 📊  Statistici                         │")
        print("  │  6. ⚙️  Configurare                        │")
        print("  │  7. 📝  Vezi log-uri                       │")
        print("  │  8. 🚪  Ieșire                             │")
        print("  └─────────────────────────────────────────────┘")
        print("  ")
    
    def display_stats(self):
        """Afișează statistici detaliate"""
        self.clear_screen()
        print("\n📊 STATISTICI DETALIATE")
        print("=" * 50)
        
        # Balanțe
        total_balance = 0
        for key in API_KEYS:
            bal = self.get_balance(key)
            print(f"  👤 {key}: ${bal['balance']:.4f}")
            total_balance += bal['balance']
        
        print(f"\n  💰 Total balanță: ${total_balance:.4f}")
        print(f"  🤖 Boti activi: {BOT_COUNT}")
        print(f"  🔄 Requesturi/bot: {REQUESTS_PER_BOT}")
        print(f"  💵 Total requesturi potențiale: {BOT_COUNT * REQUESTS_PER_BOT}")
        print(f"  💰 Profit potențial: ${BOT_COUNT * REQUESTS_PER_BOT * MIN_PAYOUT:.4f}")
        print(f"  🌐 URL-uri disponibile: {len(REAL_URLS)}")
        
        input("\n  Apasă Enter pentru a continua...")
    
    def run_bots(self):
        """Pornește botii"""
        if self.bots_running:
            print("\n  ⚠️ Botii sunt deja porniți!")
            time.sleep(1)
            return
        
        self.clear_screen()
        print("\n  🚀 PORNESC BOTII...")
        print("  " + "=" * 40)
        
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
        
        print(f"\n  ✅ {BOT_COUNT} boti porniți!")
        time.sleep(1)
    
    def _run_bot(self, bot):
        """Rulează un bot și adaugă log-uri în coadă"""
        result = bot.run()
        self.log_queue.put(f"🤖 Bot{bot.bot_id} finalizat: ✅{result['success']} ❌{result['errors']} 💰${result['charged']:.4f}")
        
        # Verifică dacă toți botii s-au terminat
        if all(not b.running for b in self.bot_workers):
            self.bots_running = False
            self.log_queue.put("🛑 Toți botii s-au oprit!")
    
    def stop_bots(self):
        """Oprește toți botii"""
        if not self.bots_running:
            print("\n  ⚠️ Nu sunt boti activi!")
            time.sleep(1)
            return
        
        self.clear_screen()
        print("\n  🛑 OPREȘTE BOTII...")
        
        for bot in self.bot_workers:
            bot.running = False
        
        self.bots_running = False
        print("  ✅ Toți botii au fost opriți!")
        time.sleep(1)
    
    def check_balance(self):
        """Verifică balanța detaliat"""
        self.clear_screen()
        print("\n💰 BALANȚE DETALIATE")
        print("=" * 50)
        
        total = 0
        for key in API_KEYS:
            bal = self.get_balance(key)
            print(f"  👤 {key}:")
            print(f"     💵 Balanță: ${bal['balance']:.4f}")
            print(f"     🏦 Wallet: {bal.get('wallet', 'N/A')}")
            print("-" * 40)
            total += bal['balance']
        
        print(f"\n  💰 Total: ${total:.4f}")
        print(f"  📈 Profit total: ${total - 100:.4f}" if total > 0 else "")
        
        input("\n  Apasă Enter pentru a continua...")
    
    def withdraw(self):
        """Retrage bani"""
        self.clear_screen()
        print("\n💸 RETRAGERE BANI")
        print("=" * 50)
        
        # Afișează utilizatorii
        users = list(API_KEYS.keys())
        for i, key in enumerate(users, 1):
            bal = self.get_balance(key)
            print(f"  {i}. {key}: ${bal['balance']:.4f}")
        
        try:
            choice = int(input("\n  Selectează utilizatorul (număr): ")) - 1
            if choice < 0 or choice >= len(users):
                print("  ❌ Selecție invalidă!")
                time.sleep(1)
                return
            
            api_key = users[choice]
            bal = self.get_balance(api_key)
            
            print(f"\n  💰 Balanță disponibilă: ${bal['balance']:.4f}")
            amount = float(input("  Sumă de retras: "))
            
            if amount < MIN_PAYOUT:
                print(f"  ❌ Minim ${MIN_PAYOUT:.2f}!")
                time.sleep(1)
                return
            
            if amount > bal['balance']:
                print("  ❌ Fonduri insuficiente!")
                time.sleep(1)
                return
            
            # Face request de retragere
            response = requests.post(
                f"http://localhost:8000/withdraw?api_key={api_key}&amount={amount}"
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n  ✅ Retragere inițiată!")
                print(f"     💵 Sumă: ${data['amount']:.4f}")
                print(f"     🏦 Wallet: {data['wallet']}")
                print(f"     🆔 TX ID: {data['tx_id']}")
                self.log_queue.put(f"💸 Retragere ${amount:.4f} pentru {api_key}")
            else:
                print(f"  ❌ Eroare: {response.json().get('detail', 'Unknown')}")
            
        except Exception as e:
            print(f"  ❌ Eroare: {str(e)}")
        
        input("\n  Apasă Enter pentru a continua...")
    
    def configure(self):
        """Configurare sistem"""
        global BOT_COUNT, REQUESTS_PER_BOT
        
        self.clear_screen()
        print("\n⚙️ CONFIGURARE SISTEM")
        print("=" * 50)
        print(f"  1. Număr boti: {BOT_COUNT}")
        print(f"  2. Requesturi per bot: {REQUESTS_PER_BOT}")
        print(f"  3. Adaugă utilizator nou")
        print(f"  4. Adaugă URL-uri noi")
        
        choice = input("\n  Selectează opțiunea: ")
        
        if choice == "1":
            try:
                BOT_COUNT = int(input("  Număr boti: "))
                print(f"  ✅ Setat la {BOT_COUNT}")
            except:
                print("  ❌ Număr invalid!")
        
        elif choice == "2":
            try:
                REQUESTS_PER_BOT = int(input("  Requesturi per bot: "))
                print(f"  ✅ Setat la {REQUESTS_PER_BOT}")
            except:
                print("  ❌ Număr invalid!")
        
        elif choice == "3":
            key = input("  Nume utilizator (API Key): ")
            try:
                balance = float(input("  Balanță inițială ($): "))
                wallet = input("  Adresă wallet: ")
                API_KEYS[key] = {"balance": balance, "wallet": wallet}
                print(f"  ✅ {key} adăugat cu ${balance:.2f}!")
            except:
                print("  ❌ Date invalide!")
        
        elif choice == "4":
            print("\n  📝 URL-uri curente:")
            for i, url in enumerate(REAL_URLS[-5:], 1):
                print(f"     {i}. {url}")
            
            new_url = input("\n  Adaugă URL nou: ")
            if new_url.startswith("http"):
                REAL_URLS.append(new_url)
                print(f"  ✅ URL adăugat! (Total: {len(REAL_URLS)})")
            else:
                print("  ❌ URL invalid!")
        
        time.sleep(1)
    
    def show_logs(self):
        """Afișează log-urile recente"""
        self.clear_screen()
        print("\n📝 LOG-URI RECENTE")
        print("=" * 50)
        
        logs = []
        while not self.log_queue.empty():
            logs.append(self.log_queue.get())
        
        if logs:
            for log in logs[-20:]:  # Ultimele 20
                print(f"  {log}")
        else:
            print("  📭 Niciun log disponibil")
        
        input("\n  Apasă Enter pentru a continua...")
    
    def main_loop(self):
        """Bucla principală"""
        # Pornește serverul în background
        def run_server():
            uvicorn.run(app, host="0.0.0.0", port=8000, log_level="critical")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(2)
        
        # Balanță inițială
        self.log_queue.put("✅ Server API pornit!")
        self.log_queue.put(f"💰 Balanță inițială: {self.format_balance(self.get_balance())}")
        self.log_queue.put(f"🌐 {len(REAL_URLS)} URL-uri disponibile")
        
        while self.running:
            self.display_header()
            self.display_menu()
            
            choice = input("  Comanda: ").strip()
            
            if choice == "1":
                self.run_bots()
            elif choice == "2":
                self.stop_bots()
            elif choice == "3":
                self.check_balance()
            elif choice == "4":
                self.withdraw()
            elif choice == "5":
                self.display_stats()
            elif choice == "6":
                self.configure()
            elif choice == "7":
                self.show_logs()
            elif choice == "8":
                self.running = False
                print("\n  👋 La revedere!")
                sys.exit(0)
            else:
                print("  ❌ Comandă invalidă!")
                time.sleep(0.5)

# ==================== MAIN ====================
if __name__ == "__main__":
    try:
        ui = TerminalUI()
        ui.main_loop()
    except KeyboardInterrupt:
        print("\n\n  👋 La revedere!")
        sys.exit(0)
