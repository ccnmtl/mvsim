def small_business_capital(depreciation_rate, current_capital,
                           added_investment):
    return (1 - depreciation_rate) * current_capital + added_investment

def small_business_max_borrow(depreciation_rate, previous_capital,
                              added_investment):
    available_capital = small_business_capital(depreciation_rate,
                                               previous_capital,
                                               added_investment)
    subsistence_cost = 0

    return subsistence_cost + available_capital

def subsistence_cost(family_needs, food_cost, school_meals=False):
    if school_meals:
        food_cost *= 1.2
    return family_needs / 100 * food_cost



def family_energy_requirements(family_size, energy_needed_per_person,
                               entropy_factor=None):
    """
    a high entropy factor means a lot of energy is needed
    to survive. a low entropy factor means the opposite.

    it represents the stove's inefficiency in converting raw food
    to cooked food

    entropy_factor<=0 will silently convert to 1.0
    """

    entropy_factor = entropy_factor or 1.0

    family_energy = energy_needed_per_person * family_size
    family_energy *= entropy_factor
    return family_energy


def family_food_requirements(family_size, food_needed_per_person):
    return family_size * food_needed_per_person



# http://wiki.ccnmtl.columbia.edu/index.php/MVSim_scratchpad#On_Bednets
def village_bednets(family_bednets,
                    family_population, village_population,
                    family_bednet_coefficient, village_bednet_coefficient):
    
    return family_bednets \
        * (family_bednet_coefficient / village_bednet_coefficient) \
        * (village_population / family_population)
