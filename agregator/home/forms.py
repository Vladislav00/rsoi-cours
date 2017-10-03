from django import forms
from django.forms import DateInput


class DateWidget(DateInput):
    input_type = 'date'


class RedeemForm(forms.Form):
    code = forms.CharField(max_length=8)


class LoginForm(forms.Form):
    login = forms.CharField(max_length=32, label="Логин")
    pas = forms.CharField(max_length=32, label="Пароль", widget=forms.PasswordInput())


class RegisterForm(forms.Form):
    login = forms.CharField(max_length=32, label="Логин")
    pas = forms.CharField(max_length=32, label="Пароль", widget=forms.PasswordInput())
    pas_again = forms.CharField(max_length=32, label="Повторите пароль", widget=forms.PasswordInput())


class OrderForm(forms.Form):
    name = forms.CharField(max_length=32, label="Имя")
    phone = forms.CharField(max_length=32, label="Номер телефона")
    address = forms.CharField(max_length=256, label="Адрес доставки")


class PreferencesForm(forms.Form):
    Start_date = forms.DateTimeField(required=False, widget=DateWidget())
    Start_date_change = forms.BooleanField(required=False)

    End_date = forms.DateTimeField(required=False, widget=DateWidget())
    End_date_change = forms.BooleanField(required=False)

    Start_money = forms.IntegerField(required=False, min_value=0)
    Start_money_change = forms.BooleanField(required=False)

    Current_money = forms.IntegerField(required=False)
    Сurrent_money_change = forms.BooleanField(required=False)

    Base_course = forms.FloatField(required=False)
    Base_course_change = forms.BooleanField(required=False)

    Refresh_time = forms.IntegerField(required=False, min_value=0)
    Refresh_time_change = forms.BooleanField(required=False)

    Code_bonus = forms.IntegerField(required=False, min_value=0)
    Code_bonus_change = forms.BooleanField(required=False)


class FabricForm(forms.Form):
    count = forms.IntegerField(min_value=0)


class DeleteForm(forms.Form):
    pass


class UserForm(forms.Form):
    name = forms.CharField(max_length=128, required=False)
    vk_id = forms.CharField(max_length=32, required=False)
    fb_id = forms.CharField(max_length=32, required=False)
    ok_id = forms.CharField(max_length=32, required=False)
    go_id = forms.CharField(max_length=32, required=False)
    login = forms.CharField(max_length=32, required=False)
    password = forms.CharField(max_length=64, required=False)
    ROLE_CHOICES = (
        ("user", "user"),
        ("manager", "manager"),
        ("fabric", "fabric"),
        ("service", "service")
    )
    role = forms.ChoiceField(ROLE_CHOICES)
    balance = forms.IntegerField(min_value=0, required=False)


class PrizeForm(forms.Form):
    title = forms.CharField(max_length=128)
    pic = forms.ImageField(required=False)
    cost = forms.IntegerField(min_value=0)
    provider = forms.CharField(max_length=128)


class AOrderForm(forms.Form):
    prize = forms.UUIDField()
    user = forms.UUIDField()
    user_contacts = forms.CharField(max_length=512)


class UserUpdateForm(forms.Form):
    name = forms.CharField(max_length=128, required=False)
    password = forms.CharField(max_length=64, required=False)