#!/usr/bin/env python3
"""
Backend API testing for Impulse AI Phase 1 Changes
Tests tier limits, credit system, admin dashboard, and new user fields
"""

import requests
import sys
import json
import time
from datetime import datetime

class ImpulseAITester:
    def __init__(self, base_url="https://ai-chat-builder-55.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_cookies = None
        self.test_user_cookies = None
        self.test_chat_id = None
        self.test_message_id = None
        self.results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.results.append({
            "test": name,
            "success": success,
            "details": str(details),  # Convert to string to avoid serialization issues
            "timestamp": datetime.now().isoformat()
        })
        return success

    def make_request(self, method, endpoint, data=None, cookies=None, expected_status=200):
        """Make HTTP request and return response"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers, cookies=cookies)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers, cookies=cookies)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers, cookies=cookies)
            else:
                return None, f"Unsupported method: {method}"

            success = response.status_code == expected_status
            return response, "" if success else f"Expected {expected_status}, got {response.status_code}"
        except Exception as e:
            return None, f"Request failed: {str(e)}"

    def test_auth_register(self):
        """Test user registration"""
        test_email = f"testuser_{int(time.time())}@impulseai.com"
        data = {
            "email": test_email,
            "password": "test1234",
            "name": "Test User"
        }
        
        response, error = self.make_request('POST', 'auth/register', data, expected_status=200)
        if not response:
            return self.log_test("Auth Register", False, error)
        
        try:
            result = response.json()
            success = (
                result.get('email') == test_email and
                result.get('role') == 'free' and
                'id' in result
            )
            if success:
                self.test_user_cookies = response.cookies
            return self.log_test("Auth Register", success, 
                               "Invalid response format" if not success else "")
        except:
            return self.log_test("Auth Register", False, "Invalid JSON response")

    def test_auth_login_admin(self):
        """Test admin login"""
        data = {
            "email": "admin@impulseai.com",
            "password": "admin123"
        }
        
        response, error = self.make_request('POST', 'auth/login', data, expected_status=200)
        if not response:
            return self.log_test("Auth Login (Admin)", False, error)
        
        try:
            result = response.json()
            success = (
                result.get('email') == 'admin@impulseai.com' and
                result.get('role') == 'free' and
                'id' in result
            )
            if success:
                self.admin_cookies = response.cookies
            return self.log_test("Auth Login (Admin)", success,
                               "Invalid response format" if not success else "")
        except:
            return self.log_test("Auth Login (Admin)", False, "Invalid JSON response")

    def test_auth_me(self):
        """Test get current user"""
        if not self.admin_cookies:
            return self.log_test("Auth Me", False, "No admin cookies available")
        
        response, error = self.make_request('GET', 'auth/me', cookies=self.admin_cookies)
        if not response:
            return self.log_test("Auth Me", False, error)
        
        try:
            result = response.json()
            success = (
                result.get('email') == 'admin@impulseai.com' and
                'id' in result and
                'role' in result
            )
            return self.log_test("Auth Me", success,
                               "Invalid response format" if not success else "")
        except:
            return self.log_test("Auth Me", False, "Invalid JSON response")

    def test_auth_logout(self):
        """Test logout"""
        if not self.admin_cookies:
            return self.log_test("Auth Logout", False, "No admin cookies available")
        
        response, error = self.make_request('POST', 'auth/logout', cookies=self.admin_cookies)
        if not response:
            return self.log_test("Auth Logout", False, error)
        
        try:
            result = response.json()
            success = result.get('message') == 'Logged out'
            return self.log_test("Auth Logout", success,
                               "Invalid response message" if not success else "")
        except:
            return self.log_test("Auth Logout", False, "Invalid JSON response")

    def test_brute_force_protection(self):
        """Test brute force protection (5 failed attempts)"""
        test_email = f"bruteforce_{int(time.time())}@test.com"
        
        # Make 5 failed login attempts
        for i in range(5):
            data = {"email": test_email, "password": "wrongpassword"}
            response, _ = self.make_request('POST', 'auth/login', data, expected_status=401)
        
        # 6th attempt should be blocked
        data = {"email": test_email, "password": "wrongpassword"}
        response, error = self.make_request('POST', 'auth/login', data, expected_status=429)
        
        if not response:
            return self.log_test("Brute Force Protection", False, error)
        
        try:
            result = response.json()
            success = "Too many failed attempts" in result.get('detail', '')
            return self.log_test("Brute Force Protection", success,
                               "Lockout not triggered" if not success else "")
        except:
            return self.log_test("Brute Force Protection", False, "Invalid JSON response")

    def test_chat_send_message(self):
        """Test sending a chat message"""
        if not self.admin_cookies:
            return self.log_test("Chat Send Message", False, "No admin cookies available")
        
        data = {
            "content": "Hello, this is a test message for Impulse AI!"
        }
        
        response, error = self.make_request('POST', 'chat/send', data, cookies=self.admin_cookies)
        if not response:
            return self.log_test("Chat Send Message", False, error)
        
        try:
            result = response.json()
            success = (
                'chat_id' in result and
                'user_message' in result and
                'ai_message' in result and
                result['user_message']['content'] == data['content'] and
                result['ai_message']['role'] == 'assistant'
            )
            if success:
                self.test_chat_id = result['chat_id']
                self.test_message_id = result['ai_message']['id']
            return self.log_test("Chat Send Message", success,
                               "Invalid response format" if not success else "")
        except:
            return self.log_test("Chat Send Message", False, "Invalid JSON response")

    def test_chat_list(self):
        """Test listing chats"""
        if not self.admin_cookies:
            return self.log_test("Chat List", False, "No admin cookies available")
        
        response, error = self.make_request('GET', 'chat/list', cookies=self.admin_cookies)
        if not response:
            return self.log_test("Chat List", False, error)
        
        try:
            result = response.json()
            success = isinstance(result, list)
            if success and len(result) > 0:
                # Check if our test chat is in the list
                chat_found = any(chat.get('id') == self.test_chat_id for chat in result)
                success = chat_found
            return self.log_test("Chat List", success,
                               "Test chat not found in list" if not success else "")
        except:
            return self.log_test("Chat List", False, "Invalid JSON response")

    def test_chat_get_messages(self):
        """Test getting chat messages"""
        if not self.admin_cookies or not self.test_chat_id:
            return self.log_test("Chat Get Messages", False, "No admin cookies or chat ID available")
        
        response, error = self.make_request('GET', f'chat/{self.test_chat_id}/messages', cookies=self.admin_cookies)
        if not response:
            return self.log_test("Chat Get Messages", False, error)
        
        try:
            result = response.json()
            success = (
                isinstance(result, list) and
                len(result) >= 2  # Should have user message + AI response
            )
            return self.log_test("Chat Get Messages", success,
                               "Invalid messages format" if not success else "")
        except:
            return self.log_test("Chat Get Messages", False, "Invalid JSON response")

    def test_feedback_submission(self):
        """Test submitting feedback"""
        if not self.admin_cookies or not self.test_message_id:
            return self.log_test("Feedback Submission", False, "No admin cookies or message ID available")
        
        data = {
            "message_id": self.test_message_id,
            "rating": "up"
        }
        
        response, error = self.make_request('POST', 'feedback', data, cookies=self.admin_cookies)
        if not response:
            return self.log_test("Feedback Submission", False, error)
        
        try:
            result = response.json()
            success = (
                result.get('message') == 'Feedback recorded' and
                result.get('rating') == 'up'
            )
            return self.log_test("Feedback Submission", success,
                               "Invalid feedback response" if not success else "")
        except:
            return self.log_test("Feedback Submission", False, "Invalid JSON response")

    def test_user_usage(self):
        """Test getting user usage"""
        if not self.admin_cookies:
            return self.log_test("User Usage", False, "No admin cookies available")
        
        response, error = self.make_request('GET', 'user/usage', cookies=self.admin_cookies)
        if not response:
            return self.log_test("User Usage", False, error)
        
        try:
            result = response.json()
            success = (
                'role' in result and
                'daily_message_count' in result and
                'daily_limit' in result
            )
            return self.log_test("User Usage", success,
                               "Invalid usage response" if not success else "")
        except:
            return self.log_test("User Usage", False, "Invalid JSON response")

    def test_stripe_checkout_create(self):
        """Test creating Stripe checkout session"""
        if not self.admin_cookies:
            return self.log_test("Stripe Checkout Create", False, "No admin cookies available")
        
        data = {
            "plan": "pro_reasoning",
            "origin_url": "https://ai-chat-builder-55.preview.emergentagent.com"
        }
        
        response, error = self.make_request('POST', 'checkout/create', data, cookies=self.admin_cookies)
        if not response:
            return self.log_test("Stripe Checkout Create", False, error)
        
        try:
            result = response.json()
            success = (
                'url' in result and
                'session_id' in result and
                result['url'].startswith('https://checkout.stripe.com')
            )
            return self.log_test("Stripe Checkout Create", success,
                               "Invalid checkout response" if not success else "")
        except:
            return self.log_test("Stripe Checkout Create", False, "Invalid JSON response")

    def test_daily_limit_enforcement(self):
        """Test daily message limit for free users"""
        if not self.test_user_cookies:
            return self.log_test("Daily Limit Enforcement", False, "No test user cookies available")
        
        # Send 10 messages (the daily limit)
        for i in range(10):
            data = {"content": f"Test message {i+1}"}
            response, _ = self.make_request('POST', 'chat/send', data, cookies=self.test_user_cookies)
            if not response or response.status_code != 200:
                return self.log_test("Daily Limit Enforcement", False, f"Failed to send message {i+1}")
        
        # 11th message should be blocked
        data = {"content": "This should be blocked"}
        response, error = self.make_request('POST', 'chat/send', data, cookies=self.test_user_cookies, expected_status=429)
        
        if not response:
            return self.log_test("Daily Limit Enforcement", False, error)
        
        try:
            result = response.json()
            success = "Daily message limit reached" in result.get('detail', '')
            return self.log_test("Daily Limit Enforcement", success,
                               "Limit not enforced" if not success else "")
        except:
            return self.log_test("Daily Limit Enforcement", False, "Invalid JSON response")

    def test_chat_delete(self):
        """Test deleting a chat"""
        if not self.admin_cookies or not self.test_chat_id:
            return self.log_test("Chat Delete", False, "No admin cookies or chat ID available")
        
        response, error = self.make_request('DELETE', f'chat/{self.test_chat_id}', cookies=self.admin_cookies)
        if not response:
            return self.log_test("Chat Delete", False, error)
        
        try:
            result = response.json()
            success = result.get('message') == 'Chat deleted'
            return self.log_test("Chat Delete", success,
                               "Invalid delete response" if not success else "")
        except:
            return self.log_test("Chat Delete", False, "Invalid JSON response")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Impulse AI Backend API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Auth tests
        print("\n🔐 Authentication Tests")
        self.test_auth_register()
        self.test_auth_login_admin()
        self.test_auth_me()
        self.test_brute_force_protection()
        self.test_auth_logout()
        
        # Re-login for subsequent tests
        self.test_auth_login_admin()
        
        # Chat tests
        print("\n💬 Chat Tests")
        self.test_chat_send_message()
        self.test_chat_list()
        self.test_chat_get_messages()
        self.test_chat_delete()
        
        # Feedback tests
        print("\n👍 Feedback Tests")
        # Send another message for feedback testing
        data = {"content": "Test message for feedback"}
        response, _ = self.make_request('POST', 'chat/send', data, cookies=self.admin_cookies)
        if response:
            result = response.json()
            self.test_message_id = result.get('ai_message', {}).get('id')
        self.test_feedback_submission()
        
        # Usage tests
        print("\n📊 Usage Tests")
        self.test_user_usage()
        
        # Phase 1 specific tests
        print("\n🚀 Phase 1 Tests")
        self.test_phase1_user_registration()
        self.test_phase1_admin_role()
        self.test_phase1_usage_endpoint()
        self.test_phase1_admin_dashboard()
        self.test_phase1_credit_packs()
        self.test_phase1_credit_purchase_restrictions()
        self.test_phase1_free_user_limits()
        self.test_phase1_admin_unlimited_messages()
        
        # Results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

    def test_phase1_user_registration(self):
        """Test POST /api/auth/register - new user gets all new fields"""
        test_email = f"phase1_user_{int(time.time())}@impulseai.com"
        response, error = self.make_request('POST', 'auth/register', {
            'email': test_email,
            'password': 'test1234',
            'name': 'Phase1 User'
        })
        
        if not self.log_test("User registration", response and response.status_code == 200, error):
            return False
        
        # Check if user gets free role
        data = response.json()
        if not self.log_test("New user gets free role", data.get('role') == 'free', f"Got role: {data.get('role')}"):
            return False
        
        # Test /api/auth/me to check new fields
        me_response, me_error = self.make_request('GET', 'auth/me')
        if not self.log_test("GET /api/auth/me after registration", me_response and me_response.status_code == 200, me_error):
            return False
        
        me_data = me_response.json()
        required_fields = ["daily_message_count", "daily_image_count", "daily_video_count", "video_credits", "limits"]
        missing_fields = [field for field in required_fields if field not in me_data]
        
        return self.log_test("New user has all required fields", len(missing_fields) == 0, f"Missing: {missing_fields}")

    def test_phase1_admin_role(self):
        """Test admin user has role 'admin' not 'free'"""
        response, error = self.make_request('POST', 'auth/login', {
            'email': 'admin@impulseai.com',
            'password': 'admin123'
        })
        
        if not self.log_test("Admin login", response and response.status_code == 200, error):
            return False
        
        data = response.json()
        return self.log_test("Admin has role 'admin'", data.get('role') == 'admin', f"Got role: {data.get('role')}")

    def test_phase1_usage_endpoint(self):
        """Test GET /api/user/usage returns all daily limits, video credits, watermark flag"""
        response, error = self.make_request('GET', 'user/usage')
        
        if not self.log_test("GET /api/user/usage", response and response.status_code == 200, error):
            return False
        
        data = response.json()
        required_fields = [
            "role", "daily_message_count", "daily_message_limit",
            "daily_image_count", "daily_image_limit", 
            "daily_video_count", "daily_video_limit",
            "video_credits", "max_video_duration", "video_quality", "watermark", "uses_credits"
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        return self.log_test("Usage endpoint returns all required fields", len(missing_fields) == 0, f"Missing: {missing_fields}")

    def test_phase1_admin_dashboard(self):
        """Test GET /api/admin/dashboard returns user counts, feedback stats, revenue (admin only)"""
        # Test admin access
        admin_response, admin_error = self.make_request('POST', 'auth/login', {
            'email': 'admin@impulseai.com',
            'password': 'admin123'
        })
        
        if not self.log_test("Admin login for dashboard test", admin_response and admin_response.status_code == 200, admin_error):
            return False
        
        dashboard_response, dashboard_error = self.make_request('GET', 'admin/dashboard')
        
        if not self.log_test("GET /api/admin/dashboard (admin access)", dashboard_response and dashboard_response.status_code == 200, dashboard_error):
            return False
        
        data = dashboard_response.json()
        required_sections = ["users", "feedback", "revenue"]
        missing_sections = [section for section in required_sections if section not in data]
        
        if not self.log_test("Admin dashboard has required sections", len(missing_sections) == 0, f"Missing: {missing_sections}"):
            return False
        
        # Test non-admin access (403)
        user_response, user_error = self.make_request('POST', 'auth/register', {
            'email': f'regular_{int(time.time())}@impulseai.com',
            'password': 'test1234'
        })
        
        if user_response and user_response.status_code == 200:
            forbidden_response, forbidden_error = self.make_request('GET', 'admin/dashboard', expected_status=403)
            return self.log_test("GET /api/admin/dashboard returns 403 for non-admin", forbidden_response is not None and forbidden_error == "", f"Error: {forbidden_error}")
        else:
            return self.log_test("GET /api/admin/dashboard returns 403 for non-admin", False, "Could not register test user")
        
        return True

    def test_phase1_credit_packs(self):
        """Test GET /api/credits/packs returns 3 credit packs with correct pricing"""
        response, error = self.make_request('GET', 'credits/packs')
        
        if not self.log_test("GET /api/credits/packs", response and response.status_code == 200, error):
            return False
        
        data = response.json()
        packs = data.get("packs", [])
        
        if not self.log_test("Credit packs returns 3 packs", len(packs) == 3, f"Got {len(packs)} packs"):
            return False
        
        # Check specific pricing
        pack_dict = {pack["id"]: pack for pack in packs}
        expected_packs = {
            "starter": {"credits": 50, "amount": 5.0},
            "standard": {"credits": 120, "amount": 10.0},
            "power": {"credits": 300, "amount": 20.0}
        }
        
        pricing_correct = True
        for pack_id, expected in expected_packs.items():
            if pack_id not in pack_dict:
                pricing_correct = False
                break
            pack = pack_dict[pack_id]
            if pack.get("credits") != expected["credits"] or pack.get("amount") != expected["amount"]:
                pricing_correct = False
                break
        
        return self.log_test("Credit packs have correct pricing", pricing_correct, f"Expected: {expected_packs}, Got: {pack_dict}")

    def test_phase1_credit_purchase_restrictions(self):
        """Test POST /api/credits/purchase returns 403 for non-Creative Pro users"""
        # Register as free user
        test_email = f"free_user_{int(time.time())}@impulseai.com"
        reg_response, reg_error = self.make_request('POST', 'auth/register', {
            'email': test_email,
            'password': 'test1234'
        })
        
        if not self.log_test("Register free user for credit test", reg_response and reg_response.status_code == 200, reg_error):
            return False
        
        # Try to purchase credits
        purchase_response, purchase_error = self.make_request('POST', 'credits/purchase', {
            'pack_id': 'starter',
            'origin_url': 'https://example.com'
        }, expected_status=403)
        
        return self.log_test("Credit purchase returns 403 for non-Creative Pro", purchase_response is not None and purchase_error == "", f"Error: {purchase_error}")

    def test_phase1_free_user_limits(self):
        """Test free user daily message limit is now 20 (not 10)"""
        # Register new free user
        test_email = f"limit_test_{int(time.time())}@impulseai.com"
        reg_response, reg_error = self.make_request('POST', 'auth/register', {
            'email': test_email,
            'password': 'test1234'
        })
        
        if not self.log_test("Register user for limit test", reg_response and reg_response.status_code == 200, reg_error):
            return False
        
        # Check usage endpoint
        usage_response, usage_error = self.make_request('GET', 'user/usage')
        
        if not self.log_test("Get usage for limit test", usage_response and usage_response.status_code == 200, usage_error):
            return False
        
        data = usage_response.json()
        message_limit = data.get("daily_message_limit")
        image_limit = data.get("daily_image_limit")
        video_limit = data.get("daily_video_limit")
        
        success = True
        details = []
        
        if message_limit != 20:
            success = False
            details.append(f"Message limit: expected 20, got {message_limit}")
        
        if image_limit != 2:
            success = False
            details.append(f"Image limit: expected 2, got {image_limit}")
        
        if video_limit != 1:
            success = False
            details.append(f"Video limit: expected 1, got {video_limit}")
        
        return self.log_test("Free user has correct limits (20/2/1)", success, "; ".join(details))

    def test_phase1_admin_unlimited_messages(self):
        """Test POST /api/chat/send - admin user can send unlimited messages (no limit)"""
        # Login as admin
        admin_response, admin_error = self.make_request('POST', 'auth/login', {
            'email': 'admin@impulseai.com',
            'password': 'admin123'
        })
        
        if not self.log_test("Admin login for message test", admin_response and admin_response.status_code == 200, admin_error):
            return False
        
        # Send a message
        message_response, message_error = self.make_request('POST', 'chat/send', {
            'content': 'Test admin unlimited messages'
        })
        
        if not self.log_test("Admin can send messages", message_response and message_response.status_code == 200, message_error):
            return False
        
        data = message_response.json()
        daily_limit = data.get("daily_limit")
        
        return self.log_test("Admin has unlimited messages (daily_limit=None)", daily_limit is None, f"Got daily_limit: {daily_limit}")

def main():
    tester = ImpulseAITester()
    success = tester.run_all_tests()
    
    # Save detailed results for Phase 1
    with open("/app/phase1_backend_results.json", "w") as f:
        json.dump({
            "summary": {
                "total_tests": tester.tests_run,
                "passed_tests": tester.tests_passed,
                "success_rate": f"{(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "0%",
                "timestamp": datetime.now().isoformat()
            },
            "results": tester.results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())