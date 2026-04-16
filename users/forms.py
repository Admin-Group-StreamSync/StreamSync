from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class RegistroUsuarioForm(UserCreationForm):
    username = forms.CharField(max_length=150, required=True, label="Nom d'usuari")
    first_name = forms.CharField(max_length=100, required=True, label="Nom complet")
    email = forms.EmailField(required=True, label="Correu electrònic")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Aquest correu ja està registrat.")
        return email

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, required=True, label="Nom complet")
    username = forms.CharField(max_length=150, required=True, label="Nom d'usuari")

    class Meta:
        model = User
        fields = ['username', 'first_name']

