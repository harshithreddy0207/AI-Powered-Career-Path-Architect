"""
Unit tests for AI services
Tests: Gemini client, Prompt templates, AI analysis
"""

from django.test import TestCase
from django.conf import settings
from unittest.mock import patch, Mock
from ai_services.gemini_client import GeminiClient
from ai_services.prompt_templates import (
    get_skill_gap_text_prompt,
    get_resume_analysis_prompt,
    get_market_insights_text_prompt,
    get_roadmap_text_prompt
)
from ai_services.models import AIAnalysis, AIRecommendation
from users.models import User
import json
from django.utils import timezone


class PromptTemplateTests(TestCase):
    """Test cases for AI prompt templates"""
    
    def test_skill_gap_prompt_generation(self):
        """✅ Test: Skill gap prompt is generated correctly"""
        target_role = "Senior Developer"
        current_skills = ["Python", "Django", "JavaScript"]
        experience_level = "mid"
        
        prompt = get_skill_gap_text_prompt(target_role, current_skills, experience_level)
        
        self.assertIn(target_role, prompt)
        self.assertIn("Python", prompt)
        self.assertIn("Django", prompt)
        self.assertIn("JavaScript", prompt)
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 100)
        print("✅ PASS: Skill gap prompt generated correctly")
    
    def test_resume_analysis_prompt_generation(self):
        """✅ Test: Resume analysis prompt is generated correctly"""
        resume_text = "Experienced software developer with 5 years of Python experience"
        target_role = "Senior Engineer"
        
        prompt = get_resume_analysis_prompt(resume_text, target_role)
        
        self.assertIn(resume_text, prompt)
        self.assertIn(target_role, prompt)
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 100)
        print("✅ PASS: Resume analysis prompt generated correctly")
    
    def test_market_insights_prompt_generation(self):
        """✅ Test: Market insights prompt is generated correctly"""
        role = "Data Scientist"
        location = "United States"
        
        prompt = get_market_insights_text_prompt(role, location)
        
        self.assertIn(role, prompt)
        self.assertIn(location, prompt)
        self.assertIsInstance(prompt, str)
        self.assertGreater(len(prompt), 100)
        print("✅ PASS: Market insights prompt generated correctly")
    
    def test_roadmap_prompt_generation(self):
        """✅ Test: Roadmap prompt is generated correctly"""
        data = {
            'target_role': 'Full Stack Developer',
            'target_industry': 'Technology',
            'timeframe_months': 12,
            'current_skills': ['React', 'Python', 'Node.js'],
            'experience_level': 'intermediate'
        }
        
        prompt = get_roadmap_text_prompt(data)
        
        self.assertIn(data['target_role'], prompt)
        self.assertIn('React', prompt)
        self.assertIn('Python', prompt)
        self.assertIsInstance(prompt, str)
        print("✅ PASS: Roadmap prompt generated correctly")


class GeminiClientTests(TestCase):
    """Test cases for Gemini API client"""
    
    def setUp(self):
        self.client = GeminiClient()
    
    def test_client_initialization(self):
        """✅ Test: Gemini client initializes correctly"""
        self.assertIsNotNone(self.client)
        self.assertIsNotNone(self.client.api_key)
        self.assertIsNotNone(self.client.model)
        print("✅ PASS: Gemini client initialized")
    
    def test_api_key_configured(self):
        """✅ Test: API key is configured"""
        api_key = settings.GEMINI_API_KEY
        self.assertIsNotNone(api_key)
        self.assertNotEqual(api_key, "")
        print("✅ PASS: Gemini API key configured")
    
    @patch('google.generativeai.GenerativeModel.generate_content')
    def test_generate_content_called(self, mock_generate):
        """✅ Test: Generate content method is callable"""
        mock_response = Mock()
        mock_response.text = "Test AI response"
        mock_generate.return_value = mock_response
        
        result = self.client.generate_content("Test prompt")
        
        self.assertIsNotNone(result)
        mock_generate.assert_called()
        print("✅ PASS: Generate content method works")


class AIAnalysisModelTests(TestCase):
    """Test cases for AI Analysis model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='aianalysis@example.com',
            username='aianalysis',
            password='pass123'
        )
    
    def test_create_analysis_record(self):
        """✅ Test: AI analysis record can be created"""
        analysis = AIAnalysis.objects.create(
            user=self.user,
            analysis_type='skill_gap',
            input_data={'test': 'data'},
            output_data={'result': 'analysis'},
            status='completed'
        )
        self.assertEqual(analysis.user.email, 'aianalysis@example.com')
        self.assertEqual(analysis.analysis_type, 'skill_gap')
        self.assertEqual(analysis.status, 'completed')
        print("✅ PASS: AI analysis record created")
    
    def test_analysis_status_tracking(self):
        """✅ Test: Analysis status can be updated"""
        analysis = AIAnalysis.objects.create(
            user=self.user,
            analysis_type='resume',
            status='pending'
        )
        
        analysis.status = 'processing'
        analysis.save()
        self.assertEqual(analysis.status, 'processing')
        
        analysis.status = 'completed'
        analysis.completed_at = timezone.now()
        analysis.save()
        self.assertEqual(analysis.status, 'completed')
        print("✅ PASS: Analysis status tracking works")


class AIRecommendationModelTests(TestCase):
    """Test cases for AI Recommendation model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='airec@example.com',
            username='airec',
            password='pass123'
        )
    
    def test_create_recommendation(self):
        """✅ Test: AI recommendation can be created"""
        recommendation = AIRecommendation.objects.create(
            user=self.user,
            recommendation_type='skill',
            content={'title': 'Learn Python', 'priority': 5},
            priority=1,
            status='pending'
        )
        self.assertEqual(recommendation.user.email, 'airec@example.com')
        self.assertEqual(recommendation.recommendation_type, 'skill')
        self.assertEqual(recommendation.status, 'pending')
        print("✅ PASS: AI recommendation created")
    
    def test_accept_recommendation(self):
        """✅ Test: Recommendation can be accepted"""
        recommendation = AIRecommendation.objects.create(
            user=self.user,
            recommendation_type='course',
            content={'title': 'Django Course'},
            status='pending'
        )
        
        recommendation.status = 'accepted'
        recommendation.save()
        self.assertEqual(recommendation.status, 'accepted')
        print("✅ PASS: Recommendation acceptance works")
    
    def test_reject_recommendation(self):
        """✅ Test: Recommendation can be rejected with feedback"""
        recommendation = AIRecommendation.objects.create(
            user=self.user,
            recommendation_type='job',
            content={'title': 'Job Match'},
            status='pending'
        )
        
        recommendation.status = 'rejected'
        recommendation.feedback = 'Not interested in this role'
        recommendation.save()
        
        self.assertEqual(recommendation.status, 'rejected')
        self.assertIsNotNone(recommendation.feedback)
        print("✅ PASS: Recommendation rejection with feedback works")


# Run all tests
if __name__ == '__main__':
    import unittest
    import timezone
    unittest.main()