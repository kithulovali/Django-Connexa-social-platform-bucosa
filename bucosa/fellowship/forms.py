from django import forms 
from . models import fellowship_edit , donation , DailyVerse

class fellowship_editForm( forms.ModelForm):
    class Meta:
        model= fellowship_edit
        fields = ['name', 'email', 'profile','back_image',  'description']

class donationForm(forms.ModelForm):
    class Meta :
        model = donation
        fields =['name','email','amount','payment_method','mobile_money_number']
         
from django import forms
from .models import DailyVerse

class DailyVerseForm(forms.ModelForm):
    class Meta:
        model = DailyVerse
        fields = ['verse_text', 'reference']  
        widgets = {
            'verse_text': forms.Textarea(attrs={'class': 'form-textarea rounded-lg border p-2 w-full', 'rows': 5}),
            'reference': forms.TextInput(attrs={'class': 'form-input rounded-lg border p-2 w-full'}),
        }
