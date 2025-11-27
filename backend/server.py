from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, UploadFile, File, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any
import uuid
import re
from datetime import datetime, timezone, timedelta
import bcrypt
from jose import jwt
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel as PydanticBaseModel
from bson import ObjectId

import cloudinary
import cloudinary.uploader
import io


from dotenv import load_dotenv
load_dotenv()


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
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week



# Email Configuration (optional) 
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_FROM = os.environ.get('MAIL_FROM', MAIL_USERNAME)
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')

# FastAPI-Mail Configuration (only if email settings are provided)
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

# Security
security = HTTPBearer()

# Create the main app
app = FastAPI(title="E-Commerce API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# CORS Middleware
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "https://my-ecommerce-ph4f04ead-abuzar-khans-projects-e87a6346.vercel.app",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ==================== MODELS ====================

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "user"  # user or admin

class UserCreate(UserBase):
    password: str

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



class ProductBase(BaseModel):
    name: str
    price: float
    description: str
    category: str
    stock: int = 0
    images: List[str] = []

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

class DeleteAccountRequest(BaseModel):
    password: str









# ==================== AUTH UTILITIES ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

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
@api_router.post("/auth/register", response_model=dict)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password and create user
    hashed_password = hash_password(user_data.password)
    user = User(**user_data.dict(exclude={"password"}))
    user_dict = user.dict()
    user_dict["password_hash"] = hashed_password

    # Insert user
    await db.users.insert_one(user_dict)

    return {
        "user": user.dict(),
        "message": "User registered successfully."
    }

@api_router.post("/auth/login", response_model=dict)
async def login(login_data: UserLogin, request: Request):
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")

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
    return [Product(**product) for product in products]

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
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}



# ORDER ROUTES
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

        # Create order dict with user information
        order_dict = order_data.dict()
        delivery_address_data = user_doc.get("delivery_address")
        if delivery_address_data:
            # Ensure delivery_address is properly serialized
            delivery_address = DeliveryAddress(**delivery_address_data)
            order_dict["delivery_address"] = delivery_address.dict()
        else:
            order_dict["delivery_address"] = None

        order_dict.update({
            "user_id": current_user.id,
            "user_email": current_user.email,
            "status": "pending"
        })

        # Create Order instance
        order = Order(**order_dict)

        # Insert order into database
        await db.orders.insert_one(order.dict())

        # Return Order instance to ensure proper serialization
        return order

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Order creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create order")

@api_router.put("/admin/orders/{order_id}")
async def update_order_status(order_id: str, status: str = Query(...), admin_user: User = Depends(get_admin_user)):
    valid_statuses = ["pending", "confirmed", "shipped", "delivered"]
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
                public_url = f"{os.environ.get('BACKEND_PUBLIC_URL', 'http://localhost:8000')}/uploads/{unique_filename}"
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
    test_message = MessageSchema(
        subject="Test Email - E-Commerce App",
        recipients=[email],
        body="""
        <html>
        <body>
            <h2>Test Email</h2>
            <p>This is a test email to verify SMTP configuration.</p>
            <p>If you received this email, your SMTP settings are working correctly!</p>
        </body>
        </html>
        """,
        subtype="html"
    )

    try:
        await mail.send_message(test_message)
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
