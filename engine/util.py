""" some general utils that other parts can use """


def rand_n(tc, n):
    return tc.randint(a=0, b=n, n=1).values[0]
