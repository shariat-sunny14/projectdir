from django.core.management.base import BaseCommand
from facebook_feed.tasks import sync_facebook_posts


class Command(BaseCommand):

    help = "Sync Facebook posts"

    def handle(self, *args, **kwargs):

        sync_facebook_posts()

        self.stdout.write(self.style.SUCCESS("Facebook posts synced successfully"))