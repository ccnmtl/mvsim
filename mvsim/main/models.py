import colander
from django.db import models
from django.contrib.auth.models import User, Group
import json
from django.db.models.signals import post_save
from deform.widget import MappingWidget


def self_registered_user(sender, **kwargs):
    """ if a user self-registers, we automatically
    put them into the NON_CU group, so they get a
    Course affiliation """
    try:
        u = kwargs['instance']
        if u.is_anonymous():
            return
        if len(u.groups.all()) == 0:
            (g, created) = Group.objects.get_or_create(name="NON_CU")
            if created:
                # TODO also create the right course
                pass
            u.groups.add(g)
    except:
        pass
post_save.connect(self_registered_user, sender=User)

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
    ('list', "Sequence"), )

schema_node_factories = {
    'int': colander.Int,
    'float': colander.Float,
    'str': colander.String,
    'bool': colander.Boolean,
    'tuple': Mapping,
    'list': colander.Sequence, }


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name


class Variable(models.Model):
    name = models.TextField(unique=True)
    symbol = models.TextField(unique=True)
    description = models.TextField(blank=True)
    type = models.TextField(choices=variable_types)
    extra_type_information = models.TextField(blank=True)
    category = models.ForeignKey(Category, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def graphable(self):
        return self.type in ("int", "float", "bool")

    def schema(self, required=True, variable_type=None):
        type = schema_node_factories[self.type]
        kw = dict()

        info = (self.extra_type_information
                and json.loads(self.extra_type_information)
                or {})
        if 'choices' in info:
            choices = list(info['choices'])
            kw['validator'] = colander.OneOf(choices)

        kw['description'] = self.description
        kw['variable_type'] = variable_type

        if self.category:
            kw['category'] = self.category.name
        else:
            kw['category'] = 'Uncategorized'

        missing = required if colander.required else colander.null
        schema = colander.SchemaNode(type(),
                                     name=self.name,
                                     missing=missing,
                                     **kw)

        if self.type == "list":
            list_element_type = info['listof']
            if list_element_type in schema_node_factories:
                list_element_name = list_element_type
                list_element_type = schema_node_factories[list_element_type]
                list_element_type = colander.SchemaNode(list_element_type(),
                                                        name=list_element_name,
                                                        missing=missing)
            else:
                list_element_type = Variable.objects.get(
                    name=list_element_type)
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

    coefficients = models.ManyToManyField(
        Variable, related_name='configurations_as_coefficient')
    variables = models.ManyToManyField(
        Variable, related_name='configurations_as_variable')

    def schema(self, ignore_missing=False):
        coefficients = colander.SchemaNode(
            Mapping(), name="coefficients",
            ignore_missing_required=ignore_missing,
            widget=MappingWidget(item_template='mapping_variable'))
        variables = colander.SchemaNode(
            Mapping(), name="variables",
            ignore_missing_required=ignore_missing,
            widget=MappingWidget(item_template='mapping_variable'))

        for coefficient in self.coefficients.all():
            coefficients.add(coefficient.schema(ignore_missing, 'Coefficient'))

        for variable in self.variables.all():
            variables.add(variable.schema(ignore_missing, 'Variable'))

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


def high_scores(course=None, limit=10):
    games = []
    if course is not None:
        games = Game.objects.filter(
            status="finished",
            course=course, ).order_by("-score")
    else:
        games = Game.objects.filter(
            status="finished", ).order_by("-score")
    return games[:limit]


def user_scores(user):
    data = dict()
    games = Game.objects.filter(user=user, status="finished")
    data['user'] = user
    data['count'] = games.count()
    if games.count() == 0:
        # bail out now
        return data
    #  max/mean/min score | max/mean/min number of turns per game
    scores = [g.score for g in list(games)]
    data['max_score'] = max(scores)
    data['min_score'] = min(scores)
    data['mean_score'] = float(sum(scores)) / len(scores)

    turns = [g.state_set.count() for g in list(games)]
    data['max_turns'] = max(turns)
    data['min_turns'] = min(turns)
    data['mean_turns'] = float(sum(turns) / len(turns))

    return data


class Game(models.Model):
    user = models.ForeignKey('auth.User')
    configuration = models.ForeignKey(Configuration)
    user_input = models.ForeignKey(UserInput)
    course = models.ForeignKey('courseaffils.Course')
    status = models.CharField(max_length=100, default="notstarted")
    score = models.IntegerField(default=0)
    name = models.CharField(max_length=256, default="", blank=True, null=True)

    def __unicode__(self):
        if self.name:
            return self.name
        else:
            return "%s - in course %s [%d]" % (self.user, self.course, self.id)

    @classmethod
    def initialize_from_state(cls, starting_state, **kw):
        game = Game(**kw)
        game.save()
        new_state = State(game=game, state=starting_state.state)
        new_state.save()
        game.status = "inprogress"
        game.score = 0
        game.save()
        return game

    def viewable(self, request):
        return (self.user == request.user or
                request.user.is_staff or
                self.course.is_faculty(request.user)
                )

    def turns(self):
        return self.state_set.order_by("created")

    @models.permalink
    def show_game_url(self):
        return ('game_show', [self.pk], {})

    @models.permalink
    def delete_url(self):
        return ('game_delete', [self.pk], {})

    @models.permalink
    def game_history_url(self):
        return ('game_history', [self.pk], {})

    @models.permalink
    def game_over_url(self):
        return ('game_over', [self.pk], {})

    @models.permalink
    def graph_url(self):
        return ('game_graph', [self.pk], {})

    def current_state(self):
        return self.state_set.latest("created")

    def get_state(self, turn_number):
        return self.state_set.order_by("created")[turn_number - 1]

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

    def calculate_score(self):
        return self.deserialize(self.current_state()).variables.u_points

    def init(self, state):
        if self.state_set.count() > 0:
            raise RuntimeError(
                "Game.initialize_from_state requires "
                + "a new game with no states attached.")

        # Validate the state against this game's configuration interface;
        # let any validation errors bubble up and interrupt the call.
        self.deserialize(state)

        new_state = state.state

        state = State(state=new_state, game=self)
        state.save()

    def course_section(self, user=None):
        """ get the CourseSection associated with this game
        (via the CourseAffils.Course)

        filtering by user if one is specified.

        auto-vivify if necessary"""
        if user:
            sections = CourseSection.objects.filter(
                users=user,
                course=self.course)
            if sections.count() > 0:
                return sections[0]
            else:
                section = CourseSection.objects.filter(course=self.course)[0]
                section.users.add(user)
                section.save()
                return section
        else:
            return CourseSection.objects.filter(course=self.course)[0]


class State(models.Model):
    name = models.TextField(blank=True)
    game = models.ForeignKey(Game, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)

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

    @models.permalink
    def view_state_url(self):
        return ('view_state', [self.pk], {})

    def loads(self):
        return json.loads(self.state)


class CourseSection(models.Model):
    name = models.TextField()
    users = models.ManyToManyField('auth.User')
    starting_states = models.ManyToManyField(State)
    course = models.ForeignKey('courseaffils.Course')

    def __unicode__(self):
        return self.name

    def ensure_default_starting_state(self):
        if self.starting_states.all().count() == 0:
            s = State.objects.filter(name="Default Starting State")
            if s.count() > 0:
                self.starting_states.add(s[0])

    def available_states(self):
        state_ids = [s.id for s in self.starting_states.all()]
        return State.objects.all().exclude(name="").exclude(id__in=state_ids)

    def stats(self):
        for user in self.users.all():
            yield user_scores(user)


def ensure_section_exists(sender, instance, created, **kwargs):
    num_sections = CourseSection.objects.filter(
        course=instance).count()
    if num_sections > 0:
        return
    section = CourseSection(name="Default Section",
                            course=instance)
    # have to save before m2m relations work.
    # see: https://code.djangoproject.com/ticket/19580
    section.save()
    section.ensure_default_starting_state()
    section.save()

from courseaffils.models import Course
models.signals.post_save.connect(
    ensure_section_exists, sender=Course)
