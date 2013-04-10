from .util import rand_n


class Village:
    #uses the same state object as everyone else
    #village stuff:
    # state.village_population (and SIR model for demographics/epidemics)
    # state.fund   -- village fund amount
    # state.tax_rate   -- tax rate
    # state.fish_stock, state.wood_stock   -- states of lake & forest
    # state.fish_limit, state.wood_limit   -- wood & fish collection limits
    # state.clinic, state.irrigation, state.water_pump, state.meals,
    #    state.electricity      -- village-wide improvements
    # possibly also drought/precipitation?

    def __init__(self, state, coeffs, tc):
        self.state = state
        self.coeffs = coeffs
        self.tc = tc

    def update_population(self):
        """ update population each turn based on demographics (SIR model) """
        I = self.state.village_infected_pop \
            - self.recovered() \
            + self.sickened() \
            - self.coeffs.death_rate * self.state.village_infected_pop \
            - self.died_of_illness()

        if (self.coeffs.enable_epidemic and self.coeffs.enable_free_bednets
            and (self.state.year == self.coeffs.starting_year
                 + self.coeffs.free_bednet_year + 3)):
            # canned epidemic once everyone has bednets
            I = self.state.village_population * 0.3

        S = self.susceptible_pop() \
            + self.recovered() \
            - self.sickened() \
            - self.died() \
            + self.born()

        if S < 0:
            S = 0

        self.state.village_infected_pop = int(round(I))
        if self.state.village_infected_pop < 0:
            self.state.village_infected_pop = 0

        self.state.village_population = int(round(S + I))

        if self.state.village_population < 0:
            self.state.village_population = 0

    def check_epidemic(self):
        """ sets epidemic flag if the infected pop is high enough """
        self.state.epidemic = False
        if self.state.village_population == 0:
            return 0
        # TODO: 0.3 magic number should probably be a coefficient
        if (self.state.village_infected_pop
                / float(self.state.village_population) >= 0.3):
            self.state.epidemic = True

    def precipitation_modifier(self):
        assert self.coeffs.avg_precipitation != 0
        deviation = self.state.precipitation / self.coeffs.avg_precipitation

        component = (deviation
                     ** self.coeffs.epidemic_precipitation_deviation_exponent)

        return self.coeffs.precipitation_infection_modifier * component

    def avg_family_health(self):
        if self.state.population == 0:
            return 0
        return sum(self.state.health) / float(self.state.population)

    def village_health(self):
        # we assume the rest of the village is in the same health we are
        return (self.avg_family_health() / 100.0)

    def family_bednets(self):
        """ number of bednets the family owns """
        return len([elem for elem in self.state.owned_items
                    if elem == "bednet"])

    def bednet_modifier(self):
        """ avg bednets per villager """
        # we assume the rest of the village has bednets like we do
        if self.state.population == 0:
            return 0

        # @@ XXX TODO this is wrong
        # -- it's currently assuming the village has
        # the same number of bednets as the family,
        # instead of the same proportion
        return self.coeffs.bednet_infection_modifier \
            * ((self.family_bednets() * 2.0) / self.state.population)

    def infection_rate(self):
        if (not self.coeffs.enable_epidemic
            or (self.state.year < (self.coeffs.starting_year
                                   + self.coeffs.no_epidemics_before))):
            return 0

        return self.coeffs.base_infection_rate \
            + self.bednet_modifier() \
            + self.precipitation_modifier()

    def mortality(self):
        self.state.malaria_deaths = self.coeffs.mortality1 \
            + self.coeffs.mortality2 * self.village_health()
        return self.state.malaria_deaths

    def recovery_rate(self):
        return (self.coeffs.recovery_rate1
                + self.coeffs.recovery_rate2 * self.state.clinic
                + (self.coeffs.recovery_rate3 * self.state.clinic
                   * self.state.electricity))

    def susceptible_pop(self):
        return self.state.village_population - self.state.village_infected_pop

    def recovered(self):
        return self.recovery_rate() * self.state.village_infected_pop

    def died_of_illness(self):
        self.state.malaria_deaths = (self.mortality()
                                     * self.state.village_infected_pop)
        return self.state.malaria_deaths

    def born(self):
        self.state.village_births = (self.coeffs.birth_rate
                                     * self.state.village_population)
        return self.state.village_births

    def died(self):
        self.state.village_deaths = (self.coeffs.death_rate
                                     * self.susceptible_pop())
        return self.state.village_deaths

    def sickened(self):
        # jumpstart the SIR model if the timing is right
        if (self.coeffs.enable_epidemic and self.state.season
            and self.state.year == (self.coeffs.starting_year
                                    + self.coeffs.no_epidemics_before)):
            self.state.village_infected_pop = self.coeffs.initial_infected_pop

        sickened = (self.infection_rate() * self.susceptible_pop()
                    * self.state.village_infected_pop)
        if sickened < 0:
            sickened = 0
        return min(sickened, self.state.village_population)

    def improvements_count(self):
        """ count of how many village improvements have been made """
        cnt = 0
        for v in [self.state.clinic, self.state.irrigation,
                  self.state.road, self.state.sanitation,
                  self.state.water_pump, self.state.meals,
                  self.state.electricity]:
            if v:
                cnt += 1
        return cnt

    def calculate_taxes(self, taxes_paid_by_family):
        if self.state.tax_rate == 0:
            return 0
        if self.state.population == 0:
            return 0

        assert self.coeffs.avg_family_size, \
            ("avg_family_size coefficient must be nonzero! "
             "Talk to an administrator.")

        # divide by the average family size because we're taxing families,
        # not villagers
        num_families_in_village = (self.state.village_population
                                   / self.coeffs.avg_family_size)

        multiplier = (95.0 + rand_n(self.tc, 10)) / 100.0

        return taxes_paid_by_family * multiplier * num_families_in_village

    def family_taxes(self, taxable_income):
        return taxable_income * 0.01 * self.state.tax_rate

    def collect_taxes(self, taxes_paid_by_family):
        village_taxes = self.calculate_taxes(taxes_paid_by_family)
        self.state.fund += village_taxes

    def message(self, m):
        self.state.user_messages.append(m)

    def eligible_for_road_subsidy_offer(self):
        # After the first (n) years, it should be highly likely (about 50%)
        # that the government offer to subsidize a road
        if not self.state.road:
            if self.state.year > (self.coeffs.starting_year
                                  + self.coeffs.road_subsidy_year):
                if 'road' not in self.state.subsidy_offers:
                    return True
        return False

    def eligible_for_other_subsidy_offers(self):
        # Before there is a road, there should be no offers to subsidize
        # village improvements
        if not self.state.road:
            return False

        # Assuming you have a road, then beginning in the year defined
        # in the coeffs, there is a 5% chance on any given turn that
        # an NGO will offer to subsidize a village improvement.

        if self.state.year < (self.coeffs.starting_year
                              + self.coeffs.other_subsidy_year):
            return False
        return True

    def bernoulli_variable(self, percentage):
        """ returns True percentage % of the time

        (integer percentage values only)
        """
        return rand_n(self.tc, 100) < percentage

    def update_subsidy_offers(self):
        """NGOs occasionally offer to subsidize various village improvements"""
        if not self.coeffs.enable_NGO_offers:
            return

        if self.eligible_for_road_subsidy_offer():
            if self.bernoulli_variable(50):
                self.message("road subsidy")
                self.state.subsidy_offers.append('road')

        if not self.eligible_for_other_subsidy_offers():
            return

        # power, sanitation, water pump, irrigation, or school meals, clinic

        if not self.state.clinic and 'clinic' not in self.state.subsidy_offers:
            if self.bernoulli_variable(5):
                self.message("clinic subsidy")
                self.state.subsidy_offers.append('clinic')
        if (not self.state.irrigation
                and 'irrigation' not in self.state.subsidy_offers):
            if self.bernoulli_variable(5):
                self.message("irrigation subsidy")
                self.state.subsidy_offers.append('irrigation')
        if (not self.state.sanitation
                and 'sanitation' not in self.state.subsidy_offers):
            if self.bernoulli_variable(5):
                self.message("sanitation subsidy")
                self.state.subsidy_offers.append('sanitation')

        if (not self.state.water_pump
                and 'water_pump' not in self.state.subsidy_offers):
            if self.bernoulli_variable(5):
                self.message('water pump subsidy')
                self.state.subsidy_offers.append('water_pump')
        if (not self.state.meals
                and 'meals' not in self.state.subsidy_offers):
            if self.bernoulli_variable(5):
                self.message('meals subsidy')
                self.state.subsidy_offers.append("meals")
        if (not self.state.electricity
                and 'electricity' not in self.state.subsidy_offers):
            if self.bernoulli_variable(5):
                self.message('electricity subsidy')
                self.state.subsidy_offers.append("electricity")

    def check_improvement_price(self, improvement):
        price = self.raw_improvement_price(improvement)
        if improvement in self.state.subsidy_offers:
            # if there's an NGO subsidy offer, the price is reduced by 95%
            price *= self.coeffs.subsidy_price_reduction
        return price

    def raw_improvement_price(self, improvement):
        prices = dict()
        for i, price in zip(self.coeffs.available_improvements,
                            self.coeffs.improvement_prices):
            prices[i] = price
        return prices[improvement]

    def buy_improvements(self):
        for improvement in self.state.improvements:
            if improvement == '':
                continue

            # fail if the village can't afford it
            price = self.check_improvement_price(improvement)
            if self.state.fund < price:
                continue

            self.state.fund -= price
            setattr(self.state, improvement, True)

    def calc_new_improvements_value(self):
        return sum([self.check_improvement_price(improvement)
                    for improvement in self.state.improvements
                    if improvement != ""])

    def calc_fish_stock(self):
        assert self.coeffs.avg_family_size != 0
        assert self.coeffs.fish_k != 0

        households = (self.state.village_population
                      / self.coeffs.avg_family_size)
        total_fish_caught = self.state.amount_fish * households \
            * ((90.0 + rand_n(self.tc, 20)) / 100.0)

        return max(self.state.fish_stock
                   + (self.coeffs.fish_growth_rate * self.state.fish_stock
                      * (1.0 - (self.state.fish_stock
                                / float(self.coeffs.fish_k))))
                   - total_fish_caught,
                   0)

    def update_fish_stock(self):
        self.state.fish_stock = max(self.calc_fish_stock(), 0)
        assert self.coeffs.fish_stock_warn_threshold >= 0.0
        assert self.coeffs.fish_stock_warn_threshold <= 1.0
        if self.state.fish_stock < (self.coeffs.fish_k
                                    * self.coeffs.fish_stock_warn_threshold):
            self.message('fish stock depletion')

    def calc_wood_stock(self):
        assert self.coeffs.avg_family_size != 0
        assert self.coeffs.wood_k != 0
        total_wood_chopped = self.state.amount_wood \
            * ((95.0 + rand_n(self.tc, 10)) / 100.0) \
            * (self.state.village_population
               / self.coeffs.avg_family_size)
        return max(self.state.wood_stock
                   + (self.coeffs.forest_growth_rate
                      * self.state.wood_stock * (1 - (self.state.wood_stock
                                                      / self.coeffs.wood_k))
                      - total_wood_chopped), 0)

    def update_wood_stock(self):
        self.state.wood_stock = max(self.calc_wood_stock(), 0)
        assert self.coeffs.wood_stock_warn_threshold >= 0.0
        assert self.coeffs.wood_stock_warn_threshold <= 1.0
        if self.state.wood_stock < (self.coeffs.wood_k
                                    * self.coeffs.wood_stock_warn_threshold):
            self.message('wood stock depletion')

    def update_precipitation(self):
        self.state.precipitation = (rand_n(self.tc, 1000) / 1000.00) \
            * self.coeffs.max_precipitation

        # no drought allowed during first n years
        if self.state.precipitation < self.coeffs.drought_threshold:
            if not self.coeffs.enable_drought:
                self.state.precipitation = self.coeffs.drought_threshold
            earliest_allowed_drought_year = (self.coeffs.starting_year
                                             + self.coeffs.no_droughts_before)
            if self.state.year < earliest_allowed_drought_year:
                self.state.precipitation = self.coeffs.drought_threshold

        # update user messages
        if self.state.precipitation >= 2 * self.coeffs.avg_precipitation:
            self.message("good rains")
