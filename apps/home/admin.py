from django.contrib import admin
from .models import Websites
# Register your models here.

class WebsitesAdmin(admin.ModelAdmin):
    list_display = ('seller_id', 'name')


admin.site.register(Websites, WebsitesAdmin)
