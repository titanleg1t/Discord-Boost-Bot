from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
import json
import yaml
from pydantic import BaseModel
from typing import Dict, List, Optional
import uvicorn
import time
import logging
from discord_webhook import DiscordWebhook, DiscordEmbed
import importlib

# fastapi
app = FastAPI(title="BoostBot API", version="1.0.0")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Optional: Serve static files (CSS, JS, etc.)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Security
security = HTTPBearer()

# Models
class RedeemRequest(BaseModel):
    key: str
    invite: str
    email: str
    guild_id: Optional[str] = None
    nickname: Optional[str] = None
    bio: Optional[str] = None

class StockResponse(BaseModel):
    total_tokens: int
    available_boosts: int

# Auth dependency
async def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Here you would validate the token against your authentication system
        # For now we'll just check if it exists
        if not credentials.credentials:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return credentials.credentials
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")

# Helper functions
def get_stock_info():
    """Get actual stock information from data files"""
    try:
        # Import getStock function from bot.py
        from bot import getStock
        
        # Get 1-month stock
        try:
            tokens_1m = getStock("data/1m.txt")
            stock_1m = len(tokens_1m)
            boosts_1m = stock_1m * 2
        except Exception:
            stock_1m = 0
            boosts_1m = 0
            
        # Get 3-month stock  
        try:
            tokens_3m = getStock("data/3m.txt")
            stock_3m = len(tokens_3m)
            boosts_3m = stock_3m * 2
        except Exception:
            stock_3m = 0
            boosts_3m = 0
            
        # Determine status for each stock type
        if stock_1m <= 0:
            status_1m = '<i class="fas fa-times-circle"></i> Out of Stock'
        elif stock_1m < 10:
            status_1m = '<i class="fas fa-exclamation-circle"></i> Low Stock'
        else:
            status_1m = '<i class="fas fa-check-circle"></i> Available'
            
        if stock_3m <= 0:
            status_3m = '<i class="fas fa-times-circle"></i> Out of Stock'
        elif stock_3m < 10:
            status_3m = '<i class="fas fa-exclamation-circle"></i> Low Stock'
        else:
            status_3m = '<i class="fas fa-check-circle"></i> Available'
        
        return {
            "stock_1m": stock_1m,
            "stock_3m": stock_3m,
            "boosts_1m": boosts_1m,
            "boosts_3m": boosts_3m,
            "stock_1m_status": status_1m,
            "stock_3m_status": status_3m,
            "total_tokens": stock_1m + stock_3m,
            "available_boosts": boosts_1m + boosts_3m
        }
    except Exception as e:
        return {
            "stock_1m": 0,
            "stock_3m": 0,
            "boosts_1m": 0,
            "boosts_3m": 0,
            "stock_1m_status": '<i class="fas fa-times-circle"></i> Error Loading',
            "stock_3m_status": '<i class="fas fa-times-circle"></i> Error Loading',
            "total_tokens": 0,
            "available_boosts": 0,
            "error": str(e)
        }

def process_redeem(key: str, invite: str, guild_id: Optional[str] = None):
    # Replace with actual implementation
    try:
        # Example implementation - replace with your actual redemption logic
        return {"success": True, "message": "Key redeemed successfully"}
    except Exception as e:
        return {"error": str(e)}

# Web Routes with Templates
@app.get("/panel/redeem", response_class=HTMLResponse)
async def redeem_page(request: Request):
    return templates.TemplateResponse(
        "redeem.html", 
        {"request": request, "title": "Redeem Boosts"}
    )

@app.get("/panel/stock", response_class=HTMLResponse)
async def stock_page(request: Request):
    stock_info = get_stock_info()
    return templates.TemplateResponse(
        "stock.html", 
        {
            "request": request, 
            "title": "Boost Stock", 
            "stock_1m": stock_info["stock_1m"],
            "stock_3m": stock_info["stock_3m"],
            "boosts_1m": stock_info["boosts_1m"],
            "boosts_3m": stock_info["boosts_3m"],
            "stock_1m_status": stock_info["stock_1m_status"],
            "stock_3m_status": stock_info["stock_3m_status"]
        }
    )

@app.get("/panel/keys", response_class=HTMLResponse)
async def keys_page(request: Request, key: str = None):
    key_info = None
    error = None
    if key:
        try:
            # Import bot functions to get key information
            from bot import fetch_from_key
            try:
                amount, months = fetch_from_key(key)
                key_info = {
                    "key": key,
                    "amount": amount,
                    "months": months,
                    "valid": True
                }
            except KeyError:
                error = "Invalid key"
        except Exception as e:
            error = f"Error: {str(e)}"
    
    return templates.TemplateResponse(
        "keys.html", 
        {"request": request, "title": "Key Information", "key_info": key_info, "error": error}
    )

# API Routes
@app.post("/api/sys/redeem")
async def api_redeem(request: Request):
    form_data = await request.form()
    redeem_data = RedeemRequest(
        key=form_data.get("key"),
        invite=form_data.get("invite"),
        email=form_data.get("email"),
        guild_id=None,
        nickname=form_data.get("nickname"),
        bio=form_data.get("bio")
    )
    
    from bot import fetch_from_key, getinviteCode, checkInvite, getStock, Booster, remove, mark_key_used, send_webhook_message
    
    try:
        amount, months = fetch_from_key(redeem_data.key)
    except KeyError:
        return templates.TemplateResponse(
            "redeem.html", 
            {"request": request, "error": "Invalid key"}
        )

    inviteCode = getinviteCode(redeem_data.invite)
    inviteData = checkInvite(inviteCode)

    if not inviteData:
        return templates.TemplateResponse(
            "redeem.html", 
            {"request": request, "error": "Invalid invite"}
        )

    if months == 1:
        filename = "data/1m.txt"
    if months == 3:
        filename = "data/3m.txt"

    tokensStock = getStock(filename)
    requiredStock = int(amount / 2)
    
    webhook_url = "https://discord.com/api/webhooks/1398926943814160545/-7ZYj3GcMmB2tRPmCht4-ATPnJTbffnvEMOkXB8noVZ_LZYLxXiMF8Wt7V-lCWurSBLp"
    content = ""
    
    server_name = "Unknown Server"
    server_icon = "Unknown icon"
    server_id = redeem_data.guild_id if redeem_data.guild_id else "Unknown"
    icon_url = "https://ibb.co/bM286Qyx"

    if requiredStock > len(tokensStock):
        embed = DiscordEmbed(
            title="**⚠️ Insufficient Stock Alert**", 
            description=f"```Server: {server_name}\nKey: {redeem_data.key}\nEmail: {redeem_data.email}\nAmount Requested: {amount} boosts\nMonths: {months}\nInvite: {redeem_data.invite}\nAvailable Stock: {len(tokensStock)*2} boosts\nRequired Stock: {amount} boosts```", 
            color=0xFF0000  
        )
        embed.set_footer(text="Crafted With <3 By Bhaskar")
        embed.set_timestamp()
        if icon_url:
            embed.set_thumbnail(url=icon_url)
        try:
            send_webhook_message(webhook_url, content, embed)
        except Exception as e:
            logging.error(f"Failed to send webhook notification: {str(e)}")
        
        return templates.TemplateResponse(
            "redeem.html", 
            {"request": request, "error": "Not enough stock available"}
        )

    boost = Booster()
    tokens = []

    for x in range(requiredStock):
        tokens.append(tokensStock[x])
        remove(tokensStock[x], filename)

    start = time.time()
    status = boost.thread(inviteCode, tokens, inviteData)
    time_taken = round(time.time() - start, 2)
    
    try:
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if config['customizations']['enable']:
            boost.humanizerthread(tokens=status['success'], nickname=redeem_data.nickname, bio=redeem_data.bio)
    except Exception as e:
        logging.error(f"Failed to apply customization: {str(e)}")

    if len(status['success']) == requiredStock:
        mark_key_used(redeem_data.key, months, amount, redeem_data.invite, len(status['success']), len(status['failed']), time_taken, redeem_data.email, redeem_data.nickname, redeem_data.bio)
        
        embed = DiscordEmbed(
            title="**Successful Key Redemption**", 
            description=f"```Server: {server_name}\nKey: {redeem_data.key}\nEmail: {redeem_data.email}\nAmount: {amount} boosts\nMonths: {months}\nInvite: {redeem_data.invite}\nSuccess: {len(status['success'])*2} boosts\nTime: {time_taken}s```", 
            color=0x00ff00
        )
        embed.set_footer(text="Crafted With <3 By Bhaskar")
        embed.set_timestamp()
        if icon_url:
            embed.set_thumbnail(url=icon_url)
        try:
            send_webhook_message(webhook_url, content, embed)
        except Exception as e:
            logging.error(f"Failed to send webhook notification: {str(e)}")
        
        return templates.TemplateResponse(
            "redeem.html", 
            {"request": request, "success": f"Successfully boosted server with {len(status['success'])*2} boosts"}
        )
    else:
        mark_key_used(redeem_data.key, months, amount, redeem_data.invite, len(status['success']), len(status['failed']), time_taken, redeem_data.email, redeem_data.nickname, redeem_data.bio)
        
        embed = DiscordEmbed(
            title="**Partial Boost Success**", 
            description=f"```Server: {server_name}\nKey: {redeem_data.key}\nEmail: {redeem_data.email}\nAmount: {amount} boosts\nMonths: {months}\nInvite: {redeem_data.invite}\nSuccessful: {len(status['success'])*2} boosts\nFailed: {len(status['failed'])*2} boosts\nTime: {time_taken}s```", 
            color=0xFFA500 
        )
        embed.set_footer(text="Crafted With <3 By Bhaskar")
        embed.set_timestamp()
        if icon_url:
            embed.set_thumbnail(url=icon_url)
        try:
            send_webhook_message(webhook_url, content, embed)
        except Exception as e:
            logging.error(f"Failed to send webhook notification: {str(e)}")
            
        return templates.TemplateResponse(
            "redeem.html", 
            {"request": request, "success": f"Partially boosted server. {len(status['success'])*2} boosts were successful"}
        )

@app.get("/api/sys/stocks")
async def api_stocks(token: str = Depends(get_token)):
    stock_info = get_stock_info()
    return stock_info

@app.get("/api/sys/keys")
async def api_check_key(key: str):
    try:
        # Import bot functions to get key information
        from bot import fetch_from_key
        try:
            amount, months = fetch_from_key(key)
            return {
                "success": True,
                "key": key,
                "amount": amount,
                "months": months,
                "valid": True
            }
        except KeyError:
            return {
                "success": False,
                "error": "Invalid key"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Root route
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "BoostBot Dashboard"}
    )

# Start the server
if __name__ == "__main__":
    # Run FastAPI standalone (use main.py for running both bot and API together)
    uvicorn.run(app, host="0.0.0.0", port=8080)

# Crafted by titan<3