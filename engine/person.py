from schooling import SchoolingFSM
from disease import available_diseases


def rand_n(tc, n):
    return tc.randint(a=0, b=n, n=1).values[0]


def in_range(low, high, v):
    if v < low:
        return low
    if v > high:
        return high
    return v


class Person:
    name = ''
    gender = ''
    age = 0
    health = 100
    health_t1 = 100
    health_t2 = 100
    health_t3 = 100
    education = 0
    pregnant = False
    sick = ""
    schooling_state = "under 5"
    coeffs = None
    tc = None
    effort = 12

    def __init__(self, name="", gender="", age=0, health=100, education=0,
                 pregnant=False, sick="",
                 schooling_state="under 5", health_t1=100, health_t2=100,
                 health_t3=100, effort=effort, coeffs=None, tc=None):
        self.name = name
        self.gender = gender
        self.age = age
        self.health = health
        self.health_t1 = health_t1
        self.health_t2 = health_t2
        self.health_t3 = health_t3
        self.education = education
        self.pregnant = pregnant
        self.sick = sick
        self.schooling_state = schooling_state
        self.effort = effort
        self.coeffs = coeffs
        self.tc = tc

    def __str__(self):
        return ("<Person name=%s gender=%s age=%s health=%d>"
                % (self.name, self.gender, self.age, self.health))

    def age_group(self):
        if self.age < 2:
            return 'baby'
        elif self.age < 10:
            return 'child'
        elif self.age < 15:
            return 'teen'
        else:
            return 'adult'

    def img(self, under=False):
        # a tiny bit of display logic in here since it gets re-used
        age_group = self.age_group()
        sep = "-"
        if under:
            sep = "_"
        img = age_group + sep + self.gender.lower() + sep + self.name.lower()
        if age_group == 'baby':
            img = age_group + sep + self.gender.lower()
        return img

    def img_under(self):
        return self.img(under=True)

    def secondary(self):
        if "secondary" in self.schooling_state:
            return "notsecondary"
        else:
            return "secondary"

    def school_effort(self):
        if "secondary" in self.schooling_state:
            return self.coeffs.primary_school_effort
        else:
            return self.coeffs.secondary_school_effort

    def increment_health(self, health_increment):
        self.health += health_increment
        self.health = in_range(0, 100, self.health)

    def decrement_health(self, health_decrement):
        self.health -= health_decrement
        self.health = in_range(0, 100, self.health)

    def update_health(self, cals, clinic, electricity):
        # "Health at time t is a function of your health in the
        # previous period, of your nutrition (the difference between
        # your consumed calories and the minimal calorie requirement),
        # and a boost if there is a clinic, a boost if there is
        # electricity, and a loss if you are sick."

        self.health = in_range(0.0, 100.0,
                               self.calculate_health(cals, clinic,
                                                     electricity))

    def calculate_health(self, cals, clinic, electricity):
        # cals - number of calories consumed this turn
        # clinic - whether there is a clinic
        # electricity - whether there is a power grid
        return in_range(0, 100,
                        (self.health
                         + (self.coeffs.health_nutrition_coeff
                            * (cals - self.coeffs.subsistence))
                         + (self.coeffs.health_clinic_coeff
                            * clinic * (100.0 - self.health))
                         + (self.coeffs.health_power_coeff
                            * clinic * electricity * (100.0 - self.health))
                         - (self.coeffs.health_sickness_coeff
                            * bool(self.sick))))

    def visit_doctor(self):
        self.sick = ""
        if self.health > 90:
            self.health = 100
            return
        delta_health = (100.0 - self.health) / 2.0
        self.increment_health(delta_health)

    def starve(self, allocation):
        t_starve = 100.0 * ((self.coeffs.subsistence - allocation)
                            / float(self.coeffs.subsistence))
        self.decrement_health(t_starve)

    def dehydrate(self, family_water_needs, amount_water, population):
        if population == 0:
            return
        water_subsistence = family_water_needs / float(population)
        t_dehydrate = (100.0 * ((family_water_needs - amount_water)
                                / population) / water_subsistence)
        self.decrement_health(t_dehydrate)

    def maximum_effort(self):
        """ maximum effort for the individual """
        if self.age >= 15:
            if self.pregnant:
                return self.coeffs.pregnant_effort
            return self.coeffs.adult_effort
        if self.age >= 10:
            return self.coeffs.child_3_effort
        if self.age >= 5:
            return self.coeffs.child_2_effort
        return self.coeffs.child_1_effort

    def current_max_effort(self):
        return min(self.maximum_effort(), self.effort)

    def is_infant(self):
        return self.age < 5

    def productivity(self):
        # babies are /completely/ unproductive.
        if self.age < 5:
            return 0

        # if you're not a baby, your productivity is a function of
        # your education

        years_education = self.education / 2.0
        education_factor = ((6.0 + years_education) / 12.0)

        # if you're getting on in years, your productivity will decline
        # with every passing year
        if self.age >= 50:
            elderly_coefficient = 0.95 ** (self.age - 50)
            return self.health * elderly_coefficient * education_factor

        # ok, you're neither a baby nor a senior citizen
        return self.health * education_factor

    def check_sick(self, state):
        infections = []
        for disease in available_diseases:
            if disease.try_to_infect(self, state):
                infections.append(disease.verbose_name)
        infections = '+'.join(infections)

        if infections:
            self.sick = infections
        elif ((rand_n(self.tc, 100) / 100.0)
              > (1.0 - self.coeffs.chance_of_getting_the_flu)):
            # we can also get random unspecified diseases like flu
            # but only if we don't have anything bigger!
            # this is independent of your recent health -- on 5%
            # of turns, you will get sick, no exceptions.
            self.sick = "the flu"
        else:
            self.sick = ""
        self.check_effort(state)

    def check_effort(self, state):
        # is effort not optimal?
        if self.effort > self.maximum_effort():
            # optimal effort is now the maximum they can do
            self.effort = self.maximum_effort()
            # working too hard
        if self.effort < self.maximum_effort():
            # resting up lets them heal faster
            d = self.maximum_effort() - self.effort
            e = self.coeffs.resting_health_gain * d
            self.increment_health(e)

    def update_schooling_state(self, enroll):
        """ finite state machine for schooling """
        fsm = SchoolingFSM(self.age, self.education, self.schooling_state)
        self.schooling_state = fsm.calculate_next_state(enroll)

    def update_education(self):
        # if they're in school, increase the education count
        if self.schooling_state == "enrolled in primary" or \
                self.schooling_state == "enrolled in secondary":
            self.education += 1

    def average_health_over_past_three_turns(self):
        return (self.health_t1 + self.health_t2 + self.health_t3) / 3.0

    def in_primary_school(self):
        return self.schooling_state.startswith("enrolled in primary")

    def in_secondary_school(self):
        return self.schooling_state.startswith("enrolled in secondary")

    def make_pregnant(self):
        if self.name != 'Fatou':
            # only the mother can become pregnant
            return
        if self.age < 20 or self.age > 39:
            # we don't allow pregnancies after age 40
            # or before age 20
            self.pregnant = False
        else:
            self.pregnant = True

    def is_dead(self):
        if self.health <= self.coeffs.death_threshold_1:
            # health is too low
            return True
        else:
            # health this turn is OK, but if their average
            # over the last three turns is too low,
            # they can still die
            avg_health = self.average_health_over_past_three_turns()
            if avg_health < self.coeffs.death_threshold_2:
                return True
        return False
