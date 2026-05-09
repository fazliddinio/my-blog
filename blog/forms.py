from django import forms
from .models import NewsletterSubscriber, ContactMessage


class NewsletterForm(forms.ModelForm):
    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'you@gmail.com',
                'required': True,
            }),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['email', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'you@gmail.com',
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'What are you working on?',
                'rows': 4,
            }),
        }
