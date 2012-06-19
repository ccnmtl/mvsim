class Disease(object):
    """
    encapsulate the fun facts about a particular disease type
    """

    verbose_name = "the flu"
    health_coefficient = "DEFINE IN SUBCLASS"

    def random(self, person):
        from person import rand_n
        return rand_n(person.tc, 100) / 100.0

    def t_sick(self, person, state):
        """
        The illness equations are written so that you want a high score.
        """
        health_coeff = getattr(person.coeffs, self.health_coefficient)
        return health_coeff * person.health

    def add_to_the_mix(self):
        return True

    def try_to_infect(self, person, state):
        raise NotImplementedError("Subclass me")


class RespiratoryIllness(Disease):
    verbose_name = "pneumonia"
    health_coefficient = "disease_respiratory_health_factor"

    def try_to_infect(self, person, state):
        t_sick = self.t_sick(person, state)

        if state.stove:
            # this is a propane stove
            smog_factor = person.coeffs.disease_respiratory_propane_factor
        elif state.improved_stove:
             # this is an improved wood stove
            smog_factor = person.coeffs.disease_respiratory_stove_factor
        else:
            # there is no stove improvement at all,
            # so there will be no benefit at all
            smog_factor = 0

        youth_factor = person.coeffs.disease_respiratory_youth_factor
        if person.age >= 5:
            # but that's good (unlike the others)
            youth_factor = 0

        score = t_sick - youth_factor + smog_factor

        random_factor = self.random(person)
        score *= random_factor

        if score < 0.5:
            return 1
        return 0


class WaterborneIllness(Disease):
    verbose_name = "diahrreal disease"
    health_coefficient = "disease_waterborne_health_factor"

    def try_to_infect(self, person, state):
        """
        XXX TODO this is MISSING the WATER COMPONENT
        (w*((HH*Wmin)-Wt))(Wt<(HH*Wmin))
        """

        t_sick = self.t_sick(person, state)

        latrine_factor, waterpump_factor =\
            (person.coeffs.disease_waterborne_latrine_factor,
             person.coeffs.disease_waterborne_waterpump_factor)
        if not state.sanitation:
            latrine_factor = 0
        if not state.water_pump:
            waterpump_factor = 0

        score = t_sick + latrine_factor + waterpump_factor

        random_factor = self.random(person)
        score *= random_factor

        if score < 0.5:
            return 1
        return 0


class Malaria(Disease):
    verbose_name = "malaria"
    health_coefficient = "disease_malaria_health_factor"

    def try_to_infect(self, person, state):
        t_sick = self.t_sick(person, state)

        self.random(person)

        num_bednets = len([item for item in state.owned_items
                           if item == "bednet"])
        num_family_members = state.population
        # each bednet covers two people
        family_bednet_coverage = 2 * num_bednets / num_family_members
        bednet_factor = (person.coeffs.disease_malaria_bednet_factor
                         * family_bednet_coverage)

        # village_infection_proportion === I_t / V_t
        village_infection_proportion = (state.village_infected_pop
                                        / float(state.village_population))

        infection_rate_i0 = person.coeffs.base_infection_rate

        precipitation_factor = person.coeffs.precipitation_infection_modifier \
            * (state.precipitation / person.coeffs.avg_precipitation)

        infection_rate = infection_rate_i0 + precipitation_factor

        from stateless_logic import village_bednets
        num_village_bednets = village_bednets(
            num_bednets,
            num_family_members,
            state.village_population,
            person.coeffs.disease_malaria_bednet_factor,
            person.coeffs.bednet_infection_modifier)
        village_bednet_infection_component = (
            person.coeffs.bednet_infection_modifier
            * num_village_bednets
            * 2.0 / state.village_population)
        infection_rate += village_bednet_infection_component

        # note that this one is bad when high
        infection_factor = (person.coeffs.disease_malaria_sir_factor
                            * village_infection_proportion
                            * infection_rate)

        score = t_sick + bednet_factor - infection_factor

        if score < 0.5:
            return 1
        return 0

available_diseases = (RespiratoryIllness(), WaterborneIllness(), Malaria())
