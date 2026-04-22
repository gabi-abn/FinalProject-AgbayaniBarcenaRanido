from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    """
    Used for both Create Employee and Update Employee pages.
    Allowance is optional (nullable per Business Rule #5).
    """
    class Meta:
        model  = Employee
        fields = ['name', 'id_number', 'rate', 'allowance']
        labels = {
            'name'      : 'Name',
            'id_number' : 'ID Number',
            'rate'      : 'Rate',
            'allowance' : 'Allowance (Optional)',
        }
        widgets = {
            'name'      : forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'id_number' : forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Employee ID'}),
            'rate'      : forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'allowance' : forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00 (optional)', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['allowance'].required = False
