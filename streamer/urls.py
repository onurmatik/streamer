from django.conf.urls import url
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

admin.site.site_header = _('Streamer')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]
