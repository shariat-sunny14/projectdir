import os
import requests
from django.db import transaction
from datetime import datetime
from django.core.files.base import ContentFile
from .models import FacebookPost, FacebookSettings
from django.conf import settings

@transaction.atomic
def sync_facebook_posts():

    # ===== 1. GET SETTINGS =====
    settings_obj = FacebookSettings.objects.first()
    if not settings_obj:
        return "Facebook settings not configured."

    PAGE_ID = settings_obj.page_id
    ACCESS_TOKEN = settings_obj.access_token

    # ===== 2. DELETE OLD DATA + FILES =====
    old_posts = FacebookPost.objects.all()

    for post in old_posts:
        if post.image:
            post.image.delete(save=False)   # 🔥 delete file from storage

    old_posts.delete()  # 🔥 delete DB records

    # ===== 3. FETCH NEW DATA =====
    url = f"https://graph.facebook.com/v25.0/{PAGE_ID}/posts?fields=message,created_time,full_picture,permalink_url&access_token={ACCESS_TOKEN}"

    response = requests.get(url)
    data = response.json()

    posts = data.get("data", [])

    created_count = 0

    for post in posts:
        fb_id = post.get("id")

        created_time_str = post.get("created_time")
        created_time = datetime.strptime(created_time_str, "%Y-%m-%dT%H:%M:%S%z")

        image_url = post.get("full_picture")
        image_file = None

        # ===== 4. DOWNLOAD IMAGE =====
        if image_url:
            try:
                img_response = requests.get(image_url, timeout=10)
                if img_response.status_code == 200:
                    img_name = f"{fb_id}.jpg"
                    image_file = ContentFile(img_response.content, name=img_name)
            except Exception as e:
                print("Image download error:", e)

        # ===== 5. CREATE NEW POST =====
        FacebookPost.objects.create(
            fb_post_id=fb_id,
            message=post.get("message"),
            image=image_file,
            post_url=post.get("permalink_url"),
            created_time=created_time
        )

        created_count += 1

    return f"{created_count} posts synced successfully (old data cleared)."