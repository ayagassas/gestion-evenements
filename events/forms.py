from django import forms
from .models import Event


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location', 'latitude', 'longitude', 'image']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class EventSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Recherche',
                        widget=forms.TextInput(attrs={'placeholder': 'Titre ou description...'}))
    location = forms.CharField(required=False, label='Lieu',
                               widget=forms.TextInput(attrs={'placeholder': 'Ville, salle...'}))
    date_from = forms.DateField(required=False, label='À partir de',
                                widget=forms.DateInput(attrs={'type': 'date'}))
