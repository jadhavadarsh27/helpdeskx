from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'is_published', 'views', 'updated_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
