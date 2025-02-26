from django.contrib import admin
from .models import CustomUser, Friendship,FriendRequest

class CustomUserAdmin(admin.ModelAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'email_verified', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'is_staff')

admin.site.register(CustomUser, CustomUserAdmin)


class FriendshipAdmin(admin.ModelAdmin):
    model = Friendship
    list_display = ('user', 'friend', 'user_approved', 'friend_approved', 'created_at', 'updated_at')
    search_fields = ('user__username', 'friend__username')
    list_filter = ('user_approved', 'friend_approved', 'created_at')

admin.site.register(Friendship)
admin.site.register(FriendRequest)
