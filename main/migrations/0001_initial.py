# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Variable'
        db.create_table('main_variable', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')(unique=True)),
            ('symbol', self.gf('django.db.models.fields.TextField')(unique=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('type', self.gf('django.db.models.fields.TextField')()),
            ('extra_type_information', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['Variable'])

        # Adding model 'Configuration'
        db.create_table('main_configuration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')(unique=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('main', ['Configuration'])

        # Adding M2M table for field coefficients on 'Configuration'
        db.create_table('main_configuration_coefficients', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('configuration', models.ForeignKey(orm['main.configuration'], null=False)),
            ('variable', models.ForeignKey(orm['main.variable'], null=False))
        ))
        db.create_unique('main_configuration_coefficients', ['configuration_id', 'variable_id'])

        # Adding M2M table for field variables on 'Configuration'
        db.create_table('main_configuration_variables', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('configuration', models.ForeignKey(orm['main.configuration'], null=False)),
            ('variable', models.ForeignKey(orm['main.variable'], null=False))
        ))
        db.create_unique('main_configuration_variables', ['configuration_id', 'variable_id'])

        # Adding model 'UserInput'
        db.create_table('main_userinput', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('main', ['UserInput'])

        # Adding M2M table for field variables on 'UserInput'
        db.create_table('main_userinput_variables', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userinput', models.ForeignKey(orm['main.userinput'], null=False)),
            ('variable', models.ForeignKey(orm['main.variable'], null=False))
        ))
        db.create_unique('main_userinput_variables', ['userinput_id', 'variable_id'])

        # Adding model 'Game'
        db.create_table('main_game', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('configuration', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Configuration'])),
            ('user_input', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.UserInput'])),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['courseaffils.Course'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='notstarted', max_length=100)),
        ))
        db.send_create_signal('main', ['Game'])

        # Adding model 'State'
        db.create_table('main_state', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('game', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Game'], null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('state', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('main', ['State'])

        # Adding model 'CourseSection'
        db.create_table('main_coursesection', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.TextField')()),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['courseaffils.Course'])),
        ))
        db.send_create_signal('main', ['CourseSection'])

        # Adding M2M table for field users on 'CourseSection'
        db.create_table('main_coursesection_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('coursesection', models.ForeignKey(orm['main.coursesection'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('main_coursesection_users', ['coursesection_id', 'user_id'])

        # Adding M2M table for field starting_states on 'CourseSection'
        db.create_table('main_coursesection_starting_states', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('coursesection', models.ForeignKey(orm['main.coursesection'], null=False)),
            ('state', models.ForeignKey(orm['main.state'], null=False))
        ))
        db.create_unique('main_coursesection_starting_states', ['coursesection_id', 'state_id'])


    def backwards(self, orm):
        
        # Deleting model 'Variable'
        db.delete_table('main_variable')

        # Deleting model 'Configuration'
        db.delete_table('main_configuration')

        # Removing M2M table for field coefficients on 'Configuration'
        db.delete_table('main_configuration_coefficients')

        # Removing M2M table for field variables on 'Configuration'
        db.delete_table('main_configuration_variables')

        # Deleting model 'UserInput'
        db.delete_table('main_userinput')

        # Removing M2M table for field variables on 'UserInput'
        db.delete_table('main_userinput_variables')

        # Deleting model 'Game'
        db.delete_table('main_game')

        # Deleting model 'State'
        db.delete_table('main_state')

        # Deleting model 'CourseSection'
        db.delete_table('main_coursesection')

        # Removing M2M table for field users on 'CourseSection'
        db.delete_table('main_coursesection_users')

        # Removing M2M table for field starting_states on 'CourseSection'
        db.delete_table('main_coursesection_starting_states')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'courseaffils.course': {
            'Meta': {'object_name': 'Course'},
            'faculty_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'faculty_of'", 'null': 'True', 'to': "orm['auth.Group']"}),
            'group': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.Group']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        'main.configuration': {
            'Meta': {'object_name': 'Configuration'},
            'coefficients': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'configurations_as_coefficient'", 'symmetrical': 'False', 'to': "orm['main.Variable']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'variables': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'configurations_as_variable'", 'symmetrical': 'False', 'to': "orm['main.Variable']"})
        },
        'main.coursesection': {
            'Meta': {'object_name': 'CourseSection'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['courseaffils.Course']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {}),
            'starting_states': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.State']", 'symmetrical': 'False'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'symmetrical': 'False'})
        },
        'main.game': {
            'Meta': {'object_name': 'Game'},
            'configuration': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Configuration']"}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['courseaffils.Course']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'notstarted'", 'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'user_input': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.UserInput']"})
        },
        'main.state': {
            'Meta': {'ordering': "['created']", 'object_name': 'State'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'game': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Game']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'state': ('django.db.models.fields.TextField', [], {})
        },
        'main.userinput': {
            'Meta': {'object_name': 'UserInput'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'variables': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['main.Variable']", 'symmetrical': 'False'})
        },
        'main.variable': {
            'Meta': {'object_name': 'Variable'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'extra_type_information': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'symbol': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'type': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['main']
