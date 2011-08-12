from django.conf import settings
from django.http import HttpResponseRedirect as redirect, HttpResponse
from djangohelpers.lib import allow_http, rendered_with
from main.models import Game, State, CourseSection, Configuration, UserInput
from engine.logic import get_notifications
from engine import logic
from engine import display_logic

@rendered_with("graphing/graph.html")
def graph(request, game_id):
    game = Game.objects.get(pk=game_id)
    turns = [game.deserialize(state) for state in game.state_set.order_by("created")]

    params = {}
    
    primary_layers = []
    
    primary_xaxis = None
    secondary_xaxis = None
    
    layer_names = {}
    kw = request.GET
    for key in kw:
        if key == "primary_xaxis":
            primary_xaxis = kw['primary_xaxis']
            continue
        if key == "secondary_xaxis":
            secondary_xaxis = kw['secondary_xaxis']
            continue
            
        if key.endswith("_label"):
            layer = key[:-1*len("_label")]
            name = kw[key]
            layer_names[layer] = name
            continue

        if key == "primary":
            for val in kw.getlist(key):
                primary_layers.append(val)
            continue

        for val in kw.getlist(key):
            params.setdefault(key, []).append(val)

    params = params or {"layer_1": []}
    primary_layers = sorted(primary_layers) or []

    all_variables = game.configuration.variables.all()
    excluded_variables = (
        'calculated_food_cost',
        'cotton_yield',
        'energy_req',
        'fertilizer_last_turn',
        'fertilizer_t1',
        'fertilizer_t2',
        'fish_coeff',
        'food_yield',
        'initial_population',
        'market',
        'maximum_effort',
        'propane_fuel',
        'season',
        'try_for_child',
        'wood_coeff',
        'wood_fuel',
        'year',
        )
    class BoundVariable(object):
        def __init__(self, name, getter=None, descriptive_name=None):
            self.name = name
            self.descriptive_name = descriptive_name or name.replace("_", " ").title()
            self.values = []
            for turn in turns:
                if getter is None:
                    self.values.append(
                        turn.variables[name])
                else:
                    self.values.append(
                        getter(turn, name))
    variables = []
    def add_divided_farming():
        # in addition to effort_farming, we also want to calculate
        # separate variables for each turn's effort farming spent
        # on each of maize and cotton
        def getter(turn, name):
            total_effort = turn.variables.effort_farming
            plots = turn.variables.crops
            if name == "effort_farming_maize":
                amount = sum(1 for i in plots if i == "Maize")
            elif name == "effort_farming_cotton":
                amount = sum(1 for i in plots if i == "Cotton")
            amount = 1.0 * amount / len(plots)
            return total_effort * amount
    
        variables.append(BoundVariable("effort_farming_maize", getter, "Effort Farming Maize (person-hours/day)"))
        variables.append(BoundVariable("effort_farming_cotton", getter, "Effort Farming Cotton (person-hours/day)"))
    def add_divided_health():
        # since health is a compound variable, we want to split it apart
        # into individual variables for each family member
        def getter(turn, name):
            health = turn.variables.health
            person_name = name[len("health_"):].title() # name will be like health_kodjo
            names = turn.variables.names
            try:
                index = names.index(person_name)
            except ValueError:
                # this person was not yet born, or was dead, at this turn
                return 0 
            return health[index]
        # we need to figure out all the people who were ever part of the family
        all_names = {}
        for turn in turns:
            names = turn.variables.names
            for name in names:
                all_names[name] = "health_" + name.lower()
        for name, var_name in all_names.items():
            variables.append(BoundVariable(
                    var_name, getter, 
                    "Health %s " % name + "(%)"))
    def add_average_health():
        # since health is a compound variable, we want to split it apart
        # into individual variables for each family member
        def getter(turn, name):
            health = turn.variables.health
            names = turn.variables.names
            if len(names) == 0:
                return 0
            return sum(health) / len(names)
        variables.append(BoundVariable(
                "health_average", getter,
                "Average Family Health (%)"))
    
    def add_divided_sickness():
        # since sick is a compound variable, we want to split it apart
        # into individual variables for each family member
        def getter(turn, name):
            sick = turn.variables.sick
            person_name = name[len("sick_"):].title() # name will be like health_kodjo
            names = turn.variables.names
            try:
                index = names.index(person_name)
            except ValueError:
                # this person was not yet born, or was dead, at this turn
                return 0
            return int(bool(sick[index].strip()))
        # we need to figure out all the people who were ever part of the family
        all_names = {}
        for turn in turns:
            names = turn.variables.names
            for name in names:
                all_names[name] = "sick_" + name.lower()
        for name, var_name in all_names.items():
            variables.append(BoundVariable(
                    var_name, getter,
                    "%s Sick" % name))
    def add_percent_sickness():
        def getter(turn, name):
            sick = turn.variables.sick
            names = turn.variables.names
            if len(names) == 0:
                return 0
            return 1.0 * sum(bool(i.strip()) for i in sick) / len(names)
        variables.append(BoundVariable(
                "sick_percent", getter,
                "Family Sick (% of family)"))
    for variable in all_variables:
        if variable.name in excluded_variables:
            continue
        if variable.name == "health":
            add_divided_health()
            add_average_health()
            continue
        if variable.name == "sick":
            add_divided_sickness()
            add_percent_sickness()
            continue
        if variable.type == "bool":
            def getter(turn, name):
                value = turn.variables[name]
                return int(value)
            variables.append(BoundVariable(
                    variable.name, getter,
                    variable.description))
            continue
        if not variable.graphable():
            continue
        variables.append(BoundVariable(
                variable.name,
                descriptive_name=variable.description))
        if variable.name == "effort_farming":
            add_divided_farming()
    
    return dict(game=game,
                params=params,
                variables=variables,
                primary_xaxis=primary_xaxis,
                secondary_xaxis=secondary_xaxis,
                primary_layers=primary_layers,
                layers=params,
                layer_names=layer_names,
                turns=turns)
    
    
