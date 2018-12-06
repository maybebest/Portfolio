from django.db import models
from django.contrib.postgres.fields import JSONField


class Transaction(models.Model):
    data = JSONField(blank=True, null=True)
