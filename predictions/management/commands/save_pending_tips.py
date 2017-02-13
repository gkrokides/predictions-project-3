from django.core.management.base import BaseCommand, CommandError
from predictions.models import Tip


class Command(BaseCommand):
    help = 'Saves all tips that do not have a Success or Fail status'

    def handle(self, *args, **options):
        tips_to_save = Tip.objects.all().exclude(tip_status='Success').exclude(tip_status='Fail')
        cnt = tips_to_save.count()
        counter = 0
        if cnt < 1:
            self.stdout.write('All tips up to date')
        else:
            for tip in tips_to_save:
                tip.save()
                counter += 1
                self.stdout.write('Successfully saved tip "%s" of "%s"' % (counter, cnt))
