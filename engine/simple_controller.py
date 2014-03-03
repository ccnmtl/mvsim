import locale


def force_integers(kwargs):
    integer_fields = ['fishing_limit', 'cotton', 'effort-Fatou',
                      'effort-Kodjo', 'effort_farming', 'effort_fishing',
                      'effort_fuel_wood', 'effort_small_business',
                      'effort_water', 'food_to_buy',
                      'maize', 'purchase-bednet-quantity',
                      'purchase-boat-quantity', 'purchase-dragnet-quantity',
                      'purchase-fertilizer-quantity',
                      'purchase-high_yield_seeds-quantity',
                      'purchase-propane-quantity',
                      'purchase-stove-quantity',
                      'sell-bednet-quantity',
                      'sell-improvedstove-quantity',
                      'small_business_investment',
                      'tax_rate',
                      'wood_limit']
    for field in integer_fields:
        if field in kwargs:
            if '%' in kwargs[field]:
                kwargs[field] = kwargs[field].replace('%', '')
            if kwargs[field] == u"NaN":
                kwargs[field] = 0
            try:
                kwargs[field] = "%d" % (int(float(kwargs[field] or '0')),)
            except:
                kwargs[field] = '0'
    return kwargs


def extract_item_quantity(k, kwargs):
    (p, item, q) = k.split('-')
    if kwargs[k] == '':
        return None
    q = int(kwargs[k])
    if q != 0:
        return "%s|%d" % (item, q)
    return None


def extract_purchase_items(kwargs):
    for k in kwargs.keys():
        if k.startswith('purchase-'):
            iqstring = extract_item_quantity(k, kwargs)
            if iqstring:
                yield iqstring


def extract_sell_items(kwargs):
    for k in kwargs.keys():
        if k.startswith('sell-'):
            iqstring = extract_item_quantity(k, kwargs)
            if iqstring:
                yield iqstring


def extract_improvements(kwargs):
    for k in kwargs.keys():
        if k.startswith('improvement-'):
            (p, item) = k.split('-')
            yield item


def enrollments(kwargs, name_positions, names):
    enroll = [False] * len(names)
    for k in kwargs.keys():
        if k.startswith('enroll-'):
            (e, name) = k.split('-')
            if kwargs[k] == '' or name not in name_positions:
                continue
            enroll[name_positions[name]] = True
    return enroll


def doctor_visits(kwargs, name_positions, names):
    doctor = [False] * len(names)
    for k in kwargs.keys():
        if k.startswith('doctor-'):
            (e, name) = k.split('-')
            if kwargs[k] == '' or name not in name_positions:
                continue
            doctor[name_positions[name]] = True
    return doctor


def effort_list(kwargs, name_positions, names):
    efforts = [12] * len(names)
    for k in kwargs.keys():
        if k.startswith('effort-'):
            (e, name) = k.split('-')
            if kwargs[k] == '' or name not in name_positions:
                continue
            efforts[name_positions[name]] = int(kwargs[k])
    return efforts


def calories_list(kwargs, name_positions, names):
    calories = [0] * len(names)
    for k in kwargs.keys():
        if k.startswith('calories-'):
            (c, name) = k.split('-')
            if kwargs[k] == '' or name not in name_positions:
                continue
            calories[name_positions[name]] = int(float(kwargs[k]))
    return calories


def adjust_submission(kwargs, names):
    """ the backend expects things in a slightly different format than
    what comes in from the forms """

    kwargs = force_integers(kwargs.copy())

    # sometimes when there are JS errors (ie, if they are using IE
    # even though they're not supposed to be) the form comes in
    # without 'maize' or 'cotton' fields set. Instead of
    # giving them a 500 error, we'll just default to all maize.
    # not perfect, but what can you do?
    maize = int(float(kwargs.get('maize', '4') or '4'))
    cotton = int(float(kwargs.get('cotton', '0') or '0'))
    # this is confusing, but I couldn't resist:
    kwargs['crops'] = ["Cotton"] * cotton + ["Maize"] * maize
    try:
        del kwargs['maize']
        del kwargs['cotton']
    except KeyError:
        pass

    name_positions = dict()
    i = 0
    for n in names:
        name_positions[n] = i
        i += 1

    keys = kwargs.keys()

    purchase_items = list(extract_purchase_items(kwargs))
    sell_items = list(extract_sell_items(kwargs))
    improvements = list(extract_improvements(kwargs))
    enroll = enrollments(kwargs, name_positions, names)
    doctor = doctor_visits(kwargs, name_positions, names)
    efforts = effort_list(kwargs, name_positions, names)
    calories = calories_list(kwargs, name_positions, names)

    prefixes = ['purchase-', 'sell-', 'improvement-',
                'enroll-', 'doctor-', 'effort-', 'calories-']

    for k in keys:
        for p in prefixes:
            if k.startswith(p):
                del kwargs[k]

    if kwargs.get('try_for_child', '') != '':
        kwargs['try_for_child'] = True
    else:
        kwargs['try_for_child'] = False

    kwargs['purchase_items'] = purchase_items
    kwargs['sell_items'] = sell_items
    kwargs['improvements'] = improvements
    kwargs['enroll'] = enroll
    kwargs['doctor'] = doctor
    kwargs['efforts'] = efforts
    kwargs['calorie_allocation'] = calories

    return kwargs


def format_float(number, decimals=1):
    return locale.format('%.' + str(decimals) + 'f', number, True)


def format_int(number):
    return locale.format('%i', round(number), True)


def money_report(value):
    value = float(value)
    if value > 0:
        value = format_float(value)
        return ("<span style='color: green; font-weight: bold;'>%s</span>"
                % value)
    if value < 0:
        value = format_float(value)
        return ("<span style='color: red; font-weight: bold;'>%s</span>"
                % value)
    value = format_float(value)
    return value


def get_interval_class(value, intervals):
    intervals = sorted(intervals)
    interval_classes = ["completely_empty", "mostly_empty", "partially_empty",
                        "partially_full", "completely_full"]
    for number, string in zip(intervals, interval_classes):
        if value < number:
            return string
    return interval_classes[-1]
