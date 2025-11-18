from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML
from crispy_forms.bootstrap import FormActions
from .models import Company, Department, Affiliate, SubAffiliate, Employee
from django.db.models import Q
import re
from django.urls import reverse



# Function to rename first choice in selection menu
def set_first_choice(field, placeholder):
    """Set the first choice of a specified field."""
    choices = list(field.choices)  # Convert to list
    choices[0] = ('', placeholder)  # Rename first choice with the provided placeholder
    field.choices = choices  # Set the modified choices

# Function to set attributes for all fields in the form
def set_field_attrs(form):
    """Set common attributes for all fields in the form."""
    for field_name in form.fields:
        field = form.fields.get(field_name)
        # Common attributes
        field.widget.attrs['placeholder'] = field.label  # Set placeholder as field label
        field.widget.attrs['dir'] = 'rtl'  # Set text direction
        field.widget.attrs['autocomplete'] = 'off'  # Disable autocomplete
        field.label = ''  # Clear the label

# Function to validate some form fields
def validator(form):
    """Set common attributes for all fields in the form."""
    for field_name in form.fields:
        field = form.fields.get(field_name)
        # Set specific patterns based on field name
        if field_name == 'name' :
            # Allow Arabic letters only.
            field.widget.attrs['pattern'] = r'^[\u0621-\u064A\s]+$'

            def clean_name():
                name = form.cleaned_data['name']
                if not re.match(r'^[\u0621-\u064A\s]+$', name):
                    raise forms.ValidationError('الرجاء إستخدام الحروف العربية.')
                return name
            form.clean_name = clean_name

        elif field_name == 'phone':
            # Allow digits only.
            field.widget.attrs['pattern'] = r'^\d+$'

            def clean_phone():
                phone = form.cleaned_data['phone']
                if not re.match(r'^09\d{8}$', phone):
                    raise forms.ValidationError('يرجى إدخال رقم هاتف صحيح ابتداء بـ09.')

                return phone
            form.clean_phone = clean_phone

        elif 'date' in field_name:
            # Add Flatpickr attributes for date fields
            field.widget.attrs['id'] = 'monthSelector'  # Class for Flatpickr

# Function to generate cancel button URL
def get_cancel_button_url(self, model_name):
    if self.instance.id:
        return f'<button type="button" onclick="window.location.href = document.referrer || \'/\';" class="btn btn-danger me-2">الغاء</button>'
    return ''


# Entity Forms
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'address', 'phone']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'name',
            'address',
            'phone',
            FormActions(
                Submit('submit', '{% if form.instance.id %}تحديث{% else %}اضافة{% endif %}', css_class='btn btn-primary'),
                HTML(get_cancel_button_url(self, 'company'))
            )
        )
        set_field_attrs(self)
        validator(self)


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['type', 'name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_first_choice(self.fields['type'], 'نوع التقسيم')
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field('type', css_class='form-control'), css_class='col-sm-2 me-3'),
                Div(Field('name', css_class='form-control'), css_class='col'),
                css_class='input-group'
            ),
            FormActions(
                Submit('submit', '{% if form.instance.id %}تحديث{% else %}اضافة{% endif %}', css_class='btn btn-primary'),
                HTML(get_cancel_button_url(self, 'department'))
            )
        )
        set_field_attrs(self)
        validator(self)


class AffiliateForm(forms.ModelForm):
    class Meta:
        model = Affiliate
        fields = ['type', 'name', 'address']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_first_choice(self.fields['type'], 'نوع الجهة')

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field('type', css_class='form-control'), css_class='col-sm-2 me-3'),
                Div(Field('name', css_class='form-control'), css_class='col'),
                css_class='input-group'
            ),
            Field('address', css_class='form-control'),
            FormActions(
                Submit('submit', '{% if form.instance.id %}تحديث{% else %}اضافة{% endif %}', css_class='btn btn-primary'),
                HTML(get_cancel_button_url(self, 'affiliate'))
            )
        )
        set_field_attrs(self)
        validator(self)


class SubAffiliateForm(forms.ModelForm):
    class Meta:
        model = SubAffiliate
        fields = ['subname', 'subtype']  # Make sure to include affiliate field if needed

    def __init__(self, *args, **kwargs):
        self.affiliate_id = kwargs.pop('affiliate_id', None)
        super().__init__(*args, **kwargs)
        # set_first_choice(self.fields['affiliate'], 'اختر الجهة')
        set_first_choice(self.fields['subtype'], 'التقسيم الاداري')

        self.helper = FormHelper()
        self.helper.layout = Layout(
            # Field('affiliate', css_class='form-control'),
            Div(
                Div(Field('subtype', css_class='form-control'), css_class='col-sm-2 me-3'),
                Div(Field('subname', css_class='form-control'), css_class='col'),
                css_class='input-group'
            ),

            FormActions(
                Submit('submit', '{% if form.instance.id %}تحديث{% else %}اضافة{% endif %}', css_class='btn btn-primary'),
                HTML(self.get_cancel_button_url())
            )
        )
        set_field_attrs(self)
        validator(self)

    def save(self, commit=True):
        # Overriding the save method to automatically set the affiliate
        instance = super().save(commit=False)
        if self.affiliate_id:
            instance.affiliate_id = self.affiliate_id  # Set the affiliate from the passed ID
        if commit:
            instance.save()
        return instance

    def get_cancel_button_url(self):
        # Check if the instance has an ID
        if self.instance.id:
            # Generate the URL for the cancel button
            return f'<a href="{reverse("sub_affiliate_view", args=[self.instance.affiliate.id])}" class="btn btn-danger">إالغاء</a>'
        return ''  # Return an empty string if no ID
        

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'job_title', 'department', 'email', 'phone', 'date_employed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_first_choice(self.fields['job_title'], 'الوظيفة')
        set_first_choice(self.fields['department'], 'الادارة/المكتب')

        # Filter the queryset for the department field
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='form-control'),
            Div(
                Div(Field('job_title', css_class='form-control'), css_class='col-sm-4 me-3'),
                Div(Field('department', css_class='form-control'), css_class='col'),
                css_class='input-group'
            ),
            Div(
                Div(Field('email', css_class='form-control'), css_class='col-sm-4 me-3'),
                Div(Field('phone', css_class='form-control'), css_class='col-sm-4 me-3'),
                Div(Field('date_employed', css_class='form-control'), css_class='col'),
                css_class='input-group'
            ),

            FormActions(
                Submit('submit', '{% if form.instance.id %}تحديث{% else %}اضافة{% endif %}', css_class='btn btn-primary'),
                HTML(get_cancel_button_url(self, 'employee'))
            )
        )
        set_field_attrs(self)
        validator(self)

