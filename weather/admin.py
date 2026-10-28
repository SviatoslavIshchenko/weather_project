from django.contrib import admin
from .models import SearchHistory


@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "city",
        "temperature",
        "description",
        "search_date",
    )

    list_filter = ("search_date", "city")
    search_fields = ("city", "user__username")
    ordering = ("-search_date",)
