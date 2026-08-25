from django import forms
from .models import Ticket, TicketComment, TicketAttachment, TicketFeedback


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('subject', 'description', 'category', 'priority')
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short summary of the issue'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Describe the issue in detail'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }


class TicketAttachmentForm(forms.ModelForm):
    class Meta:
        model = TicketAttachment
        fields = ('file',)
        widgets = {'file': forms.ClearableFileInput(attrs={'class': 'form-control'})}


class TicketCommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ('body', 'is_internal_note')
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add a comment or update...'}),
            'is_internal_note': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TicketAssignForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ('assigned_to', 'priority', 'status')
        widgets = {
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from accounts.models import User
        self.fields['assigned_to'].queryset = User.objects.filter(role__in=[User.Role.AGENT, User.Role.ADMIN])


class TicketFeedbackForm(forms.ModelForm):
    class Meta:
        model = TicketFeedback
        fields = ('rating', 'comment')
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} star{"s" if i != 1 else ""}') for i in range(1, 6)], attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
