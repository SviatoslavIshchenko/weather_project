
from django.contrib import admin
from django.urls import path, include
from weather import views as weather_views
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", weather_views.home, name="home"),
    path("history/", weather_views.history, name="history"),

    path(
        "history/delete/<int:search_id>/",
        weather_views.delete_search,
        name="delete_search"
    ),
    path(
        "history/clear/",
        weather_views.clear_history,
        name="clear_history"
    ),
    path("", include("accounts.urls")),

]
