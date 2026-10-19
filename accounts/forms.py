from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # без статичних підказок — помилки лише після невдалої спроби
        for name in ('username', 'password1', 'password2', 'email'):
            self.fields[name].help_text = ''
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'maxlength': '150',
            'autocomplete': 'username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Підтвердження пароля'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['preferred_currency']
        widgets = {
            'preferred_currency': forms.Select(attrs={'class': 'form-select'}),
        }


class ProfileEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
