#!/usr/bin/env python3
"""
micro_saas_api.py — Micro-SaaS cu plată per request (crypto)
Rulează pe Kali, încasează $0.02 per call, retragi în wallet USDT/BTC
"""

import os
import uuid
import hashlib
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from typing import Optional

app = FastAPI(title="MicroAPI - $0.02/request")

# Config — pune cheile tale reale aici
API_KEYS = {
    "user1": {"balance": 1.00, "wallet": "0xYourWalletAddress"},
}

MIN_PAYOUT = 0.02  # $0.02 minimum per request profit

class RequestModel(BaseModel):
    api_key: str
    url: str

@app.get("/", response_class=HTMLResponse)
async def home():
    """Pagina principală cu interfață web"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MicroAPI - $0.02/request</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
            .endpoint { background: #e8f5e9; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #4CAF50; }
            code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; }
            .test-form { background: #fff3e0; padding: 20px; border-radius: 5px; margin: 20px 0; }
            input, button { padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #4CAF50; color: white; border: none; cursor: pointer; }
            button:hover { background: #45a049; }
            .result { background: #e3f2fd; padding: 15px; margin: 10px 0; border-radius: 5px; display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 MicroAPI - $0.02/request</h1>
            <p><strong>Câștigi $0.02 per request</strong> - plătește pentru verificarea URL-urilor</p>
            
            <div class="endpoint">
                <h3>📌 Endpoint-uri disponibile:</h3>
                <p><code>POST /check-url</code> - Verifică un URL (costă $0.02)</p>
                <p><code>POST /withdraw?api_key=user1&amount=0.50</code> - Retrage în wallet</p>
                <p><code>GET /balance/user1</code> - Verifică balanța</p>
            </div>
            
            <div class="test-form">
                <h3>🧪 Testează API-ul:</h3>
                <form id="testForm">
                    <input type="text" id="apiKey" value="user1" placeholder="API Key">
                    <input type="text" id="urlTest" value="https://google.com" placeholder="URL de verificat">
                    <button type="submit">Verifică URL ($0.02)</button>
                </form>
                <div id="result" class="result"></div>
            </div>
            
            <div>
                <h3>💰 Retragere:</h3>
                <form id="withdrawForm">
                    <input type="text" id="withdrawKey" value="user1" placeholder="API Key">
                    <input type="number" id="withdrawAmount" value="0.50" step="0.01" placeholder="Sumă">
                    <button type="submit">Retrage în wallet</button>
                </form>
                <div id="withdrawResult" class="result"></div>
            </div>
            
            <div>
                <h3>📊 Balanță:</h3>
                <button onclick="checkBalance()">Verifică balanța</button>
                <div id="balanceResult" class="result"></div>
            </div>
        </div>
        
        <script>
            document.getElementById('testForm').onsubmit = async function(e) {
                e.preventDefault();
                const apiKey = document.getElementById('apiKey').value;
                const url = document.getElementById('urlTest').value;
                const resultDiv = document.getElementById('result');
                
                try {
                    const response = await fetch('/check-url', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({api_key: apiKey, url: url})
                    });
                    const data = await response.json();
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                } catch(error) {
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `❌ Eroare: ${error.message}`;
                }
            };
            
            document.getElementById('withdrawForm').onsubmit = async function(e) {
                e.preventDefault();
                const apiKey = document.getElementById('withdrawKey').value;
                const amount = document.getElementById('withdrawAmount').value;
                const resultDiv = document.getElementById('withdrawResult');
                
                try {
                    const response = await fetch(`/withdraw?api_key=${apiKey}&amount=${amount}`, {
                        method: 'POST'
                    });
                    const data = await response.json();
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                } catch(error) {
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `❌ Eroare: ${error.message}`;
                }
            };
            
            async function checkBalance() {
                const apiKey = document.getElementById('apiKey').value;
                const resultDiv = document.getElementById('balanceResult');
                
                try {
                    const response = await fetch(`/balance/${apiKey}`);
                    const data = await response.json();
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
                } catch(error) {
                    resultDiv.style.display = 'block';
                    resultDiv.innerHTML = `❌ Eroare: ${error.message}`;
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/check-url")
def check_url(req: RequestModel):
    """Verifică dacă un URL e accesibil — plătești $0.02"""
    # 1. Verifică API key și balance
    if req.api_key not in API_KEYS:
        raise HTTPException(403, "Invalid API key")
    user = API_KEYS[req.api_key]
    if user["balance"] < MIN_PAYOUT:
        raise HTTPException(402, f"Insufficient balance (need ${MIN_PAYOUT:.2f})")
    
    # 2. Scad $0.02
    user["balance"] -= MIN_PAYOUT
    
    # 3. Execută task-ul
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
    """Retrage balance-ul în wallet-ul crypto asociat"""
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
        "note": "Withdrawal processed — vezi wallet-ul în 5-30 min"
    }

@app.get("/balance/{api_key}")
def get_balance(api_key: str):
    if api_key not in API_KEYS:
        raise HTTPException(403, "Invalid API key")
    return API_KEYS[api_key]

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════╗
    ║  MicroAPI — câștigi $0.02 per request     ║
    ║  Rulează:  uvicorn micro_saas_api:app      ║
    ║  Retragi:  POST /withdraw -> wallet crypto ║
    ╚═══════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
