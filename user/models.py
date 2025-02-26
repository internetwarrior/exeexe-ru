# C:\Users\user\Desktop\config\user\models.py
from django.contrib.auth.models import AbstractUser
from django.db import models




def user_profile_picture_path(instance, filename):
    return f"profile_pictures/{instance.username}/{filename}"

class CustomUser(AbstractUser):
    birthdate = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to=user_profile_picture_path, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    def get_username_by_user(self):
        return self.username

    def __str__(self):
        return self.username
    

class Friendship(models.Model):
    user = models.ForeignKey(CustomUser, related_name="friendship_set", on_delete=models.CASCADE)
    friend = models.ForeignKey(CustomUser, related_name="friends_set", on_delete=models.CASCADE)
    user_approved = models.BooleanField(default=True)  # Automatically approved for the user who sends the request
    friend_approved = models.BooleanField(default=False)  # Pending approval for the second user

    def __str__(self):
        return f"{self.user.username} - {self.friend.username}"

    class Meta:
        unique_together = ('user', 'friend')  # Ensure a unique friendship between the two users

    def save(self, *args, **kwargs):
        if self.user == self.friend:
            raise ValueError("User cannot be friends with themselves.")
        super().save(*args, **kwargs)

    def add_friend(self, user):
        """Adds a friend if the user is not already a friend and the friend has approved the request"""
        if self.user_approved and self.friend_approved:
            return
        Friendship.objects.create(user=self.user, friend=user, user_approved=True, friend_approved=False)
        
    def accept_friend(self):
        """Accepts the friendship from the second user"""
        self.friend_approved = True
        self.save()

class FriendRequest(models.Model):
    friendship = models.ForeignKey(Friendship, on_delete=models.CASCADE, related_name="requests")  # Changed to ForeignKey with CASCADE
    from_user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, related_name="sent_friend_requests")
    to_user = models.ForeignKey(CustomUser, on_delete=models.DO_NOTHING, related_name="received_friend_requests")
    status = models.BooleanField(null=True, default=None)  # None = Pending, True = Accepted, False = Rejected
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def can_create_new_request(self):
        from django.utils.timezone import now
        return (now() - self.updated_at).days >= 2


