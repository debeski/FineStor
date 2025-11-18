import django_tables2 as tables
from .models import AssetCategory, Asset, ImportRecord, ExportRecord, ExportItem
from django.utils.safestring import mark_safe
from django.urls import reverse


class AssetCategoryTable(tables.Table):
    edit = tables.Column(accessor='id', verbose_name='', empty_values=())

    class Meta:
        model = AssetCategory
        template_name = "django_tables2/bootstrap5.html"
        fields = ['name', 'discription']
        attrs = {'class': 'table table-striped table-sm table align-middle'}

    def render_edit(self, value):
        return mark_safe(f'<a href="{reverse("edit_category", args=[value])}" class="btn btn-secondary btn-sm">تعديل</a>')


class AssetTable(tables.Table):
    edit = tables.Column(accessor='id', verbose_name='', empty_values=())

    class Meta:
        model = Asset
        template_name = "django_tables2/bootstrap5.html"
        fields = ('name', 'category', 'brand', 'brand_en', 'stock', 'unit')
        attrs = {'class': 'table table-striped table-sm table align-middle'}

    def render_edit(self, value, record):
        return mark_safe(f'<a href="{reverse("manage_assets")}?category={record.category.id}&id={value}" class="btn btn-secondary btn-sm">تعديل</a>')


class ImportRecordTable(tables.Table):
    details_pdf = tables.Column(accessor='trans_id', verbose_name='', empty_values=())

    # Define table columns
    trans_id = tables.Column()
    company = tables.Column()
    date = tables.Column()

    class Meta:
        model = ImportRecord
        template_name = "django_tables2/bootstrap5.html"  # You can choose a different template style
        fields = ("trans_id", "date", "assign_number", "assign_date", "items", "company")  # Fields to display in the table
        attrs = {'class': 'table table-striped table-sm table-hover table align-middle'}

    def render_details_pdf(self, value):
        model_type = 'import'
        pdf_button = f'<a href="{reverse("gen_pdf", args=[model_type, value])}" target="_blank" class="btn btn-primary btn-sm">طباعة</a>'
        detail_button = f'<a href="{reverse("import_details", args=[value])}" class="btn btn-secondary btn-sm">عرض</a>'
        return mark_safe(f'{detail_button} {pdf_button}')  # Combine both buttons


class ExportRecordTable(tables.Table):
    details_pdf = tables.Column(accessor='trans_id', verbose_name='', empty_values=())

    # Define table columns
    trans_id = tables.Column(verbose_name="رقم الإذن")
    date = tables.DateColumn(verbose_name="تاريخ الإذن")
    export_type = tables.Column(verbose_name="نوع الإذن")
    entity = tables.Column(accessor='entity_selection', verbose_name="الجهة")

    class Meta:
        model = ExportRecord
        template_name = "django_tables2/bootstrap5.html"  # You can choose a different template style
        fields = ("trans_id", "date", "export_type", "entity", "items")  # Fields to display in the table
        attrs = {'class': 'table table-striped table-sm table-hover table align-middle'}

    def render_details_pdf(self, value):
        model_type = 'export'
        pdf_button = f'<a href="{reverse("gen_pdf", args=[model_type, value])}" target="_blank" class="btn btn-primary btn-sm">طباعة</a>'
        detail_button = f'<a href="{reverse("export_details", args=[value])}" class="btn btn-secondary btn-sm">عرض</a>'
        # return_button = f'<a href="{reverse("export_return", args=[value])}" class="btn btn-danger btn-sm">ارجاع</a>'
        return mark_safe(f'{detail_button} {pdf_button}')


class InventoryReportTable(tables.Table):
    category = tables.Column(verbose_name="التصنيف")
    name = tables.Column(verbose_name="اسم الصنف")
    brand = tables.Column(verbose_name="العلامة")
    stock = tables.Column(verbose_name="الكمية بالمخزن")
    net_quantity = tables.Column(verbose_name="المدون بالسجل")
    average_price = tables.Column(verbose_name="متوسط السعر")


    class Meta:
        attrs = {"class": "table table-striped table-sm table align-middle"}  # Add Bootstrap class for styling
        template_name = "django_tables2/bootstrap5.html"  # Or any other template
        fields = ("category", "name", "brand", "stock", "net_quantity", "average_price")


class ExportReturnTable(tables.Table):
    class Meta:
        model = ExportItem
        fields = ['return_id', 'return_at', 'return_purpose', 'asset', 'return_condition', 'record', 'record.date', 'record.entity_selection']
        attrs = {'class': 'table table-striped table-bordered'}
