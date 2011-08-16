from django.conf import settings
from django.http import HttpResponseRedirect as redirect, HttpResponse
from djangohelpers.lib import allow_http, rendered_with
from main.models import Game, State, CourseSection, Configuration, UserInput
from engine.logic import get_notifications
from engine import logic
from engine import display_logic
import deform

def view_state(request, state_id):
    state = State.objects.get(id=state_id)
    config = Configuration.objects.get(pk=1)
    schema = config.schema()
    form = deform.Form(schema, buttons=('submit',))
    return HttpResponse(form.render(state.loads(), readonly=True))

@rendered_with("home.html")
def home(request):
    return {}

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
        state = section.starting_states.get(id=request.POST['configuration_id'])
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
    game = Game.objects.get(pk=game_id)
    if game.in_progress():
        print game.show_game_url()
        return redirect(game.show_game_url())
    display_vars = build_template_context(request, game)
    return display_vars

@allow_http("GET")
@rendered_with("game/game_history_view.html")
def history(request, game_id):
    game = Game.objects.get(pk=game_id)
    display_vars = build_template_context(request, game)
    return display_vars

@allow_http("GET")
@rendered_with("game/game.html")
def show_turn(request, game_id):
    game = Game.objects.get(pk=game_id)
    if not game.in_progress():
        return redirect(game.game_over_url())
    display_vars = build_template_context(request, game)
    return display_vars

@allow_http("GET")
@rendered_with("game/view_turn_first_turn.html")
def view_turn_history_first_turn(request, game_id):
    game = Game.objects.get(pk=game_id)
    return {'game': game}

@allow_http("GET")
@rendered_with("game/view_turn.html")
def view_turn_history(request, game_id, turn_number):
    game = Game.objects.get(pk=game_id)
    turn_number = int(turn_number)
    if turn_number == 1:
        return view_turn_history_first_turn(request, game_id)

    turn = game.get_state(int(turn_number))
    display_vars = build_template_context(request, game, turn_number)
    return display_vars

@allow_http("POST")
def submit_turn(request, game_id):
    game = Game.objects.get(pk=game_id)
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

    return redirect(game.show_game_url())

