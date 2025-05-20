from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.admin import UserAdmin
from django import forms
# from django.contrib.auth.forms import UserCreationForm, UserChangeForm

class CustomUserCreationForm(forms.ModelForm):
	"""A form for creating new users. Includes all the required
    fields, plus a repeated password."""

	password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
	password2 = forms.CharField(
	    label="Password confirmation", widget=forms.PasswordInput
	)

	class Meta:
		model = CustomUser
		fields = ['full_name', 'email', 'business_name', 'business_email', 'country', 'state', 'currency']

	def clean_password2(self):
	    # Check that the two password entries match
	    password1 = self.cleaned_data.get("password1")
	    password2 = self.cleaned_data.get("password2")
	    if password1 and password2 and password1 != password2:
	        raise ValidationError("Passwords don't match")
	    return password2

	def save(self, commit=True):
	    # Save the provided password in hashed format
	    user = super().save(commit=False)
	    user.set_password(self.cleaned_data["password1"])
	    if commit:
	        user.save()
	    return user
	

class CustomUserChangeForm(forms.ModelForm):
	class Meta:
		model = CustomUser
		fields = ('full_name', 'email', 'business_name', 'business_email', 'password', 'country', 'state', 'currency')

class CustomUserAdmin(UserAdmin):
	model = CustomUser
	form = CustomUserCreationForm
	add_form = CustomUserCreationForm
	list_display = ['id', 'email', 'full_name', 'business_name', 'is_staff', 'is_active'] # 
	list_filter = ['email', 'is_superuser', 'is_staff', 'is_active'] #
	search_fields = ("email", "full_name", "business_name")
	ordering = ("email",)

	fieldsets = (
		(None, {'fields': ('email', 'full_name', 'business_name', 'password')},),
		('Permissions', {'fields': ('is_staff', 'is_active',)},),
		('More Details', {
			'fields': ('currency', 'business_type', 'country', 'state', 'date_joined')
		})
	)

	add_fieldsets = (
		(None, {
			'classes': ('wide',),
			'fields': ('email', 'full_name', 'business_name', 'password1', 'password2')
		}),
		('More Details', {
			'classes': ('wide',),
			'fields': ('currency', 'business_type', 'country', 'state', 'date_joined', 'is_active', 'is_staff')
		})
	)

admin.site.register(CustomUser, CustomUserAdmin)
