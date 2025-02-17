from django.contrib import admin
from django import forms
from .models import ChatRoom, Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.chat_room:
            participants = self.instance.chat_room.participants.all()
            self.fields['read_by'].queryset = participants
            self.fields['deleted_for'].queryset = participants

class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    filter_horizontal = ('participants',)

# class MessageAdmin(admin.ModelAdmin):
#     form = MessageForm
#     list_display = ('chat_room', 'sender', 'timestamp', 'content', 'is_deleted_for_all')
#     search_fields = ('content',)
#     list_filter = ('chat_room', 'sender', 'is_deleted_for_all')

admin.site.register(ChatRoom, ChatRoomAdmin)
admin.site.register(Message)
