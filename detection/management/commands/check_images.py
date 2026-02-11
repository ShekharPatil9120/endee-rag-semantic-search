from django.core.management.base import BaseCommand

from detection.utils import process_latest_remote_image


class Command(BaseCommand):
    help = 'Check remote photos for new images and run detection'

    def handle(self, *args, **options):
        result = process_latest_remote_image()
        if result == 'no_new_image':
            self.stdout.write('No new image to process.')
        elif result == 'detected':
            self.stdout.write('New image processed and detection saved.')
        else:
            self.stdout.write('An error occurred during processing.')
