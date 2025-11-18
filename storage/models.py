from django.db import models
import uuid
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from decimal import Decimal, ROUND_HALF_UP
from django.apps import apps


# PDF and IMG Files Naming Functions:
def generate_random_filename(instance, filename):
    """Generate a random filename for uploaded files."""
    random_filename = f"{uuid.uuid4().hex}.pdf"
    model_name = instance.__class__.__name__.lower()
    return f'{model_name}/{random_filename}'

def get_pdf_upload_path(instance, filename):
    """Get the upload path for PDF files."""
    return f'pdfs/{generate_random_filename(instance, filename)}'

def get_img_upload_path(instance, filename):
    """Get the upload path for IMG files."""
    return f'item_img/{generate_random_filename(instance, filename)}'


# ASSET_TYPES = [
#     ('Car', 'سيارات'),
#     ('Electronic', 'الكترونيات'),
#     ('Computer', 'اجهزة تقنية'),
#     ('Hardware', 'قطع غيار تقنية'),
#     ('Printers', 'طابعات وماسحات'),
#     ('Office', 'مكتبية'),
#     ('Appliance', 'كهرومنزلية'),
#     ('Electrical', 'كهربائية'),
#     ('Equipment', 'معدات ورش'),
#     ('Furniture', 'اثاث'),
#     ('Cleaner', 'مواد تنظيف'),
#     ('Food', 'مواد اعاشة'),
#     ('Other', 'اخرى'),
# ]

class AssetCategory(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="اسم التصنيف")
    discription = models.CharField(max_length=255, blank=True, verbose_name="التفاصيل...")  # For Arabic or other descriptive names
    
    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "تصنيفات"
        ordering = ['name']

    def __str__(self):
        return self.name


# Asset Models:
class Asset(models.Model):
    category = models.ForeignKey('AssetCategory', on_delete=models.PROTECT, related_name='assets', blank=True, verbose_name="التصنيف")
    name = models.CharField(max_length=255, unique=True, verbose_name="اسم الصنف")
    brand = models.CharField(max_length=255, verbose_name="العلامة بالعربية", blank=True)
    brand_en = models.CharField(max_length=255, verbose_name="Brand in English", blank=True)
    pic = models.ImageField(upload_to=get_img_upload_path, blank=True, verbose_name="صورة الصنف")

    unit = models.CharField(max_length=50, choices=[
        ('piece', 'قطعة'),
        ('box', 'عبوة'),
        ('set', 'طقم'),
    ], verbose_name="وحدة القياس", default='piece')
    price_history = models.JSONField(default=list, verbose_name="تاريخ الأسعار")  # To store price history
    stock = models.PositiveIntegerField(default=0, verbose_name="الكمية بالمخزن")  # Current quantity in stock

    class Meta:
        verbose_name = "صنف"
        verbose_name_plural = "اصناف"
        ordering = ['category']

    def update_stock(self, quantity_change):
        """
        Update the quantity of this asset.
        If quantity_change is positive, it's an import; if negative, it's an export.
        """
        self.stock += quantity_change
        self.save()

    def add_price(self, price):
        # Convert the price to Decimal before appending
        self.price_history.append(price)
        self.save()

    def round_to_nearest_quarter(self, value):
        """Round a Decimal to the nearest .00, .25, .50, .75, or 1.00."""
        if value is None:
            return None
        
        return round(value * 4) / 4

    def average_price(self):
        if not self.price_history:
            return None
        # Convert all prices to Decimal to ensure precision
        avg_price = sum(map(Decimal, self.price_history)) / len(self.price_history)
        return self.round_to_nearest_quarter(avg_price)

    def median_price(self):
        if not self.price_history:
            return None
        sorted_prices = sorted(map(Decimal, self.price_history))
        mid = len(sorted_prices) // 2
        if len(sorted_prices) % 2 == 0:
            median_value = (sorted_prices[mid - 1] + sorted_prices[mid]) / 2
        else:
            median_value = sorted_prices[mid]
        
        return self.round_to_nearest_quarter(median_value)
    
    def __str__(self):
        return self.name


# Import Transaction Model:
class ImportRecord(models.Model):
    trans_id = models.AutoField(primary_key=True, verbose_name="رقم الاذن")
    company = models.ForeignKey('core.Company', on_delete=models.PROTECT, null=True, verbose_name="الشركة")
    date = models.DateField(verbose_name="تاريخ الاذن")
    assign_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="امر التكليف")
    assign_date = models.DateField(verbose_name="تاريخ التكليف")
    items = models.ManyToManyField(Asset, through='ImportItem', verbose_name="الاصناف") 
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    pdf_file = models.FileField(upload_to=get_pdf_upload_path, blank=True, verbose_name="مرفقات")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "اضن استلام"
        verbose_name_plural = "اذونات الاستلام"
        ordering = ['-date']

    def __str__(self):
        return f"Import {self.trans_id} - {self.date}"

    
# Import Transaction Items:
class ImportItem(models.Model):
    record = models.ForeignKey('ImportRecord', related_name='Importeditems', on_delete=models.CASCADE, verbose_name="رقم الاذن")
    asset = models.ForeignKey('Asset', related_name='ImportRecord', on_delete=models.PROTECT, verbose_name="الاصناف")
    quantity = models.PositiveIntegerField(verbose_name="الكمية")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر")
    created_at = models.DateTimeField(auto_now_add=True)
    return_id = models.IntegerField(blank=True, null=True)
    return_at = models.DateField(blank=True, null=True)
    return_purpose = models.CharField(max_length=50, choices=[
        ('Damaged', 'متضرر'),
        ('Replace', 'استبدال'),
    ], blank=True, null=True)
    return_notes = models.TextField(blank=True, null=True)


# Export Transaction Model:
class ExportRecord(models.Model):
    trans_id = models.AutoField(primary_key=True, verbose_name="رقم الاذن")
    date = models.DateField(verbose_name="تاريخ الاذن")
    export_type = models.CharField(max_length=50, choices=[
        ('Consume', 'استهلاك'),
        ('Personal', 'عهدة شخصية'),
        ('Department', 'عهدة ادارية'),
        ('Loan', 'اعارة'),
    ])
    # ContentType for dynamic ForeignKey
    entity_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    entity_id = models.PositiveIntegerField()
    entity_selection = GenericForeignKey('entity_type', 'entity_id')
    items = models.ManyToManyField(Asset, through='ExportItem', verbose_name="الاصناف") 
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "اذن صرف"
        verbose_name_plural = "اذونات الصرف"
        ordering = ['-date']

    def __str__(self):
        return f"Export {self.trans_id} - {self.date}"


# Export Transaction Items:
class ExportItem(models.Model):
    record = models.ForeignKey('ExportRecord', related_name='Exporteditems', on_delete=models.CASCADE, verbose_name="رقم الاذن")
    asset = models.ForeignKey('Asset', related_name='ExportRecord', on_delete=models.PROTECT, verbose_name="الاصناف")
    quantity = models.PositiveIntegerField(verbose_name="الكمية")
    sn = models.CharField(max_length=12, blank=True, null=True, verbose_name="الرقم التسلسلي")
    created_at = models.DateTimeField(auto_now_add=True)
    return_id = models.IntegerField(blank=True, null=True, verbose_name="رقم الاعادة")
    return_at = models.DateField(blank=True, null=True, verbose_name="تاريخ الاعادة")
    return_purpose = models.CharField(max_length=50, choices=[
    ('EndJob', 'انتهاء مدة'),
    ('Stolen', 'مسروق'),
    ('Dead', 'تالف'),
    ('Other', 'اخرى'),
    ], blank=True, null=True, verbose_name="سبب الاعادة")
    return_condition = models.CharField(max_length=50, choices=[
    ('Good', 'جيدة'),
    ('Bad', 'سيئة'),
    ], blank=True, null=True, verbose_name="الحالة")
    return_pic = models.ImageField(upload_to=get_img_upload_path, blank=True)
    return_pdf = models.FileField(upload_to=get_pdf_upload_path, blank=True)
    return_notes = models.TextField(blank=True, null=True)


# Report Committee Model
class Committee(models.Model):
    year = models.IntegerField(primary_key=True)
    president = models.ForeignKey('core.Employee', on_delete=models.PROTECT)
    members = models.ManyToManyField('core.Employee', related_name='committee_members')

    def __str__(self):
        return f"Committee for {self.year} - President: {self.president.name} - Members: {', '.join([m.name for m in self.members.all()])}"
