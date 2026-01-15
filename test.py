import unittest
from app import app
from pymongo import MongoClient
import json

class SmartPantryTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and test database"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Use test database
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client.smart_pantry_test
        
    def tearDown(self):
        """Clean up after tests"""
        # Drop test database
        self.client.drop_database('smart_pantry_test')
        
    def test_welcome_page(self):
        """Test welcome page loads correctly"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Smart Pantry', response.data)
        
    def test_signup_page(self):
        """Test signup page loads correctly"""
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Join Smart Pantry', response.data)
        
    def test_login_page(self):
        """Test login page loads correctly"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome Back', response.data)
        
    def test_signup_process(self):
        """Test user signup process"""
        response = self.app.post('/signup', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        # Should redirect to login after successful signup
        self.assertEqual(response.status_code, 302)
        
    def test_login_process(self):
        """Test user login process"""
        # First create a user
        self.app.post('/signup', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        # Then try to login
        response = self.app.post('/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Should redirect to pantry after successful login
        self.assertEqual(response.status_code, 302)
        
    def test_pantry_requires_login(self):
        """Test that pantry page requires authentication"""
        response = self.app.get('/pantry')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        
    def test_recipes_page(self):
        """Test recipes page loads correctly"""
        response = self.app.get('/recipes')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Recipes', response.data)
        
    def test_recipes_with_item(self):
        """Test recipes page with specific item"""
        response = self.app.get('/recipes?item=tomato')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'tomato', response.data)
        
    def test_planner_requires_login(self):
        """Test that planner page requires authentication"""
        response = self.app.get('/planner')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

if __name__ == '__main__':
    unittest.main()