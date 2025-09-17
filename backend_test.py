#!/usr/bin/env python3
"""
Comprehensive backend API testing for ShopMate e-commerce application.
Tests all API endpoints including authentication, products, payments, orders, support, and admin features.
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ShopMateAPITester:
    def __init__(self, base_url="https://shopmate-24.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.user_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })

    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"status_code": response.status_code, "text": response.text}

            return success, response_data

        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}

    def test_health_check(self):
        """Test API health check"""
        success, response = self.make_request('GET', '')
        self.log_test("Health Check", success and "E-Commerce API is running" in str(response))
        return success

    def test_user_registration(self):
        """Test user registration"""
        test_user_data = {
            "name": f"Test User {datetime.now().strftime('%H%M%S')}",
            "email": f"testuser_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "testpass123"
        }
        
        success, response = self.make_request('POST', 'auth/register', test_user_data)
        
        if success and 'access_token' in response:
            self.log_test("User Registration", True)
            return True, response['access_token']
        else:
            self.log_test("User Registration", False, str(response))
            return False, None

    def test_admin_login(self):
        """Test admin login"""
        login_data = {
            "email": "admin@shopmate.com",
            "password": "admin123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            self.log_test("Admin Login", True)
            return True
        else:
            self.log_test("Admin Login", False, str(response))
            return False

    def test_user_login(self):
        """Test regular user login"""
        login_data = {
            "email": "john@example.com",
            "password": "password123"
        }
        
        success, response = self.make_request('POST', 'auth/login', login_data)
        
        if success and 'access_token' in response:
            self.user_token = response['access_token']
            self.log_test("User Login", True)
            return True
        else:
            self.log_test("User Login", False, str(response))
            return False

    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.user_token:
            self.log_test("Get Current User", False, "No user token available")
            return False
            
        success, response = self.make_request('GET', 'auth/me', token=self.user_token)
        
        if success and 'email' in response:
            self.log_test("Get Current User", True)
            return True
        else:
            self.log_test("Get Current User", False, str(response))
            return False

    def test_get_products(self):
        """Test getting all products"""
        success, response = self.make_request('GET', 'products')
        
        if success and isinstance(response, list) and len(response) > 0:
            self.log_test("Get Products", True)
            return True, response
        else:
            self.log_test("Get Products", False, str(response))
            return False, []

    def test_search_products(self):
        """Test product search functionality"""
        success, response = self.make_request('GET', 'products?search=headphones')
        
        if success and isinstance(response, list):
            self.log_test("Search Products", True)
            return True
        else:
            self.log_test("Search Products", False, str(response))
            return False

    def test_filter_products_by_category(self):
        """Test product filtering by category"""
        success, response = self.make_request('GET', 'products?category=Electronics')
        
        if success and isinstance(response, list):
            self.log_test("Filter Products by Category", True)
            return True
        else:
            self.log_test("Filter Products by Category", False, str(response))
            return False

    def test_get_single_product(self, product_id: str):
        """Test getting a single product"""
        success, response = self.make_request('GET', f'products/{product_id}')
        
        if success and 'id' in response:
            self.log_test("Get Single Product", True)
            return True
        else:
            self.log_test("Get Single Product", False, str(response))
            return False

    def test_admin_create_product(self):
        """Test admin creating a new product"""
        if not self.admin_token:
            self.log_test("Admin Create Product", False, "No admin token available")
            return False, None
            
        new_product = {
            "name": f"Test Product {datetime.now().strftime('%H%M%S')}",
            "price": 99.99,
            "description": "This is a test product created by automated testing",
            "category": "Test Category",
            "stock": 10,
            "images": ["https://via.placeholder.com/400x400"]
        }
        
        success, response = self.make_request('POST', 'products', new_product, self.admin_token, 200)
        
        if success and 'id' in response:
            self.log_test("Admin Create Product", True)
            return True, response['id']
        else:
            self.log_test("Admin Create Product", False, str(response))
            return False, None

    def test_admin_update_product(self, product_id: str):
        """Test admin updating a product"""
        if not self.admin_token or not product_id:
            self.log_test("Admin Update Product", False, "No admin token or product ID available")
            return False
            
        updated_product = {
            "name": f"Updated Test Product {datetime.now().strftime('%H%M%S')}",
            "price": 149.99,
            "description": "This product has been updated by automated testing",
            "category": "Updated Category",
            "stock": 5,
            "images": ["https://via.placeholder.com/400x400"]
        }
        
        success, response = self.make_request('PUT', f'products/{product_id}', updated_product, self.admin_token)
        
        if success and 'id' in response:
            self.log_test("Admin Update Product", True)
            return True
        else:
            self.log_test("Admin Update Product", False, str(response))
            return False

    def test_admin_delete_product(self, product_id: str):
        """Test admin deleting a product"""
        if not self.admin_token or not product_id:
            self.log_test("Admin Delete Product", False, "No admin token or product ID available")
            return False
            
        success, response = self.make_request('DELETE', f'products/{product_id}', token=self.admin_token)
        
        if success and 'message' in response:
            self.log_test("Admin Delete Product", True)
            return True
        else:
            self.log_test("Admin Delete Product", False, str(response))
            return False

    def test_checkout_session_creation(self, product_id: str):
        """Test creating a Stripe checkout session"""
        if not self.user_token or not product_id:
            self.log_test("Create Checkout Session", False, "No user token or product ID available")
            return False, None
            
        checkout_data = {
            "cart_items": [
                {
                    "product_id": product_id,
                    "quantity": 2
                }
            ],
            "host_url": self.base_url
        }
        
        success, response = self.make_request('POST', 'payments/checkout', checkout_data, self.user_token)
        
        if success and 'checkout_url' in response and 'session_id' in response:
            self.log_test("Create Checkout Session", True)
            return True, response['session_id']
        else:
            self.log_test("Create Checkout Session", False, str(response))
            return False, None

    def test_payment_status_check(self, session_id: str):
        """Test checking payment status"""
        if not self.user_token or not session_id:
            self.log_test("Check Payment Status", False, "No user token or session ID available")
            return False
            
        success, response = self.make_request('GET', f'payments/status/{session_id}', token=self.user_token)
        
        if success and 'payment_status' in response:
            self.log_test("Check Payment Status", True)
            return True
        else:
            self.log_test("Check Payment Status", False, str(response))
            return False

    def test_get_user_orders(self):
        """Test getting user's orders"""
        if not self.user_token:
            self.log_test("Get User Orders", False, "No user token available")
            return False
            
        success, response = self.make_request('GET', 'orders', token=self.user_token)
        
        if success and isinstance(response, list):
            self.log_test("Get User Orders", True)
            return True
        else:
            self.log_test("Get User Orders", False, str(response))
            return False

    def test_admin_get_all_orders(self):
        """Test admin getting all orders"""
        if not self.admin_token:
            self.log_test("Admin Get All Orders", False, "No admin token available")
            return False
            
        success, response = self.make_request('GET', 'admin/orders', token=self.admin_token)
        
        if success and isinstance(response, list):
            self.log_test("Admin Get All Orders", True)
            return True
        else:
            self.log_test("Admin Get All Orders", False, str(response))
            return False

    def test_create_support_ticket(self):
        """Test creating a support ticket"""
        if not self.user_token:
            self.log_test("Create Support Ticket", False, "No user token available")
            return False
            
        ticket_data = {
            "name": "Test User",
            "email": "test@example.com",
            "subject": f"Test Support Ticket {datetime.now().strftime('%H%M%S')}",
            "description": "This is a test support ticket created by automated testing."
        }
        
        success, response = self.make_request('POST', 'support/tickets', ticket_data, self.user_token)
        
        if success and 'id' in response:
            self.log_test("Create Support Ticket", True)
            return True
        else:
            self.log_test("Create Support Ticket", False, str(response))
            return False

    def test_admin_get_support_tickets(self):
        """Test admin getting all support tickets"""
        if not self.admin_token:
            self.log_test("Admin Get Support Tickets", False, "No admin token available")
            return False
            
        success, response = self.make_request('GET', 'admin/support/tickets', token=self.admin_token)
        
        if success and isinstance(response, list):
            self.log_test("Admin Get Support Tickets", True)
            return True
        else:
            self.log_test("Admin Get Support Tickets", False, str(response))
            return False

    def test_get_faqs(self):
        """Test getting FAQs"""
        success, response = self.make_request('GET', 'faqs')
        
        if success and isinstance(response, list):
            self.log_test("Get FAQs", True)
            return True
        else:
            self.log_test("Get FAQs", False, str(response))
            return False

    def test_admin_create_faq(self):
        """Test admin creating a new FAQ"""
        if not self.admin_token:
            self.log_test("Admin Create FAQ", False, "No admin token available")
            return False
            
        faq_data = {
            "question": f"Test FAQ Question {datetime.now().strftime('%H%M%S')}?",
            "answer": "This is a test FAQ answer created by automated testing.",
            "category": "Testing"
        }
        
        success, response = self.make_request('POST', 'admin/faqs', faq_data, self.admin_token)
        
        if success and 'id' in response:
            self.log_test("Admin Create FAQ", True)
            return True
        else:
            self.log_test("Admin Create FAQ", False, str(response))
            return False

    def test_admin_dashboard(self):
        """Test admin dashboard data"""
        if not self.admin_token:
            self.log_test("Admin Dashboard", False, "No admin token available")
            return False
            
        success, response = self.make_request('GET', 'admin/dashboard', token=self.admin_token)
        
        if success and 'stats' in response:
            self.log_test("Admin Dashboard", True)
            return True
        else:
            self.log_test("Admin Dashboard", False, str(response))
            return False

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting ShopMate Backend API Tests")
        print("=" * 50)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ Health check failed - stopping tests")
            return False
        
        # Authentication tests
        print("\n🔐 Testing Authentication...")
        admin_login_success = self.test_admin_login()
        user_login_success = self.test_user_login()
        self.test_user_registration()
        self.test_get_current_user()
        
        # Product tests
        print("\n📦 Testing Products...")
        products_success, products = self.test_get_products()
        self.test_search_products()
        self.test_filter_products_by_category()
        
        product_id = None
        if products and len(products) > 0:
            product_id = products[0]['id']
            self.test_get_single_product(product_id)
        
        # Admin product management
        print("\n🛠️ Testing Admin Product Management...")
        created_product_success, created_product_id = self.test_admin_create_product()
        if created_product_success and created_product_id:
            self.test_admin_update_product(created_product_id)
            self.test_admin_delete_product(created_product_id)
        
        # Payment tests
        print("\n💳 Testing Payments...")
        if product_id:
            checkout_success, session_id = self.test_checkout_session_creation(product_id)
            if checkout_success and session_id:
                self.test_payment_status_check(session_id)
        
        # Order tests
        print("\n📋 Testing Orders...")
        self.test_get_user_orders()
        self.test_admin_get_all_orders()
        
        # Support tests
        print("\n🎫 Testing Support...")
        self.test_create_support_ticket()
        self.test_admin_get_support_tickets()
        
        # FAQ tests
        print("\n❓ Testing FAQs...")
        self.test_get_faqs()
        self.test_admin_create_faq()
        
        # Admin dashboard
        print("\n📊 Testing Admin Dashboard...")
        self.test_admin_dashboard()
        
        # Print results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        # Show failed tests
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"   • {test['name']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

def main():
    """Main function to run all tests"""
    tester = ShopMateAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())