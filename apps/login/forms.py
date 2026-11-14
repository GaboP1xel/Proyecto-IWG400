from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


User = get_user_model()


class UsernameAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "El nombre de usuario o la contraseña no son correctos.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nombre de usuario"
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "username", "placeholder": "Nombre de usuario"}
        )
        self.fields["password"].label = "Contraseña"
        self.fields["password"].widget.attrs.update(
            {"autocomplete": "current-password", "placeholder": "Contraseña"}
        )


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "autocomplete": "new-password",
                "placeholder": "Contraseña",
            }
        ),
    )

    class Meta:
        model = User
        fields = ("username",)
        labels = {"username": "Nombre de usuario"}
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "autocomplete": "username",
                    "placeholder": "Nombre de usuario",
                }
            )
        }

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise ValidationError(
                "Este nombre de usuario ya está registrado.",
                code="duplicate_username",
            )
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        if password:
            self.instance.username = cleaned_data.get("username", "")
            try:
                validate_password(password, self.instance)
            except ValidationError as error:
                for password_error in error.error_list:
                    params = password_error.params or {}
                    if password_error.code == "password_too_short":
                        message = (
                            "La contraseña debe tener al menos "
                            f"{params.get('min_length', 8)} caracteres."
                        )
                    elif password_error.code == "password_too_common":
                        message = "Esta contraseña es demasiado común."
                    elif password_error.code == "password_entirely_numeric":
                        message = "La contraseña no puede contener solo números."
                    elif password_error.code == "password_too_similar":
                        message = "La contraseña es demasiado similar a tus datos."
                    else:
                        message = password_error.messages[0]
                    self.add_error("password", message)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
