"""
Sample Test File for Online Exam Application
Created to test Git repository connection
"""

import unittest
from datetime import datetime


class SampleTest(unittest.TestCase):
    """Sample test class for demonstration purposes"""
    
    def test_addition(self):
        """Test basic addition operation"""
        result = 2 + 2
        self.assertEqual(result, 4)
    
    def test_string_concatenation(self):
        """Test string concatenation"""
        greeting = "Hello" + " " + "World"
        self.assertEqual(greeting, "Hello World")
    
    def test_list_operations(self):
        """Test list operations"""
        test_list = [1, 2, 3]
        test_list.append(4)
        self.assertEqual(len(test_list), 4)
        self.assertIn(4, test_list)
    
    def test_dictionary_operations(self):
        """Test dictionary operations"""
        test_dict = {"name": "Online Exam", "version": "1.0"}
        test_dict["status"] = "active"
        self.assertEqual(test_dict["status"], "active")
        self.assertIn("name", test_dict)
    
    def test_datetime(self):
        """Test datetime functionality"""
        now = datetime.now()
        self.assertIsNotNone(now)
        self.assertIsInstance(now, datetime)


if __name__ == "__main__":
    unittest.main()