from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserSkill, UserEducation, UserExperience, Resume, CareerGoal

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'created_at')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'location', 'bio')}),
        ('Professional info', {'fields': ('current_position', 'current_company', 'years_experience')}),
        ('Social links', {'fields': ('linkedin_url', 'github_url', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login')

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill_name', 'proficiency_level', 'years_experience', 'verified')
    list_filter = ('proficiency_level', 'verified')
    search_fields = ('user__email', 'skill_name')

@admin.register(UserEducation)
class UserEducationAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'degree', 'field_of_study', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('user__email', 'institution', 'degree')

@admin.register(UserExperience)
class UserExperienceAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'company', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('user__email', 'title', 'company')

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'original_filename', 'file_type', 'file_size', 'is_primary', 'upload_date')
    list_filter = ('file_type', 'is_primary', 'upload_date')
    search_fields = ('user__email', 'original_filename')

@admin.register(CareerGoal)
class CareerGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_role', 'target_industry', 'timeframe_months', 'priority_level', 'is_active')
    list_filter = ('priority_level', 'is_active')
    search_fields = ('user__email', 'target_role', 'target_industry')