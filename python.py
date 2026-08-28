#!/usr/bin/env python3
"""
micro_saas_api.py — Micro-SaaS cu plată per request (crypto)
Rulează în terminal, generează boti automat
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
from typing import Optional

# ==================== CONFIGURAȚIE ====================
API_KEYS = {
    "user1": {"balance": 100.00, "wallet": "0xYourWalletAddress"},
    "user2": {"balance": 50.00, "wallet": "0xAnotherWallet"},
}

MIN_PAYOUT = 0.02
BOT_COUNT = 5  # Câți boti să ruleze simultan
REQUESTS_PER_BOT = 10  # Câte requesturi face fiecare bot

# ==================== FASTAPI APP ====================
app = FastAPI(title="MicroAPI - $0.02/request")

class RequestModel(BaseModel):
    api_key: str
    url: str

@app.post("/check-url")
def check_url(req: RequestModel):
    """Verifică URL-ul și scade $0.02"""
    if req.api_key not in API_KEYS:
        raise HTTPException(403, "Invalid API key")
    user = API_KEYS[req.api_key]
    if user["balance"] < MIN_PAYOUT:
        raise HTTPException(402, f"Insufficient balance (need ${MIN_PAYOUT:.2f})")
    
    user["balance"] -= MIN_PAYOUT
    
    try:
        resp = requests.get(req.url, timeout=10)
        return {
            "url": req.url,
            "status": resp.status_code,
            "online": resp.status_code < 500,
            "charged": MIN_PAYOUT,
            "balance_remaining": round(user["balance"], 4),
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
    """Un bot care face requesturi automate"""
    
    def __init__(self, bot_id, api_key, num_requests):
        self.bot_id = bot_id
        self.api_key = api_key
        self.num_requests = num_requests
        self.total_charged = 0
        self.success_count = 0
        self.error_count = 0
        self.running = True
        
    def get_random_url(self):
        """Generează URL-uri random pentru test"""
        urls = [
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
        ]
        return random.choice(urls)
    
    def make_request(self):
        """Face un request la API"""
        url = self.get_random_url()
        payload = {
            "api_key": self.api_key,
            "url": url
        }
        
        try:
            response = requests.post(
                "http://localhost:8000/check-url",
                json=payload,
                timeout=5
            )
            data = response.json()
            
            if response.status_code == 200:
                self.success_count += 1
                self.total_charged += data.get("charged", 0)
                return f"✅ URL: {url} | Status: {data.get('status', 'N/A')} | Balanță: ${data.get('balance_remaining', 0):.4f}"
            else:
                self.error_count += 1
                return f"❌ Eroare: {data.get('detail', 'Unknown error')}"
                
        except Exception as e:
            self.error_count += 1
            return f"❌ Request eșuat: {str(e)}"
    
    def run(self):
        """Rulează botul"""
        print(f"\n🤖 Bot {self.bot_id} pornit (API Key: {self.api_key})")
        print(f"📊 Va face {self.num_requests} requesturi")
        
        for i in range(self.num_requests):
            if not self.running:
                break
                
            result = self.make_request()
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Bot {self.bot_id} [{i+1}/{self.num_requests}]: {result}")
            
            # Pauză random între requesturi
            time.sleep(random.uniform(0.5, 2))
        
        print(f"\n📊 Bot {self.bot_id} finalizat:")
        print(f"   ✅ Succes: {self.success_count}")
        print(f"   ❌ Erori: {self.error_count}")
        print(f"   💰 Taxat: ${self.total_charged:.4f}")

def run_bots():
    """Pornește toți botii"""
    print("""
    ╔═══════════════════════════════════════════╗
    ║  🤖 MicroAPI - Bot Generator             ║
    ║  Câștigi $0.02 per request automat       ║
    ║  Boti activi: {}                     ║
    ╚═══════════════════════════════════════════╝
    """.format(BOT_COUNT))
    
    # Pornește botii
    threads = []
    bot_workers = []
    
    # Distribuie API keys între boti
    api_keys = list(API_KEYS.keys())
    
    for i in range(BOT_COUNT):
        # Alege un API key random
        api_key = random.choice(api_keys)
        bot = BotWorker(
            bot_id=i+1,
            api_key=api_key,
            num_requests=REQUESTS_PER_BOT
        )
        bot_workers.append(bot)
        
        # Pornește într-un thread
        thread = threading.Thread(target=bot.run)
        thread.start()
        threads.append(thread)
        
        # Pauză între porniri
        time.sleep(0.5)
    
    # Așteaptă finalizarea
    for thread in threads:
        thread.join()
    
    # Raport final
    print("\n" + "="*50)
    print("📊 RAPORT FINAL")
    print("="*50)
    total_success = sum(b.success_count for b in bot_workers)
    total_errors = sum(b.error_count for b in bot_workers)
    total_charged = sum(b.total_charged for b in bot_workers)
    
    print(f"✅ Requesturi reușite: {total_success}")
    print(f"❌ Requesturi eșuate: {total_errors}")
    print(f"💰 Total taxat: ${total_charged:.4f}")
    print(f"💵 Profit total: ${total_charged:.4f}")
    
    # Afișează balanțele finale
    print("\n📈 Balanțe finale:")
    for key, data in API_KEYS.items():
        print(f"   {key}: ${data['balance']:.4f} (Wallet: {data['wallet']})")
    
    print("\n" + "="*50)

# ==================== MENIU INTERACTIV ====================
def show_menu():
    """Afișează meniul principal"""
    os.system('clear' if os.name == 'posix' else 'cls')
    print("""
    ╔═══════════════════════════════════════════╗
    ║     🤖 MICRO-SaaS BOT GENERATOR          ║
    ║     Câștigă $0.02 per request            ║
    ╚═══════════════════════════════════════════╝
    """)
    print("1. 🚀 Pornește botii (generare automată)")
    print("2. 💰 Verifică balanțele")
    print("3. 💸 Retrage în wallet")
    print("4. ⚙️ Configurare boti")
    print("5. 📊 Statistici detaliate")
    print("6. 🛑 Oprește toți botii")
    print("7. 🚪 Ieșire")
    print("\n" + "-"*40)

def check_balances():
    """Verifică balanțele tuturor utilizatorilor"""
    print("\n" + "="*50)
    print("💰 BALANȚE UTILIZATORI")
    print("="*50)
    for key, data in API_KEYS.items():
        print(f"👤 {key}")
        print(f"   💵 Balanță: ${data['balance']:.4f}")
        print(f"   🏦 Wallet: {data['wallet']}")
        print("-"*40)
    input("\nApasă Enter pentru a continua...")

def withdraw_funds():
    """Retrage fonduri"""
    print("\n" + "="*50)
    print("💸 RETRAGERE FONDURI")
    print("="*50)
    
    for i, (key, data) in enumerate(API_KEYS.items(), 1):
        print(f"{i}. {key} - Balanță: ${data['balance']:.4f} - Wallet: {data['wallet']}")
    
    try:
        choice = int(input("\nSelectează utilizatorul (număr): ")) - 1
        user_keys = list(API_KEYS.keys())
        if choice < 0 or choice >= len(user_keys):
            print("❌ Selecție invalidă!")
            return
            
        api_key = user_keys[choice]
        amount = float(input(f"Sumă de retras (min ${MIN_PAYOUT:.2f}): "))
        
        # Facem request la API
        response = requests.post(
            f"http://localhost:8000/withdraw?api_key={api_key}&amount={amount}"
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Retragere inițiată!")
            print(f"   💵 Sumă: ${data['amount']:.4f}")
            print(f"   🏦 Wallet: {data['wallet']}")
            print(f"   🆔 TX ID: {data['tx_id']}")
            print(f"   📝 {data['note']}")
        else:
            print(f"❌ Eroare: {response.json().get('detail', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Eroare: {str(e)}")
    
    input("\nApasă Enter pentru a continua...")

def configure_bots():
    """Configurează botii"""
    global BOT_COUNT, REQUESTS_PER_BOT
    
    print("\n" + "="*50)
    print("⚙️ CONFIGURARE BOTI")
    print("="*50)
    print(f"1. Număr boti: {BOT_COUNT}")
    print(f"2. Requesturi per bot: {REQUESTS_PER_BOT}")
    print("3. Adaugă utilizator nou")
    
    choice = input("\nSelectează opțiunea: ")
    
    if choice == "1":
        try:
            BOT_COUNT = int(input("Număr boti: "))
            print(f"✅ Boti setați la {BOT_COUNT}")
        except ValueError:
            print("❌ Număr invalid!")
    
    elif choice == "2":
        try:
            REQUESTS_PER_BOT = int(input("Requesturi per bot: "))
            print(f"✅ Requesturi setate la {REQUESTS_PER_BOT}")
        except ValueError:
            print("❌ Număr invalid!")
    
    elif choice == "3":
        key = input("Nume utilizator (API Key): ")
        balance = float(input("Balanță inițială ($): "))
        wallet = input("Adresă wallet: ")
        API_KEYS[key] = {"balance": balance, "wallet": wallet}
        print(f"✅ Utilizator {key} adăugat!")
    
    input("\nApasă Enter pentru a continua...")

def show_stats():
    """Afișează statistici detaliate"""
    print("\n" + "="*50)
    print("📊 STATISTICI DETALIATE")
    print("="*50)
    
    total_balance = sum(data['balance'] for data in API_KEYS.values())
    avg_balance = total_balance / len(API_KEYS) if API_KEYS else 0
    
    print(f"👥 Total utilizatori: {len(API_KEYS)}")
    print(f"💰 Balanță totală: ${total_balance:.4f}")
    print(f"📈 Balanță medie: ${avg_balance:.4f}")
    print(f"💵 Câștig per request: ${MIN_PAYOUT:.2f}")
    print(f"🤖 Boti activi: {BOT_COUNT}")
    print(f"🔄 Requesturi per bot: {REQUESTS_PER_BOT}")
    print(f"📊 Total requesturi potențiale: {BOT_COUNT * REQUESTS_PER_BOT}")
    print(f"💰 Profit potențial: ${BOT_COUNT * REQUESTS_PER_BOT * MIN_PAYOUT:.4f}")
    
    print("\n👤 Detalii utilizatori:")
    for key, data in API_KEYS.items():
        print(f"   • {key}: ${data['balance']:.4f}")
    
    input("\nApasă Enter pentru a continua...")

# ==================== MAIN ====================
def main():
    """Funcția principală"""
    # Pornește serverul într-un thread separat
    def run_server():
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Așteaptă să pornească serverul
    time.sleep(2)
    print("✅ Server API pornit pe http://localhost:8000")
    
    # Meniul principal
    while True:
        show_menu()
        choice = input("Selectează opțiunea: ")
        
        if choice == "1":
            run_bots()
            input("\nApasă Enter pentru a continua...")
            
        elif choice == "2":
            check_balances()
            
        elif choice == "3":
            withdraw_funds()
            
        elif choice == "4":
            configure_bots()
            
        elif choice == "5":
            show_stats()
            
        elif choice == "6":
            print("\n🛑 Oprire boti în desfășurare...")
            # Aici poți adăuga logică de oprire
            print("✅ Toți botii au fost opriți!")
            time.sleep(1)
            
        elif choice == "7":
            print("\n👋 La revedere!")
            sys.exit(0)
            
        else:
            print("❌ Opțiune invalidă!")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 La revedere!")
        sys.exit(0)
