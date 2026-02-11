from django import forms
from .models import Integration

class IntegrationForm(forms.ModelForm):
    class Meta:
        model = Integration
        fields = ['source', 'target', 'type', 'direction', 'volume', 'data_sensitivity']
        widgets = {
            field: forms.Select(attrs={'class': 'w-full p-3 bg-gray-50 border border-gray-200 rounded-xl mb-4'})
            if field in ['source', 'target', 'type', 'data_sensitivity'] else
            forms.TextInput(attrs={'class': 'w-full p-3 bg-gray-50 border border-gray-200 rounded-xl mb-4'})
            for field in ['source', 'target', 'type', 'direction', 'volume', 'data_sensitivity']
        }