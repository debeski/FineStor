from django import forms
from django.contrib.contenttypes.models import ContentType
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div, HTML, Fieldset, ButtonHolder
from crispy_forms.bootstrap import FormActions
from .models import AssetCategory, Asset, ImportRecord, ImportItem, ExportRecord, ExportItem, Committee
from core.models import Company, Department, Affiliate, SubAffiliate, Employee
from core.forms import set_first_choice
from django.urls import reverse
from datetime import datetime

# Get the current year
current_year = datetime.now().year
last_year = current_year - 1

# Function to set attributes for all fields in the form
def set_field_attrs(form):
    """Set common attributes for all fields in the form."""
    for field_name in form.fields:
        field = form.fields.get(field_name)
        # Common attributes
        field.widget.attrs['placeholder'] = field.label  # Set placeholder as field label
        field.widget.attrs['dir'] = 'rtl'  # Set text direction
        # field.widget.attrs['autocomplete'] = 'off'  # Disable autocomplete
        field.label = ''  # Clear the label

# New Asset category Form
class AssetCategoryForm(forms.ModelForm):
    class Meta:
        model = AssetCategory
        fields = ['name', 'discription']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()

        # Define the cancel button HTML only if the instance has an ID
        cancel_button = ""
        if self.instance.id:
            cancel_button = '<a href="#" onclick="window.history.back();" class="btn btn-danger">إلغاء</a>'


        self.helper.layout = Layout(
            Div(
                Div(Field('name', css_class='form-control'), css_class='col-md-5 me-3'),
                Div(Field('discription', css_class='form-control'), css_class='col'),
                css_class='input-group mb-1'
            ),
            FormActions(
                Submit('submit', '{% if form.instance.id %}تحديث{% else %}اضافة{% endif %}', css_class='btn btn-primary'),
                HTML(cancel_button)  # Cancel button is shown conditionally
            )
        )
        set_field_attrs(self)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if AssetCategory.objects.filter(name=name).exists():
            raise forms.ValidationError("A category with this name already exists.")
        return name

# New Asset Form
class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['category', 'name', 'brand', 'brand_en', 'unit']

    def __init__(self, *args, **kwargs):
        self.selected_cat = kwargs.pop('selected_cat', None)
        super().__init__(*args, **kwargs)
        set_first_choice(self.fields['category'], 'التصنيف')

        # Dynamically set the type field
        if self.selected_cat:
            self.fields['category'].initial = self.selected_cat
            self.fields['category'].widget = forms.HiddenInput()

        # Configure crispy form helper
        self.helper = FormHelper()

        # Define the cancel button HTML only if the instance has an ID
        cancel_button = ""
        if self.instance.id:
            cancel_button = '<a href="#" onclick="window.history.back();" class="btn btn-danger">إلغاء</a>'

        self.helper.layout = Layout(
            'category',
            Div(
                Div(Field('name', css_class='form-control'), css_class='col-sm-4 me-3'),
                Div(Field('brand', css_class='form-control'), css_class='col-sm-3 me-3'),
                Div(Field('brand_en', css_class='form-control'), css_class='col-sm-3 me-3'),
                Div(Field('unit', css_class='form-control'), css_class='col'),
                css_class='input-group mb-1'
            ),
            FormActions(
                Submit('submit', '{% if form.instance.id %}تحديث{% else %}اضافة{% endif %}', css_class='btn btn-primary'),
                HTML(cancel_button)  # Cancel button is shown conditionally
            )
        )
        set_field_attrs(self)

# New ImportRecord Form
class ImportRecordForm(forms.ModelForm):
    hidden_field = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = ImportRecord
        fields = ['company', 'date', 'assign_number', 'assign_date', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].queryset = Company.objects.all()
        self.fields['notes'].required = False
        set_first_choice(self.fields['company'], 'الشركة')

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(
                Div(Field('company', css_class='form-control'), css_class='col-md-8 me-3'),
                Div(Field('date', css_class='form-control flatpickr'), css_class='col'),
                css_class='input-group'
            ),
            Div(
                Div(Field('assign_number', css_class='form-control'), css_class='col me-3'),
                Div(Field('assign_date', css_class='form-control flatpickr'), css_class='col'),
                css_class='input-group'
            ),
            Field('notes', css_class='form-control', rows=1),
            FormActions(
                HTML(f'<a class="btn btn-danger me-2" href="{reverse("import_records")}">الغاء</a>'),
                Submit('submit_record', 'حفظ', css_class='btn btn-primary col-2'),
                css_class='text-end mt-3'
            )
        )
        set_field_attrs(self)

# Add Import Item Form
class ImportItemForm(forms.ModelForm):

    asset_cat = forms.ModelChoiceField(
    queryset=AssetCategory.objects.all(),
    required=False,
    label="اختر التصنيف"
)
    class Meta:
        model = ImportItem
        fields = ['asset_cat', 'asset', 'quantity', 'price']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.objects.all()
        self.fields['quantity'].widget.attrs.update({
            'min': '1.00',
        })
        self.fields['price'].widget.attrs.update({
            'min': '1.00',
            'step': '0.25',
        })
        set_first_choice(self.fields['asset_cat'], 'التصنيف')
        set_first_choice(self.fields['asset'], 'الصنف')

        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(Field('asset_cat', css_class='form-control', id='id_asset_cat'), css_class='col'),
            Div(Field('asset', css_class='form-control', id='id_asset'), css_class='col'),
            Div(
                Div(Field('quantity', css_class='form-control'), css_class='col me-3'),
                Div(Field('price', css_class='form-control'), css_class='col'),
                css_class='input-group'
            ),
            FormActions(
                Submit('submit', 'اضافة', css_class='btn btn-primary'),
            )
        )
        set_field_attrs(self)

# New ExportRecord Forms
class ExportRecordForm(forms.ModelForm):
    hidden_field = forms.CharField(widget=forms.HiddenInput(), required=False)
    entity = forms.ModelChoiceField(
        queryset=None,  # Queryset will be dynamically assigned based on export_type
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ExportRecord
        fields = ['date', 'export_type', 'entity', 'notes']  # Include 'export_type' directly

    def __init__(self, *args, **kwargs):
        # Get export_type from the form instance or passed kwargs
        self.export_type = kwargs.pop('export_type', None)  # Remove export_type from kwargs if passed
        super().__init__(*args, **kwargs)  # Call parent constructor

        # Dynamically set field properties for `entity` based on `export_type`
        if self.export_type:
            self._set_entity_queryset(self.export_type)
            self.fields['export_type'].initial = self.export_type
            self.fields['export_type'].widget = forms.HiddenInput()


        self.helper = FormHelper()
        self.helper.layout = Layout(
            'export_type',
            Div(
                Div(Field('entity', css_class='form-control'), css_class='col-md-6 me-3'),
                Div(Field('date', css_class='form-control flatpickr'), css_class='col'),
                css_class='row'
            ),
            Field('notes', css_class='form-control', rows=3),
            FormActions(
                HTML(f'<a class="btn btn-danger me-2" href="{reverse("export_records")}">الغاء</a>'),
                Submit('submit_record', 'حـفـظ', css_class='btn btn-primary col-2'),
                css_class='text-end mt-3'
            )
        )
        set_field_attrs(self)

    def _set_entity_queryset(self, export_type):
        """Set the queryset for the `entity` field based on the export type."""
        if export_type == 'Consume':
            self.fields['entity'].queryset = Department.objects.all()
            set_first_choice(self.fields['entity'], 'الادارة او المكتب')
        elif export_type == 'Personal':
            self.fields['entity'].queryset = Employee.objects.all()
            set_first_choice(self.fields['entity'], 'اسم الموظف')
        elif export_type == 'Department':
            self.fields['entity'].queryset = Department.objects.all()
            set_first_choice(self.fields['entity'], 'الادارة او المكتب')
        elif export_type == 'Loan':
            self.fields['entity'].queryset = SubAffiliate.objects.all()
            set_first_choice(self.fields['entity'], 'الجهة المستفيدة')

        print(f"Set queryset for export_type '{export_type}': {self.fields['entity'].queryset}")

    def clean(self):
        cleaned_data = super().clean()
        entity = cleaned_data.get('entity')

        if not entity:
            raise forms.ValidationError("Please select a valid entity based on the export type.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Set the `entity_content_type` and `entity_object_id`
        entity = self.cleaned_data['entity']
        instance.entity_type = ContentType.objects.get_for_model(entity)
        instance.entity_id = self.cleaned_data['entity'].id

        if commit:
            instance.save()
        return instance

# Add Export Item Form
class ExportItemForm(forms.ModelForm):

    asset_cat = forms.ModelChoiceField(
    queryset=AssetCategory.objects.all(),
    required=False,
    label="اختر التصنيف"
)
    class Meta:
        model = ExportItem
        fields = ['asset_cat', 'asset', 'quantity', 'sn']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['asset'].queryset = Asset.objects.filter(stock__gt=0)
        self.fields['quantity'].widget.attrs.update({
            'min': '1.00',
        })
        set_first_choice(self.fields['asset_cat'], 'التصنيف')
        set_first_choice(self.fields['asset'], 'الصنف')
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Div(Field('asset_cat', css_class='form-control', id='id_asset_cat'), css_class='col'),
            Div(Field('asset', css_class='form-control', id='id_asset'), css_class='col'),
            Div(
                Div(Field('quantity', css_class='form-control'), css_class='col me-3'),
                Div(Field('sn', css_class='form-control'), css_class='col-md-4 me-3'),
                css_class='input-group'
            ),
            FormActions(
                Submit('submit', 'اضافة', css_class='btn btn-primary'),
            )
        )
        set_field_attrs(self)

# New Ruturn Form
class ReturnRecordForm(forms.ModelForm):

    class Meta:
        model = None
        fields = ['return_at', 'return_purpose', 'return_condition']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        set_first_choice(self.fields['return_purpose'], 'سبب الترجيع')
        set_first_choice(self.fields['return_condition'], 'حالة الصنف')
        self.helper = FormHelper()
        set_field_attrs(self)

# New Report Form
class ReportForm(forms.ModelForm):
    year = forms.IntegerField(
        min_value=2011,
        max_value=current_year,
        initial=last_year,
        widget=forms.NumberInput(attrs={
            'type': 'number',
            'step': 1,
            'class': 'form-control',
            'direction': 'rtl',
        }),
        label="السنة",
    )

    president = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        label="",
    )
    members = forms.ModelMultipleChoiceField(
        queryset=Employee.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'p-2 lh-lg option-separator'}),
        required=False,
        label="",
    )

    class Meta:
        model = Committee
        fields = ['year', 'president', 'members']
