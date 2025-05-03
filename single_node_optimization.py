from dispatch_optimization import BusElectricity
import param
import pandas as pd
import matplotlib.pyplot as plt
import utils

country = 'FRA'
#france_net = BusElectricity(country, param.year, technologies=param.technologies_france)
france_net = BusElectricity(country, param.year, technologies=param.technologies_france)#, storage_technologies= param.technologies_storage_france)

# Optimize
#france_net.add_co2_constraints(0)
france_net.optimize()

#france_net.plot_duration_curve()
start_date_winter=pd.Timestamp(f"{param.year}-01-05 00:00")
end_date_winter= pd.Timestamp(f"{param.year}-01-12 00:00")
start_date_summer=pd.Timestamp(f"{param.year}-07-06 00:00")
end_date_summer= pd.Timestamp(f"{param.year}-07-13 00:00")

# france_net.plot_line(start_date_winter, end_date_winter)
# france_net.plot_line(start_date_summer, end_date_summer)
france_net.plot_pie(False)
# france_net.plot_duration_curve()
# france_net.plot_storage(start_date_summer, end_date_summer)
france_net.plot_dispatch(f'{param.year}-07')

print(france_net.network.generators.p_nom_opt)
print(france_net.network.carriers)
print(-france_net.network.global_constraints.mu)
print(france_net.network.generators.marginal_cost)
print(france_net.objective_value)
print(france_net.electricity_price)

#utils.fourier_transform(france_net.network.storage_units_t.p['PHS'], color=param.colors['PHS'])


#print([generator for generator in france_net.network.generators.loc[france_net.network.generators.p_nom_opt !=0].index])
hours_in_year = pd.date_range(f'{param.year}-01-01 00:00Z',
                              f'{param.year}-12-31 23:00Z',
                              freq='h')
plt.plot(param.df_offshorewind.loc[hours_in_year, country].sort_values(ascending=False,ignore_index=True),
                     color=param.colors["Wind Offshore"],
                     label="Wind Offshore")
plt.plot(param.df_onshorewind.loc[hours_in_year, country].sort_values(ascending=False,ignore_index=True),
                     color=param.colors["Wind Onshore"],
                     label="Wind Onshore")
plt.plot(param.df_solar.loc[hours_in_year, country].sort_values(ascending=False,ignore_index=True),
                     color=param.colors["PV"],
                     label="PV")
plt.plot(param.df_hydro.loc[pd.date_range(f'2010-01-01 00:00',
                              f'2010-12-31 23:00',
                              freq='h'), 'Inflow pu'].sort_values(ascending=False,ignore_index=True),
                     color=param.colors["Hydro"],
                     label="Hydro")

plt.xlabel('Hours')
plt.ylabel('Capacity factor')
plt.grid(linewidth='0.4', linestyle='--')
plt.legend()
plt.show()

ramps_pv = param.df_solar.resample('Y').sum().diff()
ramps_pv.plot(kind='hist', xlabel='ramps solar PV', color='orange')
plt.show()