import datetime
from django.conf import settings
from django.http import (HttpResponse,
                         HttpResponseForbidden as forbidden)
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from djangohelpers.lib import allow_http, rendered_with
from mvsim.main.models import Game
import os
import os.path
import tempfile
from json import loads
import subprocess  # nosec


@allow_http("GET")
def graph_download(request, game_id):
    key = request.GET.get('filename', None)

    # rudimentary sanitization - keys are timestamps, so they should
    # be int'able
    try:
        int(key)
    except:
        raise Http404

    graph_dir = settings.MVSIM_GRAPH_OUTPUT_DIRECTORY
    path = os.path.join(graph_dir, "%s.png" % key)
    if not os.path.exists(path):
        raise Http404
    fp = open(path)
    try:
        data = fp.read()
    finally:
        fp.close()
    response = HttpResponse(data)
    response['Content-Disposition'] = (
        'attachment;filename="game_%s_graph.png"' % game_id)
    return response


@csrf_exempt
@allow_http("POST")
def graph_svg(request, game_id):
    json = request.POST['json']
    json = loads(json)
    output = ["""<svg xmlns="http://www.w3.org/2000/svg" """,
              """xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" """,
              """width="%s" height="%s" """ % ('640', '__GRAPH_HEIGHT__'),
              """xml:space="preserve"><desc>Created with Raphael</desc>""",
              """<defs></defs>"""]
    output.append("""<text x="%s" y="35" text-anchor="middle"
font-family="Arial" font-size="28" stroke="none" fill="#000"><tspan>
%s
</tspan></text>""" % ("320", request.POST['title'].strip()))

    output.append("""<text x="100" y="335" text-anchor="left"
font-family="Arial" font-size="18" stroke="none" fill="#000"><tspan>
X-axis: %s
</tspan></text>""" % request.POST['xAxis'].strip())

    for item in json:
        if item['type'] == "text":
            output.append("""<text x="%(x)s" y="%(y)s"
 text-anchor="%(text_anchor)s"
      font="%(font)s" stroke="%(stroke)s" fill="%(fill)s">
    <tspan>%(text)s</tspan>
</text>""" % {
                'x': item['x'] - 45,
                'y': int(item['y'] + 35),
                'text_anchor': item.get('text-anchor', "left"),
                'font': item['font'],
                'stroke': item['stroke'],
                'fill': item['fill'],
                'text': item['text'], })
        if item['type'] == "path":
            output.append("""<path fill="%(fill)s" stroke="%(stroke)s"
 d="%(path)s" opacity="%(opacity)s" stroke-width="%(swidth)s"
 transform="%(transform)s"></path>""" % {
                'fill': item['fill'],
                'stroke': item['stroke'],
                'path': item['path'],
                'opacity': item.get('opacity', 1),
                'transform': "translate(0,35)",
                'swidth': item.get('stroke-width', 1), })
        if item['type'] == "circle":
            if not item.get('fill', "").strip():
                continue
            output.append("""<circle cx="%(cx)s" cy="%(cy)s"
 stroke="%(stroke)s" fill="%(fill)s" r="%(radius)s"
 style="opacity: %(opacity)s; stroke-width: %(swidth)s;"
 opacity="%(opacity)s" stroke-width="%(swidth)s"></circle>""" % {
                'fill': item['fill'],
                'stroke': item['stroke'],
                'cx': item['cx'],
                'cy': int(item['cy']) + 35,
                'radius': item['r'],
                'opacity': item.get('opacity', 0),
                'swidth': item.get('stroke-width', 0), })

    vars = request.POST['vars']
    vars = loads(vars)
    y = 370
    x = 320
    for item in vars:
        var = item['text']
        color = item['color']
        opacity = item['opacity']
        output.append(
            """<text x="%s" y="%s" text-anchor="middle" font-size="14"
 font-family="Arial" stroke="%s" opacity="%s"
 fill="%s"><tspan>%s</tspan></text>"""
            % (x, y, color, str(opacity), color, var))
        y += 20

    output.append("</svg>")
    output = '\n'.join(output)
    # from the variable-legend loop above
    output = output.replace("__GRAPH_HEIGHT__", str(y))
    name = convert(output)

    return HttpResponse(name, content_type="text/plain")


def convert(svg_data):
    """ convert svg to png. takes svg data string, returns filename """
    output = svg_data

    tmpfd, tmpname = tempfile.mkstemp(suffix=".svg")
    tmp = os.fdopen(tmpfd, 'w')

    tmp.write(output)
    tmp.close()

    name = datetime.datetime.now().strftime("%s")

    graph_dir = settings.MVSIM_GRAPH_OUTPUT_DIRECTORY
    path = os.path.join(graph_dir, "%s.png" % name)

    try:
        subprocess.call(['convert', tmpname, path])  # nosec
    finally:
        os.unlink(tmpname)

    return name


class BoundVariable(object):
    def __init__(self, name, getter=None, descriptive_name=None, turns=None):
        self.name = name
        self.descriptive_name = (descriptive_name or
                                 name.replace("_", " ").title())
        self.values = []
        if turns is None:
            turns = []
        for turn in turns:
            if getter is None:
                self.values.append(
                    turn.variables[name])
            else:
                self.values.append(
                    getter(turn, name))


def percent_sickness_getter(turn, name):
    sick = turn.variables.sick
    names = turn.variables.names
    if len(names) == 0:
        return 0

    return 1.0 * sum(bool(str(i).strip()) for i in sick) / len(names)


def add_percent_sickness(variables, turns):
    variables.append(BoundVariable(
        "sick_percent", percent_sickness_getter,
        "Family Sick (% of family)", turns))
    return variables


# since sick is a compound variable, we want to split it apart
# into individual variables for each family member
def add_divided_sickness_getter(turn, name):
    sick = turn.variables.sick
    # name will be like health_kodjo
    person_name = name[len("sick_"):].title()
    names = turn.variables.names
    try:
        index = names.index(person_name)
    except ValueError:
        # this person was not yet born, or was dead, at this turn
        return 0
    return int(bool(str(sick[index]).strip()))


def add_divided_sickness(variables, turns):
    # we need to figure out all the people who were ever part of
    # the family
    all_names = {}
    for turn in turns:
        names = turn.variables.names
        for name in names:
            all_names[name] = "sick_" + name.lower()
    for name, var_name in all_names.items():
        variables.append(BoundVariable(
            var_name, add_divided_sickness_getter,
            "%s Sick" % name, turns))
    return variables


def add_average_health_getter(turn, name):
    health = turn.variables.health
    names = turn.variables.names
    if len(names) == 0:
        return 0
    return sum(health) / len(names)


def add_average_health(variables, turns):
    # since health is a compound variable, we want to split it apart
    # into individual variables for each family member
    variables.append(BoundVariable(
        "health_average", add_average_health_getter,
        "Average Family Health (%)", turns))
    return variables


def add_divided_health_getter(turn, name):
    health = turn.variables.health
    # name will be like health_kodjo
    person_name = name[len("health_"):].title()
    names = turn.variables.names
    try:
        index = names.index(person_name)
    except ValueError:
        # this person was not yet born, or was dead, at this turn
        return 0
    return health[index]


def add_divided_health(variables, turns):
    # since health is a compound variable, we want to split it apart
    # into individual variables for each family member

    # we need to figure out all the people who were ever part of
    # the family

    all_names = {}
    for turn in turns:
        names = turn.variables.names
        for name in names:
            all_names[name] = "health_" + name.lower()
    for name, var_name in all_names.items():
        variables.append(BoundVariable(
            var_name, add_divided_health_getter,
            "Health %s " % name + "(%)", turns))
    return variables


def add_divided_farming_getter(turn, name):
    total_effort = turn.variables.effort_farming
    plots = turn.variables.crops
    if name == "effort_farming_maize":
        amount = sum(1 for i in plots if i == "Maize")
    elif name == "effort_farming_cotton":
        amount = sum(1 for i in plots if i == "Cotton")
    amount = 1.0 * amount / len(plots)
    return total_effort * amount


def add_divided_farming(variables, turns):
    # in addition to effort_farming, we also want to calculate
    # separate variables for each turn's effort farming spent
    # on each of maize and cotton

    variables.append(BoundVariable(
        "effort_farming_maize", add_divided_farming_getter,
        "Effort Farming Maize (person-hours/day)", turns))
    variables.append(BoundVariable(
        "effort_farming_cotton", add_divided_farming_getter,
        "Effort Farming Cotton (person-hours/day)", turns))
    return variables


def getter(turn, name):
    value = turn.variables[name]
    return int(value)


def process_variable(variable, variables, turns):
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
        'year', )

    if variable.name in excluded_variables:
        return variables
    if variable.name == "health":
        variables = add_divided_health(variables, turns)
        variables = add_average_health(variables, turns)
        return variables
    if variable.name == "sick":
        variables = add_divided_sickness(variables, turns)
        variables = add_percent_sickness(variables, turns)
        return variables
    if variable.type == "bool":
        variables.append(BoundVariable(
            variable.name, getter,
            variable.description, turns))
        return variables
    if not variable.graphable():
        return variables
    variables.append(BoundVariable(
        variable.name,
        descriptive_name=variable.description, turns=turns))
    if variable.name == "effort_farming":
        variables = add_divided_farming(variables, turns)
    return variables


def extract_primary_layers(kw, key, primary_layers):
    for val in kw.getlist(key):
        primary_layers.append(val)
    return primary_layers


def extract_params(kw, key, params):
    for val in kw.getlist(key):
        params.setdefault(key, []).append(val)
    return params


def process_variables(all_variables, turns):
    variables = []

    for variable in all_variables:
        variables = process_variable(variable, variables, turns)
    return variables


@rendered_with("graphing/graph.html")
def graph(request, game_id):
    game = get_object_or_404(Game, id=game_id)

    if not game.viewable(request.user):
        return forbidden()

    turns = [game.deserialize(state) for state
             in game.state_set.order_by("created")]

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
            layer = key[:-1 * len("_label")]
            name = kw[key]
            layer_names[layer] = name
            continue

        if key == "primary":
            primary_layers = extract_primary_layers(kw, key, primary_layers)
            continue

        params = extract_params(kw, key, params)

    params = params or {"layer_1": []}
    primary_layers = sorted(primary_layers) or []

    all_variables = game.configuration.variables.all()
    variables = process_variables(all_variables, turns)

    return dict(game=game,
                params=params,
                variables=variables,
                primary_xaxis=primary_xaxis,
                secondary_xaxis=secondary_xaxis,
                primary_layers=primary_layers,
                layers=params,
                layer_names=layer_names,
                turns=turns)
