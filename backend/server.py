from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, UploadFile, File, Query, Header
from fastapi.responses import Response as FastAPIResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import bcrypt
import jwt
import secrets
import random
import math
import uuid
import base64
import requests as sync_requests
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from emergentintegrations.llm.chat import LlmChat, UserMessage

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
# Tier Limits Configuration
# ---------------------
TIER_LIMITS = {
    "free": {
        "daily_messages": 20,
        "daily_images": 2,
        "daily_videos": 1,
        "max_video_duration": 5,
        "video_quality": ["standard"],
        "watermark": True,
        "uses_credits": False,
    },
    "pro_reasoning": {
        "daily_messages": None,  # unlimited
        "daily_images": 10,
        "daily_videos": 3,
        "max_video_duration": 10,
        "video_quality": ["standard", "hd"],
        "watermark": False,
        "uses_credits": False,
    },
    "pro_creative": {
        "daily_messages": None,  # unlimited
        "daily_images": None,  # unlimited
        "daily_videos": None,  # unlimited (credit-based)
        "max_video_duration": 15,
        "video_quality": ["standard", "hd"],
        "watermark": False,
        "uses_credits": True,
        "monthly_credits": 100,
    },
    "admin": {
        "daily_messages": None,
        "daily_images": None,
        "daily_videos": None,
        "max_video_duration": 15,
        "video_quality": ["standard", "hd"],
        "watermark": False,
        "uses_credits": False,
    },
}

# Credit top-up packs
CREDIT_PACKS = {
    "starter": {"name": "Starter Pack", "credits": 50, "amount": 5.00},
    "standard": {"name": "Standard Pack", "credits": 120, "amount": 10.00},
    "power": {"name": "Power Pack", "credits": 300, "amount": 20.00},
}

def calculate_video_credits(duration_seconds: int, quality: str = "standard") -> int:
    """Calculate credits for a video generation request."""
    if duration_seconds <= 5:
        base = 1
    elif duration_seconds <= 10:
        base = 2
    else:
        base = 3
    multiplier = 2 if quality == "hd" else 1
    return base * multiplier

def get_default_user_fields():
    """Return default fields for a new user document."""
    return {
        "daily_message_count": 0,
        "daily_image_count": 0,
        "daily_video_count": 0,
        "last_message_date": None,
        "last_image_date": None,
        "last_video_date": None,
        "video_credits": 0,
        "credits_reset_date": None,
        "is_first_login": True,
        "stripe_customer_id": None,
    }

# ---------------------
# Object Storage
# ---------------------
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "impulse-ai"
storage_key = None

def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        logger.warning("EMERGENT_LLM_KEY not set, storage disabled")
        return None
    resp = sync_requests.post(f"{STORAGE_URL}/init", json={"emergent_key": emergent_key}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not configured")
    resp = sync_requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str):
    key = init_storage()
    if not key:
        raise HTTPException(status_code=500, detail="Storage not configured")
    resp = sync_requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

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
    payload = {"sub": user_id, "email": email, "exp": datetime.now(timezone.utc) + timedelta(hours=1), "type": "access"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(days=7), "type": "refresh"}
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(key="access_token", value=access_token, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
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

class CreditPurchaseRequest(BaseModel):
    pack_id: str  # "starter", "standard", "power"
    origin_url: str

class ImageGenRequest(BaseModel):
    prompt: str
    chat_id: Optional[str] = None

# ---------------------
# Brute Force Protection
# ---------------------
async def check_brute_force(email: str):
    # Use email only as identifier for reliability through proxies
    attempt = await db.login_attempts.find_one({"identifier": email}, {"_id": 0})
    if attempt and attempt.get("count", 0) >= 5:
        lockout_until = attempt.get("locked_until")
        if lockout_until:
            if isinstance(lockout_until, str):
                lockout_until = datetime.fromisoformat(lockout_until)
            if datetime.now(timezone.utc) < lockout_until:
                raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in 15 minutes.")
        # Lockout expired, reset
        await db.login_attempts.delete_one({"identifier": email})

async def record_failed_attempt(email: str):
    result = await db.login_attempts.find_one_and_update(
        {"identifier": email},
        {
            "$inc": {"count": 1},
            "$set": {"last_attempt": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True,
        return_document=True
    )
    if result and result.get("count", 0) >= 5:
        await db.login_attempts.update_one(
            {"identifier": email},
            {"$set": {"locked_until": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()}}
        )

async def clear_failed_attempts(email: str):
    await db.login_attempts.delete_one({"identifier": email})

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
        **get_default_user_fields(),
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
    
    await check_brute_force(email)
    
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(req.password, user["password_hash"]):
        await record_failed_attempt(email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    await clear_failed_attempts(email)
    
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
    role = user.get("role", "free")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    limits = TIER_LIMITS.get(role, TIER_LIMITS["free"])
    
    # Reset daily counts if date changed
    msg_count = user.get("daily_message_count", 0) if user.get("last_message_date") == today else 0
    img_count = user.get("daily_image_count", 0) if user.get("last_image_date") == today else 0
    vid_count = user.get("daily_video_count", 0) if user.get("last_video_date") == today else 0
    
    return {
        "id": user["_id"], "email": user["email"],
        "name": user.get("name", ""), "role": role,
        "daily_message_count": msg_count,
        "daily_image_count": img_count,
        "daily_video_count": vid_count,
        "video_credits": user.get("video_credits", 0),
        "is_first_login": user.get("is_first_login", True),
        "limits": limits,
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
        response.set_cookie(key="access_token", value=new_access, httponly=True, secure=False, samesite="lax", max_age=3600, path="/")
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# ---------------------
# Chat Endpoints (Claude Integration)
# ---------------------
SYSTEM_MESSAGE = """You are Impulse AI, a premium AI assistant. You are helpful, concise, and knowledgeable. 
You provide clear, well-structured responses. You can help with coding, writing, analysis, math, and creative tasks.
Keep responses focused and useful. Use markdown formatting when appropriate."""

FALLBACK_RESPONSES = [
    "I'm Impulse AI. The AI service is temporarily unavailable due to API key budget limits. Please ensure your Emergent LLM key has sufficient balance.",
    "The AI engine is currently rate-limited. Please check your API key balance at Profile > Universal Key > Add Balance.",
]

async def get_claude_response(chat_id: str, user_id: str, content: str) -> str:
    """Get response from Claude via emergentintegrations."""
    try:
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            return random.choice(FALLBACK_RESPONSES)
        
        # Build conversation history from last 10 messages
        recent_msgs = await db.messages.find(
            {"chat_id": chat_id}, {"_id": 0}
        ).sort("created_at", -1).to_list(10)
        recent_msgs.reverse()
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"impulse-{chat_id}-{uuid.uuid4()}",
            system_message=SYSTEM_MESSAGE
        )
        chat.with_model("anthropic", "claude-4-sonnet-20250514")
        
        # Feed history by appending to messages list
        for msg in recent_msgs:
            if msg.get("role") == "user":
                chat.messages.append({"role": "user", "content": msg["content"]})
            elif msg.get("role") == "assistant":
                chat.messages.append({"role": "assistant", "content": msg["content"]})
        
        # Send current message
        user_msg = UserMessage(text=content)
        response = await chat.send_message(user_msg)
        return response
    except Exception as e:
        logger.error(f"Claude error: {e}")
        error_str = str(e).lower()
        if "budget" in error_str or "exceeded" in error_str:
            return "The AI service budget has been reached. Please add balance to your Emergent Universal Key at Profile > Universal Key > Add Balance."
        return "I encountered an issue processing your request. Please try again."

@api_router.post("/chat/send")
async def send_message(req: ChatMessageRequest, request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]
    role = user.get("role", "free")
    limits = TIER_LIMITS.get(role, TIER_LIMITS["free"])
    
    # Check daily limit for message-limited tiers
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    daily_limit = limits["daily_messages"]
    if daily_limit is not None:
        last_date = user.get("last_message_date")
        count = user.get("daily_message_count", 0)
        if last_date != today:
            count = 0
        if count >= daily_limit:
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
    
    # Get AI response from Claude
    ai_content = await get_claude_response(chat_id, user_id, req.content)
    
    ai_msg_id = str(ObjectId())
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
        "daily_message_count": updated_user.get("daily_message_count", 0) if daily_limit is not None else None,
        "daily_limit": daily_limit
    }

@api_router.get("/chat/list")
async def list_chats(request: Request):
    user = await get_current_user(request)
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
# Image Generation (Nano Banana)
# ---------------------
@api_router.post("/image/generate")
async def generate_image(req: ImageGenRequest, request: Request):
    user = await get_current_user(request)
    user_id = user["_id"]
    role = user.get("role", "free")
    limits = TIER_LIMITS.get(role, TIER_LIMITS["free"])
    
    # Check daily image limit
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    img_limit = limits["daily_images"]
    if img_limit is not None:
        last_date = user.get("last_image_date")
        img_count = user.get("daily_image_count", 0)
        if last_date != today:
            img_count = 0
        if img_count >= img_limit:
            raise HTTPException(status_code=429, detail="Daily image generation limit reached.")
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"daily_image_count": img_count + 1, "last_image_date": today}}
        )
    
    try:
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Image generation not configured")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"img-{user_id}-{uuid.uuid4()}",
            system_message="You are an image generation assistant. Generate the requested image."
        )
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        
        msg = UserMessage(text=req.prompt)
        text_response, images = await chat.send_message_multimodal_response(msg)
        
        if not images:
            raise HTTPException(status_code=500, detail="No image was generated. Try a different prompt.")
        
        # Save first image to object storage
        img_data = base64.b64decode(images[0]["data"])
        img_path = f"{APP_NAME}/images/{user_id}/{uuid.uuid4()}.png"
        put_object(img_path, img_data, "image/png")
        
        # Store reference in DB
        img_id = str(uuid.uuid4())
        await db.generated_images.insert_one({
            "id": img_id,
            "user_id": user_id,
            "storage_path": img_path,
            "prompt": req.prompt,
            "chat_id": req.chat_id,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Also save as a chat message if in a chat context
        if req.chat_id:
            ai_msg_id = str(ObjectId())
            await db.messages.insert_one({
                "id": ai_msg_id,
                "chat_id": req.chat_id,
                "user_id": user_id,
                "role": "assistant",
                "content": f"![Generated Image](/api/files/{img_path})\n\n{text_response or ''}",
                "image_path": img_path,
                "type": "image",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        return {
            "image_id": img_id,
            "image_url": f"/api/files/{img_path}",
            "text": text_response or "",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail="Image generation failed. Please try again.")

@api_router.get("/files/{path:path}")
async def serve_file(path: str, request: Request, auth: str = Query(None)):
    # Auth check - either cookie or query param
    try:
        if auth:
            # Verify the auth token
            payload = jwt.decode(auth, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token")
        else:
            await get_current_user(request)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        data, content_type = get_object(path)
        return FastAPIResponse(content=data, media_type=content_type)
    except Exception as e:
        logger.error(f"File serve error: {e}")
        raise HTTPException(status_code=404, detail="File not found")

@api_router.get("/user/images")
async def list_user_images(request: Request):
    user = await get_current_user(request)
    images = await db.generated_images.find(
        {"user_id": user["_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return images

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
    
    await get_current_user(request)  # auth check
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
        
        # If paid and not already processed
        if status.payment_status == "paid" and tx.get("payment_status") != "paid":
            tx_type = tx.get("type", "subscription")
            if tx_type == "credit_purchase":
                # Add credits to user
                credits_to_add = tx.get("credits", 0)
                await db.users.update_one(
                    {"_id": ObjectId(tx["user_id"])},
                    {"$inc": {"video_credits": credits_to_add}}
                )
                update_data["credits_added"] = credits_to_add
                logger.info(f"Added {credits_to_add} credits to user {tx['user_id']}")
            else:
                # Subscription upgrade
                plan = tx.get("plan")
                if plan in SUBSCRIPTION_PLANS:
                    new_role = SUBSCRIPTION_PLANS[plan]["role"]
                    update_fields = {"role": new_role}
                    # Initialize credits for Creative Pro
                    if new_role == "pro_creative":
                        update_fields["video_credits"] = 100
                        update_fields["credits_reset_date"] = datetime.now(timezone.utc).isoformat()
                    await db.users.update_one(
                        {"_id": ObjectId(tx["user_id"])},
                        {"$set": update_fields}
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
                tx_type = tx.get("type", "subscription")
                if tx_type == "credit_purchase":
                    credits_to_add = tx.get("credits", 0)
                    await db.users.update_one(
                        {"_id": ObjectId(tx["user_id"])},
                        {"$inc": {"video_credits": credits_to_add}}
                    )
                else:
                    plan = tx.get("plan")
                    if plan in SUBSCRIPTION_PLANS:
                        new_role = SUBSCRIPTION_PLANS[plan]["role"]
                        update_fields = {"role": new_role}
                        if new_role == "pro_creative":
                            update_fields["video_credits"] = 100
                            update_fields["credits_reset_date"] = datetime.now(timezone.utc).isoformat()
                        await db.users.update_one(
                            {"_id": ObjectId(tx["user_id"])},
                            {"$set": update_fields}
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
# User Profile & Usage
# ---------------------
@api_router.get("/user/usage")
async def get_user_usage(request: Request):
    user = await get_current_user(request)
    role = user.get("role", "free")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    limits = TIER_LIMITS.get(role, TIER_LIMITS["free"])
    
    msg_count = user.get("daily_message_count", 0) if user.get("last_message_date") == today else 0
    img_count = user.get("daily_image_count", 0) if user.get("last_image_date") == today else 0
    vid_count = user.get("daily_video_count", 0) if user.get("last_video_date") == today else 0
    
    # Monthly credit reset for Creative Pro
    video_credits = user.get("video_credits", 0)
    if role == "pro_creative":
        reset_date = user.get("credits_reset_date")
        now = datetime.now(timezone.utc)
        if not reset_date or (now - datetime.fromisoformat(reset_date)).days >= 30:
            video_credits = limits.get("monthly_credits", 100)
            await db.users.update_one(
                {"_id": ObjectId(user["_id"])},
                {"$set": {"video_credits": video_credits, "credits_reset_date": now.isoformat()}}
            )
    
    return {
        "role": role,
        "daily_message_count": msg_count,
        "daily_message_limit": limits["daily_messages"],
        "daily_image_count": img_count,
        "daily_image_limit": limits["daily_images"],
        "daily_video_count": vid_count,
        "daily_video_limit": limits["daily_videos"],
        "video_credits": video_credits,
        "max_video_duration": limits["max_video_duration"],
        "video_quality": limits["video_quality"],
        "watermark": limits["watermark"],
        "uses_credits": limits["uses_credits"],
    }

# ---------------------
# Credit Top-Up Store
# ---------------------
@api_router.get("/credits/packs")
async def get_credit_packs(request: Request):
    user = await get_current_user(request)
    return {
        "packs": [
            {"id": k, "name": v["name"], "credits": v["credits"], "amount": v["amount"]}
            for k, v in CREDIT_PACKS.items()
        ],
        "current_credits": user.get("video_credits", 0)
    }

@api_router.post("/credits/purchase")
async def purchase_credits(req: CreditPurchaseRequest, request: Request):
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
    
    user = await get_current_user(request)
    role = user.get("role", "free")
    
    if role != "pro_creative" and role != "admin":
        raise HTTPException(status_code=403, detail="Credit top-ups are only available for Creative Pro users.")
    
    if req.pack_id not in CREDIT_PACKS:
        raise HTTPException(status_code=400, detail="Invalid credit pack")
    
    pack = CREDIT_PACKS[req.pack_id]
    api_key = os.environ.get("STRIPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    origin_url = req.origin_url.rstrip("/")
    success_url = f"{origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}&type=credits"
    cancel_url = f"{origin_url}/credits"
    
    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    checkout_request = CheckoutSessionRequest(
        amount=pack["amount"],
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["_id"],
            "type": "credit_purchase",
            "pack_id": req.pack_id,
            "credits": str(pack["credits"]),
            "user_email": user["email"]
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "user_id": user["_id"],
        "email": user["email"],
        "type": "credit_purchase",
        "pack_id": req.pack_id,
        "credits": pack["credits"],
        "amount": pack["amount"],
        "currency": "usd",
        "payment_status": "initiated",
        "status": "pending",
        "metadata": {"pack_id": req.pack_id, "credits": str(pack["credits"])},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"url": session.url, "session_id": session.session_id}

# ---------------------
# Admin Dashboard
# ---------------------
@api_router.get("/admin/dashboard")
async def admin_dashboard(request: Request):
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_users = await db.users.count_documents({})
    free_users = await db.users.count_documents({"role": "free"})
    reasoning_users = await db.users.count_documents({"role": "pro_reasoning"})
    creative_users = await db.users.count_documents({"role": "pro_creative"})
    
    total_feedback = await db.feedback_logs.count_documents({})
    thumbs_up = await db.feedback_logs.count_documents({"rating": "up"})
    thumbs_down = await db.feedback_logs.count_documents({"rating": "down"})
    
    total_credit_purchases = await db.payment_transactions.count_documents({
        "type": "credit_purchase", "payment_status": "paid"
    })
    credit_revenue_pipeline = [
        {"$match": {"type": "credit_purchase", "payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    credit_revenue_result = await db.payment_transactions.aggregate(credit_revenue_pipeline).to_list(1)
    credit_revenue = credit_revenue_result[0]["total"] if credit_revenue_result else 0
    
    sub_revenue_pipeline = [
        {"$match": {"type": {"$ne": "credit_purchase"}, "payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    sub_revenue_result = await db.payment_transactions.aggregate(sub_revenue_pipeline).to_list(1)
    sub_revenue = sub_revenue_result[0]["total"] if sub_revenue_result else 0
    
    return {
        "users": {"total": total_users, "free": free_users, "pro_reasoning": reasoning_users, "pro_creative": creative_users},
        "feedback": {"total": total_feedback, "thumbs_up": thumbs_up, "thumbs_down": thumbs_down},
        "revenue": {"subscriptions": sub_revenue, "credit_purchases": credit_revenue, "total_credit_purchases": total_credit_purchases}
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
    
    # Initialize object storage
    try:
        init_storage()
        logger.info("Object storage initialized")
    except Exception as e:
        logger.warning(f"Storage init failed (non-critical): {e}")
    
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@impulseai.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    existing = await db.users.find_one({"email": admin_email})
    if existing is None:
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hash_password(admin_password),
            "name": "Admin",
            "role": "admin",
            **get_default_user_fields(),
            "is_first_login": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Admin user created: {admin_email}")
    else:
        updates = {}
        if existing.get("role") != "admin":
            updates["role"] = "admin"
        if not verify_password(admin_password, existing["password_hash"]):
            updates["password_hash"] = hash_password(admin_password)
        # Ensure new fields exist
        for field, default in get_default_user_fields().items():
            if field not in existing:
                updates[field] = default
        if updates:
            await db.users.update_one({"email": admin_email}, {"$set": updates})
            logger.info(f"Admin user updated: {admin_email}")
    
    # Write test credentials
    os.makedirs("/app/memory", exist_ok=True)
    with open("/app/memory/test_credentials.md", "w") as f:
        f.write("# Test Credentials\n\n")
        f.write(f"## Admin\n- Email: {admin_email}\n- Password: {admin_password}\n- Role: admin\n\n")
        f.write("## Test User\n- Email: testuser@impulseai.com\n- Password: test1234\n- Role: free (register via /api/auth/register)\n\n")
        f.write("## Auth Endpoints\n")
        f.write("- POST /api/auth/register\n- POST /api/auth/login\n- POST /api/auth/logout\n")
        f.write("- GET /api/auth/me\n- POST /api/auth/refresh\n\n")
        f.write("## Chat Endpoints\n")
        f.write("- POST /api/chat/send\n- GET /api/chat/list\n- GET /api/chat/{chat_id}/messages\n")
        f.write("- DELETE /api/chat/{chat_id}\n\n")
        f.write("## Usage & Credits\n")
        f.write("- GET /api/user/usage\n- GET /api/credits/packs\n- POST /api/credits/purchase\n\n")
        f.write("## Admin\n- GET /api/admin/dashboard\n\n")
        f.write("## Other Endpoints\n")
        f.write("- POST /api/feedback\n- POST /api/checkout/create\n")
        f.write("- GET /api/checkout/status/{session_id}\n")

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
