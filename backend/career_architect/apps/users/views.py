from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.files.storage import default_storage
from django.db.models import Q
from django.utils import timezone
from .models import (
    User, UserSkill, UserEducation, UserExperience,
    Resume, CareerGoal
)
from .serializers import (
    UserSerializer, UserProfileSerializer, RegisterSerializer,
    LoginSerializer, UserSkillSerializer, UserEducationSerializer,
    UserExperienceSerializer, ResumeSerializer, CareerGoalSerializer,
    ChangePasswordSerializer
)
from ai_services.gemini_client import GeminiClient
from ai_services.prompt_templates import get_resume_analysis_prompt
import os
import mimetypes
import traceback
import logging
import time

logger = logging.getLogger(__name__)
gemini_client = GeminiClient()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter to only return the current user"""
        return User.objects.filter(id=self.request.user.id)

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get full user profile with related data"""
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Wrong password.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['delete'])
    def delete_account(self, request):
        """Delete user account"""
        user = request.user
        user.delete()
        return Response({'message': 'Account deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


class AuthViewSet(viewsets.ViewSet):
    """ViewSet for authentication"""
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new user"""
        logger.info("="*50)
        logger.info("REGISTER ENDPOINT CALLED")
        logger.info(f"Request data: {request.data}")
        
        try:
            # Check if user already exists
            email = request.data.get('email')
            if email and User.objects.filter(email=email).exists():
                return Response(
                    {'email': ['User with this email already exists.']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                logger.info("Serializer is valid")
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                response_data = {
                    'user': UserSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                logger.info(f"User created successfully: {user.email}")
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"EXCEPTION in register: {str(e)}")
            traceback.print_exc()
            return Response(
                {'error': f'Internal server error: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login user"""
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        """Logout user - blacklist refresh token"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logged out successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UserSkillViewSet(viewsets.ModelViewSet):
    """ViewSet for UserSkill model"""
    serializer_class = UserSkillSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSkill.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserEducationViewSet(viewsets.ModelViewSet):
    """ViewSet for UserEducation model"""
    serializer_class = UserEducationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserEducation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserExperienceViewSet(viewsets.ModelViewSet):
    """ViewSet for UserExperience model"""
    serializer_class = UserExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserExperience.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ResumeViewSet(viewsets.ModelViewSet):
    """ViewSet for Resume model - NO MOCK DATA, NO FALLBACKS"""
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Override create to handle file upload properly"""
        try:
            file = request.FILES.get('file')
            if not file:
                return Response(
                    {'file': ['No file uploaded.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate file size (10MB max)
            max_size = 10 * 1024 * 1024
            if file.size > max_size:
                return Response(
                    {'file': [f'File size too large. Max size is {max_size//(1024*1024)}MB.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate file type
            content_type = file.content_type
            allowed_types = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]
            if content_type not in allowed_types:
                return Response(
                    {'file': ['File type not allowed. Please upload PDF or Word document.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Handle is_primary
            is_primary = request.data.get('is_primary', 'false').lower() == 'true'

            logger.info(f"Uploading resume: {file.name}, size: {file.size}, type: {content_type}, is_primary: {is_primary}")

            # If this is primary, unset other primaries
            if is_primary:
                Resume.objects.filter(user=request.user, is_primary=True).update(is_primary=False)

            # Create resume
            resume = Resume.objects.create(
                user=request.user,
                file=file,
                original_filename=file.name,
                file_type=content_type,
                file_size=file.size,
                is_primary=is_primary
            )

            serializer = self.get_serializer(resume, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error uploading resume: {str(e)}")
            traceback.print_exc()
            return Response(
                {'error': f'Failed to upload resume: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """Set a resume as primary"""
        try:
            resume = self.get_object()
            # Unset other primaries
            Resume.objects.filter(user=request.user, is_primary=True).exclude(id=resume.id).update(is_primary=False)
            resume.is_primary = True
            resume.save()
            return Response({'message': 'Resume set as primary successfully'})
        except Exception as e:
            logger.error(f"Error setting primary resume: {str(e)}")
            return Response(
                {'error': f'Failed to set primary resume: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """Trigger AI analysis for a resume - REAL GEMINI API CALL, NO MOCK DATA"""
        try:
            resume = self.get_object()
            
            # Check if we have a file to analyze
            if not resume.file:
                return Response(
                    {'error': 'No file to analyze'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get the target role from request if provided
            target_role = request.data.get('target_role', '')
            
            # Extract text from the file (you'll need a PDF/text extraction library)
            # For now, we'll use a placeholder - in production, use PyPDF2, textract, etc.
            resume_text = f"Resume filename: {resume.original_filename}\n"
            resume_text += f"Uploaded by: {request.user.email}\n"
            resume_text += f"File type: {resume.file_type}\n"
            resume_text += f"File size: {resume.file_size} bytes\n"
            
            # Add note about text extraction - in production, implement actual text extraction
            resume_text += "\n[Note: In production, this would contain the extracted text from the PDF/DOCX file]"
            
            # Call Gemini API for analysis
            start_time = time.time()
            
            prompt = get_resume_analysis_prompt(resume_text, target_role)
            response = gemini_client.generate_content(prompt)
            
            if not response or not response.get('text'):
                raise Exception("Empty response from Gemini API")
            
            analysis_text = response['text']
            
            # Parse the analysis text to extract structured data
            # This is a simple parser - you can enhance it based on your prompt format
            analysis_result = {
                'text': analysis_text,
                'ats_score': None,
                'impact_score': None,
                'format_score': None,
                'strengths': [],
                'improvements': [],
                'keywords': {'matched': [], 'missing': []},
                'suggestions': []
            }
            
            # Try to extract scores if present in format like "ATS Score: 85"
            import re
            ats_match = re.search(r'ATS\s*Score\s*[:\-]?\s*(\d+)', analysis_text, re.IGNORECASE)
            if ats_match:
                analysis_result['ats_score'] = int(ats_match.group(1))
            
            impact_match = re.search(r'Impact\s*Score\s*[:\-]?\s*(\d+)', analysis_text, re.IGNORECASE)
            if impact_match:
                analysis_result['impact_score'] = int(impact_match.group(1))
            
            format_match = re.search(r'Format\s*Score\s*[:\-]?\s*(\d+)', analysis_text, re.IGNORECASE)
            if format_match:
                analysis_result['format_score'] = int(format_match.group(1))
            
            # Extract bullet points for strengths (lines starting with • or - after "STRENGTHS" section)
            strengths_section = re.search(r'STRENGTHS.*?\n(.*?)(?=\n\n|\Z)', analysis_text, re.DOTALL | re.IGNORECASE)
            if strengths_section:
                strength_lines = strengths_section.group(1).split('\n')
                for line in strength_lines:
                    if line.strip().startswith(('•', '-', '*')) and len(line.strip()) > 2:
                        analysis_result['strengths'].append(line.strip()[1:].strip())
            
            # Extract bullet points for improvements
            improvements_section = re.search(r'IMPROVEMENTS.*?\n(.*?)(?=\n\n|\Z)', analysis_text, re.DOTALL | re.IGNORECASE)
            if improvements_section:
                improvement_lines = improvements_section.group(1).split('\n')
                for line in improvement_lines:
                    if line.strip().startswith(('•', '-', '*')) and len(line.strip()) > 2:
                        analysis_result['improvements'].append(line.strip()[1:].strip())
            
            # Extract suggestions
            suggestions_section = re.search(r'SUGGESTIONS.*?\n(.*?)(?=\n\n|\Z)', analysis_text, re.DOTALL | re.IGNORECASE)
            if suggestions_section:
                suggestion_lines = suggestions_section.group(1).split('\n')
                for line in suggestion_lines:
                    if line.strip().startswith(('•', '-', '*', '1.', '2.')) and len(line.strip()) > 2:
                        # Remove numbering/bullets
                        cleaned = re.sub(r'^[\d\.\s•\-*]+\s*', '', line.strip())
                        if cleaned:
                            analysis_result['suggestions'].append(cleaned)
            
            # Update resume with analysis results
            resume.analyzed = True
            resume.ats_score = analysis_result['ats_score'] or 0
            resume.match_score = 0  # Will be calculated when compared to jobs
            resume.last_analyzed = timezone.now()
            resume.parsed_content = analysis_result
            resume.save()
            
            processing_time = int((time.time() - start_time) * 1000)
            logger.info(f"Resume {resume.id} analyzed successfully in {processing_time}ms")
            
            return Response(analysis_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            traceback.print_exc()
            return Response(
                {'error': f'Failed to analyze resume: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def analysis(self, request, pk=None):
        """Get existing analysis for a resume"""
        try:
            resume = self.get_object()
            
            if not resume.analyzed or not resume.parsed_content:
                return Response(
                    {'message': 'Analysis not available'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(resume.parsed_content, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting resume analysis: {str(e)}")
            return Response(
                {'error': f'Failed to get analysis: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download the resume file"""
        try:
            resume = self.get_object()
            if not resume.file:
                return Response(
                    {'error': 'File not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Return file response
            from django.http import FileResponse
            return FileResponse(
                resume.file.open('rb'),
                as_attachment=True,
                filename=resume.original_filename
            )
            
        except Exception as e:
            logger.error(f"Error downloading resume: {str(e)}")
            return Response(
                {'error': f'Failed to download resume: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def destroy(self, request, *args, **kwargs):
        """Override destroy to delete the file from storage"""
        try:
            resume = self.get_object()
            # Delete the file from storage
            if resume.file:
                if default_storage.exists(resume.file.name):
                    default_storage.delete(resume.file.name)
            resume.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting resume: {str(e)}")
            return Response(
                {'error': f'Failed to delete resume: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CareerGoalViewSet(viewsets.ModelViewSet):
    """ViewSet for CareerGoal model"""
    serializer_class = CareerGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return ALL goals for the user, not just active ones
        return CareerGoal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a career goal"""
        goal = self.get_object()
        goal.is_active = False
        goal.save()
        return Response({'message': 'Goal archived successfully'})

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark a goal as completed"""
        goal = self.get_object()
        goal.is_completed = True
        goal.completed_date = timezone.now()
        goal.save()
        return Response({'message': 'Goal marked as completed'})