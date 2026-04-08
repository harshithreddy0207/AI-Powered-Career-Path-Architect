# This file makes the tests directory a Python package
# It also contains test configuration and helpers

import os
import sys
import django

# Set up Django environment for tests
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'career_architect.settings')
django.setup()

# Test configuration
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
TEST_APPS = ['users', 'roadmap', 'ai_services']

# Helper function to get test data path
def get_test_data_path(filename):
    """Get the full path to a test data file"""
    return os.path.join(os.path.dirname(__file__), 'test_data', filename)

print(f"✅ Test suite initialized for Career Path Architect")
print(f"📁 Test directory: {os.path.dirname(__file__)}")