from chainedrandom import ChainedRandom
from django.conf import settings
from django.http import HttpResponseRedirect as redirect, HttpResponse, \
    HttpResponseForbidden as forbidden
from django.shortcuts import get_object_or_404
from django_statsd.clients import statsd
from djangohelpers.lib import allow_http, rendered_with
from engine import display_logic, logic
from engine.logic import get_notifications
from mvsim.main.models import Game, State, CourseSection, Configuration, \
    UserInput, high_scores
from pkg_resources import resource_filename
from urlparse import parse_qsl
import deform
import json


@allow_http("POST")
def clone_state(request, state_id):
    if not request.user.is_superuser:
        return forbidden("Forbidden")

    state = State.objects.get(id=state_id)

    new_state = State(name=request.POST.get('state_name') or state.name)
    new_state.state = state.state
    new_state.visible = request.POST.get('visible', False) == "True"
    new_state.save()

    # Add new sections
    posted_sections = request.POST.getlist('associated_sections')
    for section_id in posted_sections:
        section = get_object_or_404(CourseSection, id=section_id)
        section.starting_states.add(new_state)
        section.save()

    return redirect(new_state.view_state_url())


@allow_http("POST")
def edit_state(request, state_id):
    if not request.user.is_superuser:
        return forbidden()

    state = State.objects.get(id=state_id)

    if 'visible' in request.POST:
        state.visible = request.POST.get('visible') == "True"
        state.save()

    posted_sections = request.POST.getlist('associated_sections')
    associated_sections = list(state.coursesection_set.all())

    # Add new sections
    for section_id in posted_sections:
        section = get_object_or_404(CourseSection, id=section_id)
        if section not in associated_sections:
            section.starting_states.add(state)
            section.save()

    # Remove sections as needed
    for section in associated_sections:
        if str(section.id) not in posted_sections:
            section.starting_states.remove(state)
            section.save()

    return redirect(state.view_state_url())


@rendered_with("admin/view_state.html")
def view_state(request, state_id):
    if not request.user.is_superuser:
        return forbidden()

    state = State.objects.get(id=state_id)
    config = Configuration.objects.get(pk=1)
    schema = config.schema()

    deform_templates = resource_filename('deform', 'templates')
    search_path = (settings.DEFORM_TEMPLATE_OVERRIDES, deform_templates)
    renderer = deform.ZPTRendererFactory(search_path)
    form = deform.Form(schema, buttons=('submit',), renderer=renderer)

    readonly = False
    if state.game:
        readonly = True

    available_sections = []
    if state.game:
        for section in state.game.course.coursesection_set.all():
            if section not in state.coursesection_set.all():
                available_sections.append(section)

    # Deform's form.render API allows you to pass a readonly=True flag
    # to have deform render a readonly representation of the data;
    # but, the default readonly templates aren't form-like, they're just
    # unstyled lists which look really ugly in our layout.
    # So, instead, the mvsim django template receives the readonly flag,
    # and, if it's set, removes Deform's javascript and injects some JS
    # to disable all the form fields on page load.  The result is prettier.
    if request.method == "GET":
        course = None
        if state.game:
            course = state.game.course
        return {'form': form.render(state.loads()),
                'readonly': readonly,
                'state': state,
                'course': course,
                'available_sections': available_sections,
                'saved': request.GET.get('msg', None)}

    if readonly:
        return forbidden()

    #else if request.method == "POST"
    controls = parse_qsl(request.raw_post_data, keep_blank_values=True)

    try:
        appstruct = form.validate(controls)
    except deform.ValidationFailure, e:
        course = None
        if state.game:
            course = state.game.course
        rv = {
            'form': e.render(),
            'readonly': readonly,
            'state': state,
            'course': course,
            'available_sections': available_sections}
        return rv

    new_state = json.dumps(appstruct)
    state.state = new_state
    state.save()
    url = "%s?msg=saved" % state.view_state_url()
    return redirect(url)


@rendered_with("admin/course_sections.html")
def admin_course_sections(request):
    if not request.user.is_superuser:
        return forbidden()

    sections = CourseSection.objects.all()
    states = State.objects.all().exclude(name="").order_by("name")
    return dict(sections=sections, all_states=states)


@rendered_with("admin/course_section.html")
def admin_course_section(request, section_id):
    if not request.user.is_superuser:
        return forbidden()
    section = get_object_or_404(CourseSection, id=section_id)
    states = State.objects.all().exclude(name="")

    users = []
    for u in section.users.all():
        users.append(u.get_full_name() if u.get_full_name() else u.username)

    return dict(section=section, all_states=states, users=sorted(users))


@rendered_with("admin/course_section_game_stats.html")
def course_section_game_stats(request, section_id):
    if not request.user.is_superuser:
        return forbidden()
    section = get_object_or_404(CourseSection, id=section_id)
    return dict(section=section)


def associate_state(request, section_id):
    if not request.user.is_superuser:
        return forbidden()

    section = get_object_or_404(CourseSection, id=section_id)

    posted_states = request.POST.getlist('associated_states')
    associated_states = list(section.starting_states.all())

    # Add new states
    for state_id in posted_states:
        state = get_object_or_404(State, id=state_id)
        if state not in associated_states:
            section.starting_states.add(state)
            section.save()

    # Remove sections as needed
    for state in associated_states:
        if str(state.id) not in posted_states:
            section.starting_states.remove(state)
            section.save()

    return redirect("/course_sections/%d/" % section.id)


@rendered_with("home.html")
def home(request):
    return dict(
        starting_state_id=None,
        sections=CourseSection.objects.filter(users=request.user))


@rendered_with("games_index.html")
def games_index(request, section_id):
    section = get_object_or_404(CourseSection, id=section_id)

    if request.method == "POST":
        state = section.starting_states.get(
            id=request.POST['starting_state_id'])
        game = Game.initialize_from_state(
            user=request.user,
            configuration=Configuration.objects.get(pk=1),
            user_input=UserInput.objects.get(pk=1),
            course=section.course,
            starting_state=state)
        return redirect(game.show_game_url())

    states = section.starting_states.all()
    if not request.user.is_superuser:
        states = states.exclude(visible=False)

    games = Game.objects.filter(user=request.user)
    return {'games': games,
            'section': section,
            'high_scores': high_scores(course=section.course),
            'starting_states': states}


def build_template_context(request, game, turn_number=None):
    if turn_number is not None:
        state = game.deserialize(game.get_state(turn_number))
    else:
        state = game.deserialize(game.current_state())

    variables, coefficients = state['variables'], state['coefficients']

    while '' in variables.owned_items:
        variables.owned_items.remove('')
    while '' in variables.user_messages:
        variables.user_messages.remove('')

    people = list(logic.setup_people(variables, coefficients, None))

    display_vars = dict(game=game, state=variables, coeffs=coefficients,
                        people=people)
    display_vars = display_logic.add_extra_gameshow_context(display_vars)
    display_vars = display_logic.add_extra_seasonreport_context(display_vars)

    display_vars['user'] = request.user

    turn_number = turn_number or game.state_set.count()
    display_vars['turn'] = dict(number=turn_number)

    if turn_number > 1:
        previous_state = game.deserialize(game.get_state(turn_number - 1))
        display_vars['notifications'] = get_notifications(
            previous_state['variables'], state['variables'],
            state['coefficients'], events_csv=settings.MVSIM_EVENTS_CSV)

    display_vars['FIXME'] = ''
    return display_vars


@allow_http("GET")
@rendered_with("game/game_over.html")
def game_over(request, game_id):
    statsd.incr("event.game_over")
    game = get_object_or_404(Game, id=game_id)
    if not game.viewable(request):
        return forbidden()

    section = game.course_section(user=request.user)
    starting_state_id = None
    if section.starting_states.all().count() > 0:
        starting_state_id = section.starting_states.all()[0].id

    if game.in_progress():
        return redirect(game.show_game_url())

    display_vars = build_template_context(request, game)
    display_vars['starting_state_id'] = starting_state_id
    display_vars['section'] = section
    return display_vars


@allow_http("GET")
@rendered_with("game/game_history_view.html")
def history(request, game_id):
    game = Game.objects.get(pk=game_id)

    if not game.viewable(request):
        return forbidden()

    section = game.course_section(user=request.user)
    starting_state_id = None
    if section.starting_states.all().count() > 0:
        starting_state_id = section.starting_states.all()[0].id

    display_vars = build_template_context(request, game)
    display_vars['starting_state_id'] = starting_state_id
    display_vars['section'] = section
    return display_vars


@allow_http("POST")
def delete_game(request, game_id):
    statsd.incr("event.delete_game")
    game = get_object_or_404(Game, pk=game_id)
    section = game.course_section()
    if not game.viewable(request):
        return forbidden()
    game.delete()
    return redirect("/section/%d/games/" % section.id)


@allow_http("GET")
def edit_game(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    if not game.viewable(request):
        return forbidden()
    game.name = request.GET.get('name', unicode(game))
    game.save()
    return HttpResponse("ok")


@allow_http("GET")
@rendered_with("game/game.html")
def show_turn(request, game_id):
    game = Game.objects.get(pk=game_id)

    if not game.viewable(request):
        return forbidden()

    if not game.in_progress():
        return redirect(game.game_over_url())
    display_vars = build_template_context(request, game)
    return display_vars


@allow_http("GET")
@rendered_with("game/view_turn_first_turn.html")
def view_turn_history_first_turn(request, game_id):
    game = Game.objects.get(pk=game_id)

    if not game.viewable(request):
        return forbidden()
    return {'game': game}


@allow_http("GET")
@rendered_with("game/view_turn.html")
def view_turn_history(request, game_id, turn_number):
    game = Game.objects.get(pk=game_id)

    if not game.viewable(request):
        return forbidden()
    turn_number = int(turn_number)
    if turn_number == 1:
        return view_turn_history_first_turn(request, game_id)

    display_vars = build_template_context(request, game, turn_number)
    return display_vars


@allow_http("POST")
def submit_turn(request, game_id):
    statsd.incr("event.play_turn")
    game = Game.objects.get(pk=game_id)

    if not game.viewable(request):
        return forbidden()
    state = game.deserialize(game.current_state())
    variables, coefficients = state['variables'], state['coefficients']

    while '' in variables.owned_items:
        variables.owned_items.remove('')
    while '' in variables.user_messages:
        variables.user_messages.remove('')

    from engine.simple_controller import adjust_submission
    kwargs = {}
    for key in request.POST:
        kwargs[key] = request.POST.get(key)
    kwargs = adjust_submission(kwargs, variables.names)

    user_submission = game.user_input.schema().deserialize(kwargs)

    for key in user_submission:
        variables[key] = user_submission[key]

    tc = ChainedRandom()
    turn = logic.Turn(variables, coefficients, tc)
    alive, variables = turn.go()

    del variables.people

    old_state = game.current_state()
    new_state = State(name=old_state.name, game=old_state.game)
    new_state.state = json.dumps(dict(
        variables=variables,
        coefficients=coefficients))
    new_state.save()

    if not alive:
        game.mark_finished()
        game.save()

    game.score = game.calculate_score()
    game.save()
    return redirect(game.show_game_url())
