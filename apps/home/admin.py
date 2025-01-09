from django.contrib import admin
from .models import Websites, Blogs, Products, Words
# Register your models here.

class WebsitesAdmin(admin.ModelAdmin):
    list_display = ('seller_id', 'name')

class BlogsAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')

class ProductsAdmin(admin.ModelAdmin):
    list_display = ('name', 'categoryId')

class WordsAdmin(admin.ModelAdmin):
    list_display = ('name', 'name')



admin.site.register(Websites, WebsitesAdmin)
admin.site.register(Blogs, BlogsAdmin)
admin.site.register(Products, ProductsAdmin)
admin.site.register(Words, WordsAdmin)
