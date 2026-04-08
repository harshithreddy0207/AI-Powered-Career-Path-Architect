"""
Unit tests for database models
Tests: User, UserSkill, Roadmap, RoadmapStep, CareerGoal models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone
from users.models import UserSkill, CareerGoal
from roadmap.models import Roadmap, RoadmapStep
from datetime import date, timedelta
import json

User = get_user_model()


class UserModelTests(TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        """Create test data before each test"""
        self.user_data = {
            'email': 'test@example.com',
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPass123!'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_create_user(self):
        """✅ Test: User can be created successfully"""
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.check_password('TestPass123!'))
        print("✅ PASS: User created successfully")
    
    def test_user_str_method(self):
        """✅ Test: User string representation returns email"""
        self.assertEqual(str(self.user), 'test@example.com (Test User)')
        print("✅ PASS: User string method works")
    
    def test_get_full_name(self):
        """✅ Test: User full name is formatted correctly"""
        full_name = self.user.get_full_name()
        self.assertEqual(full_name, 'Test User')
        print("✅ PASS: Full name returned correctly")
    
    def test_duplicate_email_not_allowed(self):
        """✅ Test: Duplicate email raises error"""
        with self.assertRaises(Exception):
            User.objects.create_user(
                email='test@example.com',
                username='testuser2',
                password='pass123'
            )
        print("✅ PASS: Duplicate email prevented")
    
    def test_profile_completion_calculation(self):
        """✅ Test: Profile completion percentage is calculated"""
        completion = self.user.profile_completion
        self.assertIsInstance(completion, int)
        self.assertGreaterEqual(completion, 0)
        self.assertLessEqual(completion, 100)
        print(f"✅ PASS: Profile completion calculated: {completion}%")


class UserSkillModelTests(TestCase):
    """Test cases for UserSkill model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='skilluser@example.com',
            username='skilluser',
            password='pass123'
        )
    
    def test_create_skill(self):
        """✅ Test: Skill can be added to user"""
        skill = UserSkill.objects.create(
            user=self.user,
            skill_name='Python',
            proficiency_level='advanced',
            years_experience=3,
            last_used=2025
        )
        self.assertEqual(skill.skill_name, 'Python')
        self.assertEqual(skill.proficiency_level, 'advanced')
        self.assertEqual(skill.user.email, 'skilluser@example.com')
        print("✅ PASS: Skill added successfully")
    
    def test_skill_str_method(self):
        """✅ Test: Skill string representation"""
        skill = UserSkill.objects.create(
            user=self.user,
            skill_name='Django',
            proficiency_level='intermediate'
        )
        self.assertIn('Django', str(skill))
        print("✅ PASS: Skill string method works")
    
    def test_user_can_have_multiple_skills(self):
        """✅ Test: User can have multiple skills"""
        skills = ['Python', 'JavaScript', 'React']
        for skill_name in skills:
            UserSkill.objects.create(
                user=self.user,
                skill_name=skill_name,
                proficiency_level='intermediate'
            )
        self.assertEqual(self.user.skills.count(), 3)
        print("✅ PASS: Multiple skills added to user")


class RoadmapModelTests(TestCase):
    """Test cases for Roadmap model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='roadmapuser@example.com',
            username='roadmapuser',
            password='pass123'
        )
        self.roadmap = Roadmap.objects.create(
            user=self.user,
            title='Full Stack Developer Roadmap',
            target_role='Full Stack Developer',
            total_duration_months=12,
            difficulty_level='intermediate',
            generated_by_ai=True
        )
    
    def test_create_roadmap(self):
        """✅ Test: Roadmap can be created"""
        self.assertEqual(self.roadmap.title, 'Full Stack Developer Roadmap')
        self.assertEqual(self.roadmap.user.email, 'roadmapuser@example.com')
        self.assertEqual(self.roadmap.completion_percentage, 0.0)
        self.assertFalse(self.roadmap.is_completed)
        print("✅ PASS: Roadmap created successfully")
    
    def test_roadmap_str_method(self):
        """✅ Test: Roadmap string representation"""
        self.assertIn('Full Stack Developer Roadmap', str(self.roadmap))
        print("✅ PASS: Roadmap string method works")
    
    def test_roadmap_progress_update(self):
        """✅ Test: Roadmap progress updates correctly"""
        # Add steps to roadmap
        step1 = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            step_number=1,
            title='Learn Python',
            description='Master Python basics',
            step_type='learning',
            estimated_duration_hours=40,
            is_completed=True
        )
        step2 = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            step_number=2,
            title='Learn Django',
            description='Master Django framework',
            step_type='learning',
            estimated_duration_hours=60,
            is_completed=False
        )
        
        # Update progress
        self.roadmap.update_progress()
        
        # Should be 50% (1 of 2 steps completed)
        self.assertEqual(self.roadmap.completion_percentage, 50.0)
        print("✅ PASS: Roadmap progress updates correctly")
    
    def test_roadmap_analytics(self):
        """✅ Test: Roadmap analytics data"""
        # Create steps
        for i in range(1, 5):
            RoadmapStep.objects.create(
                roadmap=self.roadmap,
                step_number=i,
                title=f'Step {i}',
                description=f'Description for step {i}',
                step_type='learning',
                estimated_duration_hours=40
            )
        
        total_steps = self.roadmap.steps.count()
        total_hours = sum(s.estimated_duration_hours for s in self.roadmap.steps.all())
        
        self.assertEqual(total_steps, 4)
        self.assertEqual(total_hours, 160)
        print(f"✅ PASS: Roadmap analytics - Steps: {total_steps}, Hours: {total_hours}")


class RoadmapStepModelTests(TestCase):
    """Test cases for RoadmapStep model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='stepuser@example.com',
            username='stepuser',
            password='pass123'
        )
        self.roadmap = Roadmap.objects.create(
            user=self.user,
            title='Test Roadmap',
            target_role='Test Role'
        )
    
    def test_create_step(self):
        """✅ Test: Step can be added to roadmap"""
        step = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            step_number=1,
            title='Learn Testing',
            description='Learn unit testing',
            step_type='learning',
            estimated_duration_hours=20
        )
        self.assertEqual(step.step_number, 1)
        self.assertEqual(step.title, 'Learn Testing')
        self.assertFalse(step.is_completed)
        print("✅ PASS: Step created successfully")
    
    def test_step_completion_tracking(self):
        """✅ Test: Step completion status can be toggled"""
        step = RoadmapStep.objects.create(
            roadmap=self.roadmap,
            step_number=1,
            title='Complete Task',
            description='Complete the task',
            step_type='learning',
            estimated_duration_hours=10
        )
        
        step.is_completed = True
        step.completion_date = timezone.now()
        step.save()
        
        self.assertTrue(step.is_completed)
        self.assertIsNotNone(step.completion_date)
        print("✅ PASS: Step completion tracked correctly")


class CareerGoalModelTests(TestCase):
    """Test cases for CareerGoal model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='goaluser@example.com',
            username='goaluser',
            password='pass123'
        )
    
    def test_create_career_goal(self):
        """✅ Test: Career goal can be created"""
        goal = CareerGoal.objects.create(
            user=self.user,
            title='Become Senior Developer',
            target_role='Senior Software Engineer',
            target_industry='Technology',
            timeframe_months=24,
            priority_level='high'
        )
        self.assertEqual(goal.target_role, 'Senior Software Engineer')
        self.assertTrue(goal.is_active)
        print("✅ PASS: Career goal created successfully")
    
    def test_archive_goal(self):
        """✅ Test: Career goal can be archived"""
        goal = CareerGoal.objects.create(
            user=self.user,
            title='Learn AI',
            target_role='AI Engineer',
            target_industry='AI/ML',
            timeframe_months=12
        )
        
        goal.is_active = False
        goal.save()
        
        self.assertFalse(goal.is_active)
        print("✅ PASS: Career goal archived successfully")
    
    def test_complete_goal(self):
        """✅ Test: Career goal can be marked complete"""
        goal = CareerGoal.objects.create(
            user=self.user,
            title='Complete Project',
            target_role='Project Manager',
            target_industry='Technology',
            timeframe_months=6
        )
        
        goal.is_completed = True
        goal.completed_date = timezone.now()
        goal.save()
        
        self.assertTrue(goal.is_completed)
        self.assertIsNotNone(goal.completed_date)
        print("✅ PASS: Career goal marked complete")


# Run all tests
if __name__ == '__main__':
    import unittest
    unittest.main()