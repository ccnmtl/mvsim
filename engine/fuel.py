class FuelType(object):
    """ 
    encapsulate the properties of a fuel type 
    w.r.t. conversion of raw food to consumable calories

    when instantiated with a numerical quantity, represents
    a real supply of the fuel which can convert raw to cooked food
    """

    _coefficient = "define in subclass"

    @classmethod
    def coefficient(cls, coeffs):
        return getattr(coeffs, cls._coefficient)

    @classmethod
    def capacity(cls, coeffs, state):
        """
        should return a floating-point number, typically >= 1,
        representing the amount of food that can be cooked
        with a single unit of this fuel type

        the implicit unit of this number is <kCal per unit fuel>
        """
        raise NotImplementedError("subclass me")

    def __init__(self, stock):
        self.stock = stock

    def convert(self, raw_food_cals, coeffs, state):

        food_to_cook = min(raw_food_cals, state.family_needs)

        capacity = self.capacity(coeffs, state)

        potential_capacity = self.stock * capacity

        if potential_capacity == 0:
            # save some calculations -- do nothing and abort 
            # also avoids potential ZeroDivisionError below if capacity=0
            return 0.0, raw_food_cals
        elif potential_capacity < food_to_cook:
            real_capacity = potential_capacity
            self.stock = 0
        else:
            real_capacity = food_to_cook
            self.stock -= real_capacity / capacity

        raw_food_cals = raw_food_cals - real_capacity

        energy = real_capacity

        return energy, raw_food_cals

class Propane(FuelType):

    _coefficient = 'propane_fuel_coeff'

    @classmethod
    def capacity(cls, coeffs, state):
        if not state.stove:
            return 0.0
        return cls.coefficient(coeffs) * 50000.0

class Wood(FuelType):

    _coefficient = 'wood_fuel_coeff'
    
    @classmethod
    def capacity(cls, coeffs, state):
        capacity = cls.coefficient(coeffs) * 50000.0
        if state.improved_stove:
            capacity *= 1.33333333
        return capacity

# if knowledge of particular fuel types is abstracted out,
# then FuelSupply() should maintain a list of fuels ordered
# from most-efficient to least-efficient, and use that list
# to determine the sequence of conversions
class FuelSupply(object):
    """ 
    represents a mixed stock of fuels 

    this object is stateful. iff it has been used to convert fuel,
    you can ask its property `.was_sufficient` whether there was
    excess food (i.e. the quantity of fuel was insufficient) and
    you can ask its property `.raw_leftovers` for the quantity
    of uncooked food (which will be 0 the fuel stock was sufficient)
    """
    def __init__(self, coeffs, state):
        self.propane = Propane(state.amount_propane)
        self.wood = Wood(state.amount_wood)
        self.coeffs = coeffs
        self.state = state

        self._sufficient = None
        self._uncooked = None

    @property
    def was_sufficient(self):
        if self._sufficient is None:
            raise RuntimeError("This fuel supply has not yet been used!"
                               "First .convert() some food.")

        return self._sufficient

    @property
    def raw_leftovers(self):
        if self._uncooked is None:
            raise RuntimeError("This fuel supply has not yet been used!"
                               "First .convert() some food.")
        return self._uncooked

    def stock(self, type):
        assert type in ('propane', 'wood')
        fuel = getattr(self, type)
        return fuel.stock

    def convert(self, raw_food_cals):
        """
        given raw food cals, outputs (cooked food cals, uncooked food cals)
        """
        energy = 0
        for fuel in (self.propane, self.wood):            
            more_energy, raw_food_cals = fuel.convert(raw_food_cals,
                                                      self.coeffs, self.state)
            energy += more_energy
            if energy >= self.state.family_needs:
                break

        if energy < self.state.family_needs:
            self._sufficient = False
        else:
            self._sufficient = True
        self._uncooked = int(raw_food_cals)

        return energy
