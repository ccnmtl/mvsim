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
            if kwargs[field] == u"NaN":
                kwargs[field] = 0
            try:
                kwargs[field] = "%d" % (int(float(kwargs[field] or '0')),)
            except:
                pass
    return kwargs


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
    except:
        pass

    enroll = [False] * len(names)
    doctor = [False] * len(names)
    efforts = [12] * len(names)
    calories = [0] * len(names)
    name_positions = dict()
    i = 0
    for n in names:
        name_positions[n] = i
        i += 1

    purchase_items = []
    sell_items = []
    improvements = []
    keys = kwargs.keys()

    for k in keys:
        if k.startswith('purchase-'):
            (p, item, q) = k.split('-')
            if kwargs[k] == '':
                continue
            q = int(kwargs[k])
            if q != 0:
                purchase_items.append("%s|%d" % (item, q))
            del kwargs[k]
        if k.startswith('sell-'):
            (p, item, q) = k.split('-')
            if kwargs[k] == '':
                continue
            q = int(kwargs[k])
            if q != 0:
                sell_items.append("%s|%d" % (item, q))
            del kwargs[k]
        if k.startswith('improvement-'):
            (p, item) = k.split('-')
            improvements.append(item)
            del kwargs[k]
        if k.startswith('enroll-'):
            (e, name) = k.split('-')
            if kwargs[k] == '' or name not in name_positions:
                continue
            enroll[name_positions[name]] = True
            del kwargs[k]
        if k.startswith('doctor-'):
            (d, name) = k.split('-')
            if kwargs[k] == '' or name not in name_positions:
                continue
            doctor[name_positions[name]] = True
            del kwargs[k]
        if k.startswith('effort-'):
            (e, name) = k.split('-')
            if kwargs[k] == '' or name not in name_positions:
                continue
            efforts[name_positions[name]] = int(kwargs[k])
            del kwargs[k]
        if k.startswith('calories-'):
            (c, name) = k.split('-')
            if kwargs[k] == '' or name not in name_positions:
                continue
            calories[name_positions[name]] = int(float(kwargs[k]))
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
