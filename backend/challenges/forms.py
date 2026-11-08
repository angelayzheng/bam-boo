from django import forms


class ChallengeFilterForm(forms.Form):
    name = forms.CharField(required=False)
    category = forms.CharField(required=False)
    date = forms.DateField(required=False, input_formats=["%Y-%m-%d"])
    difficulty = forms.IntegerField(required=False, min_value=1, max_value=5)
