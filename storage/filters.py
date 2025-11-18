import django_filters
from .models import Asset, AssetCategory
from django.db.models import Q

class AssetFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method='filter_search', label='Search')

    class Meta:
        model = Asset
        fields = []  # We don't need to list the individual fields here anymore

    def filter_search(self, queryset, name, value):
        # Combine filtering for name, brand, and brand_en
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(brand__icontains=value) |
                Q(brand_en__icontains=value)
            )
        return queryset