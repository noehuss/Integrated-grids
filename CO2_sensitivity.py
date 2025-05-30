from dispatch_optimization import BusElectricity
import param
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pypsa

co2_limits = np.linspace(0, 2*param.co2_limit_1990, 10)
df = pd.DataFrame(index=[key for key, df in param.technologies_france.items()])
df_prices = pd.DataFrame()
for co2_limit in co2_limits:
    france_net = BusElectricity('FRA', param.year, technologies=param.technologies_france, network=pypsa.Network())
    france_net.add_co2_constraints(co2_limit)
    france_net.optimize()
    df[co2_limit] = france_net.return_production_mix()/1E6
    df_prices[co2_limit] = pd.concat([france_net.network.buses_t.marginal_price.mean()
                                     ,-france_net.network.global_constraints.mu])

fig, ax1 = plt.subplots()
ax1.stackplot(co2_limits, df,
             labels=[generator for generator in df.index], alpha=0.9,
             colors=[param.colors[generator] for generator in df.index])
ax1.set(xlabel='CO2 limit (tCO2eq)', ylabel='Production (TWh)')
ax1.legend(loc='upper right')
ax1.grid(linewidth='0.4', linestyle='--')
ax2 = ax1.twinx()
ax2.plot(co2_limits, df_prices.iloc[0,:], label='Average electricity price', color=param.colors['elec'], marker='^')
ax2.plot(co2_limits, df_prices.iloc[1,:], label='$CO_2$ price', color=param.colors['tCO2'], marker='.')
ax2.set(xlabel='CO2 limit (tCO2eq)')
ax2.axvline(param.co2_limit_1990, label='1990 tCO2', linestyle='--', color='black')
ax2.axvline(param.co2_limit_2019, label='2019 tCO2', linestyle='--', color='gray')
ax2.axvline(param.co2_limit_2030, label='2030 tCO2 target', linestyle='--', color='skyblue')
ax2.legend(loc='lower right')
ax2.set(ylim=(0,300))
#ax2.grid(linewidth='0.4', linestyle='--')
plt.show()
print(df_prices)