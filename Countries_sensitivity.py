# from dispatch_optimization import BusElectricity
from dispatch_optimization import NetworkElectricity
import param
import pandas as pd
import matplotlib.pyplot as plt

countries = param.countries
technologies_by_country = param.technologies_by_country
cost_HVAC_line = param.cost_HVAC_line

# Dataframe to store the result
df = pd.DataFrame()
df_prices = pd.DataFrame()

for cost_line in cost_HVAC_line:
    Europe_net = NetworkElectricity(param.year)
    for country in countries:
        print("Country: ", country)
        Europe_net.add_country(
            country, technologies=technologies_by_country[country])
        if country != "FRA":
            Europe_net.add_line("FRA", country, 0, 1, 1,
                                cost_line*param.Distance_to_Paris[country], True)
    Europe_net.optimize()

    production_mix = Europe_net.return_production_mix() / 1E6
    df[cost_line] = production_mix.sum()

    # Store marginal prices and global constraints in df_prices
    marginal_prices = Europe_net.network.buses_t.marginal_price.mean()
    global_constraints = -Europe_net.network.global_constraints.mu
    df_prices[cost_line] = pd.concat([marginal_prices, global_constraints])

print(df)
print(df_prices)
# Europe_net.plot()

# Result

# Europe_net.generation()
# print("========")
# Europe_net.energy()
# print("========")
# Europe_net.energy_dir()
# print("========")
# Europe_net.line_capacity()

# Europe_net.plot_map()
