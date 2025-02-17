from django.contrib import admin
from django.utils.html import mark_safe
from .models import Post, PostPicture

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("user", "id", "created", "updated", "views", "likes", "display_pictures")
    search_fields = ("id", "text")
    list_filter = ("created", "updated")
    
    def display_pictures(self, obj):
        pictures = obj.pictures.all()
        image_html = ""
        for picture in pictures:
            image_html += f'<img src="{picture.image.url}" width="100" height="100" style="margin: 5px;" />'
        return mark_safe(image_html)
    
    display_pictures.short_description = "Pictures"

@admin.register(PostPicture)
class PostPictureAdmin(admin.ModelAdmin):
    list_display = ("id", "image", "created_at", "updated_at")
