from django import forms


class LoginForm(forms.Form):
    usuario_login = forms.CharField(
        label="Usuario",
        max_length=50,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Usuario", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Contraseña"}
        ),
    )
