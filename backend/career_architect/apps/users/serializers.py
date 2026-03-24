from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, UserSkill, UserEducation, UserExperience,
    Resume, CareerGoal
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    full_name = serializers.SerializerMethodField()
    profile_completion = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone', 'location', 'bio', 'current_position', 'current_company',
            'years_experience', 'linkedin_url', 'github_url', 'portfolio_url',
            'profile_picture', 'is_premium', 'profile_completion',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.get_full_name()


class UserProfileSerializer(serializers.ModelSerializer):
    """Detailed user profile serializer with related data"""
    skills = serializers.SerializerMethodField()
    education = serializers.SerializerMethodField()
    experiences = serializers.SerializerMethodField()
    resumes = serializers.SerializerMethodField()
    goals = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    profile_completion = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone', 'location', 'bio', 'current_position', 'current_company',
            'years_experience', 'linkedin_url', 'github_url', 'portfolio_url',
            'profile_picture', 'is_premium', 'profile_completion',
            'skills', 'education', 'experiences', 'resumes', 'goals',
            'created_at', 'updated_at'
        ]

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_skills(self, obj):
        return UserSkillSerializer(obj.skills.all(), many=True).data

    def get_education(self, obj):
        return UserEducationSerializer(obj.education.all(), many=True).data

    def get_experiences(self, obj):
        return UserExperienceSerializer(obj.experiences.all(), many=True).data

    def get_resumes(self, obj):
        return ResumeSerializer(obj.resumes.all(), many=True, context=self.context).data

    def get_goals(self, obj):
        return CareerGoalSerializer(obj.career_goals.filter(is_active=True), many=True).data


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password.")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled.")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'.")

        data['user'] = user
        return data


class UserSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSkill
        fields = ['id', 'skill_name', 'proficiency_level', 'years_experience',
                  'last_used', 'is_learning', 'verified', 'created_at', 'updated_at', 'notes']
        read_only_fields = ['id', 'created_at', 'updated_at', 'verified']


class UserEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserEducation
        fields = ['id', 'institution', 'degree', 'field_of_study', 'start_date',
                  'end_date', 'gpa', 'description', 'is_current', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserExperienceSerializer(serializers.ModelSerializer):
    skills_used = serializers.PrimaryKeyRelatedField(many=True, queryset=UserSkill.objects.all(), required=False)

    class Meta:
        model = UserExperience
        fields = ['id', 'title', 'company', 'location', 'start_date', 'end_date',
                  'is_current', 'description', 'achievements', 'skills_used',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ResumeSerializer(serializers.ModelSerializer):
    """Serializer for Resume model"""
    file_url = serializers.SerializerMethodField()
    file = serializers.FileField(write_only=True, required=False)  # Make file write-only for uploads

    class Meta:
        model = Resume
        fields = [
            'id', 'original_filename', 'file', 'file_url', 'file_type', 'file_size',
            'parsed_content', 'is_primary', 'upload_date', 'last_analyzed',
            'ats_score', 'match_score', 'analyzed'
        ]
        read_only_fields = [
            'id', 'original_filename', 'file_size', 'upload_date', 'last_analyzed',
            'ats_score', 'match_score', 'analyzed', 'file_url', 'file_type'
        ]

    def get_file_url(self, obj):
        """Get absolute URL for the file"""
        if obj.file and hasattr(obj.file, 'url'):
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def validate_file(self, value):
        """Validate the uploaded file"""
        if not value:
            return value
            
        # Check file size (10MB)
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(f"File size must be less than {max_size//(1024*1024)}MB")
        
        # Check file type
        content_type = value.content_type
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if content_type not in allowed_types:
            raise serializers.ValidationError("File type must be PDF or Word document")
        
        return value

    def to_representation(self, instance):
        """Customize the representation"""
        data = super().to_representation(instance)
        # Remove file field from representation since it's write-only
        data.pop('file', None)
        return data


class CareerGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerGoal
        fields = ['id', 'title', 'description', 'target_role', 'target_industry',
                  'target_companies', 'timeframe_months', 'priority_level',
                  'is_active', 'is_completed', 'completed_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_date']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data