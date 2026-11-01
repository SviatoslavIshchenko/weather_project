from django.db import models
from django.contrib.auth.models import User


class SearchHistory(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    city = models.CharField(max_length=100)

    temperature = models.FloatField()

    description = models.CharField(max_length=255)

    humidity = models.IntegerField(null=True, blank=True)

    feels_like = models.FloatField(null=True, blank=True)

    wind_speed = models.FloatField(null=True, blank=True)

    pressure = models.IntegerField(null=True, blank=True)

    search_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.city} - {self.user.username}"

