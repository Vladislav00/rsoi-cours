from django import forms


class PrizeForm(forms.Form):
    title = forms.CharField(max_length=128)
    pic = forms.ImageField(required=False)
    cost = forms.IntegerField(min_value=0)
    provider = forms.CharField(max_length=128)
