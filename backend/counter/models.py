from django.db import models


class Counter(models.Model):
    key = models.CharField(
        max_length=32, primary_key=True, default="main", editable=False
    )
    value = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
