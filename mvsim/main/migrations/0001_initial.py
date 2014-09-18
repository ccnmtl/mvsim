# flake8: noqa
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('courseaffils', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Configuration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CourseSection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('course', models.ForeignKey(to='courseaffils.Course')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(default=b'notstarted', max_length=100)),
                ('score', models.IntegerField(default=0)),
                ('name', models.CharField(default=b'', max_length=256, null=True, blank=True)),
                ('configuration', models.ForeignKey(to='main.Configuration')),
                ('course', models.ForeignKey(to='courseaffils.Course')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('visible', models.BooleanField(default=True)),
                ('state', models.TextField()),
                ('game', models.ForeignKey(blank=True, to='main.Game', null=True)),
            ],
            options={
                'ordering': ['created'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserInput',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Variable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(unique=True)),
                ('symbol', models.TextField(unique=True)),
                ('description', models.TextField(blank=True)),
                ('type', models.TextField(choices=[(b'int', b'Integer'), (b'float', b'Decimal'), (b'str', b'String'), (b'bool', b'Boolean'), (b'tuple', b'Data Collection'), (b'list', b'Sequence')])),
                ('extra_type_information', models.TextField(blank=True)),
                ('category', models.ForeignKey(blank=True, to='main.Category', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='userinput',
            name='variables',
            field=models.ManyToManyField(to='main.Variable'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='game',
            name='user_input',
            field=models.ForeignKey(to='main.UserInput'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='coursesection',
            name='starting_states',
            field=models.ManyToManyField(to='main.State'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='coursesection',
            name='users',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='configuration',
            name='coefficients',
            field=models.ManyToManyField(related_name=b'configurations_as_coefficient', to='main.Variable'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='configuration',
            name='variables',
            field=models.ManyToManyField(related_name=b'configurations_as_variable', to='main.Variable'),
            preserve_default=True,
        ),
    ]
