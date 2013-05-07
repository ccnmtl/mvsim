#!/usr/bin/env python

import engine.stateless_logic as stateless_logic

from .person import Person
import engine.fuel as fuel

from .event import get_events
from .util import rand_n
from .village import Village


def get_notifications(before, after, coeffs, events_csv=None):
    """
    Takes two states, before and after, and static coeffs

    Returns events that should be reported
    """
    all_events = get_events(events_csv)
    true_events = []

    for event in all_events:
        if event.test(before, after, coeffs):
            true_events.append(event)
    return true_events


class Coeffs:
    """
    This is a non-persistent class that contains the set of coefficients
    loaded for a given game, with their values converted to python.

    It is built by the method Game.coeffs() in model.py, by loading each
    (persistent) ConfigurationCoefficient object associated with
    the game's (persistent) Configuration.

    It is built during the method Turn.execute() when the player submits
    a turn.  It's also built a bunch of times in controllers.py
    but I'm not sure why needs to happen.

    Since a game's Coefficients never change after the game starts,
    this object is not serialized back into the database when a turn
    ends.  Its attributes are held constant throughout the game, unless
    the underlying Configuration or its ConfigurationCoefficients are
    changed by an admin before the game ends.
    """

    def __json__(self):
        return self.__dict__


class State:
    """
    This is a non-persistent class that contains the set of coefficients
    loaded for a given game turn, with their values converted to python.

    It is built by the methods Turn.state() and Game.state() in model.py;
    they are called all over the place.

    After a turn is completed, the values of the attributes on this object
    will have changed, because a game's state changes throughout the game.
    So, when the turn has been processed, the attributes of this object
    are serialized back to the database.  That happens in Turn.execute()
    after the turn has been processed.
    """
    def __json__(self):
        return self.__dict__

    def __getitem__(self, item):
        return self.__dict__[item]

# ================


def setup_people(state, coeffs, tc):
    """ instantiate people objects from attribute lists """

    # Ugly, ugly, ugly...
    #
    # tracking the health for the last three turns
    # is particularly difficult because people can die
    # and be born which means we can't count on list
    # indices to be stable. So instead we do sort of a
    # poor man's dictionary by putting in Name|Health entries
    # and then here we reconstruct them back into proper
    # dictionaries. Ultimately, to really do this cleanly
    # I think we're going to need a dictionary data type
    # for variables/coefficients and the associated mechanisms
    # for serializing/deserializing them.

    health_t1_dict, health_t2_dict, health_t3_dict = dict(), dict(), dict()

    for (d, l) in [(health_t1_dict, state.health_t1),
                   (health_t2_dict, state.health_t2),
                   (health_t3_dict, state.health_t3)]:
        for e in l:
            (name, health) = e.split("|")
            d[name] = float(health)

    for (name, gender, age, health, education, sick, schooling_state,
         effort) in zip(state.names, state.genders, state.ages, state.health,
                        state.education, state.sick,
                        state.schooling_state, state.efforts):
        health_t1 = health_t1_dict.get(name, 100.0)
        health_t2 = health_t2_dict.get(name, 100.0)
        health_t3 = health_t3_dict.get(name, 100.0)
        if sick == " ":
            sick = ""  # see PMT:#61928

        # instead of storing everybody's pregnancy-state in a list,
        # we just store a global state.fatou_pregnant boolean
        pregnant = False
        if name == "Fatou" and state.fatou_pregnant:
            pregnant = True
        yield Person(name, gender, age, health, education, pregnant,
                     sick, schooling_state, health_t1, health_t2,
                     health_t3, effort, coeffs, tc)


def marshall_people(people, state):
    """ turn people list back to individual attribute lists """

    (state.names, state.genders, state.ages,
     state.health, state.education,
     state.sick, state.efforts,
     state.schooling_state) = (
         [p.name for p in people],
         [p.gender for p in people],
         [p.age for p in people],
         [p.health for p in people],
         [p.education for p in people],
         [p.sick != "" and p.sick or ' ' for p in people],  # see PMT:#61928
         [p.effort for p in people],
         [p.schooling_state for p in people])

    for p in people:
        if p.name == "Fatou":
            if p.pregnant:
                state.fatou_pregnant = True
            else:
                state.fatou_pregnant = False

    # see comment in setup_people()
    state.health_t1 = []
    state.health_t2 = []
    state.health_t3 = []
    for p in people:
        state.health_t1.append("%s|%f" % (p.name, p.health))
        state.health_t2.append("%s|%f" % (p.name, p.health_t1))
        state.health_t3.append("%s|%f" % (p.name, p.health_t2))
    return state


def new_child(tc, coeffs, state):
    if state.births < len(coeffs.child_names):
        name = coeffs.child_names[state.births]
    else:
        # start numbering the children
        name = "child%d" % (state.births + 1)
    if state.births < len(coeffs.child_genders):
        gender = coeffs.child_genders[state.births]
    else:
        # randomly pick one?
        gender = ['Male', 'Female'][tc.randint(a=0, b=1, n=1).values[0]]
    health = tc.randint(a=0, b=100, n=1).values[0]  # is this right?
    state.births += 1
    return Person(name=name, gender=gender, age=0, health=health,
                  education=0, pregnant=False, sick="",
                  schooling_state="under 5", health_t1=health,
                  health_t2=health, health_t3=health, coeffs=coeffs,
                  tc=tc)


class Turn:
    def __init__(self, state, coeffs, tc):
        self.state = state
        self.coeffs = coeffs
        self.tc = tc
        self.village = None

    def calc_maximum_effort(self):
        return sum([p.maximum_effort()
                    for p in self.state.people]) - self.calc_school_effort()

    def reset(self):
        self.state.expenditure = 0
        self.state.tons_to_market = 0
        self.state.income = 0
        self.state.initial_population = self.state.population
        self.state.total_effort = sum(self.state.efforts)
        self.state.fertilizer = False
        self.state.high_yield_seeds = False
        self.state.user_messages = []
        self.state.died = []
        self.state.died_reasons = []

    def message(self, m):
        self.state.user_messages.append(m)

    def is_game_over(self):
        return self.is_everyone_dead() or self.is_debt_too_high()

    def is_everyone_dead(self):
        if self.state.population < 1:
            return True
        return False

    def is_debt_too_high(self):
        if self.state.cash < -100:
            return True
        return False

    def go(self):

        """ run one turn of the simulation. """

        self.state.people = list(setup_people(self.state, self.coeffs,
                                              self.tc))
        self.village = Village(self.state, self.coeffs, self.tc)

        # only run if they're already alive
        if self.is_game_over():
            return (False, self.state)

        self.reset()

        # allocate calories
        if not self.state.subsistence_met:
            self.buy_food()

        # buy and sell goods in the village market
        self.sell_items()
        self.purchase_items()

        self.doctor()
        self.pregnancy()
        self.education()

        self.state.maximum_effort = self.calc_maximum_effort()

        self.check_sick()

        # village-wide updates
        self.village.buy_improvements()
        self.free_bednets()

        self.village.update_precipitation()
        self.check_drought()

        self.village.update_population()
        self.village.check_epidemic()

        self.update_population_count()
        self.update_yield()
        self.update_subsistence()

        self.check_final_health()

        # And now we'll figure out whether subsistence was met for
        # the *next* season.
        # We have to do this after check_final_health in case someone
        # died there
        if self.is_subsistence_met():
            self.state.subsistence_met = True
        else:
            self.state.subsistence_met = False

            if not self.cooker.was_sufficient:
                # TODO finer-grained messages about fuel usage
                # (e.g. if not enough propane, but was augmented
                # with collected wood to meet req.)
                if self.cooker.raw_leftovers == 0:
                    # TODO there's no user-facing message for this one
                    self.message("insufficient food")
                elif 'stove' in self.state.owned_items:
                    self.message("insufficient propane")
                else:
                    self.message("insufficient wood")

        self.state.maximum_effort = self.calc_maximum_effort()
        self.update_finances()

        self.age_people()
        self.increment_time()
        self.age_bednets()
        self.update_population_count()

        # update state with changes to people
        self.state = marshall_people(self.state.people, self.state)

        self.state.total_effort = sum(self.state.efforts)
        self.update_points()
        self.state.try_for_child = False
        self.village.update_subsidy_offers()
        self.state.food_to_buy = 0
        if self.is_game_over():
            return (False, self.state)
        return (True, self.state)

    def free_bednets(self):
        if not self.coeffs.enable_free_bednets or \
            self.state.year != (self.coeffs.starting_year
                                + self.coeffs.free_bednet_year):
            # this only happens in a specific year
            return

        num_bednets = len([elem for elem in self.state.owned_items
                           if elem == "bednet"])
        needed_bednets = self.state.population / 2

        if num_bednets < needed_bednets:
            self.message('NGO bednets')
            self.state.owned_items.extend(['bednet'] * needed_bednets)
            self.state.bednet_ages.extend([0] * needed_bednets)

    def sell_items(self):
        # front end gives us a list of "|" seperated item,quantity pairs
        # NOTE: no validation to make sure they have the items to sell
        try:
            # just take this opportunity to keep the list clean
            self.state.owned_items.remove('')
        except:
            pass

        real_sold_items = []
        for i in self.state.sell_items:
            if i == "":
                continue
            item, quantity = i.split("|")
            quantity = int(quantity)

            num_sold = 0
            for x in range(quantity):
                try:
                    self.state.owned_items.remove(item)
                    num_sold += 1
                except ValueError:
                    # trying to sell something we don't have
                    # or more than we have of that item
                    # eg, if they try to sell bednets on the
                    # turn that they've deteriorated and are now
                    # no longer in the owned_items
                    continue

            real_sold_items.append("%s|%s" % (item, num_sold))
            price = self.check_sell_price(item) * num_sold

            self.state.cash += price
            if item == "stove":
                self.state.stove = False
            if item == "improvedstove":
                self.state.improved_stove = False
            if item == "boat":
                self.state.boat = False
            if item == "dragnet":
                self.state.dragnet = False
        self.state.sell_items = real_sold_items

    def purchase_quantity_of_item(self, item, quantity, price):
        for x in range(int(quantity)):
            # some items only affect state, are not stored
            if item == "fertilizer":
                self.state.fertilizer = True
            elif item == "propane":
                self.state.amount_propane += 10  # 10kg propane per tank
            elif item == "high_yield_seeds":
                self.state.high_yield_seeds = True
            else:
                self.state.owned_items.append(item)

    def purchase_items(self):
        # pay for education first
        self.state.cash -= self.calc_school_cost()

        # front end gives us a list of "|" separated item,quantity pairs
        # NOTE: no validation to check if they have the money
        for i in self.state.purchase_items:
            if i == "":
                continue
            item, quantity = i.split("|")
            price = self.check_purchase_price(item) * int(quantity)
            self.state.cash -= price
            self.purchase_quantity_of_item(item, quantity, price)
            if item == "bednet":
                self.state.bednet_ages.extend([0] * int(quantity))
            if item == "stove":
                self.state.stove = True
            if item == "improvedstove" or item == "improved_stove":
                self.state.improved_stove = True
            if item == "boat":
                self.state.boat = True
            if item == "dragnet":
                self.state.dragnet = True

    def food_cost(self):
        cost = self.coeffs.food_cost
        if self.state.meals:
            # school meals raise maize prices by 20%
            # TODO: should probably be a coefficient
            cost *= 1.2
        self.state.calculated_food_cost = cost
        return cost

    def subsistence_cost(self):
        return self.calc_family_needs() / 100 * self.food_cost()

    def buy_food(self):
        cost = self.state.food_to_buy * self.food_cost()
        self.state.cash -= cost
        self.state.amount_calories = (self.state.amount_calories
                                      + (self.state.food_to_buy * 10 * 180.0))

    def check_purchase_price(self, item):
        prices = dict()
        for i, price in zip(self.coeffs.market_items,
                            self.coeffs.market_purchase_prices):
            prices[i] = price
        multiplier = 1.0
        if self.state.road:
            multiplier = 0.8
        return multiplier * prices[item]

    def check_sell_price(self, item):
        prices = dict()
        for i, price in zip(self.coeffs.market_items,
                            self.coeffs.market_sell_prices):
            prices[i] = price
        return prices[item]

    def update_points(self):
        """ calculate achievement points for the turn """

        X = 30.0
        F = 2.0

        # we don't actually keep track of what the initial village
        # population was after the first turn, so i'm hard-coding it at 1000
        # for now
        initial_num_families = 1000.0 / self.coeffs.avg_family_size

        D = (100.0 * X) / initial_num_families

        V = 1000000.0 / (self.village.raw_improvement_price('road') * 0.05)

        self.state.u_points += (
            (X * self.calc_family_total_health()) +
            (self.state.income) +
            (F * self.calc_new_improvements_value()) +
            (V * self.village.calc_new_improvements_value()) +
            (D * (self.state.village_births - self.state.village_deaths)))

        # don't let points go below 0
        self.state.u_points = int(max(self.state.u_points, 0))

    def calc_family_total_health(self):
        if len(self.state.people) == 0:
            return 0
        return float(sum([p.health for p in self.state.people]))

    def calc_family_avg_health(self):
        if len(self.state.people) == 0:
            return 0
        return (float(sum([p.health for p in self.state.people]))
                / float(len(self.state.people)))

    def calc_school_effort(self):
        """ number of hours family members spent in school """
        primary = len([p for p in self.state.people
                       if p.in_primary_school()])
        secondary = len([p for p in self.state.people
                         if p.in_secondary_school()])

        return (int(self.coeffs.primary_school_effort) * primary) + \
               (int(self.coeffs.secondary_school_effort) * secondary)

    def calc_school_cost(self):
        """ francs spent on education for children """
        n = len([p for p in self.state.people if p.in_secondary_school()])
        return n * self.coeffs.secondary_school_cost

    def family_improvements_count(self):
        """ count of how many family improvements have been made """
        improvements = ["bednet", "improved_stove", "stove", "boat", "dragnet"]
        return len([i for i in self.state.owned_items if i in improvements])

    def calc_new_improvements_value(self):
        value = 0
        for i in self.state.purchase_items:
            if i == "":
                continue
            item, quantity = i.split("|")
            price = self.check_purchase_price(item) * int(quantity)
            value += price
        return value

    def village_improvements_count(self):
        """ count of how many village improvements have been made """
        return self.village.improvements_count()

    def update_population_count(self):
        """ Ensure that the population count is correct """
        self.state.population = len(self.state.people)

    def doctor(self):
        for (p, doctor) in zip(self.state.people, self.state.doctor):
            if doctor:
                p.visit_doctor()
                cost = self.coeffs.doctor_visit_cost
                if self.state.clinic:
                    # doctor visits are 20% normal when there's a clinic
                    cost *= .2
                self.state.cash -= cost

    def get_mother(self):
        """ retrieve the "mother" """
        for p in self.state.people:
            if p.name == 'Fatou':
                return p

        # if we make it here, Fatou must be dead
        # return a NullPerson instead
        class NullPerson:
            pregnant = False

            def make_pregnant(self):
                pass
        return NullPerson()

    def pregnancy(self):
        if self.state.try_for_child:
            # make Fatou pregnant
            fatou = self.get_mother()
            fatou.make_pregnant()

    def education(self):
        for (p, enroll) in zip(self.state.people, self.state.enroll):
            p.update_schooling_state(enroll=enroll)
            p.update_education()

    def children(self):
        """ have children, if any """
        if self.state.try_for_child:
            return False
        fatou = self.get_mother()
        baby = None
        if fatou.pregnant:
            baby = new_child(self.tc, self.coeffs, self.state)
            self.message('child born')
            self.state.people.append(baby)
            fatou.pregnant = False

            # maternal mortality check
            maternal_mortality_probability = 5
            if self.state.clinic:
                maternal_mortality_probability = 1
            # do it as greater than 100 - probability instead of
            # < probability because of the way rand_n() is stubbed out
            # in the unit tests to always return the lowest value
            if self.rand_n(100) > (100 - maternal_mortality_probability):
                self.state.died.append(fatou.name)
                self.state.died_reasons.append("childbirth")
                self.state.deaths += 1
                self.state.people.remove(fatou)
        self.update_population_count()
        if baby is not None:
            return True
        return False

    def update_finances(self):
        """ calculate the family's finances """
        self.determine_income()
        family_income_and_interest = self.income_plus_interest(
            self.state.income)

        taxes = self.village.family_taxes(family_income_and_interest)

        self.state.cash = self.determine_cash(self.state.income,
                                              self.state.cash, taxes)

        self.village.collect_taxes(taxes)

    def income_plus_interest(self, income):
        return max(float((float(income)
                          * float(1.0 + self.coeffs.savings_rate))), 0.0)

    def determine_cash(self, income, cash, taxes):
        if income < 0:
            return cash + income
        else:
            return cash + self.income_plus_interest(income) - taxes

    def increment_time(self):
        if self.state.season:
            self.state.year += 1
            self.state.season = False
        else:
            self.state.season = True

    def age_people(self):
        # TODO: subtly broken for children born in the wrong season
        if self.state.season:
            for p in self.state.people:
                p.age += 1

    def age_bednets(self):
        if 'bednet' not in self.state.owned_items:
            self.state.bednet_ages = []
            return
        try:
            self.state.bednet_ages.remove('')
        except:
            pass
        # age them
        self.state.bednet_ages = [age + 1 for age in self.state.bednet_ages]
        # if any are more than 5 years (10 turns)
        # we eliminate them
        to_remove = []
        for age in self.state.bednet_ages:
            if age > 9:
                try:
                    self.state.owned_items.remove('bednet')
                except ValueError:
                    # something weird.
                    pass
                to_remove.append(age)
                self.message('bednet deteriorated')
        for age in to_remove:
            try:
                self.state.bednet_ages.remove(age)
            except ValueError:
                pass

    def check_drought(self):
        self.state.drought = False

        # if there's irrigation, we have no drought
        if self.state.irrigation:
            return

        # anything less than the threshold is considered a drought
        if self.state.precipitation < self.coeffs.drought_threshold:
            self.state.drought = True

    def rand_n(self, n):
        return rand_n(self.tc, n)

    def check_final_health(self):
        dead = []
        for person in self.state.people:
            if person.is_dead():
                dead.append(person)
                self.state.died.append(person.name)
                # TODO reason for death
                self.state.died_reasons.append('unknown')
        for d in dead:
            self.state.people.remove(d)
        self.state.deaths += len(dead)
        self.update_population_count()

    def check_sick(self):
        for p in self.state.people:
            p.check_sick(self.state)

    def update_yield(self):
        self.update_avg_productivity()
        self.update_amount_fish()
        self.update_soil_health()
        self.update_amount_maize()
        self.update_amount_cotton()
        self.update_amount_wood()
        self.update_amount_water()
        self.update_small_business_income()
        self.update_microfinance_bank()
        self.convert_calories()
        self.village.update_fish_stock()
        self.village.update_wood_stock()

    def t_boat(self):
        if self.state.boat:
            return self.coeffs.boat_coeff
        return 1.0

    def t_dragnet(self):
        if self.state.dragnet:
            return self.coeffs.dragnet_coeff
        return 1.0

    def t_fert(self):
        if self.state.fertilizer:
            return self.coeffs.fertilizer_coeff
        return 1.0

    def t_fert_cotton(self):
        if self.state.fertilizer:
            return self.coeffs.fertilizer_cotton_coeff
        return 1.0

    def t_irr(self):
        if self.state.irrigation:
            return self.coeffs.irrigation_coeff
        return 1.0

    def t_drought(self):
        # XXX TODO: fix tight coupling with check_drought()
        if self.state.drought:
            return self.coeffs.drought_coeff
        return 1.0

    def update_soil_health(self):
        """ updates the soil health depending on whether fertilizer
        has been used in the last three years """
        if self.state.fertilizer or self.state.fertilizer_t1 or \
                self.state.fertilizer_t2:
            self.state.soil_health = 1.0
        else:
            #self.message("Soil health is depleted.")
            self.state.soil_health = self.coeffs.soil_depletion

        if self.state.season:
            # once a year, rotate fertilizer history
            self.state.fertilizer_t2 = self.state.fertilizer_t1
            self.state.fertilizer_t1 = (self.state.fertilizer
                                        or self.state.fertilizer_last_turn)
        else:
            # it gets a little weird since we only care about the fertilizer
            # history per year, but it's a user option on each turn
            # so we use fertilizer_last_turn to fill in the gap
            self.state.fertilizer_last_turn = self.state.fertilizer

    def calc_amount_fish(self):
        assert self.state.effort_fishing >= 0
        assert self.coeffs.avg_fishing_yield >= 0
        assert self.state.avg_productivity >= 0
        assert self.t_boat() >= 0
        assert self.t_dragnet() >= 0
        assert self.state.fish_coeff >= 0
        return self.coeffs.fishing_effort_coeff * self.state.effort_fishing \
            * self.coeffs.avg_fishing_yield \
            * ((95.0 + self.rand_n(10)) / 100.0) \
            * self.state.avg_productivity * self.t_boat() \
            * self.t_dragnet() \
            * self.state.fish_coeff

    def update_amount_fish(self):
        self.update_fish_coeff()
        self.state.amount_fish = self.calc_amount_fish()
        if self.state.fishing_limit > 0:
            self.state.amount_fish = min(self.state.fishing_limit,
                                         self.state.amount_fish)

    def calc_wood_coeff(self):
        if self.state.wood_stock >= self.coeffs.wood_k / 2.0:
            return 1
        else:
            assert self.coeffs.wood_k != 0
            return self.state.wood_stock / self.coeffs.wood_k

    def update_wood_coeff(self):
        # TODO: does wood_coeff actually need to be a state variable?
        self.state.wood_coeff = self.calc_wood_coeff()

    def calc_fish_coeff(self):
        if self.state.fish_stock < 0:
            self.state.fish_stock = 0
        if self.state.fish_stock >= self.coeffs.fish_k / 2.0:
            return 1.0
        else:
            assert self.coeffs.fish_k != 0
            return self.state.fish_stock / self.coeffs.fish_k

    def update_fish_coeff(self):
        self.state.fish_coeff = self.calc_fish_coeff()

    def percent_maize(self):
        """ what percent of the family's fields are growing Maize """
        if len(self.state.crops) == 0:
            return 0
        n_maize = len([x for x in self.state.crops if x.lower() == 'maize'])
        return float(n_maize) / len(self.state.crops)

    def percent_cotton(self):
        """ what percent of the family's fields are growing Cotton """
        if len(self.state.crops) == 0:
            return 0
        n_cotton = len([x for x in self.state.crops if x.lower() == 'cotton'])
        return float(n_cotton) / len(self.state.crops)

    def t_high_yield_seeds(self):
        if self.state.high_yield_seeds:
            return self.coeffs.maize_high_yield_seeds_multiplier
        return 1.0

    def calc_amount_maize(self):
        assert self.coeffs.productivity_effort_coeff >= 0
        assert self.state.effort_farming >= 0
        assert self.coeffs.avg_maize_yield >= 0
        assert self.state.avg_productivity >= 0
        assert self.state.soil_health >= 0
        assert self.t_fert() >= 0
        assert self.t_irr() >= 0
        assert self.t_high_yield_seeds() >= 0
        assert self.percent_maize() >= 0 and self.percent_maize() <= 1.0
        return max(
            (
                (
                    (self.coeffs.productivity_effort_coeff
                     * self.state.effort_farming)
                    ** self.coeffs.maize_productivity_exponent)
                * self.coeffs.avg_maize_yield
                * ((95.0 + self.rand_n(10)) / 100.0)
                * self.state.avg_productivity
                * self.t_drought() * self.t_irr()
                * self.state.soil_health * self.t_fert()
                * self.t_high_yield_seeds()
                * self.percent_maize()),
            0.0)

    def calc_amount_cotton(self):
        return max(((self.coeffs.productivity_effort_coeff
                     * self.state.effort_farming)
                    ** self.coeffs.cotton_productivity_exponent)
                   * self.coeffs.avg_cotton_yield
                   * ((95.0 + self.rand_n(10)) / 100.0)
                   * self.state.avg_productivity
                   * self.state.soil_health * self.t_fert_cotton()
                   * self.t_drought() * self.t_irr()
                   * self.percent_cotton(),
                   0.0)

    def update_amount_cotton(self):
        self.state.amount_cotton = self.calc_amount_cotton()
        assert self.state.amount_cotton >= 0
        # update user messages
        if self.state.amount_cotton > 1:
            self.message('good cotton')

    def update_amount_maize(self):
        self.state.amount_maize = self.calc_amount_maize()
        assert self.state.amount_maize >= 0
        # update user messages
        if self.state.amount_maize > 0:
            if self.state.amount_maize < 1:
                self.message('poor maize')
        if self.state.amount_maize > 3:
            self.message('good maize')

    def calc_amount_wood(self):
        return self.coeffs.wood_effort_coeff * self.state.effort_fuel_wood \
            * self.coeffs.avg_wood_yield \
            * ((95.0 + self.rand_n(10)) / 100.0) \
            * self.state.avg_productivity * self.calc_wood_coeff()

    def update_amount_wood(self):
        self.state.amount_wood = self.calc_amount_wood()
        if self.state.wood_limit > 0 and \
                self.state.amount_wood > self.state.wood_limit:
            self.state.amount_wood = self.state.wood_limit
        assert self.state.amount_wood >= 0

    def calc_amount_water(self):
        return self.state.effort_water \
            * self.coeffs.avg_water_yield \
            * ((95.0 + self.rand_n(10)) / 100.0) \
            * self.calc_family_avg_health()

    def update_amount_water(self):
        self.state.amount_water = self.calc_amount_water()
        assert self.state.amount_water >= 0

    def calc_small_business_capital(self):
        return ((1 - self.coeffs.small_business_depreciation_rate)
                * self.state.small_business_capital
                + self.state.small_business_investment)

    def calc_small_business_income(self):
        # update capital, accounting for depreciation
        self.state.small_business_capital = self.calc_small_business_capital()
        self.state.cash -= self.state.small_business_investment

        assert self.state.effort_small_business >= 0
        assert self.state.small_business_capital >= 0

        return (self.coeffs.small_business_productivity_effect
                * (((self.state.avg_productivity
                     * self.state.effort_small_business)
                    ** self.coeffs.small_business_diminishing_return)
                   * (self.state.small_business_capital
                      ** (1 - self.coeffs.small_business_diminishing_return)))
                * (1 + (self.coeffs.small_business_road_effect
                        * self.state.road))
                * (1 + (self.coeffs.small_business_electricity_effect
                        * self.state.electricity))
                * (self.coeffs.small_business_drought_effect
                   * ((self.state.precipitation
                       / self.coeffs.avg_precipitation) ** 0.4))
                * (self.coeffs.small_business_epidemic_effect
                   * (1 - self.state.epidemic)))

    def update_small_business_income(self):
        self.state.small_business_income = self.calc_small_business_income()
        assert self.state.small_business_income >= 0

    def calc_microfinance_max_borrow(self):
        return self.subsistence_cost() + self.state.small_business_capital

    def pay_microfinance_bank(self):
        # first from family fund, then business capital, then carryover
        amount_due = self.state.microfinance_amount_due
        amount_paid = 0.0
        if self.state.cash >= amount_due:
            self.state.cash -= amount_due
            amount_paid += amount_due
        elif self.state.cash < 0:
            amount_paid = 0.0
        else:
            amount_paid = self.state.cash
            self.state.cash = 0

        remaining_due = amount_due - amount_paid
        if self.state.small_business_capital >= remaining_due:
            self.state.small_business_capital -= remaining_due
            amount_paid += remaining_due
        else:
            amount_paid += self.state.small_business_capital
            self.state.small_business_capital = 0

        self.state.microfinance_balance -= amount_paid

        # save carryovers if we couldn't pay it all
        self.state.microfinance_amount_paid = amount_paid
        self.state.microfinance_amount_due -= amount_paid

        if self.state.microfinance_balance < 0:
            self.state.microfinance_balance = 0.0

        return

    def calc_microfinance_balance(self):
        interest = (self.state.microfinance_balance
                    * self.state.microfinance_interest_rate / 100)

        self.state.microfinance_balance += interest
        payment_amount = (self.state.microfinance_borrow
                          / self.coeffs.microfinance_repay_period)

        # add any amount carried over from the previous turn
        if self.state.microfinance_balance > payment_amount:
            self.state.microfinance_amount_due += payment_amount + interest
        else:
            self.state.microfinance_amount_due += \
                self.state.microfinance_balance

        # now actually pay
        self.pay_microfinance_bank()
        return self.state.microfinance_balance

    def calc_microfinance_interest(self):
        return (self.coeffs.microfinance_base_interest
                * ((100.0 + self.rand_n(10)) / 100.0)
                + (self.coeffs.microfinance_drought_effect
                   * (self.state.precipitation
                      / self.coeffs.avg_precipitation))
                + (self.coeffs.microfinance_epidemic_effect
                   * self.state.epidemic))

    def update_microfinance_interest(self):
        self.state.microfinance_current_interest_rate = \
            self.calc_microfinance_interest()

    def update_microfinance_bank(self):
        self.state.microfinance_amount_paid = 0
        if self.state.microfinance_balance == 0:
            self.state.microfinance_amount_due = 0
            if self.state.microfinance_borrow > 0:
                # new loan
                if (self.state.microfinance_borrow
                        > self.state.microfinance_max_borrow):
                    self.state.microfinance_borrow = \
                        self.state.microfinance_max_borrow
                self.state.microfinance_balance = \
                    self.state.microfinance_borrow
                self.state.cash += self.state.microfinance_borrow
            self.state.microfinance_interest_rate = \
                self.state.microfinance_current_interest_rate
        else:
            self.state.microfinance_balance = self.calc_microfinance_balance()

        # update loan offer
        self.update_bank_offer()

    def update_bank_offer(self):
        # update loan offer
        self.state.microfinance_max_borrow =\
            self.calc_microfinance_max_borrow()
        self.update_microfinance_interest()

    def convert_calories(self):
        assert self.state.amount_maize >= 0
        assert self.state.amount_fish >= 0
        assert self.coeffs.maize_cal_coeff >= 0
        assert self.coeffs.fish_cal_coeff >= 0
        self.state.maize_cals = (self.state.amount_maize
                                 * self.coeffs.maize_cal_coeff)
        self.state.fish_cals = (self.state.amount_fish
                                * self.coeffs.fish_cal_coeff)
        assert self.state.maize_cals >= 0
        assert self.state.fish_cals >= 0

    @property
    def cooker(self):
        assert hasattr(self, '_cooker'), "You must first call new_cooker"
        return self._cooker

    def new_cooker(self):
        self._cooker = fuel.FuelSupply(self.coeffs, self.state)
        return self._cooker

    def calc_amount_calories(self):
        raw_food_cals = self.state.maize_cals + self.state.fish_cals
        cooker = self.new_cooker()
        cooked = cooker.convert(raw_food_cals)
        return cooked + self.school_meal_calories()

    def school_meal_calories(self):
        if not self.state.meals:
            return 0

        enrolled_children = len([p for p in self.state.people if
                                 p.schooling_state.startswith('enrolled')])
        return self.coeffs.school_meals_calories * enrolled_children

    def update_amount_calories(self):
        self.state.amount_calories = self.calc_amount_calories()

    def is_subsistence_met(self):
        return self.state.amount_calories >= self.calc_family_needs()

    def is_water_subsistence_met(self):
        return self.state.amount_water >= self.state.family_water_needs

    def calc_family_needs(self):
        return stateless_logic.family_food_requirements(
            self.state.population,
            self.coeffs.subsistence)

    def update_family_needs(self):
        self.state.family_needs = self.calc_family_needs()

    def calc_family_water_needs(self):
        return self.state.population * self.coeffs.w_subsistence

    def update_family_water_needs(self):
        self.state.family_water_needs = self.calc_family_water_needs()

    def update_subsistence(self):
        self.update_family_needs()
        self.update_family_water_needs()

        # first update family health based on stored food from last season
        if self.is_subsistence_met():
            for p in self.state.people:
                p.update_health(self.coeffs.subsistence,
                                self.state.clinic,
                                self.state.electricity)
        else:
            for p, daily_calories in zip(self.state.people,
                                         self.state.calorie_allocation):
                calories = daily_calories * 180
                p.update_health(calories, self.state.clinic,
                                self.state.electricity)

        # now that we've figured out whether we had enough food stored
        # for subsistence this *past* season, we need to have any new
        # children we're gonna have -- so that we can then figure out
        # whether we'll have enough food stored for subsistence *next*
        # season -- so that we can warn the player and give him a chance
        # to purchase extra needed food and/or allocate available calories
        new_children = self.children()
        if new_children:
            self.update_family_needs()
            self.update_family_water_needs()

        # now we'll update the stored calories
        # based on our newly farmed fish & grain
        self.update_amount_calories()

        self.state.food_to_sell = self.cooker.raw_leftovers

        propane_remaining = self.cooker.stock('propane')
        self.state.report_propane_used = (self.state.amount_propane
                                          - propane_remaining)
        self.state.amount_propane = propane_remaining

        self.state.wood_income = (self.coeffs.wood_price
                                  * self.cooker.stock('wood')
                                  * fuel.Wood.coefficient(self.coeffs))

        if not self.state.water_pump:
            if not self.is_water_subsistence_met():
                self.message("insufficient water")
                self.dehydrate()

    def starve(self):
        # multiply by 180 in order to reverse the transformation to
        # daily cals done in UI
        for (allocation, p) in zip(self.state.calorie_allocation,
                                   self.state.people):
            p.update_health(allocation * 180, self.state.clinic,
                            self.state.electricity)

    def dehydrate(self):
        for p in self.state.people:
            p.dehydrate(self.state.family_water_needs,
                        self.state.amount_water,
                        self.state.population)

    def num_infants(self):
        return len([p for p in self.state.people if p.is_infant()])

    def total_productivity(self):
        return sum([p.productivity() for p in self.state.people])

    def num_non_infants(self):
        return self.state.population - self.num_infants()

    def calc_avg_productivity(self):
        if self.num_non_infants() == 0:
            return 0.0
        if self.state.total_effort == 0:
            return 0.0
        s = 0.0
        for p in self.state.people:
            if p.is_infant():
                continue
            weighted = p.effort * p.productivity()
            s += weighted
        return (s / self.state.total_effort) / 100.0

    def update_avg_productivity(self):
        self.state.avg_productivity = self.calc_avg_productivity()

    def determine_income(self):
        self.state.income = 0
        self.state.tons_to_market = 0
        if self.state.food_to_sell > 0:
            (self.state.food_income, tons_food) = self.sell_food()
            self.state.income += self.state.food_income
        else:
            self.state.food_income = 0.0

        self.state.income += self.state.wood_income
        (cotton_income, tons_cotton) = self.sell_cotton()
        self.state.cotton_income = cotton_income
        self.state.income += cotton_income
        self.state.income += self.state.small_business_income
        self.state.tons_to_market = tons_cotton
        if (self.cost_of_wagon()) > 0 and (self.cost_of_wagon()
                                           > (self.state.income
                                              + self.state.cash)):
            # selling cotton would put them into debt because of
            # transport costs
            self.state.income -= cotton_income
            self.state.tons_to_market = 0
            self.state.cotton_income = 0
            self.message("transport too expensive")
        else:
            self.state.tons_to_market = tons_cotton
            self.state.expenditure = self.hire_wagon()
        self.state.income -= self.state.expenditure

    def transport_cost_per_ton(self):
        if self.state.road:
            return self.coeffs.transport_cost_road
        else:
            return self.coeffs.transport_cost_no_road

    def cost_of_wagon(self):
        return (self.state.tons_to_market * self.transport_cost_per_ton()
                * 100.0)

    def hire_wagon(self):
        cost_to_market = self.cost_of_wagon()
        self.state.cost_to_market = int(round(cost_to_market))
        return self.state.expenditure + cost_to_market

    def sell_food(self):
        totalToSell = (self.state.food_to_sell
                       * (self.coeffs.maize_export_units / 100.0))
        income = (totalToSell * self.coeffs.maize_price) / 1000.0
        if self.state.meals:
            # school meals raise prices by 20%
            income *= 1.20
        tons_to_market = totalToSell / 1000.0
        return (income, tons_to_market)

    def sell_cotton(self):
        total_to_sell = (self.state.amount_cotton
                         * (self.coeffs.cotton_export_units / 100.0))
        price = ((total_to_sell * self.coeffs.cotton_price) / 1000.0)
        tons_to_market = total_to_sell / 1000.0
        return (price, tons_to_market)
