from django.core.management.base import BaseCommand, CommandError
from predictions.models import Betslip


class Command(BaseCommand):
    help = 'Saves all betslips that do not have a Success or Fail status'

    def handle(self, *args, **options):
        betslips_to_save = Betslip.objects.all().exclude(betslip_status='Success').exclude(betslip_status='Fail')
        cnt = betslips_to_save.count()
        counter = 0
        if cnt < 1:
            self.stdout.write('All betslips up to date')
        else:
            for b in betslips_to_save:
                b.save()
                counter += 1
                self.stdout.write('Successfully saved betslip "%s" of "%s"' % (counter, cnt))
