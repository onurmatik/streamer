from __future__ import unicode_literals

from django.db import models
from streams.models import Stream


class Instance(models.Model):
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=10)
    streams = models.ForeignKey(Stream)
