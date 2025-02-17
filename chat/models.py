from django.db import models

# Create your models here.
import secrets
from django.db import models
from user.models import  CustomUser as User 

def generate_chat_name():
    return secrets.token_urlsafe(16)  # Generates a random URL-safe string

class ChatRoom(models.Model):
    name = models.CharField(max_length=32, unique=True, default=generate_chat_name, editable=False)
    participants = models.ManyToManyField(User, related_name="chatrooms")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.pk and self.participants.count() > 2:
            raise ValueError("A chat room can only have 2 participants.")
        super().save(*args, **kwargs)

    def add_participant(self, user):
        if self.participants.count() >= 2:
            raise ValueError("Chat room is full.")
        self.participants.add(user)


class Message(models.Model):
    chat_room = models.ForeignKey(ChatRoom, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read_by = models.ManyToManyField(User, related_name="read_messages", blank=True)
    deleted_for = models.ManyToManyField(User, related_name="deleted_messages", blank=True)  # Tracks who deleted the message
    is_deleted_for_all = models.BooleanField(default=False)  # If True, message is hidden for both participants

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"

    def mark_as_read(self, user):
        self.read_by.add(user)

    def delete_for_user(self, user):
        """Marks the message as deleted for a specific user."""
        if user in self.chat_room.participants.all():
            self.deleted_for.add(user)
            self.save()

    def delete_for_both(self):
        """Marks the message as deleted for both participants."""
        self.is_deleted_for_all = True
        self.save()

    def is_visible_to(self, user):
        """Checks if a message is visible to a user."""
        if self.is_deleted_for_all:
            return False
        return user not in self.deleted_for.all()

    def save(self, *args, **kwargs):
        # Check if the sender is a participant of the chat room
        if self.sender not in self.chat_room.participants.all():
            raise ValueError("Sender is not a participant in this chat room.")
        super().save(*args, **kwargs)
