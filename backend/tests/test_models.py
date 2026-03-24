import os
import sys
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import directly without 'apps.' prefix since apps are in INSTALLED_APPS
from users.models import UserSkill, UserEducation, CareerGoal
from roadmap.models import Roadmap, RoadmapStep
from datetime import date, timedelta

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    """Test cases for User model"""
    
    def setup_method(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_user_creation(self):
        """Test user creation"""
        assert self.user.email == 'test@example.com'
        assert self.user.get_full_name() == 'Test User'
        assert self.user.check_password('testpass123') is True
    
    def test_user_skill_creation(self):
        """Test skill creation"""
        skill = UserSkill.objects.create(
            user=self.user,
            skill_name='Python',
            proficiency_level='advanced',
            years_experience=3
        )
        assert skill.skill_name == 'Python'
        assert str(skill) == f"{self.user.email} - Python (advanced)"


@pytest.mark.django_db
class TestRoadmapModel:
    """Test cases for Roadmap model"""
    
    def setup_method(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.roadmap = Roadmap.objects.create(
            user=self.user,
            title='Test Roadmap',
            target_role='Software Engineer',
            total_duration_months=12
        )
    
    def test_roadmap_creation(self):
        """Test roadmap creation"""
        assert self.roadmap.title == 'Test Roadmap'
        assert self.roadmap.target_role == 'Software Engineer'
        assert self.roadmap.is_completed is False
    
    def test_update_progress(self):
        """Test progress update"""
        # Create steps
        step1 = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            step_number=1,
            title='Step 1',
            description='Description',
            estimated_duration_hours=40
        )
        step2 = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            step_number=2,
            title='Step 2',
            description='Description',
            estimated_duration_hours=40
        )
        
        # Update progress
        self.roadmap.update_progress()
        assert self.roadmap.completion_percentage == 0.0
        
        # Complete one step
        step1.is_completed = True
        step1.save()
        self.roadmap.update_progress()
        assert self.roadmap.completion_percentage == 50.0