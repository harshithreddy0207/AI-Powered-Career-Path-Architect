from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, AuthViewSet, UserSkillViewSet,
    UserEducationViewSet, UserExperienceViewSet,
    ResumeViewSet, CareerGoalViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'skills', UserSkillViewSet, basename='skill')
router.register(r'education', UserEducationViewSet, basename='education')
router.register(r'experiences', UserExperienceViewSet, basename='experience')
router.register(r'resumes', ResumeViewSet, basename='resume')
router.register(r'career-goals', CareerGoalViewSet, basename='career-goal')

urlpatterns = [
    path('', include(router.urls)),
]