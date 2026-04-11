#!/usr/bin/env python3
"""
Comprehensive backend API testing for Impulse AI SaaS app
Tests all auth, chat, feedback, usage, and Stripe endpoints
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

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
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
        
        # Stripe tests
        print("\n💳 Stripe Tests")
        self.test_stripe_checkout_create()
        
        # Daily limit tests
        print("\n⏰ Daily Limit Tests")
        self.test_daily_limit_enforcement()
        
        # Results
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"✨ Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = ImpulseAITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())