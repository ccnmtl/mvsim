from django.conf import settings
from django.http import (HttpResponseRedirect as redirect, 
                         HttpResponse,
                         HttpResponseForbidden as forbidden)
from djangohelpers.lib import allow_http, rendered_with
from main.models import Game, State, CourseSection, Configuration, UserInput
from engine.logic import get_notifications
from engine import logic
from engine import display_logic
import deform
import json
from urlparse import parse_qsl
from pkg_resources import resource_filename
from django.shortcuts import get_object_or_404

@allow_http("POST")
def clone_state(request, state_id):
    state = State.objects.get(id=state_id)
    config = Configuration.objects.get(pk=1)

    new_state = State(name=request.POST.get('state_name') or old_state.name)
    new_state.state = state.state
    new_state.save()
    return redirect(new_state.view_state_url())

@rendered_with("admin/view_state.html")
def view_state(request, state_id):
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

    # Deform's form.render API allows you to pass a readonly=True flag
    # to have deform render a readonly representation of the data;
    # but, the default readonly templates aren't form-like, they're just
    # unstyled lists which look really ugly in our layout.
    # So, instead, the mvsim django template receives the readonly flag, 
    # and, if it's set, removes Deform's javascript and injects some JS
    # to disable all the form fields on page load.  The result is prettier.
    if request.method == "GET":
        return {'form': form.render(state.loads()),
                'readonly': readonly,
                'state': state}

    if readonly:
        return forbidden()

    # trick from Chris Pyper, http://groups.google.com/group/pylons-discuss/browse_thread/thread/83b4f2950cbc1892?hl=en
    controls = parse_qsl(request.raw_post_data, keep_blank_values=True)
    try:
        appstruct = form.validate(controls)
    except deform.ValidationFailure, e:
        return {'form': e.render(),
                'readonly': readonly,
                'state': state}
    new_state = json.dumps(appstruct)
    state.state = new_state
    state.save()
    return redirect(".")

@rendered_with("admin/course_sections.html")
def admin_course_sections(request):
    if not request.user.is_superuser:
        return forbidden()
    sections = CourseSection.objects.all()
    return dict(sections=sections)

@rendered_with("admin/course_section.html")
def admin_course_section(request,section_id):
    if not request.user.is_superuser:
        return forbidden()
    section = get_object_or_404(CourseSection,id=section_id)
    return dict(section=section)
    
def associate_state(request,section_id):
    if not request.user.is_superuser:
        return forbidden()
    section = get_object_or_404(CourseSection,id=section_id)
    state = get_object_or_404(State,id=request.POST.get('state_id',''))
    section.starting_states.add(state)
    section.save()
    return redirect("/course_sections/%d/" % section.id)

def disassociate_state(request,section_id,state_id):
    if not request.user.is_superuser:
        return forbidden()
    section = get_object_or_404(CourseSection,id=section_id)
    state = get_object_or_404(State,id=state_id)
    section.starting_states.remove(state)
    section.save()
    return redirect("/course_sections/%d/" % section.id)


@rendered_with("home.html")
def home(request):
    sections = CourseSection.objects.filter(users=request.user, 
                                            course=request.course)
    try:
        section = sections[0]
    except IndexError:
        section = CourseSection.objects.filter(course=request.course)[0]
        section.users.add(request.user)
        section.save()
    try:
        starting_state_id  = section.starting_states.all()[0].id
    except:
        starting_state_id = None
    return {'starting_state_id': starting_state_id}

@rendered_with("games_index.html")
def games_index(request):
    sections = CourseSection.objects.filter(users=request.user, 
                                            course=request.course)
    try:
        section = sections[0]
    except IndexError:
        section = CourseSection.objects.filter(course=request.course)[0]
        section.users.add(request.user)
        section.save()

    if request.method == "POST":
        state = section.starting_states.get(
            id=request.POST['starting_state_id'])
        game = Game.initialize_from_state(
            user=request.user,
            configuration=Configuration.objects.get(pk=1),
            user_input=UserInput.objects.get(pk=1),
            course=request.course,
            starting_state=state)
        return redirect(game.show_game_url())

    games = Game.objects.filter(user=request.user,
                                course=request.course)
    return {'games': games, 'section': section}

def build_template_context(request, game, turn_number=None):
    if turn_number is not None:
        state = game.deserialize(game.get_state(turn_number))
    else:
        state = game.deserialize(game.current_state())
    
    variables, coefficients = state['variables'], state['coefficients']

    if '' in variables.owned_items: 
        variables.owned_items.remove('')
    if '' in variables.user_messages:
        variables.user_messages.remove('')
    
    people = list(logic.setup_people(variables, coefficients, None))
    
    display_vars = dict(game=game, 
                        state=variables, coeffs=coefficients,
                        people=people)
    display_vars = display_logic.add_extra_gameshow_context(display_vars)
    display_vars = display_logic.add_extra_seasonreport_context(display_vars)

    display_vars['user'] = request.user

    turn_number = turn_number or game.state_set.count()
    display_vars['turn'] = dict(number=turn_number)

    if turn_number > 1:
        previous_state = game.deserialize(game.get_state(turn_number-1))
        display_vars['notifications'] = get_notifications(
            previous_state['variables'], state['variables'], state['coefficients'],
            events_csv=settings.MVSIM_EVENTS_CSV)

    display_vars['FIXME'] = ''
    return display_vars
    
@allow_http("GET")
@rendered_with("game/game_over.html")
def game_over(request, game_id):
    sections = CourseSection.objects.filter(users=request.user, 
                                            course=request.course)
    try:
        section = sections[0]
    except IndexError:
        section = CourseSection.objects.filter(course=request.course)[0]
        section.users.add(request.user)
        section.save()
    try:
        starting_state_id  = section.starting_states.all()[0].id
    except:
        starting_state_id = None

    game = Game.objects.get(pk=game_id)
    if game.in_progress():
        return redirect(game.show_game_url())

    if not game.viewable(request):
        return forbidden()

    display_vars = build_template_context(request, game)
    display_vars['starting_state_id'] = starting_state_id
    return display_vars

@allow_http("GET")
@rendered_with("game/game_history_view.html")
def history(request, game_id):
    game = Game.objects.get(pk=game_id)

    if not game.viewable(request):
        return forbidden()

    sections = CourseSection.objects.filter(users=request.user, 
                                            course=request.course)
    try:
        section = sections[0]
    except IndexError:
        section = CourseSection.objects.filter(course=request.course)[0]
        section.users.add(request.user)
        section.save()
    try:
        starting_state_id  = section.starting_states.all()[0].id
    except:
        starting_state_id = None

    display_vars = build_template_context(request, game)
    display_vars['starting_state_id'] = starting_state_id
    return display_vars

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

    turn = game.get_state(int(turn_number))
    display_vars = build_template_context(request, game, turn_number)
    return display_vars

@allow_http("POST")
def submit_turn(request, game_id):
    game = Game.objects.get(pk=game_id)

    if not game.viewable(request):
        return forbidden()
    state = game.deserialize(game.current_state())
    variables, coefficients = state['variables'], state['coefficients']

    if '' in variables.owned_items: 
        variables.owned_items.remove('')
    if '' in variables.user_messages:
        variables.user_messages.remove('')

    from engine.simple_controller import adjust_submission
    kwargs = {}
    for key in request.POST:
        kwargs[key] = request.POST.get(key)
    kwargs = adjust_submission(kwargs, variables.names)

    user_submission = game.user_input.schema().deserialize(kwargs)

    for key in user_submission:        
        variables[key] = user_submission[key]
        
    from twisterclient import TwisterClient as TC
    tc = TC(base="http://twister.ccnmtl.columbia.edu/", chain=True)
    turn = logic.Turn(variables, coefficients, tc)
    alive, variables = turn.go()

    del variables.people
    import json
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

