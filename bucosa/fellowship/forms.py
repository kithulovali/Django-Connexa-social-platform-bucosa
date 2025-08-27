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
        
class DailyVerseForm(forms.ModelForm):
    class Meta:
        model = DailyVerse
        fields = ['reference', 'verse_text', 'is_active']
        widgets = {
            'reference': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Verse Reference'}),
            'verse_text': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Enter verse text here'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
