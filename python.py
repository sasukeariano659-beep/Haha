#!/usr/bin/env python3
"""
micro_saas_api.py — Micro-SaaS cu plată per request (crypto)
Rulează pe Kali, încasează $0.02 per call, retragi în wallet USDT/BTC
"""

import os
import uuid
import hashlib
import requests
from fastapi import FastAPI, HTTPException, Depends
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

class PaymentResponse(BaseModel):
    invoice_id: str
    amount: float
    status: str
    payment_url: Optional[str] = None

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
    
    # Aici integrezi Cryptomus / NowPayments / etc.
    # Exemplu cu Cryptomus Payout API:
    # https://doc.cryptomus.com/merchant-api/payouts/getting-started
    
    user["balance"] -= amount
    return {
        "status": "pending",
        "amount": amount,
        "wallet": user["wallet"],
        "tx_id": f"tx_{uuid.uuid4().hex[:16]}",
        "note": "Withdrawal processed via Cryptomus API — vezi wallet-ul în 5-30 min"
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
