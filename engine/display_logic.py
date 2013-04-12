import fuel
import simple_controller


def generate_disease_report(people):
    """
    Pass in a list of people.

    Returns a tuple (number_of_sick_people, sick_people_string)
    """
    sick_people = [person for person in people if person.sick]

    sick_people_string = []
    for person in sick_people:
        sick_person_string = []
        for disease in person.sick.split("+"):
            sick_person_string.append("%s has %s." % (person.name, disease))
        sick_people_string.append("".join(sick_person_string))
    sick_people_string = "\n".join(sick_people_string)

    return len(sick_people), sick_people_string


def add_extra_gameshow_context(context):
    # ------ display logic moved in from template -----
    extra_display_vars = dict(context)
    coeffs = context['coeffs']
    state = context['state']
    people = context['people']
    #turn = context['turn']

    items_to_sell = False
    for item, price in zip(coeffs.market_items, coeffs.market_sell_prices):
        if item in state.owned_items and price != 0:
            items_to_sell = True
    extra_display_vars['items_to_sell'] = items_to_sell

    # doctor visits are 20% if there's a clinic
    doctor_visit_cost = coeffs.doctor_visit_cost
    if state.clinic:
        doctor_visit_cost *= .2
    extra_display_vars['doctor_visit_cost'] = doctor_visit_cost

    # infections in the family
    extra_display_vars['n_sick_people'], \
        extra_display_vars['sick_people_string'] = \
        generate_disease_report(people)

    # malaria rate for village
    percent_infected = 0
    if state.village_population != 0:
        percent_infected = (state.village_infected_pop
                            / float(state.village_population) * 100)
    extra_display_vars['percent_infected'] = percent_infected

    # open this panel automatically on the first turn
    # and on any turn where subsistence is not met
    # see PMT http://pmt.ccnmtl.columbia.edu/item.pl?iid=42979
    family_food_class = "hs-init-hide"

    if not state.subsistence_met:
        family_food_class = ""
    extra_display_vars['family_food_class'] = family_food_class

    only_one_alive = False
    if state.population < 2:
        only_one_alive = True
    extra_display_vars['only_one_alive'] = only_one_alive

    calorie_needs_style = ""
    if not state.subsistence_met:
        calorie_needs_style = "display: none"
    extra_display_vars['calorie_needs_style'] = calorie_needs_style

    can_try_for_child = False
    for name, age in zip(state.names, state.ages):
        if name == 'Fatou':
            if age > 19 and age < 41:
                if 'Kodjo' in state.names:
                    if not state.fatou_pregnant:
                        can_try_for_child = True
    extra_display_vars['can_try_for_child'] = can_try_for_child

    extra_display_vars['maize_count'] = len([x for x in state.crops
                                             if x == 'Maize'])
    extra_display_vars['cotton_count'] = len([x for x in state.crops
                                              if x == 'Cotton'])

    extra_display_vars['num_bednets'] = len(
        [elem for elem in state.owned_items if elem == "bednet"])

    def adjust_price(price):
        # prices drop by 20% if there's a road
        if state.road:
            return int(0.8 * price)
        else:
            return price

    extra_display_vars['items_in_market'] = [
        (item, label, price, adjust_price(price))
        for (item, label, price)
        in zip(coeffs.market_items,
               coeffs.market_items_labels,
               coeffs.market_purchase_prices)
        if (item not in state.owned_items) or (item == 'bednet')]

    extra_display_vars['sellable_items'] = [
        (item, label, price,
         len([x for x in state.owned_items if x == item]))
        for (item, label, price)
        in zip(coeffs.market_items,
               coeffs.market_items_labels,
               coeffs.market_sell_prices)
        if item in state.owned_items and price != 0]

    def adjust_village_improvement_price_label(item, label, price):
        if item in state.subsidy_offers:
            price = int(round(price * coeffs.subsidy_price_reduction))
            label = label + " (subsidized)"
        return (item, label, price)

    extra_display_vars['available_village_improvements'] = [
        adjust_village_improvement_price_label(i, l, p) for (i, l, p)
        in zip(coeffs.available_improvements,
               coeffs.improvement_labels,
               coeffs.improvement_prices)]

    return extra_display_vars


def add_extra_seasonreport_context(context):
    context = dict(context)  # copy

    people = context['people']

    context['n_health_people'] = len(
        [person.name for person in people if person.health < 50])

    state = context['state']

    ngo_bednets_report = 'NGO bednets' in state.user_messages
    road_subs_report = 'road subsidy' in state.user_messages
    clinic_subs_report = 'clinic subsidy' in state.user_messages
    irrigation_subs_report = 'irrigation subsidy' in state.user_messages
    sanitation_subs_report = 'sanitation subsidy' in state.user_messages
    water_pump_report = 'water pump subsidy' in state.user_messages
    meals_subs_report = 'meals subsidy' in state.user_messages
    electric_subs_report = 'electricity subsidy' in state.user_messages
    good_rain_report = 'good rains' in state.user_messages

    has_subsidy = False
    if ngo_bednets_report or road_subs_report or clinic_subs_report or \
            irrigation_subs_report or sanitation_subs_report or \
            water_pump_report or meals_subs_report or electric_subs_report:
        has_subsidy = True

    village_goodnews_block = False
    if has_subsidy or good_rain_report:
        village_goodnews_block = True

    context['village_goodnews_block'] = village_goodnews_block
    context['village_badnews_block'] = village_badnews_block(state)
    context['has_subsidy'] = has_subsidy

    water_used = state.family_water_needs
    if water_used > state.amount_water:
        water_used = state.amount_water
    if state.water_pump:
        water_used = 0

    context['water_used'] = water_used

    coeffs = context['coeffs']

    wood_sold_energy = state.wood_income / coeffs.wood_price
    wood_sold_tons = wood_sold_energy / fuel.Wood.coefficient(coeffs)
    wood_used_tons = state.amount_wood - wood_sold_tons

    context['wood_sold_tons'] = wood_sold_tons
    context['wood_used_tons'] = wood_used_tons

    items_bought = []
    items_sold = []
    money_spent = 0
    money_earned = 0

    for item in state.purchase_items:
        if "|" not in item:
            continue
        (name, amount) = item.split("|")
        price = coeffs.market_purchase_prices[coeffs.market_items.index(name)]
        if state.road:
            price = int(0.8 * price)
        label = coeffs.market_items_labels[coeffs.market_items.index(name)]
        money_spent += float(price) * float(amount)
        items_bought.append("%s (%s)" % (label, amount))

    for item in state.sell_items:
        if "|" not in item:
            continue
        (name, amount) = item.split("|")
        price = coeffs.market_purchase_prices[coeffs.market_items.index(name)]
        if state.road:
            price = int(0.8 * price)
        label = coeffs.market_items_labels[coeffs.market_items.index(name)]
        money_earned += float(price) * float(amount)
        items_sold.append("%s (%s)" % (label, amount))

    context['money_earned'] = money_earned
    context['money_spent'] = money_spent

    # doctor visits are 20% if there's a clinic
    doctor_visit_cost = coeffs.doctor_visit_cost
    if state.clinic:
        doctor_visit_cost *= .2

    context['doctor_visit_cost'] = doctor_visit_cost
    context['items_bought'] = items_bought
    context['items_sold'] = items_sold

    context['village_improvements'] = list(village_improvements(
        coeffs.available_improvements,
        coeffs.improvement_labels,
        state.improvements))

    percent_infected = 0
    if state.village_population != 0:
        percent_infected = (state.village_infected_pop
                            / float(state.village_population) * 100)

    context['percent_infected'] = percent_infected

    if 'child born' in state.user_messages:
        context['new_baby'] = new_child_name(state.births, coeffs.child_names)

    context['foreststock'] = simple_controller.get_interval_class(
        state.wood_stock, coeffs.visual_intervals_forest)
    context['fishstock'] = simple_controller.get_interval_class(
        state.fish_stock, coeffs.visual_intervals_fish)

    context['money_report'] = simple_controller.money_report

    context['notifications'] = []

    return context


def new_child_name(births, child_names):
    if int(births) < len(child_names) + 1:
        return child_names[int(births) - 1]
    else:
        return "child%d" % int(births)


def village_improvements(available, labels, all_improvements):
    for item, label in zip(available, labels):
        if item in all_improvements:
            yield label


def village_badnews_block(state):
    fish_depletion_report = 'fish stock depletion' in state.user_messages
    wood_depletion_report = 'wood stock depletion' in state.user_messages

    if (state.drought or state.epidemic or fish_depletion_report
            or wood_depletion_report):
        return True
    else:
        return False
