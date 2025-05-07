# from dispatch_optimization import BusElectricity
from dispatch_optimization import NetworkElectricity
import param
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

countries = param.countries
technologies_by_country = param.technologies_by_country
cost_HVAC_line = np.linspace(0, 200, 11)  # EUR/MW/km

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
    # Europe_net.plot_map()

    production_mix = Europe_net.return_production_mix() / 1E6
    df[cost_line] = production_mix.sum()

    # Store marginal prices and global constraints in df_prices
    marginal_prices = Europe_net.network.buses_t.marginal_price.mean()
    global_constraints = -Europe_net.network.global_constraints.mu
    df_prices[cost_line] = pd.concat([marginal_prices, global_constraints])

print(df)
print(df_prices)


fig, ax1 = plt.subplots()
ax1.stackplot(cost_HVAC_line, df,
              labels=[generator for generator in df.index], alpha=0.9,
              colors=[param.colors[generator] for generator in df.index])
ax1.set(xlabel='Cost HVAC line (€/MW/km)', ylabel='Production (TWh)')
ax1.legend(loc='upper right')
ax1.grid(linewidth='0.4', linestyle='--')
ax2 = ax1.twinx()
for index, row in df_prices.iterrows():
    ax2.plot(cost_HVAC_line, row, label=f'{index} price', marker='o')
ax2.set(xlabel='Cost HVAC line (€/MW/km)', ylabel='Electricity price (€/MWh)')
ax2.legend(loc='upper left')
ax2.set(ylim=(40, 70))
plt.show()
print(df_prices)


# Result

# Europe_net.generation()
# print("========")
# Europe_net.energy()
# print("========")
# Europe_net.energy_dir()
# print("========")
# Europe_net.line_capacity()

# Europe_net.plot_map()
