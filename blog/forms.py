"""Public-facing forms (newsletter signup, contact)."""

from django import forms

from .models import ContactMessage, NewsletterSubscriber


class HoneypotMixin(forms.Form):
    """Mix-in that adds a hidden ``website`` field to catch bots.

    Most spam bots blindly fill every input on a form they encounter. We
    render a CSS-hidden, ``tabindex="-1"`` field; humans never touch it,
    bots almost always do. If it's filled, the form fails validation.

    The field is rendered in templates as a CSS-hidden ``<input>`` (see
    ``hp-field`` in ``style.css``).
    """

    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_website(self) -> str:
        # Anything in this field means the submission came from a bot.
        if (self.cleaned_data.get('website') or '').strip():
            raise forms.ValidationError('Spam detected.')
        return ''


class NewsletterForm(HoneypotMixin, forms.ModelForm):
    """Single-field newsletter signup form."""

    class Meta:
        model = NewsletterSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'you@gmail.com',
                'autocomplete': 'email',
                'required': True,
                # Standard upper bound for an email address (RFC 5321).
                'maxlength': 254,
            }),
        }


class ContactForm(HoneypotMixin, forms.ModelForm):
    """The hire-me / contact form. Two fields plus the honeypot."""

    class Meta:
        model = ContactMessage
        fields = ['email', 'message']
        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'you@gmail.com',
                'autocomplete': 'email',
                'maxlength': 254,
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'What are you working on?',
                'rows': 4,
                'maxlength': 4000,
            }),
        }

    def clean_message(self) -> str:
        """Reject pings that are obviously useless (one-word "hi" etc.)."""
        msg = (self.cleaned_data.get('message') or '').strip()
        if len(msg) < 10:
            raise forms.ValidationError('Tell me a bit more (at least 10 characters).')
        if len(msg) > 4000:
            raise forms.ValidationError('Please keep it under 4000 characters.')
        return msg
