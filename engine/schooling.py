class SchoolingFSM:
    """ Finite State Machine for handling schooling state """
    def __init__(self, age, education, schooling_state):
        self.age = age
        self.education = education
        self.schooling_state = schooling_state

    def calculate_next_state(self, enroll):
        # this dispatch dictionary could be replaced with some introspection
        # but I like having it clear and obvious what's going on and how things
        # are mapped
        functions = {
            "under 5": self.under5_fsm,
            "adult": self.adult_fsm,
            "enrolled in primary": self.enrolled_in_primary_fsm,
            "enrolled in secondary": self.enrolled_in_secondary_fsm,
            "not eligible for secondary": self.not_eligible_for_secondary_fsm,
            "eligible for secondary": self.eligible_for_secondary_fsm,
            "enrolled in primary but missed turn":
                self.enrolled_in_primary_but_missed_turn_fsm,
            "eligible for primary but missed turn":
                self.eligible_for_primary_but_missed_turn_fsm,
            }

        # basic guards first
        if self.age > 17:
            return "adult"

        f = functions[self.schooling_state]
        return f(enroll)

    def under5_fsm(self, enroll):
        if self.age == 5:
            # enroll or don't
            if enroll:
                return "enrolled in primary"
            else:
                return "eligible for primary but missed turn"
        else:
            return "under 5"

    def adult_fsm(self, enroll):
        return "adult"  # once an adult, always an adult

    def enrolled_in_primary_fsm(self, enroll):
        assert self.age >= 5
        assert self.age < 17
        if enroll:
            if self.education < 12:
                return "enrolled in primary"
            else:
                return "enrolled in secondary"
        else:
            if self.education < 12:
                return "eligible for primary but missed turn"
            else:
                return "not eligible for secondary"

    def eligible_for_primary_but_missed_turn_fsm(self, enroll):
        assert self.education < 12
        if enroll:
            return "enrolled in primary but missed turn"
        else:
            return "eligible for primary but missed turn"

    def enrolled_in_primary_but_missed_turn_fsm(self, enroll):
        if self.education < 12:
            if enroll:
                return "enrolled in primary but missed turn"
            else:
                return "eligible for primary but missed turn"
        else:
            return "not eligible for secondary"

    def eligible_for_secondary_fsm(self, enroll):
        if enroll:
            return "enrolled in secondary"
        else:
            return "eligible for secondary"

    def not_eligible_for_secondary_fsm(self, enroll):
        return "not eligible for secondary"

    def enrolled_in_secondary_fsm(self, enroll):
        assert self.age >= 11
        assert self.education >= 12
        assert self.age <= 17
        if enroll:
            return "enrolled in secondary"
        else:
            return "eligible for secondary"
