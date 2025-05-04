# from dispatch_optimization import BusElectricity
from dispatch_optimization import NetworkElectricity
import param
import pandas as pd
import matplotlib.pyplot as plt

Europe_net = NetworkElectricity(param.year)

countries = param.countries
technologies_by_country = param.technologies_by_country

for country in countries:
    print("Country: ", country)
    Europe_net.add_country(
        country, technologies=technologies_by_country[country])
    if country != "FRA":
        Europe_net.add_line("FRA", country, 0, 1, 1,
                            param.cost_HVAC_line*param.Distance_to_Paris[country], True)


# Europe_net.plot()

# Optimize
Europe_net.optimize()

# Result

Europe_net.generation()

Europe_net.energy()
Europe_net.line_capacity()

Europe_net.plot_map()
