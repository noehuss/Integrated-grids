from dispatch_optimization import BusElectricity
import param
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pypsa

years = np.arange(start=1980, stop=2015, step=1)
df = pd.DataFrame(index=[key for key, df in param.technologies_france.items()])
elec_prices = []

for year in years:
    france_net = BusElectricity('FRA', year, technologies=param.technologies_france, network=pypsa.Network())
    #france_net.add_co2_constraints(param.co2_limit_2019)
    france_net.optimize() 
    df[year] = france_net.return_capacity_mix()/1000
    elec_prices.append(france_net.electricity_price)
    print(elec_prices)

df = df.T
fig = plt.figure()
gs = GridSpec(1, 2, width_ratios=[6, 1])
ax1 = fig.add_subplot(gs[0])
ax2 = fig.add_subplot(gs[1])
for n, col in enumerate(df.columns):
    bplot = ax1.boxplot(df[col], positions=[n+1], patch_artist=True, tick_labels=[str(col)], showmeans=True)
    for patch in bplot['boxes']:
        patch.set_facecolor(param.colors[col])
bplot = ax2.boxplot(elec_prices, patch_artist=True, showmeans=True)
for patch in bplot['boxes']:
        patch.set_facecolor(param.colors['elec'])

ax1.set(ylabel='Capacity installed (GW)')
ax1.grid(linewidth='0.4', linestyle='--')
ax2.set(ylabel='Electricity price (€/MWh)', ylim=(0, max(elec_prices)+2))
ax2.grid(linewidth='0.4', linestyle='--')
plt.show()
# df.describe().to_csv('stats_capacity.csv')
# df.to_csv('capacity.csv')