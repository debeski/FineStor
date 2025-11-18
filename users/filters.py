# Imports of the required python modules and libraries
######################################################
import django_filters
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, HTML
from django.db.models import Q
from .models import UserActivityLog

User = get_user_model()  # Use custom user model

class UserFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(
        method='filter_keyword',
        label='',
    )

    class Meta:
        model = User
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.form_class = 'form-inline'
        self.form.helper.form_show_labels = False
        self.form.helper.layout = Layout(
            Row(
                Column(Field('keyword', placeholder="البحث"), css_class='form-group col-auto flex-fill'),
                Column(HTML('<button type="submit" class="btn btn-secondary w-100"><i class="bi bi-search bi-font text-light me-2"></i>بحـــث</button>'), css_class='col-auto text-center'),
                Column(HTML('{% if request.GET and request.GET.keys|length > 1 %} <a href="{% url "manage_users" %}" class="btn btn-warning bi-font">clear</a> {% endif %}'), css_class='form-group col-auto text-center'),
                css_class='form-row'
            ),
        )

    def filter_keyword(self, queryset, name, value):
        """
        Filter the queryset by matching the keyword in username, email, phone, and occupation.
        """
        return queryset.filter(
            Q(username__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value) |
            Q(occupation__icontains=value) |
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value)
        )



class UserActivityLogFilter(django_filters.FilterSet):
    keyword = django_filters.CharFilter(
        method='filter_keyword',
        label='',
    )

    year = django_filters.ChoiceFilter(
        field_name="timestamp__year",
        lookup_expr="exact",
        choices=[],
        empty_label="السنة",
    )

    class Meta:
        model = UserActivityLog
        fields = {
            'timestamp': ['gte', 'lte'],
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Fetch distinct years dynamically
        years = UserActivityLog.objects.dates('timestamp', 'year').distinct()
        self.filters['year'].extra['choices'] = [(year.year, year.year) for year in years]

        self.filters['year'].field.widget.attrs.update({
            'onchange': 'this.form.submit();'
        })

        self.form.helper = FormHelper()
        self.form.helper.form_method = 'GET'
        self.form.helper.form_class = 'form-inline'
        self.form.helper.form_show_labels = False
        
        self.form.helper.layout = Layout(
            Row(
                Column(Field('keyword', placeholder="البحث"), css_class='form-group col-auto flex-fill'),
                Column(Field('year', placeholder="السنة", dir="rtl"), css_class='form-group col-auto'),
                Column(
                    Row(
                        Column(Field('timestamp__gte', css_class='flatpickr', placeholder="من "), css_class='col-6'),
                        Column(Field('timestamp__lte', css_class='flatpickr', placeholder="إلى "), css_class='col-6'),
                    ), 
                    css_class='col-auto flex-fill'
                ),
                Column(HTML('<button type="submit" class="btn btn-secondary w-100"><i class="bi bi-search bi-font text-light me-2"></i>بحـــث</button>'), css_class='col-auto text-center'),
                Column(HTML('{% if request.GET and request.GET.keys|length > 1 %} <a href="{% url "user_activity_log" %}" class="btn btn-warning bi-font">clear</a> {% endif %}'), css_class='form-group col-auto text-center'),
                css_class='form-row'
            ),
        )

    def filter_keyword(self, queryset, name, value):
        """
        Filter the queryset by matching the keyword in username, email, phone, and occupation.
        """
        return queryset.filter(
            Q(user__username__icontains=value) |
            Q(user__email__icontains=value) |
            Q(user__profile__phone__icontains=value) |
            Q(user__profile__occupation__icontains=value) |
            Q(action__icontains=value) |
            Q(model_name__icontains=value) |
            Q(number__icontains=value) |
            Q(ip_address__icontains=value)
        )



