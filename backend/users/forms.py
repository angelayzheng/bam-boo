from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group


class SignupForm(UserCreationForm):
    group_id = forms.ModelChoiceField(
        queryset=Group.objects.order_by("name", "pk"), required=False
    )

    class Meta(UserCreationForm.Meta):
        fields = ("username", "email", "group_id")
