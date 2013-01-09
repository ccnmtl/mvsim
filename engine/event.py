_colors = 'green red yellow orange'.split()
_ops = {
    "==": lambda x, y: x == y,
    "!=": lambda x, y: x != y,
    ">": lambda x, y: x > y,
    ">=": lambda x, y: x >= y,
    "<": lambda x, y: x < y,
    "<=": lambda x, y: x <= y,
    "hasnot": lambda x, y: y not in x, }

import tempita


class Condition(object):
    def __init__(self, lhs, op, rhs):
        self.op = _ops[op]
        self.lhs = lhs
        self.rhs = tempita.Template(rhs)

    def __call__(self, state, coeffs, before=None):
        # We don't want to swallow KeyErrors.
        # That's up to the caller to handle.
        lhs = state[self.lhs]

        ## FIXME: we could use to_python
        rhs = self.rhs.substitute(state=state, coeffs=coeffs, before=before)

        ## FIXME: we could use to_python
        rhs = eval(rhs)

        return self.op(lhs, rhs)


import simple_controller


def format_float(number, decimals=2):
    return simple_controller.format_float(number, decimals=decimals)


class Event(object):

    def __init__(self, name,
                 before_conditions, after_conditions,
                 message, color, scope, css_class=None):
        assert color in _colors

        self._message = tempita.Template(
            message, namespace={'format_float': format_float})
        self.color = color
        self.name = name
        self.scope = scope
        self.message = None
        self.css_class = css_class or ''

        self.before_conditions = []
        before_conditions = before_conditions or []
        for condition in before_conditions:
            lhs, op, rhs = condition.split()
            self.before_conditions.append(Condition(lhs, op, rhs))

        self.after_conditions = []
        after_conditions = after_conditions or []
        for condition in after_conditions:
            lhs, op, rhs = condition.split()
            self.after_conditions.append(Condition(lhs, op, rhs))

    def test(self, before, after, coeffs):
        for condition in self.before_conditions:
            if not condition(before, coeffs):
                return False
        for condition in self.after_conditions:
            if not condition(after, coeffs, before):
                return False

        self.message = self._message.substitute(
            before=before, after=after, coeffs=coeffs)
        return True

import csv


def get_events(events_csv=None):
    fp = open(events_csv or "events.csv")
    events = []
    reader = csv.reader(fp)
    for line in reader:
        if line[0] == "Events":
            continue
        try:
            name, message, color = line[0:3]
            before, after = line[5], line[6]
            scope = line[7]
        except IndexError:
            continue

        try:
            css_class = line[8]
        except IndexError:
            css_class = None

        color = color.lower()
        if before:
            before = before.split(",")
        if after:
            after = after.split(",")
        if not before and not after:
            continue
        scope = scope.lower()
        events.append(Event(name, before, after, message, color, scope,
                            css_class=css_class))
    fp.close()
    return events

_events = [
    Event("Road Built",
          ["road == False"],
          ["road == True"],
          "A road to the town has been paved. Transport costs have decreased.",
          "green", "village"),
    Event("Fishery depleted",
          [],
          ["fish_stock <= {{coeffs.fish_k*coeffs.fish_stock_warn_threshold}}"],
          "Sadly, the lake has been more fished out than you'd like.",
          "red", "village"),
    Event("Fleem",
          [],
          ["fish_stock > state.wood_stock", "wood_stock > 0"],
          ("You have {{format_float(after.fish_stock - after.wood_stock)}} "
           "more fish than wood!  And you used to have {{before.fish_stock}}"
           "fish."),
          "yellow", "family"),
    Event("Morx",
          [],
          ["fishing_limit != before.fishing_limit", "fishing_limit > 0"],
          ("The fishing quota has been changed from {{before.fishing_limit}} "
           "to {{after.fishing_limit}} fish per family."),
          "yellow", "village"),
    Event("Morx2",
          [],
          ["fishing_limit != before.fishing_limit", "fishing_limit == 0"],
          ("The fishing quota has been rescinded.  Fish to your heart's "
           "content!"),
          "green", "village"), ]

if __name__ == '__main__':
    class attrdict(dict):
        def __getattr__(self, attr):
            return self[attr]

    before = attrdict(fish_stock=1000,
                      road=False,
                      wood_stock=40,
                      fishing_limit=40)
    after = attrdict(fish_stock=800 / 3.,
                     road=True,
                     wood_stock=10,
                     fishing_limit=0)
    coeffs = attrdict(fish_k=2000, fish_stock_warn_threshold=0.3)
    for event in _events:
        if event.test(before, after, coeffs):
            print event.message
