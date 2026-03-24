# backend/career_architect/apps/users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import os

class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    current_position = models.CharField(max_length=100, blank=True, null=True)
    current_company = models.CharField(max_length=100, blank=True, null=True)
    years_experience = models.IntegerField(default=0)
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    portfolio_url = models.URLField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        return self.first_name or self.email.split('@')[0]

    @property
    def profile_completion(self):
        """Calculate profile completion percentage"""
        fields = [
            self.first_name, self.last_name, self.phone, self.location,
            self.bio, self.current_position, self.current_company,
            self.linkedin_url, self.github_url
        ]
        completed = sum(1 for f in fields if f)
        return int((completed / len(fields)) * 100)


class UserSkill(models.Model):
    """User skills with proficiency levels"""
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    proficiency_level = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='beginner')
    years_experience = models.FloatField(default=0)
    last_used = models.IntegerField(default=timezone.now().year)
    is_learning = models.BooleanField(default=False)  # ✅ ADD THIS FIELD
    notes = models.TextField(blank=True, null=True)   # ✅ ADD THIS FIELD (optional)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_skills'
        unique_together = ['user', 'skill_name']
        ordering = ['-proficiency_level', 'skill_name']
        indexes = [
            models.Index(fields=['user', 'skill_name']),
            models.Index(fields=['proficiency_level']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.skill_name} ({self.proficiency_level})"


class UserEducation(models.Model):
    """User education history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_education'
        ordering = ['-end_date', '-start_date']
        indexes = [
            models.Index(fields=['user', 'is_current']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.degree} at {self.institution}"


class UserExperience(models.Model):
    """User work experience"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField()
    achievements = models.JSONField(default=list)
    skills_used = models.ManyToManyField(UserSkill, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_experiences'
        ordering = ['-end_date', '-start_date']
        indexes = [
            models.Index(fields=['user', 'is_current']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title} at {self.company}"


def resume_upload_path(instance, filename):
    """Generate upload path for resumes"""
    # Get file extension
    ext = filename.split('.')[-1]
    # Create new filename with timestamp
    new_filename = f"resume_{instance.user.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return f'resumes/user_{instance.user.id}/{new_filename}'


class Resume(models.Model):
    """User uploaded resumes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to=resume_upload_path)
    file_type = models.CharField(max_length=100)
    file_size = models.IntegerField()
    parsed_content = models.JSONField(default=dict)
    is_primary = models.BooleanField(default=False)
    upload_date = models.DateTimeField(auto_now_add=True)
    last_analyzed = models.DateTimeField(null=True, blank=True)
    ats_score = models.IntegerField(null=True, blank=True)
    match_score = models.IntegerField(null=True, blank=True)
    analyzed = models.BooleanField(default=False)

    class Meta:
        db_table = 'resumes'
        ordering = ['-upload_date']
        indexes = [
            models.Index(fields=['user', 'is_primary']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.original_filename}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Set all other resumes of this user to not primary
            Resume.objects.filter(user=self.user, is_primary=True).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class CareerGoal(models.Model):
    """User career goals"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='career_goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    target_role = models.CharField(max_length=100)
    target_industry = models.CharField(max_length=100, blank=True, null=True)
    target_companies = models.JSONField(default=list)
    timeframe_months = models.IntegerField(default=24)
    priority_level = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    is_completed = models.BooleanField(default=False)
    completed_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'career_goals'
        ordering = ['-priority_level', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.target_role}"