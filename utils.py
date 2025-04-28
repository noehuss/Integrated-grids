def annuity(n, r):
    """ Calculate the annuity factor for an asset with 
    lifetime n years and discount rate  r """

    if r>0:
        return r/(1.-1./(1.+r)**n)
    else:
        return 1/n

def cost_conversion(cost, year_from, year_to=2020, inflation=1.02):
    """Convert cost from year_from to year_to using inflation data. 
    Inflation: float, ex: Inflation of 2%: 1.02
    """
    years = year_to - year_from
    return cost * (inflation ** years)