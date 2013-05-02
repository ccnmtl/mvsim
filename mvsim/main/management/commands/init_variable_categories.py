from django.core.management.base import BaseCommand
from mvsim.main.models import Category, Variable
from optparse import make_option
import csv


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--csv', dest='csv', help='Base CSV file to tile'),
    )

    def handle(self, *app_labels, **options):
        args = 'Usage: ./manage.py init_variable_categories --csv csv file'

        if not options.get('csv'):
            print args
            return

        fh = open(options.get('csv'), 'r')
        table = csv.reader(fh)

        #NAME,CATEGORY,TYPE,VALUE,CHOICES,DESCRIPTION
        header = table.next()

        for i in range(len(header)):
            if header[i] == 'NAME':
                name_idx = i
            if header[i] == 'CATEGORY':
                category_idx = i
            if header[i] == 'DESCRIPTION':
                description_idx = i

        rows = list(table)
        for row in rows:
            name = row[name_idx]
            try:
                variable = Variable.objects.get(name=name)
                category_name = row[category_idx]
                category, created = Category.objects.get_or_create(
                    name=category_name)
                variable.category = category
                variable.description = row[description_idx]
                variable.save()
            except Variable.DoesNotExist:
                print "%s not found. Skipping" % name
