from django.db import models

class FacebookSettings(models.Model):
    page_id = models.CharField(max_length=100)
    access_token = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for Page: {self.page_id}"


class FacebookPost(models.Model):
    fb_post_id = models.CharField(max_length=200, unique=True)
    message = models.TextField(blank=True, null=True)

    image = models.ImageField(upload_to='facebook_images/', blank=True, null=True)
    post_url = models.URLField(blank=True, null=True)
    created_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.fb_post_id