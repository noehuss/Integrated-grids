from dispatch_optimization import BusElectricity
import param
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

years = np.arange(start=1980, stop=2015, step=2)
df = pd.DataFrame(index=[key for key, df in param.technologies_france.items()])

for year in years:
    france_net = BusElectricity('FRA', year, technologies=param.technologies_france)
    france_net.add_co2_constraints(param.co2_limit_2019)
    france_net.optimize()
    df[year] = france_net.return_capacity_mix()

df = df.T
fig, ax = plt.subplots()
for n, col in enumerate(df.columns):
    bplot = ax.boxplot(df[col], positions=[n+1], patch_artist=True, tick_labels=[str(col)])
    for patch in bplot['boxes']:
        patch.set_facecolor(param.colors[col])

plt.grid(linewidth='0.4', linestyle='--')
plt.show()
