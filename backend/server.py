from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
import uuid
import re
import random
from datetime import datetime, timezone, timedelta
import bcrypt
from jose import jwt
from pydantic import BaseModel as PydanticBaseModel
from bson import ObjectId
import httpx

import cloudinary
import cloudinary.uploader
import io


from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


ROOT_DIR = Path(__file__).parent


# Cloudinary config from environment (optional - if not set we fall back to local storage)
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")
CLOUDINARY_FOLDER = os.environ.get("CLOUDINARY_FOLDER", "ecom/uploads")

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )
else:
    # Log a warning so it's obvious in the server log that Cloudinary isn't configured
    logging.info("Cloudinary credentials not found in environment — image uploads will be saved locally.")

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'ecommerce')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week



# Email Configuration
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_FROM = MAIL_USERNAME  # Use the authenticated email address

MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')

# FastAPI-Mail Configuration
if MAIL_USERNAME and MAIL_PASSWORD:
    mail_config = ConnectionConfig(
        MAIL_USERNAME=MAIL_USERNAME,
        MAIL_PASSWORD=MAIL_PASSWORD,
        MAIL_FROM=MAIL_FROM,
        MAIL_PORT=MAIL_PORT,
        MAIL_SERVER=MAIL_SERVER,
        MAIL_STARTTLS=True,
        MAIL_SSL_TLS=False,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )
    mail = FastMail(mail_config)
else:
    mail = None

# OTP Configuration
OTP_EXPIRY_MINUTES = 10

# Security
security = HTTPBearer()

# Create the main app
app = FastAPI(title="E-Commerce API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Add validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        errors.append(f"{field}: {msg}")

    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )

# CORS Middleware
origins = [
    "https://my-ecommerce-app-mocha.vercel.app",
    "https://*.vercel.app",
    "https://my-ecommerce-app-otgm.onrender.com",
    "https://*.onrender.com",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.(vercel\.app|onrender\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# ==================== MODELS ====================

class UserBase(BaseModel):
    name: str
    email: str
    role: str = "user"  # user or admin

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class DeliveryAddress(BaseModel):
    full_name: str
    phone_number: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    pincode: Optional[str] = None  # Make pincode optional for compatibility

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None
    delivery_address: Optional[DeliveryAddress] = None

    @validator('mobile_number')
    def validate_mobile_number(cls, v):
        if v is not None and v.strip():  # Only validate if not empty after stripping
            # Remove any spaces, hyphens, or parentheses
            cleaned = re.sub(r'[\s\-\(\)]', '', v)
            # Check if it's only digits and has valid length
            if not cleaned.isdigit() or not (10 <= len(cleaned) <= 15):
                raise ValueError('Mobile number must contain only digits and be 10-15 characters long')
        elif v is not None and not v.strip():
            # If it's an empty string after stripping, set to None
            return None
        return v

    @validator('delivery_address')
    def validate_delivery_address(cls, v):
        if v is not None:
            # Clean the postal code (remove spaces, hyphens, etc.)
            cleaned_postal_code = v.postal_code.replace(' ', '').replace('-', '')
            if not cleaned_postal_code.isdigit():
                raise ValueError('Postal code must contain only digits')
            # Set pincode to postal_code for compatibility (if not already set)
            if not v.pincode:
                v.pincode = cleaned_postal_code
            # Update the postal_code with cleaned version
            v.postal_code = cleaned_postal_code
        return v

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mobile_number: Optional[str] = None
    delivery_address: Optional[Dict[str, Any]] = None  # Make it flexible to handle different address formats
    isVerified: bool = False
    otp: Optional[str] = None
    otpExpires: Optional[datetime] = None



class ProductBase(BaseModel):
    name: str
    price: float
    description: str
    category: str
    stock: int = 0
    images: List[str] = []

    @validator('name')
    def validate_name_length(cls, v):
        if len(v) > 200:
            raise ValueError('Product name must not exceed 200 characters')
        return v

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    average_rating: Optional[float] = 0.0
    total_ratings: Optional[int] = 0

class OrderItem(BaseModel):
    product_id: str
    name: str
    quantity: int
    price: float
    total: Optional[float] = None

class OrderBase(BaseModel):
    products: List[OrderItem]
    total_amount: float
    
class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Additional fields for orders
    user_email: Optional[str] = None
    status: Optional[str] = None
    delivery_address: Optional[DeliveryAddress] = None
    order_id: Optional[str] = None

class SupportTicketBase(BaseModel):
    name: str
    email: EmailStr
    subject: str
    description: str
    status: str = "open"

class SupportTicketCreate(SupportTicketBase):
    pass

class SupportTicket(SupportTicketBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    messages: List[Dict[str, Any]] = []

class FAQBase(BaseModel):
    question: str
    answer: str
    category: str

class FAQCreate(FAQBase):
    pass

class FAQ(FAQBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RatingBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)

class RatingCreate(RatingBase):
    pass

class Rating(RatingBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LoginHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    login_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

class ChangePasswordOTPRequest(BaseModel):
    old_password: str
    new_password: str

class VerifyChangePasswordOTPRequest(BaseModel):
    otp: str

class DeleteAccountRequest(BaseModel):
    password: str









# ==================== AUTH UTILITIES ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

# ==================== OTP UTILITIES ====================

def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

async def send_email(to_email: str, subject: str, body: str):
    """Send email using Resend API"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not set - skipping email send")
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": "ShopMate <no-reply@shopmate.app>",
                    "to": [to_email],
                    "subject": subject,
                    "html": body
                }
            )
            response.raise_for_status()
            logging.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logging.error(f"Failed to send email via Resend: {e}")
            raise HTTPException(status_code=500, detail="Failed to send email")

def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_access_token(token)
    user = await db.users.find_one({"id": payload["user_id"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    # Filter out fields that aren't in the User model
    user_data = {k: v for k, v in user.items() if k in User.__fields__}
    return User(**user_data)

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user




# ==================== ROUTES ====================

# Health Check
@api_router.get("/")
async def root():
    return {"message": "E-Commerce API is running"}

# AUTH ROUTES

@api_router.post("/auth/login", response_model=dict)
async def login(login_data: UserLogin, request: Request):
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Check if email is verified
    if not user_doc.get("isVerified", False):
        raise HTTPException(status_code=403, detail="Please verify your email using OTP before logging in")

    # Verify password
    if not verify_password(login_data.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials") 

    # Filter out fields that aren't in the User model
    user_data = {k: v for k, v in user_doc.items() if k != "password_hash" and k in User.__fields__}
    user = User(**user_data)

    # Log login history
    try:
        login_entry = LoginHistory(
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            device=request.headers.get("user-agent", "").split(" ")[0] if request.headers.get("user-agent") else None
        )
        await db.login_history.insert_one(login_entry.dict())
    except Exception as e:
        logging.warning(f"Failed to log login history: {e}")

    token = create_access_token(user.id, user.email, user.role)

    return {
        "access_token": token,
        "user": user.dict(),
        "message": "Login successful"
    }

# OTP AUTH ROUTES
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    otp = generate_otp()
    otp_expires = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

    user = User(**user_data.dict(exclude={"password"}))
    user.isVerified = False
    user.otp = otp
    user.otpExpires = otp_expires

    user_dict = user.dict()
    user_dict["password_hash"] = hash_password(user_data.password)

    await db.users.insert_one(user_dict)

    try:
        await send_email(
            user_data.email,
            "Email Verification OTP - Shop Mate",
            f"<h3>Your OTP is <b>{otp}</b></h3>"
        )
    except Exception as e:
        logging.error(f"OTP email failed but user created: {e}")

    return {
        "message": "Registration successful. Please verify OTP.",
        "email": user_data.email
    }

@api_router.post("/auth/resend-otp")
async def resend_otp(email: EmailStr):
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("isVerified"):
        raise HTTPException(status_code=400, detail="Email already verified")

    otp = generate_otp()
    otp_expires = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

    await db.users.update_one(
        {"email": email},
        {"$set": {"otp": otp, "otpExpires": otp_expires}}
    )

    try:
        await send_email(email, "Resend OTP - Shop Mate", f"<b>{otp}</b>")
    except Exception as e:
        logging.error(f"Resend OTP failed: {e}")

    return {"message": "OTP resent successfully"}

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

@api_router.post("/auth/verify-otp", response_model=dict)
async def verify_otp(verify_data: VerifyOTPRequest):
    # Find user
    user_doc = await db.users.find_one({"email": verify_data.email})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if already verified
    if user_doc.get("isVerified", False):
        raise HTTPException(status_code=400, detail="Email already verified")

    # Check OTP
    if user_doc.get("otp") != verify_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check expiry - ensure both datetimes are offset-aware
    current_time = datetime.now(timezone.utc)
    otp_expires = user_doc["otpExpires"]
    if isinstance(otp_expires, datetime) and otp_expires.tzinfo is None:
        # If stored as naive datetime, assume UTC
        otp_expires = otp_expires.replace(tzinfo=timezone.utc)
    if current_time > otp_expires:
        raise HTTPException(status_code=400, detail="OTP has expired")

    # Update user
    await db.users.update_one(
        {"email": verify_data.email},
        {"$set": {"isVerified": True}, "$unset": {"otp": "", "otpExpires": ""}}
    )

    return {"message": "Email verified successfully! You can now log in."}

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ForgotPasswordVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class ForgotPasswordResetRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

@api_router.post("/auth/forgot-password/request", response_model=dict)
async def forgot_password_request(request_data: ForgotPasswordRequest):
    # Find user
    user_doc = await db.users.find_one({"email": request_data.email})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate OTP
    otp = generate_otp()
    otp_expires = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

    # Save OTP with purpose
    await db.users.update_one(
        {"email": request_data.email},
        {"$set": {"otp": otp, "otpExpires": otp_expires, "otpPurpose": "reset"}}
    )

    # Send email
    subject = "Password Reset OTP - Shop Mate"
    body = f"""
    <html>
    <body>
        <h2>Password Reset</h2>
        <p>Your OTP for password reset is: <strong>{otp}</strong></p>
        <p>This OTP will expire in {OTP_EXPIRY_MINUTES} minutes.</p>
        <p>If you didn't request this, please ignore this email.</p>
    </body>
    </html>
    """
    await send_email(request_data.email, subject, body)

    return {"message": "OTP sent to your email for password reset"}

@api_router.post("/auth/forgot-password/verify", response_model=dict)
async def forgot_password_verify(verify_data: ForgotPasswordVerifyRequest):
    # Find user
    user_doc = await db.users.find_one({"email": verify_data.email})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Check OTP purpose
    if user_doc.get("otpPurpose") != "reset":
        raise HTTPException(status_code=400, detail="Invalid OTP purpose")

    # Check OTP
    if user_doc.get("otp") != verify_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check expiry - ensure both datetimes are offset-aware
    current_time = datetime.now(timezone.utc)
    otp_expires = user_doc["otpExpires"]
    if isinstance(otp_expires, datetime) and otp_expires.tzinfo is None:
        # If stored as naive datetime, assume UTC
        otp_expires = otp_expires.replace(tzinfo=timezone.utc)
    if current_time > otp_expires:
        raise HTTPException(status_code=400, detail="OTP has expired")

    return {"message": "OTP verified successfully"}

@api_router.post("/auth/forgot-password/reset", response_model=dict)
async def forgot_password_reset(reset_data: ForgotPasswordResetRequest):
    # Find user
    user_doc = await db.users.find_one({"email": reset_data.email})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    # Check OTP purpose
    if user_doc.get("otpPurpose") != "reset":
        raise HTTPException(status_code=400, detail="Invalid OTP purpose")

    # Check OTP
    if user_doc.get("otp") != reset_data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Check expiry - ensure both datetimes are offset-aware
    current_time = datetime.now(timezone.utc)
    otp_expires = user_doc["otpExpires"]
    if isinstance(otp_expires, datetime) and otp_expires.tzinfo is None:
        # If stored as naive datetime, assume UTC
        otp_expires = otp_expires.replace(tzinfo=timezone.utc)
    if current_time > otp_expires:
        raise HTTPException(status_code=400, detail="OTP has expired")

    # Hash new password
    hashed_password = hash_password(reset_data.new_password)

    # Update password and clear OTP
    await db.users.update_one(
        {"email": reset_data.email},
        {"$set": {"password_hash": hashed_password}, "$unset": {"otp": "", "otpExpires": "", "otpPurpose": ""}}
    )

    return {"message": "Password reset successfully"}

@api_router.get("/auth/verify")
async def verify_email(token: str):
    # Find verification token
    verification = await db.email_verifications.find_one({"token": token})
    if not verification:
        raise HTTPException(status_code=400, detail="Invalid verification token")

    # Check if token is expired
    if datetime.now(timezone.utc) > verification["expires_at"]:
        raise HTTPException(status_code=400, detail="Verification token has expired")

    # Update user verification status
    await db.users.update_one(
        {"id": verification["user_id"]},
        {"$set": {"is_verified": True}}
    )

    # Delete the verification token
    await db.email_verifications.delete_one({"token": token})

    return {
        "message": "Email verified successfully! You can now log in to your account."
    }

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.get("/users/profile", response_model=User)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile information"""
    return current_user

@api_router.put("/users/profile", response_model=User)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    try:
        # Check if email is being updated and if it's already taken by another user
        if profile_data.email and profile_data.email != current_user.email:
            existing_user = await db.users.find_one({"email": profile_data.email})
            if existing_user and existing_user["id"] != current_user.id:
                raise HTTPException(status_code=400, detail="Email already registered to another user")

        # Prepare update data
        update_data = {}
        if profile_data.name is not None:
            update_data["name"] = profile_data.name
        if profile_data.email is not None:
            update_data["email"] = profile_data.email
        if profile_data.mobile_number is not None:
            update_data["mobile_number"] = profile_data.mobile_number
        if profile_data.delivery_address is not None:
            update_data["delivery_address"] = profile_data.delivery_address.dict()

        # Update user in database
        if update_data:
            result = await db.users.update_one(
                {"id": current_user.id},
                {"$set": update_data}
            )

            if result.modified_count == 0:
                raise HTTPException(status_code=404, detail="User not found")

        # Fetch and return updated user
        updated_user_doc = await db.users.find_one({"id": current_user.id})
        if not updated_user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Filter out fields that aren't in the User model
        user_data = {k: v for k, v in updated_user_doc.items() if k in User.__fields__}
        return User(**user_data)

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

@api_router.put("/users/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    try:
        # Get user document
        user_doc = await db.users.find_one({"id": current_user.id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify old password
        if not verify_password(password_data.old_password, user_doc["password_hash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Hash new password
        new_hashed_password = hash_password(password_data.new_password)

        # Update password
        result = await db.users.update_one(
            {"id": current_user.id},
            {"$set": {"password_hash": new_hashed_password}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update password")

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Password change error: {e}")
        raise HTTPException(status_code=500, detail="Failed to change password")

@api_router.post("/users/change-password/request-otp")
async def request_change_password_otp(
    password_data: ChangePasswordOTPRequest,
    current_user: User = Depends(get_current_user)
):
    """Request OTP for password change"""
    try:
        # Get user document
        user_doc = await db.users.find_one({"id": current_user.id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify old password
        if not verify_password(password_data.old_password, user_doc["password_hash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Generate OTP and set expiry
        otp = generate_otp()
        otp_expires = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRY_MINUTES)

        # Store OTP and new password temporarily
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$set": {
                    "otp": otp,
                    "otpExpires": otp_expires,
                    "otpPurpose": "change_password",
                    "pendingNewPassword": hash_password(password_data.new_password)
                }
            }
        )

        # Send OTP email
        subject = "Password Change OTP - Shop Mate"
        body = f"""
        <html>
        <body>
            <h2>Password Change Verification</h2>
            <p>Your OTP for password change is: <strong>{otp}</strong></p>
            <p>This OTP will expire in {OTP_EXPIRY_MINUTES} minutes.</p>
            <p>If you didn't request this change, please ignore this email.</p>
        </body>
        </html>
        """
        await send_email(current_user.email, subject, body)

        return {"message": "OTP sent to your email for password change verification"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Password change OTP request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")

@api_router.post("/users/change-password/verify-otp")
async def verify_change_password_otp(
    otp_data: VerifyChangePasswordOTPRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify OTP and change password"""
    try:
        # Get user document
        user_doc = await db.users.find_one({"id": current_user.id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Check OTP purpose
        if user_doc.get("otpPurpose") != "change_password":
            raise HTTPException(status_code=400, detail="Invalid OTP purpose")

        # Check OTP
        if user_doc.get("otp") != otp_data.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")

        # Check expiry
        current_time = datetime.now(timezone.utc)
        otp_expires = user_doc["otpExpires"]
        if isinstance(otp_expires, datetime) and otp_expires.tzinfo is None:
            otp_expires = otp_expires.replace(tzinfo=timezone.utc)
        if current_time > otp_expires:
            raise HTTPException(status_code=400, detail="OTP has expired")

        # Get the pending new password
        new_password_hash = user_doc.get("pendingNewPassword")
        if not new_password_hash:
            raise HTTPException(status_code=400, detail="No pending password change found")

        # Update password and clear OTP data
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$set": {"password_hash": new_password_hash},
                "$unset": {"otp": "", "otpExpires": "", "otpPurpose": "", "pendingNewPassword": ""}
            }
        )

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Password change OTP verification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to change password")

@api_router.delete("/users/delete-address")
async def delete_address(current_user: User = Depends(get_current_user)):
    """Delete user's delivery address"""
    try:
        result = await db.users.update_one(
            {"id": current_user.id},
            {"$unset": {"delivery_address": ""}}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found or no address to delete")

        return {"message": "Address deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Delete address error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete address")

@api_router.get("/users/login-history")
async def get_login_history(current_user: User = Depends(get_current_user)):
    """Get user's login history"""
    try:
        login_history = await db.login_history.find(
            {"user_id": current_user.id}
        ).sort("login_time", -1).to_list(50)

        # Format the response
        history_list = []
        for entry in login_history:
            history_list.append({
                "id": entry["id"],
                "login_time": entry["login_time"].isoformat(),
                "ip_address": entry.get("ip_address", "Unknown"),
                "user_agent": entry.get("user_agent", "Unknown"),
                "device": entry.get("device", "Unknown")
            })

        return {"login_history": history_list}

    except Exception as e:
        logging.error(f"Login history error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve login history")

@api_router.delete("/users/delete-account")
async def delete_account(
    delete_data: DeleteAccountRequest,
    current_user: User = Depends(get_current_user)
):
    """Delete user account permanently"""
    try:
        # Verify password
        user_doc = await db.users.find_one({"id": current_user.id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(delete_data.password, user_doc["password_hash"]):
            raise HTTPException(status_code=400, detail="Password is incorrect")

        # Delete all user data
        await db.users.delete_one({"id": current_user.id})
        await db.login_history.delete_many({"user_id": current_user.id})
        await db.orders.delete_many({"user_id": current_user.id})
        await db.support_tickets.delete_many({"user_id": current_user.id})

        return {"message": "Account deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Delete account error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")

# ADMIN USER MANAGEMENT ROUTES
@api_router.get("/admin/users", response_model=List[User])
async def get_all_users(admin_user: User = Depends(get_admin_user)):
    users = await db.users.find({}).to_list(100)
    # Filter out fields that aren't in the User model and handle ObjectId
    filtered_users = []
    for user in users:
        user_data = {k: v for k, v in user.items() if k != "password_hash" and k in User.__fields__}
        # Convert ObjectId to string if present
        if "_id" in user_data:
            user_data["id"] = str(user_data["_id"])
            del user_data["_id"]
        filtered_users.append(User(**user_data))
    return filtered_users

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin_user: User = Depends(get_admin_user)):
    if user_id == admin_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

# PRODUCT ROUTES
@api_router.get("/products", response_model=List[Product])
async def get_products(category: Optional[str] = None, search: Optional[str] = None):
    query = {}

    # Fix: Ensure query uses correct field names matching DB schema
    if category:
        query["category"] = category
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    products = await db.products.find(query).to_list(100)
    valid_products = []

    for product in products:
        try:
            # Calculate average rating and total ratings for each product
            ratings_pipeline = [
                {"$match": {"product_id": product["id"]}},
                {"$group": {
                    "_id": "$product_id",
                    "average_rating": {"$avg": "$rating"},
                    "total_ratings": {"$sum": 1}
                }}
            ]

            rating_stats = await db.ratings.aggregate(ratings_pipeline).to_list(1)

            if rating_stats:
                product["average_rating"] = rating_stats[0]["average_rating"]
                product["total_ratings"] = rating_stats[0]["total_ratings"]
            else:
                product["average_rating"] = 0
                product["total_ratings"] = 0

            valid_products.append(Product(**product))
        except Exception as e:
            logging.warning(f"Skipping invalid product {product.get('id', 'unknown')}: {e}")
            continue
    return valid_products

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, admin_user: User = Depends(get_admin_user)):
    product = Product(**product_data.dict())
    await db.products.insert_one(product.dict())
    return product

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_data: ProductCreate, admin_user: User = Depends(get_admin_user)):
    product = Product(**product_data.dict())
    product.id = product_id
    result = await db.products.replace_one({"id": product_id}, product.dict())
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, admin_user: User = Depends(get_admin_user)):
    logging.info(f"Attempting to delete product with ID: {product_id}")

    # First, check if product exists with any query method
    product_by_id = await db.products.find_one({"id": product_id})
    product_by_objectid = None
    if ObjectId.is_valid(product_id):
        try:
            product_by_objectid = await db.products.find_one({"_id": ObjectId(product_id)})
        except Exception:
            pass

    logging.info(f"Product by id field: {product_by_id is not None}")
    logging.info(f"Product by _id field: {product_by_objectid is not None}")

    # Try to delete by id field first
    result = await db.products.delete_one({"id": product_id})

    # If not found and product_id looks like ObjectId, try by _id
    if result.deleted_count == 0:
        try:
            if ObjectId.is_valid(product_id):
                result = await db.products.delete_one({"_id": ObjectId(product_id)})
        except Exception as e:
            logging.warning(f"ObjectId conversion failed: {e}")

    logging.info(f"Delete result - deleted_count: {result.deleted_count}")

    if result.deleted_count == 0:
        # Log all products for debugging
        all_products = await db.products.find({}).limit(10).to_list(10)
        product_ids = [str(p.get('id', p.get('_id', 'no-id'))) for p in all_products]
        logging.error(f"Product {product_id} not found. Available products: {product_ids}")
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@api_router.get("/products/{product_id}/ratings")
async def get_product_ratings(product_id: str):
    """Get all ratings for a product"""
    try:
        ratings_cursor = db.ratings.find({"product_id": product_id})
        ratings = []
        async for rating_doc in ratings_cursor:
            # Convert ObjectId to string and create Rating object
            rating_data = {k: v for k, v in rating_doc.items() if k != "_id"}
            if "_id" in rating_doc:
                rating_data["id"] = str(rating_doc["_id"])
            ratings.append(Rating(**rating_data))
        return ratings
    except Exception as e:
        logging.error(f"Get ratings error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ratings")

@api_router.post("/products/{product_id}/ratings")
async def submit_product_rating(
    product_id: str,
    rating_data: RatingCreate,
    current_user: User = Depends(get_current_user)
):
    """Submit a rating for a product"""
    try:
        # Check if product exists
        product = await db.products.find_one({"id": product_id})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Check if user already rated this product
        existing_rating = await db.ratings.find_one({
            "user_id": current_user.id,
            "product_id": product_id
        })

        if existing_rating:
            raise HTTPException(status_code=400, detail="You have already rated this product and cannot change your rating.")

        # Create new rating
        rating = Rating(
            user_id=current_user.id,
            product_id=product_id,
            rating=rating_data.rating
        )
        await db.ratings.insert_one(rating.dict())

        # Recalculate and update product's average rating and total ratings
        ratings_pipeline = [
            {"$match": {"product_id": product_id}},
            {"$group": {
                "_id": "$product_id",
                "average_rating": {"$avg": "$rating"},
                "total_ratings": {"$sum": 1}
            }}
        ]

        rating_stats = await db.ratings.aggregate(ratings_pipeline).to_list(1)

        if rating_stats:
            await db.products.update_one(
                {"id": product_id},
                {"$set": {
                    "average_rating": rating_stats[0]["average_rating"],
                    "total_ratings": rating_stats[0]["total_ratings"]
                }}
            )

        return {"message": "Rating submitted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Submit rating error: {e}")
        raise HTTPException(status_code=500, detail="You have already rated this product and cannot change your rating.")

# ORDER ROUTES for cancelled order
@api_router.get("/orders", response_model=List[Order])
async def get_user_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find({"user_id": current_user.id}).sort("created_at", -1).to_list(50)
    return [Order(**order) for order in orders]

@api_router.get("/admin/orders")
async def get_all_orders(admin_user: User = Depends(get_admin_user)):
    orders = await db.orders.find({}).sort("created_at", -1).to_list(100)

    # Convert ObjectId to string for JSON serialization and ensure id field exists
    for order in orders:
        if "_id" in order:
            order["id"] = str(order["_id"])
            del order["_id"]
        # Ensure every order has an id field
        if "id" not in order or not order.get("id"):
            order["id"] = str(uuid.uuid4())
        # Ensure status field exists
        if "status" not in order:
            order["status"] = "pending"

    # Return raw order data without strict validation for admin purposes
    return orders

@api_router.post("/orders")
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user)):
    """Create a new order"""
    try:
        # Get user delivery address
        user_doc = await db.users.find_one({"id": current_user.id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user has delivery address
        delivery_address_data = user_doc.get("delivery_address")
        if not delivery_address_data:
            raise HTTPException(status_code=400, detail="Please add a delivery address before placing an order")

        # Generate sequential order ID starting from 0001
        # Find the highest existing order_id number
        last_order = await db.orders.find_one(
            {"order_id": {"$exists": True, "$ne": None}},
            sort=[("order_id", -1)]
        )

        if last_order and last_order.get("order_id"):
            # Extract number from existing order_id (e.g., "0001" -> 1)
            try:
                last_number = int(last_order["order_id"])
                next_number = last_number + 1
            except (ValueError, TypeError):
                next_number = 1
        else:
            next_number = 1

        # Format as 4-digit zero-padded string
        order_id = f"{next_number:04d}"

        # Create order dict with user information
        order_dict = order_data.dict()
        # Ensure delivery_address is properly serialized
        delivery_address = DeliveryAddress(**delivery_address_data)
        order_dict["delivery_address"] = delivery_address.dict()

        order_dict.update({
            "user_id": current_user.id,
            "user_email": current_user.email,
            "status": "pending",
            "order_id": order_id
        })

        # Create Order instance with custom id (sequential order_id)
        order = Order(**order_dict)
        # Override the id field with the sequential order_id
        order.id = order_id

        # Insert order into database
        await db.orders.insert_one(order.dict())

        # Reduce stock for each product in the order
        for order_item in order_data.products:
            product = await db.products.find_one({"id": order_item.product_id})
            if not product:
                logging.error(f"Product {order_item.product_id} not found during stock reduction")
                raise HTTPException(status_code=500, detail=f"Product {order_item.product_id} not found")

            current_stock = product.get("stock", 0)
            if current_stock < order_item.quantity:
                logging.error(f"Insufficient stock for product {order_item.product_id}: requested {order_item.quantity}, available {current_stock}")
                raise HTTPException(status_code=400, detail=f"Insufficient stock for product {order_item.name}")

            # Reduce stock
            new_stock = current_stock - order_item.quantity
            await db.products.update_one(
                {"id": order_item.product_id},
                {"$set": {"stock": new_stock}}
            )
            logging.info(f"Reduced stock for product {order_item.product_id} from {current_stock} to {new_stock}")

        # Return Order instance to ensure proper serialization
        return order

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Order creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create order")

@api_router.put("/admin/orders/{order_id}")
async def update_order_status(order_id: str, status: str = Query(...), admin_user: User = Depends(get_admin_user)):
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    logging.info(f"Updating order status for order_id: {order_id}, status: {status}")

    # Try to find by id field or _id
    try:
        result = await db.orders.update_one({"$or": [{"id": order_id}, {"_id": ObjectId(order_id)}]}, {"$set": {"status": status}})
        logging.info(f"Update result: matched_count={result.matched_count}, modified_count={result.modified_count}")
    except Exception as e:
        logging.warning(f"ObjectId conversion failed for {order_id}: {e}")
        # If ObjectId fails, try just id
        result = await db.orders.update_one({"id": order_id}, {"$set": {"status": status}})
        logging.info(f"Fallback update result: matched_count={result.matched_count}, modified_count={result.modified_count}")

    if result.matched_count == 0:
        # Log all orders for debugging
        all_orders = await db.orders.find({}).to_list(10)
        logging.error(f"Order {order_id} not found. Available orders: {[order.get('id', order.get('_id')) for order in all_orders]}")
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order status updated successfully"}

@api_router.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str, current_user: User = Depends(get_current_user)):
    """
    Allow a user to cancel their own order if it is in 'pending' or 'confirmed' status.
    """
    try:
        # First try to find by UUID-based 'id'
        order = await db.orders.find_one({"user_id": current_user.id, "id": order_id})

        # If not found and order_id could be a Mongo ObjectId, try that
        if not order:
            try:
                oid = ObjectId(order_id)
                order = await db.orders.find_one({"user_id": current_user.id, "_id": oid})
            except Exception:
                oid = None  # Not a valid ObjectId; ignore and continue

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        status = (order.get("status") or "pending").lower()
        if status not in ["pending", "confirmed"]:
            raise HTTPException(status_code=400, detail="Order cannot be cancelled in its current status")

        # Try update by UUID 'id' first
        result = await db.orders.update_one(
            {"user_id": current_user.id, "id": order_id},
            {"$set": {"status": "cancelled"}}
        )

        # If no match, try update by ObjectId if valid
        if result.matched_count == 0:
            try:
                oid = ObjectId(order_id)
                result = await db.orders.update_one(
                    {"user_id": current_user.id, "_id": oid},
                    {"$set": {"status": "cancelled"}}
                )
            except Exception:
                pass

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Order not found")

        return {"message": "Order cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Cancel order error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel order")

@api_router.post("/orders/buy-now")
async def create_buy_now_order(order_data: OrderCreate, current_user: User = Depends(get_current_user)):
    """Create a buy now order (direct purchase without cart)"""
    try:
        # Get user delivery address
        user_doc = await db.users.find_one({"id": current_user.id})
        if not user_doc:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if user has delivery address
        delivery_address_data = user_doc.get("delivery_address")
        if not delivery_address_data:
            raise HTTPException(status_code=400, detail="Please add a delivery address before placing an order")

        # Validate stock for each product
        for order_item in order_data.products:
            product = await db.products.find_one({"id": order_item.product_id})
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {order_item.product_id} not found")

            current_stock = product.get("stock", 0)
            if current_stock < order_item.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock for product {order_item.name}")

        # Generate sequential order ID starting from 0001
        last_order = await db.orders.find_one(
            {"order_id": {"$exists": True, "$ne": None}},
            sort=[("order_id", -1)]
        )

        if last_order and last_order.get("order_id"):
            try:
                last_number = int(last_order["order_id"])
                next_number = last_number + 1
            except (ValueError, TypeError):
                next_number = 1
        else:
            next_number = 1

        order_id = f"{next_number:04d}"

        # Create order dict
        order_dict = order_data.dict()
        delivery_address = DeliveryAddress(**delivery_address_data)
        order_dict["delivery_address"] = delivery_address.dict()

        order_dict.update({
            "user_id": current_user.id,
            "user_email": current_user.email,
            "status": "pending",
            "order_id": order_id
        })

        order = Order(**order_dict)
        order.id = order_id

        # Insert order
        await db.orders.insert_one(order.dict())

        # Reduce stock for each product
        for order_item in order_data.products:
            product = await db.products.find_one({"id": order_item.product_id})
            current_stock = product.get("stock", 0)
            new_stock = current_stock - order_item.quantity
            await db.products.update_one(
                {"id": order_item.product_id},
                {"$set": {"stock": new_stock}}
            )

        return order

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Buy now order creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create order")

# SUPPORT ROUTES
@api_router.post("/support/tickets", response_model=SupportTicket)
async def create_support_ticket(
    ticket_data: SupportTicketCreate,
    current_user: Optional[User] = Depends(get_current_user)
):
    ticket = SupportTicket(**ticket_data.dict())
    if current_user:
        ticket.user_id = current_user.id

    # Add initial message
    ticket.messages = [{
        "sender": "user",
        "message": ticket_data.description,
        "timestamp": ticket.created_at.isoformat()
    }]

    await db.support_tickets.insert_one(ticket.dict())
    return ticket

@api_router.get("/admin/support/tickets", response_model=List[SupportTicket])
async def get_support_tickets(admin_user: User = Depends(get_admin_user)):
    tickets = await db.support_tickets.find({}).to_list(100)
    return [SupportTicket(**ticket) for ticket in tickets]

class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None
    admin_reply: Optional[str] = None

@api_router.put("/admin/support/tickets/{ticket_id}")
async def update_support_ticket(ticket_id: str, update_data: SupportTicketUpdate, admin_user: User = Depends(get_admin_user)):
    db_update = {}

    if update_data.status:
        valid_statuses = ["open", "in_progress", "closed"]
        if update_data.status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status")
        db_update["$set"] = db_update.get("$set", {})
        db_update["$set"]["status"] = update_data.status

    if update_data.admin_reply:
        # Append admin reply to messages
        admin_message = {
            "sender": "admin",
            "message": update_data.admin_reply,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        db_update["$push"] = {"messages": admin_message}

    if not db_update:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    result = await db.support_tickets.update_one({"id": ticket_id}, db_update)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket updated successfully"}

class UserReplyRequest(BaseModel):
    user_reply: str

@api_router.put("/support/tickets/{ticket_id}/reply")
async def user_reply_to_ticket(ticket_id: str, reply_data: UserReplyRequest, current_user: User = Depends(get_current_user)):
    # Check if ticket belongs to user and is not closed
    ticket = await db.support_tickets.find_one({"id": ticket_id, "user_id": current_user.id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or access denied")

    if ticket.get("status") == "closed":
        raise HTTPException(status_code=400, detail="Cannot reply to closed ticket")

    # Append user reply to messages
    user_message = {
        "sender": "user",
        "message": reply_data.user_reply,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    result = await db.support_tickets.update_one(
        {"id": ticket_id},
        {"$push": {"messages": user_message}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {"message": "Reply sent successfully"}

@api_router.delete("/admin/support/tickets/{ticket_id}")
async def delete_support_ticket(ticket_id: str, admin_user: User = Depends(get_admin_user)):
    result = await db.support_tickets.delete_one({"id": ticket_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket deleted successfully"}

# USER SUPPORT TICKET ROUTES
@api_router.get("/support/tickets/my", response_model=List[SupportTicket])
async def get_my_support_tickets(current_user: User = Depends(get_current_user)):
    tickets = await db.support_tickets.find({"user_id": current_user.id}).to_list(100)
    return [SupportTicket(**ticket) for ticket in tickets]

@api_router.delete("/support/tickets/{ticket_id}")
async def delete_my_support_ticket(ticket_id: str, current_user: User = Depends(get_current_user)):
    # Find the ticket first to ensure it belongs to the user
    ticket = await db.support_tickets.find_one({"id": ticket_id, "user_id": current_user.id})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or access denied")

    result = await db.support_tickets.delete_one({"id": ticket_id})
    return {"message": "Ticket deleted successfully"}

# FAQ ROUTES
@api_router.get("/faqs", response_model=List[FAQ])
async def get_faqs(category: Optional[str] = None):
    query = {}
    if category:
        query["category"] = category
    
    faqs = await db.faqs.find(query).to_list(50)
    return [FAQ(**faq) for faq in faqs]

@api_router.post("/admin/faqs", response_model=FAQ)
async def create_faq(faq_data: FAQCreate, admin_user: User = Depends(get_admin_user)):
    faq = FAQ(**faq_data.dict())
    await db.faqs.insert_one(faq.dict())
    return faq

# ADMIN DASHBOARD DATA
@api_router.get("/admin/dashboard")
async def get_dashboard_data(admin_user: User = Depends(get_admin_user)):
    total_products = await db.products.count_documents({})
    total_orders = await db.orders.count_documents({})
    total_users = await db.users.count_documents({"role": "user"})
    total_tickets = await db.support_tickets.count_documents({"status": "open"})

    # Recent orders
    recent_orders = await db.orders.find({}).sort("created_at", -1).limit(5).to_list(5)

    # Process recent orders
    recent_orders_list = []
    for order in recent_orders:
        order_data = {k: v for k, v in order.items() if k in Order.__fields__}
        # Ensure required fields are present
        if 'products' not in order_data or not order_data['products']:
            order_data['products'] = order_data.get('items', [])
        if 'total_amount' not in order_data or not order_data['total_amount']:
            order_data['total_amount'] = order_data.get('total_price', 0)
        try:
            recent_orders_list.append(Order(**order_data))
        except Exception as e:
            logging.warning(f"Failed to create Order object: {e}")
            continue

    return {
        "stats": {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_users": total_users,
            "open_tickets": total_tickets
        },
        "recent_orders": recent_orders_list
    }

# ADMIN DASHBOARD COUNTERS - Real-time data for Quick Actions
@api_router.get("/admin/dashboard/counters")
async def get_dashboard_counters(admin_user: User = Depends(get_admin_user)):
    """Get real-time counters for admin dashboard Quick Actions"""
    # Total products
    total_products = await db.products.count_documents({})

    # Total pending/open orders (orders that are not completed)
    total_pending_orders = await db.orders.count_documents({
        "$or": [
            {"status": {"$ne": "delivered"}},
            {"status": {"$in": ["pending", "confirmed", "shipped"]}}
        ]
    })

    # Total registered users
    total_users = await db.users.count_documents({"role": "user"})

    # Total unresolved support tickets (open or in_progress)
    total_unresolved_tickets = await db.support_tickets.count_documents({
        "status": {"$in": ["open", "in_progress"]}
    })

    return {
        "total_products": total_products,
        "total_pending_orders": total_pending_orders,
        "total_users": total_users,
        "total_unresolved_tickets": total_unresolved_tickets
    }





# Include router
app.include_router(api_router)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)

# Serve static files for uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.post("/api/admin/upload-images")
async def upload_images(files: List[UploadFile] = File(...), admin_user: User = Depends(get_admin_user)):
    """
    Upload images. If Cloudinary credentials are configured, upload to Cloudinary.
    Otherwise save to local uploads/ directory and return local URLs.
    """
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    uploaded_urls = []

    for file in files:
        file_ext = file.filename.split(".")[-1]
        if file_ext.lower() not in ["jpg", "jpeg", "png", "gif", "webp"]:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # If Cloudinary is configured, upload there
        if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
            try:
                content = await file.read()
                file_stream = io.BytesIO(content)
                # Use use_filename=True + unique_filename=True to keep filenames meaningful but unique
                res = cloudinary.uploader.upload(
                    file_stream,
                    folder=CLOUDINARY_FOLDER,
                    resource_type="image",
                    use_filename=True,
                    unique_filename=True,
                )
                # prefer secure_url if available
                public_url = res.get("secure_url") or res.get("url")
                uploaded_urls.append(public_url)
            except Exception as e:
                logging.error(f"Cloudinary upload failed for {file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to upload {file.filename}")
            finally:
                # ensure UploadFile buffer closed
                try:
                    await file.close()
                except Exception:
                    pass

        else:
            # Fallback: save to local uploads directory
            unique_filename = f"{uuid.uuid4()}.{file_ext}"
            file_path = upload_dir / unique_filename
            try:
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                # construct public URL using your server root; in production set proper base URL
                # When deploying on Render/Vercel you should use your deployed domain here.
                public_url = f"{os.environ.get('BACKEND_BASE_URL', 'http://localhost:8000')}/uploads/{unique_filename}"
                uploaded_urls.append(public_url)
            except Exception as e:
                logging.error(f"Local file save failed for {file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to save {file.filename}")
            finally:
                try:
                    await file.close()
                except Exception:
                    pass

    return {"urls": uploaded_urls}


# Test email endpoint
@api_router.post("/test-email")
async def test_email(email: str):
    """Test email sending functionality"""
    if not mail:
        return {"error": "Email configuration not set up properly"}

    test_message = MessageSchema(
        subject="Test Email - E-Commerce App",
        recipients=[email],
        body="""
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email to verify SMTP configuration.</p>
            <p>If you received this email, your SMTP settings are working correctly!</p>
            <p>Time sent: {}</p>
        </body>
        </html>
        """.format(datetime.now(timezone.utc).isoformat()),
        subtype="html"
    )

    try:
        await mail.send_message(test_message)
        logging.info(f"Test email sent successfully to {email}")
        return {"message": "Test email sent successfully!"}
    except Exception as e:
        logging.error(f"Failed to send test email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

# Send test email endpoint
@api_router.post("/send-test-email")
async def send_test_email(email: str):
    """Send a test email to verify SMTP configuration"""
    message = MessageSchema(
        subject="SMTP Test - E-Commerce App",
        recipients=[email],
        body="""
        <html>
        <body>
            <h2>SMTP Configuration Test</h2>
            <p>This is a test email to verify that your FastAPI-Mail SMTP configuration is working correctly.</p>
            <p>If you received this email, your email settings are properly configured!</p>
            <br>
            <p>Best regards,<br>E-Commerce App Team</p>
        </body>
        </html>
        """,
        subtype="html"
    )

    try:
        await mail.send_message(message)
        return {"message": "Test email sent successfully! Check your inbox."}
    except Exception as e:
        logging.error(f"Failed to send test email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
