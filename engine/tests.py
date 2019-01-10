import unittest

from engine.logic import Person, Village, Coeffs, State, setup_people, Turn
from engine.logic import rand_n, marshall_people, new_child
from engine.schooling import SchoolingFSM
from engine.display_logic import add_extra_seasonreport_context
from engine.simple_controller import force_integers


class StubTC:
    override = None

    def __init__(self):
        pass

    def rand_n(self, **kwargs):
        return 10

    def randint(self, a=0, b=10, n=1):
        class Res:
            def __init__(self, n):
                self.values = [n]

        if self.override is None:
            return Res(a)
        else:
            return Res(self.override)

# Since we don't want to have to change our tests every time
# a coefficient or state variable is changed, instead of using
# the regular State and Coeff objects which get populated from
# the database, we create stub versions here and set every
# coefficient and variable that the tests need.


class StubCoeffs:
    def __init__(self, **kwargs):
        for k, v in list(kwargs.items()):
            setattr(self, k, v)


class StubState:
    def __init__(self, **kwargs):
        for k, v in list(kwargs.items()):
            setattr(self, k, v)


# define magic numbers
PREGNANT_EFFORT = 1
ADULT_EFFORT = 2
CHILD_1_EFFORT = 5
CHILD_2_EFFORT = 4
CHILD_3_EFFORT = 3
PRIMARY_SCHOOL_EFFORT = 1
SECONDARY_SCHOOL_EFFORT = 2


class TestPerson(unittest.TestCase):
    def setUp(self):
        coeffs = StubCoeffs(pregnant_effort=PREGNANT_EFFORT,
                            adult_effort=ADULT_EFFORT,
                            child_1_effort=CHILD_1_EFFORT,
                            child_2_effort=CHILD_2_EFFORT,
                            child_3_effort=CHILD_3_EFFORT,
                            fuelwood_health_loss=10,
                            effort_too_high_health_loss=1,
                            disease_respiratory_health_factor=0.8,
                            disease_respiratory_youth_factor=0.2,
                            disease_waterborne_health_factor=0.8,
                            disease_waterborne_latrine_factor=0.2,
                            disease_waterborne_waterpump_factor=0.2,
                            disease_malaria_health_factor=0.2,
                            disease_malaria_bednet_factor=0.2,
                            disease_respiratory_propane_factor=1.5,
                            base_infection_rate=1,
                            precipitation_infection_modifier=0.2,
                            avg_precipitation=10,
                            bednet_infection_modifier=0.2,
                            disease_malaria_sir_factor=0.2,
                            chance_of_getting_the_flu=0,
                            )

        self.kodjo = Person(name="Kodjo", gender="Male", age=15, health=100,
                            education=12, pregnant=False, sick="",
                            schooling_state="adult", coeffs=coeffs,
                            tc=StubTC())
        self.kodjo.tc.override = 1

    def tearDown(self):
        self.kodjo = None

    def test_init(self):
        assert self.kodjo.name == "Kodjo"
        assert self.kodjo.age == 15
        assert not self.kodjo.sick

    def test_increment_decrement_health(self):
        self.kodjo.health = 100
        self.kodjo.decrement_health(50)
        assert self.kodjo.health == 50
        self.kodjo.increment_health(10)
        assert self.kodjo.health == 60
        self.kodjo.increment_health(50)
        assert self.kodjo.health == 100
        self.kodjo.decrement_health(0)
        assert self.kodjo.health == 100
        self.kodjo.decrement_health(200)
        assert self.kodjo.health == 0

        self.kodjo.health = 100

    def test_visit_doctor(self):
        self.kodjo.health = 50
        self.kodjo.sick = "pneumonia+malaria"

        self.kodjo.visit_doctor()
        assert not self.kodjo.sick
        assert self.kodjo.health == 75.0

        self.kodjo.health = 100
        self.kodjo.visit_doctor()
        assert not self.kodjo.sick
        assert self.kodjo.health == 100.0

    def test_starve(self):
        self.kodjo.health = 100
        self.kodjo.coeffs.subsistence = 500
        self.kodjo.starve(250)
        assert self.kodjo.health == 50.0
        self.kodjo.health = 100
        self.kodjo.starve(500)
        assert self.kodjo.health == 100.0

    def test_dehydrate(self):
        self.kodjo.health = 100
        family_water_needs = 100.0
        amount_water = 50.0
        population = 2.0
        self.kodjo.dehydrate(family_water_needs, amount_water, population)
        assert self.kodjo.health == 50.0
        self.kodjo.health = 100
        self.kodjo.dehydrate(family_water_needs, family_water_needs,
                             population)
        assert self.kodjo.health == 100.0
        self.kodjo.dehydrate(family_water_needs, family_water_needs, 0)

    def test_maximum_effort(self):

        assert self.kodjo.maximum_effort() == ADULT_EFFORT
        self.kodjo.pregnant = True
        assert self.kodjo.maximum_effort() == PREGNANT_EFFORT
        self.kodjo.pregnant = False
        self.kodjo.age = 1
        assert self.kodjo.maximum_effort() == CHILD_1_EFFORT
        self.kodjo.age = 5
        assert self.kodjo.maximum_effort() == CHILD_2_EFFORT
        self.kodjo.age = 10
        assert self.kodjo.maximum_effort() == CHILD_3_EFFORT
        self.kodjo.age = 15
        assert self.kodjo.maximum_effort() == ADULT_EFFORT

    def test_is_infant(self):
        assert self.kodjo.is_infant() is False
        self.kodjo.age = 5
        assert self.kodjo.is_infant() is False
        self.kodjo.age = 4
        assert self.kodjo.is_infant() is True
        self.kodjo.age = 15

    def test_productivity(self):
        self.kodjo.education = 24
        self.kodjo.health = 100
        assert self.kodjo.productivity() == 150
        # should drop proportionally to health
        self.kodjo.health = 50
        assert self.kodjo.productivity() == 75
        self.kodjo.health = 25
        assert self.kodjo.productivity() == 37.5
        # proportional to education
        self.kodjo.health = 100
        self.kodjo.education = 6
        assert self.kodjo.productivity() == 75
        # infants are not productive
        self.kodjo.age = 4
        assert self.kodjo.productivity() == 0
        # drops off with age over 50
        self.kodjo.age = 51
        self.kodjo.education = 24
        for (i, age) in enumerate(range(51, 75)):
            self.kodjo.age = age
            # convert to int since it eventually gets far enough out that
            # floating point conversions aren't reliable
            assert int(self.kodjo.productivity()) == int(.95 **
                                                         (i + 1) * 150.0)
        self.kodjo.age = 15

    def test_check_sick(self):
        state = StubState(epidemic=False,
                          stove=True,
                          improved_stove=False,
                          sanitation=True,
                          water_pump=True,
                          owned_items=[],
                          population=1,
                          village_infected_pop=0,
                          village_population=1000,
                          precipitation=10,
                          )
        self.kodjo.coeffs.resting_health_gain = 2
        self.kodjo.sick = ""
        self.kodjo.check_sick(state)
        assert not self.kodjo.sick, self.kodjo.sick
        self.kodjo.age = 4
        self.kodjo.check_sick(state)
        assert not self.kodjo.sick
        state.epidemic = True
        self.kodjo.coeffs.illness_chance_coeff = 0.0
        self.kodjo.check_sick(state)
        assert not self.kodjo.sick

        self.kodjo.health = 80.0
        self.kodjo.effort = 0
        self.kodjo.sick = ""
        self.kodjo.check_sick(state)
        assert not self.kodjo.sick

        self.kodjo.coeffs.illness_chance_coeff = 10000.0
        self.kodjo.health = 1.0
        self.kodjo.tc.override = 10
        self.kodjo.check_sick(state)
        assert self.kodjo.sick

    def test_update_schooling_state(self):
        self.kodjo.schooling_state = "adult"
        self.kodjo.update_schooling_state(False)
        assert self.kodjo.schooling_state == "adult"

    def test_update_education(self):
        self.kodjo.schooling_state = "adult"
        self.kodjo.education = 12
        self.kodjo.update_education()
        assert self.kodjo.education == 12
        self.kodjo.schooling_state = "under 5"
        self.kodjo.update_education()
        assert self.kodjo.education == 12
        self.kodjo.schooling_state = "enrolled in primary"
        self.kodjo.update_education()
        assert self.kodjo.education == 13

    def test_average_health_over_past_three_turns(self):
        assert self.kodjo.average_health_over_past_three_turns() == 100
        self.kodjo.health_t3 = 0.0
        assert self.kodjo.average_health_over_past_three_turns() == 200.0 / 3.0

    def test_make_pregnant(self):
        self.kodjo.make_pregnant()
        assert self.kodjo.pregnant is False
        self.kodjo.name = 'Fatou'
        self.kodjo.make_pregnant()
        assert self.kodjo.pregnant is False
        self.kodjo.age = 25
        self.kodjo.make_pregnant()
        assert self.kodjo.pregnant is True

    def test_is_dead(self):
        self.kodjo.coeffs.death_threshold_1 = 50
        self.kodjo.coeffs.death_threshold_2 = 60
        assert self.kodjo.is_dead() is False
        self.kodjo.health = 55
        self.kodjo.health_t1 = 5
        self.kodjo.health_t2 = 5
        assert self.kodjo.is_dead() is True

# more magic numbers

VILLAGE_POPULATION = 500
BIRTH_RATE = 2
DEATH_RATE = 2
POPULATION = 1
PRECIPITATION = 1


class TestVillage(unittest.TestCase):
    def setUp(self):
        coeffs = StubCoeffs(birth_rate=BIRTH_RATE, death_rate=DEATH_RATE,
                            starting_year=2007,
                            avg_family_size=4,
                            recovery_rate0=1.0,
                            recovery_rate1=1.0,
                            recovery_rate2=1.0,
                            recovery_rate3=1.0,
                            mortality0=1.0,
                            mortality1=1.0,
                            base_infection_rate=1.0,
                            mortality2=1,
                            bednet_infection_modifier=1.0,
                            precipitation_infection_modifier=0,
                            avg_precipitation=200,
                            enable_NGO_offers=True,
                            road_subsidy_year=5,
                            other_subsidy_year=10,
                            enable_epidemic=True,
                            no_epidemics_before=10,
                            enable_free_bednets=True,
                            free_bednet_year=30,
                            fish_stock_warn_threshold=0.33,
                            wood_stock_warn_threshold=0.33,
                            available_improvements=['a', 'b'],
                            microfinance_base_interest=0.02,
                            microfinance_min_balance=100.0,
                            microfinance_repay_period=8,
                            microfinance_drought_effect=1,
                            microfinance_epidemic_effect=1,
                            max_precipitation=10,
                            drought_threshold=1,
                            enable_drought=True,
                            no_droughts_before=5,
                            )
        state = StubState(village_population=VILLAGE_POPULATION,
                          population=POPULATION,
                          clinic=False, irrigation=False, road=False,
                          sanitation=False, water_pump=False,
                          meals=False, electricity=False,
                          precipitation=PRECIPITATION,
                          health=[100],
                          year=2007,
                          season=False,
                          village_infected_pop=0,
                          owned_items=['bednet'],
                          epidemic=False,
                          tax_rate=0,
                          user_messages=[],
                          subsidy_offers=[],
                          microfinance_balance=0.0,
                          microfinance_borrow=0.0,
                          microfinance_current_interest_rate=0.0,
                          microfinance_interest_rate=0.0,
                          microfinance_amount_due=0.0,
                          microfinance_amount_paid=0.0,
                          microfinance_max_borrow=0.0,
                          )
        tc = StubTC()
        self.village = Village(state, coeffs, tc)

    def tearDown(self):
        self.village = None

    def test_update_population(self):
        self.village.update_population()
        print(self.village.state.village_population)
        assert self.village.state.village_population == VILLAGE_POPULATION

    def test_check_epidemic(self):
        self.village.check_epidemic()
        assert not self.village.state.epidemic
        self.village.state.village_infected_pop = 5.0
        self.village.state.village_population = 10.0
        self.village.check_epidemic()
        assert self.village.state.epidemic

    def test_avg_family_health(self):
        assert self.village.avg_family_health() == 100

    def test_village_health(self):
        assert self.village.village_health() == 1.0

    def test_family_bednets(self):
        assert self.village.family_bednets() == 1

    def test_bednet_modifier(self):
        assert self.village.bednet_modifier() == 2
        self.village.state.population = 0
        assert self.village.bednet_modifier() == 0

    def test_mortality(self):
        print(self.village.mortality())
        assert self.village.mortality() == 2.0

    def test_recovery_rate(self):
        assert self.village.recovery_rate() == 1

    def test_susceptible_pop(self):
        assert (self.village.susceptible_pop() ==
                self.village.state.village_population)

    def test_recovered(self):
        assert self.village.recovered() == 0

    def test_sickened(self):
        assert self.village.sickened() == 0

    def test_improvements_count(self):
        assert self.village.improvements_count() == 0

    def test_family_taxes(self):
        self.village.state.tax_rate = 10
        self.village.state.fund = 0
        assert self.village.family_taxes(100.0) == 10
        self.village.state.tax_rate = 0
        assert self.village.family_taxes(100.0) == 0

    def test_check_improvement_price(self):
        self.village.coeffs.available_improvements = ['a', 'b']
        self.village.coeffs.improvement_prices = [1, 2]
        assert self.village.check_improvement_price('a') == 1
        assert self.village.check_improvement_price('b') == 2

    def test_buy_improvements(self):
        self.village.coeffs.available_improvements = ['a', 'b']
        self.village.coeffs.improvement_prices = [1, 200]
        self.village.coeffs.subsidy_price_reduction = 1
        self.village.state.fund = 100
        self.village.state.improvements = ['a']
        self.village.buy_improvements()
        assert self.village.state.fund == 99
        assert self.village.state.a

        # try to buy one we can't afford
        self.village.state.improvements = ['b']
        self.village.buy_improvements()
        assert self.village.state.fund == 99
        assert not hasattr(self.village.state, 'b')

        self.village.state.subsidy_offers = ['b']
        self.village.coeffs.subsidy_price_reduction = .05
        self.village.state.fund = 150
        self.village.buy_improvements()
        print(self.village.state.fund)
        assert self.village.state.fund == 140

    def test_update_subsidy_offers(self):
        self.village.state.year = 2013
        self.village.state.road = False
        self.village.coeffs.enable_NGO_offers = True
        self.village.coeffs.road_subsidy_year = 2
        self.village.update_subsidy_offers()
        assert 'road' in self.village.state.subsidy_offers

        self.village.state.road = True
        self.village.state.year = 2030
        self.village.coeffs.other_subsidy_year = 4
        self.village.update_subsidy_offers()

    def test_calc_fish_stock(self):
        self.village.state.amount_fish = 5.0
        self.village.state.fish_stock = 5000.0
        self.village.coeffs.fish_growth_rate = 1.2
        self.village.coeffs.fish_k = 7500.0

        self.village.state.fish_stock = 4000000
        self.village.coeffs.fish_k = 4000000
        self.village.state.amount_fish = 917
        self.village.state.village_population = 251 * 4

        stock = self.village.calc_fish_stock()
        assert stock > 3792849 and stock < 3792850

    def test_update_fish_stock(self):
        self.village.state.amount_fish = 5.0
        self.village.state.fish_stock = 5000.0
        self.village.coeffs.fish_growth_rate = 1.2
        self.village.coeffs.fish_k = 7500.0
        self.village.update_fish_stock()

    def test_calc_wood_stock(self):
        self.village.state.amount_wood = 5.0
        self.village.state.wood_stock = 5000
        self.village.coeffs.forest_growth_rate = 1.2
        self.village.coeffs.wood_k = 7500.0

    def test_update_wood_stock(self):
        self.village.state.amount_wood = 5.0
        self.village.state.wood_stock = 5000
        self.village.coeffs.forest_growth_rate = 1.2
        self.village.coeffs.wood_k = 7500.0
        self.village.update_wood_stock()

    def test_calculate_taxes(self):
        self.village.state.avg_family_size = 4
        assert self.village.calculate_taxes(10.0) == 0
        self.village.state.tax_rate = 1.0

        # make sure that a zero population doesn't give us a divide by zero
        self.village.state.population = 0
        self.village.calculate_taxes(10.0)

    def test_update_precipitation(self):
        self.village.update_precipitation()


class TestSchoolingFSM(unittest.TestCase):
    def setUp(self):
        coeffs = StubCoeffs(adult_effort=ADULT_EFFORT,
                            primary_school_effort=PRIMARY_SCHOOL_EFFORT,
                            secondary_school_effort=SECONDARY_SCHOOL_EFFORT)
        self.kodjo = Person(name="Kodjo", gender="Male", age=15, health=100,
                            education=12, pregnant=False, sick="",
                            schooling_state="adult",
                            coeffs=coeffs, tc=StubTC())

    def tearDown(self):
        pass

    def test_calculate_next_state(self):
        fsm = SchoolingFSM(3, 0, "under 5")
        assert fsm.calculate_next_state(True) == "under 5"
        assert fsm.calculate_next_state(False) == "under 5"

        fsm = SchoolingFSM(5, 0, "under 5")
        assert fsm.calculate_next_state(True) == "enrolled in primary"
        assert (fsm.calculate_next_state(False) ==
                "eligible for primary but missed turn")

        fsm = SchoolingFSM(18, 0, "adult")
        assert fsm.calculate_next_state(True) == "adult"
        assert fsm.calculate_next_state(False) == "adult"

        fsm = SchoolingFSM(12, 13, "enrolled in secondary")
        assert fsm.calculate_next_state(True) == "enrolled in secondary"
        assert fsm.calculate_next_state(False) == "eligible for secondary"

        fsm = SchoolingFSM(6, 1, "enrolled in primary")
        assert fsm.calculate_next_state(True) == "enrolled in primary"
        assert (fsm.calculate_next_state(False) ==
                "eligible for primary but missed turn")

        fsm = SchoolingFSM(6, 12, "enrolled in primary")
        assert fsm.calculate_next_state(True) == "enrolled in secondary"
        assert fsm.calculate_next_state(False) == "not eligible for secondary"

        fsm = SchoolingFSM(7, 5, "eligible for primary but missed turn")
        assert (fsm.calculate_next_state(True) ==
                "enrolled in primary but missed turn")
        assert (fsm.calculate_next_state(False) ==
                "eligible for primary but missed turn")

        fsm = SchoolingFSM(7, 5, "enrolled in primary but missed turn")
        assert (fsm.calculate_next_state(True) ==
                "enrolled in primary but missed turn")
        assert (fsm.calculate_next_state(False) ==
                "eligible for primary but missed turn")

        fsm = SchoolingFSM(7, 12, "enrolled in primary but missed turn")
        assert fsm.calculate_next_state(True) == "not eligible for secondary"
        assert fsm.calculate_next_state(False) == "not eligible for secondary"

        fsm = SchoolingFSM(13, 10, "eligible for secondary")
        assert fsm.calculate_next_state(True) == "enrolled in secondary"
        assert fsm.calculate_next_state(False) == "eligible for secondary"

        fsm = SchoolingFSM(13, 10, "not eligible for secondary")
        assert fsm.calculate_next_state(True) == "not eligible for secondary"
        assert fsm.calculate_next_state(False) == "not eligible for secondary"


class TestCoeffs(unittest.TestCase):
    def test_json(self):
        c = Coeffs()
        assert c.__json__() == {}


class TestState(unittest.TestCase):
    def test_json(self):
        s = State()
        assert s.__json__() == {}


class TestFunctions(unittest.TestCase):
    def setUp(self):
        coeffs = StubCoeffs(adult_effort=ADULT_EFFORT,
                            primary_school_effort=PRIMARY_SCHOOL_EFFORT,
                            secondary_school_effort=SECONDARY_SCHOOL_EFFORT,
                            starting_year=2007)
        kodjo = Person(name="Kodjo", gender="Male", age=15, health=100,
                       education=12, pregnant=False, sick="",
                       schooling_state="adult", coeffs=coeffs, tc=StubTC())
        state = StubState(people=[kodjo], health_t1=['Kodjo|100'],
                          health_t2=['Kodjo|100'], health_t3=['Kodjo|100'],
                          names=['Kodjo'], genders=['Male'], ages=[16],
                          health=[100], education=[12], pregnant=[False],
                          sick=[""], schooling_state=['adult'],
                          efforts=[12, 12], year=2007)
        tc = StubTC()
        self.tc = tc
        self.state = state
        self.coeffs = coeffs

    def test_marshall_people(self):
        people = list(setup_people(self.state, self.coeffs, self.tc))
        state = marshall_people(people, self.state)
        assert len(state.health_t1) > 0

    def test_new_child(self):
        self.coeffs.child_names = ['bart']
        self.coeffs.child_genders = ['Male']
        self.state.births = 0
        child = new_child(self.tc, self.coeffs, self.state)
        assert child.name == 'bart'

    def test_new_child_more_children_than_names(self):
        """ if more children are born than we have names for
        we need to start numbering them.
        shows up as sentry: /sentry/group/1400
        """
        self.coeffs.child_names = ['bart']
        self.coeffs.child_genders = ['Male']
        self.state.births = 0
        child = new_child(self.tc, self.coeffs, self.state)
        assert child.name == 'bart'
        child2 = new_child(self.tc, self.coeffs, self.state)
        assert child2.name == 'child2'
        child3 = new_child(self.tc, self.coeffs, self.state)
        assert child3.name == 'child3'


class TestTurn(unittest.TestCase):
    def setUp(self):
        coeffs = StubCoeffs(adult_effort=ADULT_EFFORT,
                            primary_school_effort=PRIMARY_SCHOOL_EFFORT,
                            secondary_school_effort=SECONDARY_SCHOOL_EFFORT,
                            secondary_school_cost=1,
                            recovery_rate0=1, recovery_rate1=1,
                            recovery_rate2=1,
                            recovery_rate3=1,
                            market_items=['stove', 'bednet',
                                          'high_yield_seeds', 'propane',
                                          'fertilizer'],
                            market_sell_prices=[10, 5, 1, 10, 5],
                            market_purchase_prices=[10, 5, 1, 10, 5],
                            death_rate=1,
                            mortality0=1, mortality1=1, birth_rate=1,
                            mortality2=1,
                            fish_k=2500, effort_coeff=0.042,
                            avg_fishing_yield=900,
                            maize_productivity_exponent=0.9,
                            avg_maize_yield=1000,
                            cotton_productivity_exponent=0.9,
                            avg_cotton_yield=1000,
                            avg_wood_yield=80, wood_k=7500,
                            avg_water_yield=250,
                            avg_small_business_yield=50, wood_fuel_coeff=3.5,
                            avg_family_size=4,
                            propane_fuel_coeff=5.0,
                            fish_growth_rate=1.2, forest_growth_rate=1.01,
                            energy_req=18, subsistence=500,
                            maize_cal_coeff=25, fish_cal_coeff=26.5,
                            w_subsistence=30,
                            fuelwood_health_loss=2.0,
                            effort_too_high_health_loss=1.0,
                            death_threshold_1=0.0,
                            death_threshold_2=10.0,
                            wood_price=10.0, cotton_export_units=100,
                            maize_export_units=100,
                            maize_price=10,
                            cotton_price=100, savings_rate=0.2,
                            health_increment=4.0,
                            min_precipitation=100,
                            precipitation_infection_modifier=0,
                            max_precipitation=400,
                            avg_precipitation=200,
                            soil_depletion=0.5,
                            school_meals_calories=5.0,
                            effort_fuel_wood=1,
                            transport_cost_road=10.0,
                            transport_cost_no_road=100.0,
                            doctor_visit_cost=30.0,
                            enable_NGO_offers=True,
                            road_subsidy_year=5,
                            other_subsidy_year=10,
                            drought_threshold=100.0,
                            no_droughts_before=2,
                            starting_year=2007,
                            enable_epidemic=True,
                            no_epidemics_before=10,
                            enable_free_bednets=True,
                            free_bednet_year=30,
                            productivity_effort_coeff=0.2,
                            fishing_effort_coeff=0.042,
                            wood_effort_coeff=0.042,
                            food_cost=20.0,
                            dragnet_coeff=2.0,
                            fish_stock_warn_threshold=0.33,
                            wood_stock_warn_threshold=0.33,
                            available_improvements=['a', 'b', 'road'],
                            improvement_prices=[1, 2, 10],
                            small_business_depreciation_rate=0.2,
                            small_business_productivity_effect=1,
                            small_business_road_effect=1,
                            small_business_electricity_effect=1,
                            small_business_drought_effect=1,
                            small_business_epidemic_effect=1,
                            small_business_diminishing_return=1,
                            microfinance_base_interest=0.02,
                            microfinance_min_balance=100.0,
                            microfinance_repay_period=8,
                            microfinance_drought_effect=1,
                            microfinance_epidemic_effect=1,
                            health_nutrition_coeff=1.0,
                            health_clinic_coeff=1.0,
                            health_power_coeff=1.0,
                            health_sickness_coeff=1.0,
                            )
        kodjo = Person(name="Kodjo", gender="Male", age=15, health=100,
                       education=12, pregnant=False, sick="",
                       schooling_state="adult", coeffs=coeffs, tc=StubTC())
        state = StubState(expenditure=0, income=0, tons_to_market=0,
                          initial_population=0, cash=500,
                          population=2, total_effort=0, fertilizer=False,
                          people=[kodjo], health_t1=['Kodjo|100'],
                          health_t2=['Kodjo|100'], health_t3=['Kodjo|100'],
                          names=['Kodjo'], genders=['Male'], ages=[16],
                          health=[100], education=[12], pregnant=[False],
                          sick=[""], schooling_state=['adult'],
                          efforts=[12, 12], year=2007,
                          doctor=[], sell_items=['', "stove|1"],
                          purchase_items=['', 'bednet|1'],
                          try_for_child=False, enroll=[],
                          improvements=[], village_infected_pop=0,
                          clinic=1.0, electricity=1.0, village_population=500,
                          fish_stock=5000, effort_fishing=2,
                          effort_farming=12, effort_fuel_wood=4,
                          effort_water=9,
                          boat=False, fishing_limit=0, fertilizer_t1=True,
                          season=True, fertilizer_last_turn=True,
                          soil_health=1, irrigation=False,
                          crops=['Maize', 'Maize', 'Maize', 'Maize'],
                          wood_stock=1000.0, wood_limit=0,
                          effort_small_business=0,
                          improved_stove=False, food_to_buy=0,
                          meals=False, water_pump=False, stove=False,
                          epidemic=False,
                          cost_to_market=0, tax_rate=0.0, fund=0,
                          owned_items=['stove'],
                          road=False, sanitation=False,
                          amount_water=50, user_messages=[], precipitation=0.0,
                          family_needs=1.0, amount_calories=0.0, wood_fuel=0.0,
                          wood_k=500, high_yield_seeds=False,
                          avg_productivity=1.0,
                          drought=False,
                          amount_propane=0,
                          propane_fuel=0,
                          subsistence_met=True,
                          calorie_allocation=[500, 500],
                          deaths=0,
                          died=[],
                          died_reasons=[],
                          dragnet=False,
                          bednet_ages=[2],
                          u_points=0,
                          small_business_capital=0,
                          small_business_investment=0,
                          microfinance_balance=0.0,
                          microfinance_borrow=0.0,
                          microfinance_current_interest_rate=0.0,
                          microfinance_interest_rate=0.0,
                          microfinance_amount_due=0.0,
                          microfinance_amount_paid=0.0,
                          microfinance_max_borrow=0.0,
                          )
        tc = StubTC()
        self.turn = Turn(state, coeffs, tc)

    def tearDown(self):
        self.turn = None

    def test_calc_maximum_effort(self):
        assert self.turn.calc_maximum_effort() == 2

    def test_transport_cost_per_ton(self):
        self.turn.state.road = True
        self.turn.transport_cost_per_ton()
        self.turn.state.road = False
        self.turn.transport_cost_per_ton()

    def test_reset(self):
        self.turn.state.expenditure = 300
        self.turn.state.income = 20
        self.turn.reset()
        assert self.turn.state.expenditure == 0
        assert self.turn.state.income == 0

    def test_is_game_over(self):
        self.turn.state.population = 10
        self.turn.state.cash = 100
        assert self.turn.is_game_over() is False
        self.turn.state.population = 0
        assert self.turn.is_game_over() is True
        self.turn.state.population = 10
        self.turn.state.cash = -200
        assert self.turn.is_game_over() is True

    def test_is_everyone_dead(self):
        self.turn.state.population = 10
        assert self.turn.is_everyone_dead() is False
        self.turn.state.population = 0
        assert self.turn.is_everyone_dead() is True

    def test_is_debt_too_high(self):
        self.turn.state.cash = 100
        assert self.turn.is_debt_too_high() is False
        self.turn.state.cash = -101
        assert self.turn.is_debt_too_high() is True

    def test_sell_items(self):
        pass

    def test_purchase_items(self):
        self.turn.purchase_items()
        self.turn.state.purchase_items.append('high_yield_seeds|1')
        self.turn.state.purchase_items.append('propane|1')
        self.turn.state.purchase_items.append('fertilizer|1')
        self.turn.purchase_items()

    def test_check_purchase_price(self):
        pass

    def test_check_sell_price(self):
        pass

    def test_update_points(self):
        pass

    def test_calc_family_avg_health(self):
        self.turn.state.people = []
        assert self.turn.calc_family_avg_health() == 0

    def test_calc_school_effort(self):
        pass

    def test_calc_school_cost(self):
        pass

    def test_family_improvements_count(self):
        pass

    def test_village_improvements_count(self):
        pass

    def test_update_population_count(self):
        pass

    def test_doctor(self):
        self.turn.state.doctor = ['kodjo']
        self.turn.doctor()

    def test_pregnancy(self):
        self.turn.state.try_for_child = True
        self.turn.pregnancy()

    def test_education(self):
        pass

    def test_children(self):
        self.turn.children()
        fatou = Person(name="Fatou", gender="Female", age=24, health=100,
                       education=12,
                       pregnant=True, sick="", schooling_state="adult",
                       coeffs=self.turn.coeffs, tc=self.turn.tc)
        self.turn.coeffs.child_names = ['bart']
        self.turn.coeffs.child_genders = ['Male']
        self.turn.state.births = 0
        self.turn.state.people.append(fatou)
        self.turn.state.try_for_child = False
        self.turn.children()
        assert fatou.pregnant is False

    def test_update_finances(self):
        pass

    def test_determine_cash(self):
        pass

    def test_increment_time(self):
        pass

    def test_age_people(self):
        pass

    def test_check_drought(self):
        self.turn.state.drought = False
        self.turn.state.year = 2007
        self.turn.coeffs.starting_year = 2007
        self.turn.state.irrigation = False
        self.turn.coeffs.chance_of_drought = .5
        self.turn.check_drought()
        assert self.turn.state.drought is True
        self.turn.state.year = 2010
        self.turn.state.irrigation = True
        self.turn.check_drought()
        assert self.turn.state.drought is False

    def test_rand_n(self):
        r = rand_n(self.turn.tc, 5)
        assert r == 0

    def test_check_epidemic(self):
        pass

    def test_check_final_health(self):
        self.turn.check_final_health()
        self.turn.state.people[0].health = 0
        self.turn.check_final_health()

    def test_check_sick(self):
        pass

    def test_check_stove(self):
        pass

    def test_update_yield(self):
        pass

    def test_t_boat(self):
        pass

    def test_t_fert(self):
        pass

    def test_t_irr(self):
        self.turn.state.irrigation = True
        self.turn.coeffs.irrigation_coeff = 5
        assert self.turn.t_irr() == self.turn.coeffs.irrigation_coeff

    def test_t_drought(self):
        pass

    def test_update_soil_health(self):
        self.turn.update_soil_health()
        assert self.turn.state.soil_health == 1.0
        self.turn.state.fertilizer = False
        self.turn.state.fertilizer_t1 = False
        self.turn.state.fertilizer_t2 = False
        self.turn.update_soil_health()
        assert self.turn.state.soil_health < 1.0

    def test_calc_amount_fish(self):
        pass

    def test_update_amount_fish(self):
        pass

    def test_wood_coeff(self):
        assert self.turn.calc_wood_coeff() == 1000.0 / 7500.0
        self.turn.state.wood_stock = 10000
        assert self.turn.calc_wood_coeff() == 1

    def test_update_wood_coeff(self):
        self.turn.update_wood_coeff()

    def test_calc_fish_coeff(self):
        print(self.turn.calc_fish_coeff())
        print(self.turn.state.fish_stock)
        print(self.turn.coeffs.fish_k)
        assert self.turn.calc_fish_coeff() == 1
        self.turn.state.fish_stock = -10
        assert self.turn.calc_fish_coeff() == 0
        self.turn.state.fish_stock = 200.0
        print(self.turn.calc_fish_coeff())
        assert self.turn.calc_fish_coeff() == 200.0 / 2500.0

    def test_update_fish_coeff(self):
        pass

    def test_percent_maize(self):
        assert self.turn.percent_maize() == 1
        self.turn.state.crops = ["Maize", "Maize", "Maize", "Cotton"]
        assert self.turn.percent_maize() == .75
        self.turn.state.crops = ["Cotton", "Cotton", "Cotton", "Cotton"]
        assert self.turn.percent_maize() == 0

    def test_percent_cotton(self):
        assert self.turn.percent_cotton() == 0
        self.turn.state.crops = ["Maize", "Maize", "Maize", "Cotton"]
        assert self.turn.percent_cotton() == .25
        self.turn.state.crops = ["Cotton", "Cotton", "Cotton", "Cotton"]
        assert self.turn.percent_cotton() == 1

    def test_calc_amount_cotton(self):
        assert self.turn.calc_amount_cotton() == 0
        self.turn.state.crops = ["Cotton", "Cotton", "Cotton", "Cotton"]
        amt = self.turn.calc_amount_cotton()
        assert amt > 2088.0 and amt < 2089.0

    def test_update_amount_cotton(self):
        pass

    def test_update_amount_maize(self):
        pass

    def test_calc_amount_wood(self):
        pass

    def test_update_amount_wood(self):
        self.turn.update_amount_wood()
        assert self.turn.state.amount_wood >= 0
        self.turn.state.wood_limit = 10
        self.turn.state.wood_stock = 10000
        self.turn.update_amount_wood()
        assert self.turn.state.amount_wood == self.turn.state.wood_limit

    def test_calc_amount_water(self):
        pass

    def test_update_amount_water(self):
        pass

    def test_calc_small_business_income(self):
        pass

    def test_update_small_business_income(self):
        pass

    def test_convert_calories(self):
        pass

    def test_convert_fuel(self):
        pass

    def test_is_enough_wood(self):
        pass

    def test_calc_energy_req(self):
        pass

    def test_calc_amount_calories(self):
        pass

    def test_school_meal_calories(self):
        assert self.turn.school_meal_calories() == 0
        self.turn.state.meals = True
        self.turn.state.people[0].schooling_state = "enrolled in primary"
        assert self.turn.school_meal_calories() > 0

    def test_amount_calories(self):
        pass

    def test_is_subsistence_met(self):
        pass

    def test_is_water_subsistence_met(self):
        pass

    def test_calc_family_needs(self):
        pass

    def test_calc_family_water_needs(self):
        pass

    def test_update_family_water_needs(self):
        pass

    def test_calories_above_subsistence(self):
        pass

    def test_excess_wood(self):
        pass

    def test_starve(self):
        self.turn.starve()

    def test_dehydrate(self):
        pass

    def test_num_infants(self):
        pass

    def test_total_productivity(self):
        pass

    def test_num_non_infants(self):
        pass

    def test_calc_avg_productivity(self):
        pass

    def test_update_avg_productivity(self):
        pass

    def test_determine_income(self):
        pass

    def test_hire_wagon(self):
        pass

    def test_sell_food(self):
        self.turn.state.food_to_sell = 10
        self.turn.sell_food()

    def test_sell_wood(self):
        pass

    def test_sell_cotton(self):
        self.turn.state.amount_cotton = 100
        (price, tons_to_market) = self.turn.sell_cotton()
        print(price)
        print(tons_to_market)
        print(self.turn.coeffs.cotton_price)
        assert price == 10
        assert tons_to_market == 0.1
        self.turn.coeffs.cotton_price = 200
        (price, tons_to_market) = self.turn.sell_cotton()
        assert price == 20
        assert tons_to_market == 0.1

    def test_food_cost(self):
        assert self.turn.food_cost() == 20
        self.turn.state.meals = True
        assert self.turn.food_cost() == 20 * 1.2


class TestDisplayLogic(unittest.TestCase):
    def setUp(self):
        self.state = StubState(
            drought=False,
            epidemic=False,
            family_water_needs=0,
            amount_water=0,
            water_pump=False,
            wood_income=0,
            amount_wood=0,
            purchase_items=[],
            sell_items=[],
            user_messages=[],
            improvements=[],
            village_population=1,
            village_infected_pop=0,
            wood_stock=0,
            fish_stock=0,
            clinic=False,
        )
        self.coeffs = StubCoeffs(
            wood_price=1,
            wood_fuel_coeff=1,
            doctor_visit_cost=1,
            available_improvements=[],
            improvement_labels=[],
            visual_intervals_forest=[],
            visual_intervals_fish=[],
        )

    def tearDown(self):
        pass

    def test_add_extra_seasonreport_context(self):
        context = {
            'people': [],
            'state': self.state,
            'coeffs': self.coeffs,
        }
        r = add_extra_seasonreport_context(context)
        assert r['n_health_people'] == 0
        assert r['money_spent'] == 0
        assert r['money_earned'] == 0
        assert r['percent_infected'] == 0

        # needs to not barf on zero population
        context['state'].village_population = 0
        r = add_extra_seasonreport_context(context)
        assert r['percent_infected'] == 0

        # test out village improvements
        context['state'].improvements = ['foo']
        context['coeffs'].available_improvements = ['foo']
        context['coeffs'].improvement_labels = ['bar']
        r = add_extra_seasonreport_context(context)
        assert r['village_improvements'] == ['bar']

    def test_more_births_than_child_names(self):
        self.state.user_messages.append('child born')
        self.state.births = 1
        self.coeffs.child_names = []
        context = {
            'people': [],
            'state': self.state,
            'coeffs': self.coeffs,
        }
        r = add_extra_seasonreport_context(context)
        assert r['new_baby'] == "child1"

        # and make sure the normal case still works
        self.coeffs.child_names = ['bart']
        context = {
            'people': [],
            'state': self.state,
            'coeffs': self.coeffs,
        }
        r = add_extra_seasonreport_context(context)
        self.assertEqual(r['new_baby'], "bart")


class TestForceIntegers(unittest.TestCase):
    def test_normal(self):
        kwargs = dict(cotton='3')
        self.assertEqual(force_integers(kwargs)['cotton'], '3')

    def test_empty(self):
        kwargs = dict(cotton='')
        self.assertEqual(force_integers(kwargs)['cotton'], '0')

    def test_whitespace(self):
        self.assertEqual(
            force_integers(dict(fishing_limit=' '))['fishing_limit'], '0')
        self.assertEqual(
            force_integers(dict(fishing_limit='\t'))['fishing_limit'], '0')
        self.assertEqual(
            force_integers(dict(fishing_limit='\n'))['fishing_limit'], '0')

    def test_percent(self):
        self.assertEqual(
            force_integers(dict(tax_rate='100%'))['tax_rate'], '100')
