from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import bcrypt
import jwt
import secrets
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from bson import ObjectId

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# JWT Config
JWT_ALGORITHM = "HS256"

def get_jwt_secret():
    return os.environ["JWT_SECRET"]

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ---------------------
# Password Utilities
# ---------------------
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# ---------------------
# JWT Utilities
# ---------------------
def create_access_token(user_id: str, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=15), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------------------
# Models
# ---------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class ChatMessageRequest(BaseModel):
    content: str
    chat_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    message_id: str
    rating: str  # "up" or "down"

class CheckoutRequest(BaseModel):
    plan: str  # "pro_reasoning" or "pro_creative"
    origin_url: str

# ---------------------
# Brute Force Protection
# ---------------------
async def check_brute_force(ip: str, email: str):
    identifier = f"{ip}:{email}"
    attempt = await db.login_attempts.find_one({"identifier": identifier}, {"_id": 0})
    if attempt and attempt.get("count", 0) >= 5:
        lockout_until = attempt.get("locked_until")
        if lockout_until and datetime.now(timezone.utc) < lockout_until:
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")
        else:
            await db.login_attempts.delete_one({"identifier": identifier})

async def record_failed_attempt(ip: str, email: str):
    identifier = f"{ip}:{email}"
    attempt = await db.login_attempts.find_one({"identifier": identifier}, {"_id": 0})
    if attempt:
        new_count = attempt.get("count", 0) + 1
        update = {"$set": {"count": new_count, "last_attempt": datetime.now(timezone.utc)}}
        if new_count >= 5:
            update["$set"]["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.login_attempts.update_one({"identifier": identifier}, update)
    else:
        await db.login_attempts.insert_one({
            "identifier": identifier,
            "count": 1,
            "last_attempt": datetime.now(timezone.utc)
        })

async def clear_failed_attempts(ip: str, email: str):
    identifier = f"{ip}:{email}"
    await db.login_attempts.delete_one({"identifier": identifier})

# ---------------------
# Auth Endpoints
# ---------------------
@api_router.post("/auth/register")
async def register(req: RegisterRequest, response: Response):
    email = req.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_doc = {
        "email": email,
        "password_hash": hash_password(req.password),
        "name": req.name or email.split("@")[0],
        "role": "free",
        "daily_message_count": 0,
        "last_message_date": None,
        "stripe_customer_id": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    set_auth_cookies(response, access_token, refresh_token)
    
    return {"id": user_id, "email": email, "name": user_doc["name"], "role": "free"}

@api_router.post("/auth/login")
async def login(req: LoginRequest, request: Request, response: Response):
    email = req.email.lower().strip()
    ip = request.client.host if request.client else "unknown"
    
    await check_brute_force(ip, email)
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(req.password, user["password_hash"]):
        await record_failed_attempt(ip, email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    await clear_failed_attempts(ip, email)
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id)
    set_auth_cookies(response, access_token, refresh_token)
    
    return {
        "id": user_id, "email": email,
        "name": user.get("name", ""), "role": user.get("role", "free")
    }

@api_router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    return {"message": "Logged out"}

@api_router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    return {
        "id": user["_id"], "email": user["email"],
        "name": user.get("name", ""), "role": user.get("role", "free"),
        "daily_message_count": user.get("daily_message_count", 0),
        "last_message_date": user.get("last_message_date")
    }

@api_router.post("/auth/refresh")
async def refresh_token(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user_id = str(user["_id"])
        new_access = create_access_token(user_id, user["email"])
        response.set_cookie(key="access_token", value=new_access, httponly=True, secure=False, samesite="lax", max_age=900, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# ---------------------
# Chat Endpoints
# ---------------------
DAILY_FREE_LIMIT = 10

PLACEHOLDER_RESPONSES = [
    "I'm Impulse AI, your intelligent assistant. This is a placeholder response — AI integration coming soon!",
    "Great question! Once AI is connected, I'll provide real insights here. For now, this is a demo response.",
    "Interesting thought. Impulse AI will process this with advanced reasoning once the AI engine is live.",
    "I appreciate your message! This is a placeholder — the full AI experience is on its way.",
    "That's a fascinating topic. Stay tuned for real AI-powered responses in the next update!",
]

import random

@api_router.post("/chat/send")
async def send_message(req: ChatMessageRequest, request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]
    role = user.get("role", "free")
    
    # Check daily limit for free users
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if role == "free":
        last_date = user.get("last_message_date")
        count = user.get("daily_message_count", 0)
        if last_date != today:
            count = 0
        if count >= DAILY_FREE_LIMIT:
            raise HTTPException(status_code=429, detail="Daily message limit reached. Upgrade to Pro for unlimited messages.")
        new_count = count + 1
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"daily_message_count": new_count, "last_message_date": today}}
        )
    
    # Create or get chat
    chat_id = req.chat_id
    if not chat_id:
        chat_doc = {
            "user_id": user_id,
            "title": req.content[:50] + ("..." if len(req.content) > 50 else ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        result = await db.chats.insert_one(chat_doc)
        chat_id = str(result.inserted_id)
    else:
        await db.chats.update_one(
            {"_id": ObjectId(chat_id)},
            {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    # Save user message
    user_msg_id = str(ObjectId())
    user_msg = {
        "id": user_msg_id,
        "chat_id": chat_id,
        "user_id": user_id,
        "role": "user",
        "content": req.content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(user_msg)
    
    # Generate placeholder AI response
    ai_msg_id = str(ObjectId())
    ai_content = random.choice(PLACEHOLDER_RESPONSES)
    ai_msg = {
        "id": ai_msg_id,
        "chat_id": chat_id,
        "user_id": user_id,
        "role": "assistant",
        "content": ai_content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.messages.insert_one(ai_msg)
    
    # Get updated count
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 0, "daily_message_count": 1, "last_message_date": 1})
    
    return {
        "chat_id": chat_id,
        "user_message": {"id": user_msg_id, "role": "user", "content": req.content},
        "ai_message": {"id": ai_msg_id, "role": "assistant", "content": ai_content},
        "daily_message_count": updated_user.get("daily_message_count", 0) if role == "free" else None,
        "daily_limit": DAILY_FREE_LIMIT if role == "free" else None
    }

@api_router.get("/chat/list")
async def list_chats(request: Request):
    user = await get_current_user(request)
    chats = await db.chats.find(
        {"user_id": user["_id"]}, {"_id": 0}
    ).sort("updated_at", -1).to_list(100)
    # We need the chat id - stored as a separate ObjectId
    chats_with_id = []
    raw_chats = await db.chats.find({"user_id": user["_id"]}).sort("updated_at", -1).to_list(100)
    for c in raw_chats:
        chats_with_id.append({
            "id": str(c["_id"]),
            "title": c.get("title", "New Chat"),
            "created_at": c.get("created_at"),
            "updated_at": c.get("updated_at")
        })
    return chats_with_id

@api_router.get("/chat/{chat_id}/messages")
async def get_chat_messages(chat_id: str, request: Request):
    user = await get_current_user(request)
    chat = await db.chats.find_one({"_id": ObjectId(chat_id), "user_id": user["_id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    messages = await db.messages.find(
        {"chat_id": chat_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    return messages

@api_router.delete("/chat/{chat_id}")
async def delete_chat(chat_id: str, request: Request):
    user = await get_current_user(request)
    chat = await db.chats.find_one({"_id": ObjectId(chat_id), "user_id": user["_id"]})
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    await db.chats.delete_one({"_id": ObjectId(chat_id)})
    await db.messages.delete_many({"chat_id": chat_id})
    return {"message": "Chat deleted"}

# ---------------------
# Feedback Endpoints
# ---------------------
@api_router.post("/feedback")
async def submit_feedback(req: FeedbackRequest, request: Request):
    user = await get_current_user(request)
    if req.rating not in ("up", "down"):
        raise HTTPException(status_code=400, detail="Rating must be 'up' or 'down'")
    
    # Check if feedback already exists for this message from this user
    existing = await db.feedback_logs.find_one({
        "user_id": user["_id"], "message_id": req.message_id
    })
    
    if existing:
        await db.feedback_logs.update_one(
            {"user_id": user["_id"], "message_id": req.message_id},
            {"$set": {"rating": req.rating, "timestamp": datetime.now(timezone.utc).isoformat()}}
        )
    else:
        await db.feedback_logs.insert_one({
            "user_id": user["_id"],
            "message_id": req.message_id,
            "rating": req.rating,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    return {"message": "Feedback recorded", "rating": req.rating}

# ---------------------
# Stripe Subscription Endpoints
# ---------------------
SUBSCRIPTION_PLANS = {
    "pro_reasoning": {"name": "Reasoning Pro", "amount": 12.00, "role": "pro_reasoning"},
    "pro_creative": {"name": "Creative Pro", "amount": 24.00, "role": "pro_creative"}
}

@api_router.post("/checkout/create")
async def create_checkout(req: CheckoutRequest, request: Request):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
    
    user = await get_current_user(request)
    
    if req.plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan = SUBSCRIPTION_PLANS[req.plan]
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    origin_url = req.origin_url.rstrip("/")
    success_url = f"{origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/pricing"
    
    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    checkout_request = CheckoutSessionRequest(
        amount=plan["amount"],
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["_id"],
            "plan": req.plan,
            "user_email": user["email"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "user_id": user["_id"],
        "email": user["email"],
        "plan": req.plan,
        "amount": plan["amount"],
        "currency": "usd",
        "payment_status": "initiated",
        "status": "pending",
        "metadata": {"plan": req.plan},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, request: Request):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    user = await get_current_user(request)
    api_key = os.environ.get("STRIPE_API_KEY")
    
    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update payment transaction
    tx = await db.payment_transactions.find_one({"session_id": session_id})
    if tx:
        update_data = {
            "payment_status": status.payment_status,
            "status": status.status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # If paid and not already processed, update user role
        if status.payment_status == "paid" and tx.get("payment_status") != "paid":
            plan = tx.get("plan")
            if plan in SUBSCRIPTION_PLANS:
                new_role = SUBSCRIPTION_PLANS[plan]["role"]
                await db.users.update_one(
                    {"_id": ObjectId(tx["user_id"])},
                    {"$set": {"role": new_role}}
                )
                update_data["role_updated"] = True
                logger.info(f"Updated user {tx['user_id']} role to {new_role}")
        
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    api_key = os.environ.get("STRIPE_API_KEY")
    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        if webhook_response.payment_status == "paid":
            session_id = webhook_response.session_id
            tx = await db.payment_transactions.find_one({"session_id": session_id})
            if tx and tx.get("payment_status") != "paid":
                plan = tx.get("plan")
                if plan in SUBSCRIPTION_PLANS:
                    new_role = SUBSCRIPTION_PLANS[plan]["role"]
                    await db.users.update_one(
                        {"_id": ObjectId(tx["user_id"])},
                        {"$set": {"role": new_role}}
                    )
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "payment_status": "paid",
                        "status": "complete",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

# ---------------------
# User Profile
# ---------------------
@api_router.get("/user/usage")
async def get_user_usage(request: Request):
    user = await get_current_user(request)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    count = user.get("daily_message_count", 0)
    last_date = user.get("last_message_date")
    if last_date != today:
        count = 0
    
    return {
        "role": user.get("role", "free"),
        "daily_message_count": count,
        "daily_limit": DAILY_FREE_LIMIT if user.get("role", "free") == "free" else None
    }

# ---------------------
# Startup
# ---------------------
@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.messages.create_index("chat_id")
    await db.chats.create_index("user_id")
    await db.feedback_logs.create_index([("user_id", 1), ("message_id", 1)])
    await db.payment_transactions.create_index("session_id", unique=True)
    
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@impulseai.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "role": "free",
            "daily_message_count": 0,
            "last_message_date": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}}
        )
        logger.info(f"Admin password updated: {admin_email}")
    
    # Write test credentials
    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write("# Test Credentials\n\n")
        f.write(f"## Admin\n- Email: {admin_email}\n- Password: {admin_password}\n- Role: free\n\n")
        f.write("## Test User\n- Email: testuser@impulseai.com\n- Password: test1234\n- Role: free (register via /api/auth/register)\n\n")
        f.write("## Auth Endpoints\n")
        f.write("- POST /api/auth/register\n- POST /api/auth/login\n- POST /api/auth/logout\n")
        f.write("- GET /api/auth/me\n- POST /api/auth/refresh\n\n")
        f.write("## Chat Endpoints\n")
        f.write("- POST /api/chat/send\n- GET /api/chat/list\n- GET /api/chat/{chat_id}/messages\n")
        f.write("- DELETE /api/chat/{chat_id}\n\n")
        f.write("## Other Endpoints\n")
        f.write("- POST /api/feedback\n- POST /api/checkout/create\n")
        f.write("- GET /api/checkout/status/{session_id}\n- GET /api/user/usage\n")

app.include_router(api_router)

# CORS - must be after include_router
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
