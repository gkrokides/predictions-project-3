from django.core.management.base import BaseCommand, CommandError
from predictions.models import Betslip


class Command(BaseCommand):
    help = 'Saves all betslips currently in the database'

    def handle(self, *args, **options):
        betslips_to_save = Betslip.objects.all()
        cnt = betslips_to_save.count()
        counter = 0
        for b in betslips_to_save:
            b.save()
            counter += 1
            self.stdout.write('Successfully saved betslip "%s" of "%s"' % (counter, cnt))
