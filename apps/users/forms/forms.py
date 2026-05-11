from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(max_length=150, required=True, label="Username")
    first_name = forms.CharField(max_length=100, required=True, label="Full name")
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True, label="Full name")
    username = forms.CharField(max_length=150, required=True, label="Username")

    class Meta:
        model = User
        fields = ['username', 'first_name']

def clean_email(self):
    email = self.cleaned_data.get('email')
    if User.objects.filter(email=email).exists():
        raise forms.ValidationError("This email is already registered.")
    return email
