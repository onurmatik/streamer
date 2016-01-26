from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from streams.models import Stream


class Profile(models.Model):
    user = models.ForeignKey(User)
    streams = models.ManyToManyField(Stream, blank=True)
