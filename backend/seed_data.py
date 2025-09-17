#!/usr/bin/env python3
"""
Seed script to populate the database with sample data for the e-commerce application.
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import bcrypt
import uuid
from datetime import datetime, timezone

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def seed_admin_user():
    """Create an admin user"""
    admin_user = {
        "id": str(uuid.uuid4()),
        "name": "Admin User",
        "email": "admin@shopmate.com",
        "password_hash": hash_password("admin123"),
        "role": "admin",
        "created_at": datetime.now(timezone.utc)
    }
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"email": admin_user["email"]})
    if not existing_admin:
        await db.users.insert_one(admin_user)
        print("✅ Admin user created: admin@shopmate.com / admin123")
    else:
        print("ℹ️ Admin user already exists")

async def seed_sample_user():
    """Create a sample regular user"""
    sample_user = {
        "id": str(uuid.uuid4()),
        "name": "John Doe",
        "email": "john@example.com",
        "password_hash": hash_password("password123"),
        "role": "user",
        "created_at": datetime.now(timezone.utc)
    }
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": sample_user["email"]})
    if not existing_user:
        await db.users.insert_one(sample_user)
        print("✅ Sample user created: john@example.com / password123")
    else:
        print("ℹ️ Sample user already exists")

async def seed_products():
    """Create sample products"""
    sample_products = [
        {
            "id": str(uuid.uuid4()),
            "name": "Premium Wireless Headphones",
            "price": 299.99,
            "description": "High-quality wireless headphones with noise cancellation and premium sound quality. Perfect for music lovers and professionals.",
            "category": "Electronics",
            "stock": 25,
            "images": [
                "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=400&h=400&fit=crop&crop=center"
            ],
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Smart Fitness Watch",
            "price": 199.99,
            "description": "Advanced fitness tracker with heart rate monitoring, GPS, and smart notifications. Track your health and stay connected.",
            "category": "Electronics",
            "stock": 15,
            "images": [
                "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=400&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1508685096489-7aacd43bd3b1?w=400&h=400&fit=crop&crop=center"
            ],
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Ergonomic Office Chair",
            "price": 449.99,
            "description": "Comfortable ergonomic office chair with lumbar support and adjustable height. Perfect for long working hours.",
            "category": "Furniture",
            "stock": 8,
            "images": [
                "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=400&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1549497538-303791108f95?w=400&h=400&fit=crop&crop=center"
            ],
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Organic Coffee Beans",
            "price": 24.99,
            "description": "Premium organic coffee beans sourced from sustainable farms. Rich flavor and aromatic blend perfect for coffee enthusiasts.",
            "category": "Food & Beverages",
            "stock": 50,
            "images": [
                "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&h=400&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1498804103079-a6351b050096?w=400&h=400&fit=crop&crop=center"
            ],
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Modern Table Lamp",
            "price": 79.99,
            "description": "Stylish modern table lamp with adjustable brightness and warm LED lighting. Perfect for reading and ambient lighting.",
            "category": "Home & Garden",
            "stock": 20,
            "images": [
                "https://images.unsplash.com/photo-1507473885765-e6ed057c8fa4?w=400&h=400&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1518699525499-7fd0bd04a525?w=400&h=400&fit=crop&crop=center"
            ],
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Casual Cotton T-Shirt",
            "price": 29.99,
            "description": "Comfortable cotton t-shirt in various colors. Soft fabric with a relaxed fit, perfect for everyday wear.",
            "category": "Clothing",
            "stock": 100,
            "images": [
                "https://images.unsplash.com/photo-1521572163474-6864f9e17f8c?w=400&h=400&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=400&fit=crop&crop=center"
            ],
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Yoga Mat Premium",
            "price": 49.99,
            "description": "High-quality yoga mat with superior grip and cushioning. Non-slip surface perfect for all types of yoga practice.",
            "category": "Sports & Outdoors",
            "stock": 30,
            "images": [
                "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&h=400&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1506629905607-bb4fb2b40209?w=400&h=400&fit=crop&crop=center"
            ],
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Bluetooth Speaker",
            "price": 89.99,
            "description": "Portable Bluetooth speaker with powerful sound and long battery life. Waterproof design perfect for outdoor adventures.",
            "category": "Electronics",
            "stock": 35,
            "images": [
                "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=400&fit=crop&crop=center",
                "https://images.unsplash.com/photo-1545454675-3531b543be5d?w=400&h=400&fit=crop&crop=center"
            ],
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    # Check if products already exist
    existing_count = await db.products.count_documents({})
    if existing_count == 0:
        await db.products.insert_many(sample_products)
        print(f"✅ Created {len(sample_products)} sample products")
    else:
        print(f"ℹ️ Products already exist ({existing_count} products)")

async def seed_faqs():
    """Create sample FAQs"""
    sample_faqs = [
        {
            "id": str(uuid.uuid4()),
            "question": "How do I track my order?",
            "answer": "Once your order is shipped, you'll receive a tracking number via email. You can also check your order status in your account dashboard.",
            "category": "Orders",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What is your return policy?",
            "answer": "We offer a 30-day return policy for all items in original condition. Please contact our support team to initiate a return.",
            "category": "Returns",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "question": "Do you offer international shipping?",
            "answer": "Yes, we ship worldwide! International shipping rates and delivery times vary by destination. Check our shipping page for more details.",
            "category": "Shipping",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "question": "How can I change or cancel my order?",
            "answer": "Orders can be modified or cancelled within 1 hour of placement. After that, please contact our customer service team for assistance.",
            "category": "Orders",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "question": "What payment methods do you accept?",
            "answer": "We accept all major credit cards, PayPal, and other secure payment methods through our payment processor.",
            "category": "Payment",
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    existing_count = await db.faqs.count_documents({})
    if existing_count == 0:
        await db.faqs.insert_many(sample_faqs)
        print(f"✅ Created {len(sample_faqs)} sample FAQs")
    else:
        print(f"ℹ️ FAQs already exist ({existing_count} FAQs)")

async def main():
    """Main function to seed all data"""
    print("🌱 Starting database seeding...")
    try:
        await seed_admin_user()
        await seed_sample_user()
        await seed_products()
        await seed_faqs()
        print("\n🎉 Database seeding completed successfully!")
        print("\n📋 Test Accounts:")
        print("   Admin: admin@shopmate.com / admin123")
        print("   User:  john@example.com / password123")
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())