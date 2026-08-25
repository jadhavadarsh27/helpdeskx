from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User


class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'department', 'phone', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Public sign-up only allows Employee or Agent self-registration;
        # Admin accounts are provisioned via the Django admin.
        self.fields['role'].choices = [
            (User.Role.EMPLOYEE, 'Employee'),
            (User.Role.AGENT, 'Support Agent'),
        ]
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')
        self.fields['role'].widget.attrs['class'] = 'form-select'


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'department', 'phone', 'avatar')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
