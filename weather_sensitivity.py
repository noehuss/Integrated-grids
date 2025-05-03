from dispatch_optimization import BusElectricity
import param
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pypsa

years = np.arange(start=1980, stop=2015, step=1)
df = pd.DataFrame(index=[key for key, df in param.technologies_france.items()])

for year in years:
    france_net = BusElectricity('FRA', year, technologies=param.technologies_france, network=pypsa.Network())
    #france_net.add_co2_constraints(param.co2_limit_2019)
    france_net.optimize() 
    df[year] = france_net.return_capacity_mix()/1000

df = df.T
fig, ax = plt.subplots()
for n, col in enumerate(df.columns):
    bplot = ax.boxplot(df[col], positions=[n+1], patch_artist=True, tick_labels=[str(col)], showmeans=True)
    for patch in bplot['boxes']:
        patch.set_facecolor(param.colors[col])

plt.ylabel('Capacity installed (GW)')
plt.grid(linewidth='0.4', linestyle='--')
plt.show()
df.describe().to_csv('stats_capacity.csv')
df.to_csv('capacity.csv')