from django import forms 
from . models import fellowship_edit , donation , Profile

class fellowship_editForm( forms.ModelForm):
    class Meta:
        model= fellowship_edit
        fields = ['name', 'email', 'profile','back_image']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['fellowship', 'description', 'image']
    
class donationForm(forms.ModelForm):
    class Meta :
        model = donation
        fields =['name','email','amount','payment_method','mobile_money_number']