from django import forms

from metrics.models import Annotation, Project


class DateRangeForm(forms.Form):
    """Form for date-range searches"""
    from_datetime = forms.DateField(widget=forms.DateInput(attrs={'class':'datefield'}))
    to_datetime = forms.DateField(widget=forms.DateInput(attrs={'class':'datefield'}), required=False)


class AnnotationForm(forms.ModelForm):
    project = forms.ModelChoiceField(Project.objects.all(), widget=forms.HiddenInput)
    timestamp = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'class':'disabled', 'readonly': 'true'}))
    class Meta:
        model = Annotation
        