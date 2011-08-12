import colander
from django.db import models
from django.contrib.auth.models import User
import json

from collections import namedtuple
class NamedTuple(colander.Tuple):
    def __init__(self, *args, **kw):
        self.tuplename = kw.pop('tuplename', "NamedTuple")
        colander.Tuple.__init__(self, *args, **kw)

    def serialize(self, node, appstruct):
        if appstruct is colander.null:
            return colander.null
        def callback(subnode, subappstruct):
            return subnode.serialize(subappstruct)
        return self._impl(node, appstruct, callback)
    def deserialize(self, node, cstruct):
        if cstruct is colander.null:
            return colander.null
        def callback(subnode, subval):
            return subnode.deserialize(subval)
        value = self._validate(node, cstruct)
        error = None
        result = []
        names = []
        for num, subnode in enumerate(node.children):
            subval = value[num]
            try:
                result.append(callback(subnode, subval))
                names.append(subnode.name)
            except colander.Invalid, e:
                if error is None:
                    error = colander.Invalid(node)
                error.add(e, num)
                
        if error is not None:
            raise error

        typ = namedtuple(self.tuplename, " ".join(names))
        return typ(*result)

class AttrDict(dict):
    def __init__(self, *args, **kw):
        dict.__init__(self, *args, **kw)
        self.__dict__ = self
class Mapping(colander.Mapping):
    def _impl(self, node, value, callback):
        return AttrDict(colander.Mapping._impl(self, node, value, callback))

variable_types = (
    ('int', "Integer"),
    ('float', "Decimal"),
    ('str', "String"),
    ('bool', "Boolean"),
    ('tuple', "Data Collection"),
    ('list', "Sequence"),
    )

schema_node_factories = {
    'int': colander.Int,
    'float': colander.Float,
    'str': colander.String,
    'bool': colander.Boolean,
    'tuple': Mapping,
    'list': colander.Sequence,
    }

class Variable(models.Model):
    name = models.TextField(unique=True)
    symbol = models.TextField(unique=True)
    
    description = models.TextField(blank=True)

    type = models.TextField(choices=variable_types)
    extra_type_information = models.TextField(blank=True)

    def __unicode__(self):
        return self.name
    
    def graphable(self):
        return self.type in ("int", "float", "bool")
    def schema(self, required=True):
        type = schema_node_factories[self.type]
        kw = dict()

        info = (self.extra_type_information
                and json.loads(self.extra_type_information)
                or {})
        if 'choices' in info:
            choices = list(info['choices'])
            kw['validator'] = colander.OneOf(choices)

        missing = required if colander.required else colander.null
        schema = colander.SchemaNode(type(),
                                     name=self.name,
                                     missing=missing,
                                     **kw)

        if self.type == "list":
            list_element_type = info['listof']
            if list_element_type in schema_node_factories:
                list_element_type = schema_node_factories[list_element_type]
                list_element_type = colander.SchemaNode(list_element_type(),
                                                        missing=missing)
            else:
                list_element_type = Variable.objects.get(name=list_element_type)
                list_element_type = list_element_type.schema(required)
            schema.add(list_element_type)

        if self.type == "tuple":
            attributes = info['attributes']
            for attr_name, variable_name in attributes.items():
                variable = Variable.objects.get(name=variable_name)
                variable_schema = variable.schema(required)
                schema.add(variable_schema)

        return schema
        
class Configuration(models.Model):
    name = models.TextField(unique=True)

    description = models.TextField(blank=True)

    coefficients = models.ManyToManyField(Variable, related_name='configurations_as_coefficient')
    variables = models.ManyToManyField(Variable, related_name='configurations_as_variable')

    def schema(self, ignore_missing=False):
        coefficients = colander.SchemaNode(Mapping(), name="coefficients",
                                           ignore_missing_required=ignore_missing)
        variables = colander.SchemaNode(Mapping(), name="variables",
                                           ignore_missing_required=ignore_missing)

        for coefficient in self.coefficients.all():
            coefficients.add(coefficient.schema(ignore_missing))
        for variable in self.variables.all():
            variables.add(variable.schema(ignore_missing))

        schema = colander.SchemaNode(Mapping())
        schema.add(coefficients)
        schema.add(variables)

        return schema

class UserInput(models.Model):
    variables = models.ManyToManyField(Variable)

    def schema(self):
        variables = colander.SchemaNode(Mapping(), name="variables")

        for variable in self.variables.all():
            variables.add(variable.schema(required=False))

        return variables

class Game(models.Model):
    user = models.ForeignKey('auth.User')
    configuration = models.ForeignKey(Configuration)
    user_input = models.ForeignKey(UserInput)
    course = models.ForeignKey('courseaffils.Course')
    status = models.CharField(max_length=100, default="notstarted")

    def __unicode__(self):
        return "%s - in course %s" % (self.user, self.course)

    @classmethod
    def initialize_from_state(cls, starting_state, **kw):
        game = Game(**kw)
        game.save()
        new_state = State(game=game, state=starting_state.state)
        new_state.save()
        game.status = "inprogress"
        game.save()
        return game

    @models.permalink
    def show_game_url(self):
        return ('game_show', [self.pk], {})

    @models.permalink
    def game_over_url(self):
        return ('game_over', [self.pk], {})

    def current_state(self):
        return self.state_set.latest("created")

    def previous_state(self):
        return self.state_set.order_by("-created")[1]

    def deserialize(self, state):
        schema = self.configuration.schema()
        return schema.deserialize(state.loads())

    def in_progress(self):
        if self.status != "finished":
            return True

    def mark_finished(self):
        self.status = "finished"

    def created(self):
        """
        Return a DateTime for the first turn played (earliest State)
        """
        return self.state_set.order_by("created")[0].created

    def modified(self):
        """
        Return a DateTime for the most recent turn played (latest State)
        """
        return self.state_set.order_by("-created")[0].created

    def score(self):
        return self.deserialize(self.current_state()).variables.u_points

    def init(self, state):
        if self.state_set.count() > 0:
            raise RuntimeError("Game.initialize_from_state requires a new game with no states attached.")

        # Validate the state against this game's configuration interface;
        # let any validation errors bubble up and interrupt the call.
        self.deserialize(state)

        new_state = state.state

        state = State(state=new_state, game=self)
        state.save()

class State(models.Model):
    name = models.TextField(blank=True)
    game = models.ForeignKey(Game, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        if self.name: 
            return self.name

        number = 0
        for turn in self.game.state_set.all():
            number += 1
            if turn == self:
                break
        return self.name or "%s: turn %s" % (
            self.game, number)

    class Meta:
        ordering = ['created']

    state = models.TextField()

    def loads(self):
        return json.loads(self.state)

class CourseSection(models.Model):
    name = models.TextField()
    users = models.ManyToManyField('auth.User')
    starting_states = models.ManyToManyField(State)
    course = models.ForeignKey('courseaffils.Course')

    def __unicode__(self):
        return self.name

def ensure_section_exists(sender, instance, created, **kwargs):
    num_sections = CourseSection.objects.filter(
        course=instance).count()
    if num_sections > 0:
        return
    section = CourseSection(name="Default Section",
                            course=instance)
    section.save()

from courseaffils.models import Course
models.signals.post_save.connect(
    ensure_section_exists, sender=Course)

def get():
    return Game.objects.get(pk=1), State.objects.get(pk=1)
