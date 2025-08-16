from django.core.management.base import BaseCommand
from users.models import GroupProfile

class Command(BaseCommand):
    help = 'Ensure all group creators are also admins of their groups.'

    def handle(self, *args, **options):
        updated = 0
        for group_profile in GroupProfile.objects.all():
            if group_profile.creator and not group_profile.admins.filter(pk=group_profile.creator.pk).exists():
                group_profile.admins.add(group_profile.creator)
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} group(s): creators added as admins.'))
