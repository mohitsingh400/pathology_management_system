from django import forms
from .models import Report

class ReportUploadForm(forms.ModelForm):
    pdf_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'accept': '.pdf'}),
        required=False,
        label='PDF Report'
    )

    class Meta:
        model = Report
        fields = ['pdf_file', 'status', 'notes']
        widgets = {
            'pdf_file': forms.ClearableFileInput(attrs={'accept': '.pdf'})
        }

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get('pdf_file')
        if pdf_file:
            if not pdf_file.name.endswith('.pdf'):
                raise forms.ValidationError("Only PDF files are allowed.")
            if pdf_file.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError("File too large (max 5MB)")
        return pdf_file
