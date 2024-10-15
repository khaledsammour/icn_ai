from django.contrib import admin
from .models import Websites, Blogs
# Register your models here.

class WebsitesAdmin(admin.ModelAdmin):
    list_display = ('seller_id', 'name')

class BlogsAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')


admin.site.register(Websites, WebsitesAdmin)
admin.site.register(Blogs, BlogsAdmin)
