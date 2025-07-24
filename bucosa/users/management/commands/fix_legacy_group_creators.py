from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import GroupProfile

class Command(BaseCommand):
    help = 'Fixes legacy GroupProfile objects with missing creators by assigning them to a specified user.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username to assign as creator for legacy groups.')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        if not username:
            self.stderr.write(self.style.ERROR('You must provide a --username argument.'))
            return
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'User "{username}" does not exist.'))
            return
        legacy_groups = GroupProfile.objects.filter(creator__isnull=True)
        count = legacy_groups.count()
        for group in legacy_groups:
            group.creator = user
            group.save()
        self.stdout.write(self.style.SUCCESS(f'Fixed {count} legacy groups by assigning creator {username}.'))
