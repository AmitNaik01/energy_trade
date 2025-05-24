from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from captcha.fields import CaptchaField


class LoginForm(forms.Form):
    username = forms.CharField(
        widget= forms.TextInput(
            attrs={
                "class": "form-control"
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control"
            }
        )
    )
    captcha = CaptchaField()  # Add this field for CAPTCHA


class SignUpForm(UserCreationForm):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Seller', 'Seller'),
        ('Buyer', 'Buyer'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-control"}))
    # other fields...
    address = forms.CharField(
        max_length=255,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "style": "height: 100px; resize: none;"  # Adjust number of visible lines
        })
    )
    contact_no = forms.CharField(  # ✅ new field
        max_length=15,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Contact Number"
    )
    captcha = CaptchaField()

    class Meta:
        model = User
        fields = ('username', 'email', 'address', 'contact_no', 'password1', 'password2')  # no 'role' here!

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data['role']
        user.address = self.cleaned_data['address']  # ✅ set address
        user.contact_no = self.cleaned_data['contact_no']


        user.is_admin = (role == 'Admin')
        user.is_employee = (role == 'Seller')
        user.is_customer = (role == 'Buyer')

        if commit:
            user.save()
        return user



class UserEditForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Seller', 'Seller'),
        ('Buyer', 'Buyer'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ['username', 'email', 'address', 'contact_no', 'role', 'total_energy_saved']

        widgets = {
            'username': forms.TextInput(attrs={"class": "form-control"}),
            'email': forms.EmailInput(attrs={"class": "form-control"}),
            'address': forms.TextInput(attrs={"class": "form-control"}),
            'contact_no': forms.TextInput(attrs={"class": "form-control"}),
            'total_energy_saved': forms.NumberInput(attrs={"class": "form-control"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data['role']

        user.is_admin = (role == 'Admin')
        user.is_employee = (role == 'Seller')
        user.is_customer = (role == 'Buyer')

        if commit:
            user.save()
        return user


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()
    captcha = CaptchaField()

class VerifyCodeForm(forms.Form):
    code = forms.CharField(max_length=6)

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned['new_password'] != cleaned['confirm_password']:
            raise forms.ValidationError("Passwords do not match")