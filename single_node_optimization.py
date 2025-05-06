from dispatch_optimization import BusElectricity
import param
import pandas as pd
import matplotlib.pyplot as plt
import utils

country = 'FRA'
#france_net = BusElectricity(country, param.year, technologies=param.technologies_france)
france_net = BusElectricity(country, param.year, technologies=param.technologies_france, storage_technologies= param.technologies_storage_france, single_node=True)
france_net.add_co2_constraints(param.co2_limit_2030)
france_net.add_sector('Hydrogen', param.hourly_hydrogen_demand, True, False)
france_net.optimize()

# france_net = BusElectricity(country, param.year, technologies=param.technologies_france, storage_technologies= param.technologies_storage_france, single_node=True)
# france_net.add_co2_constraints(param.co2_limit_2030)
# france_net.add_sector('Hydrogen', param.hourly_hydrogen_demand, True, False)
# france_net.optimize()

# france_net = BusElectricity(country, param.year, technologies=param.technologies_france, storage_technologies= param.technologies_storage_france, single_node=True)
# france_net.add_co2_constraints(param.co2_limit_2030)
# france_net.add_sector('Hydrogen', param.hourly_hydrogen_demand, True, True)
# france_net.optimize()



#france_net.plot_duration_curve()
start_date_winter=pd.Timestamp(f"{param.year}-01-05 00:00")
end_date_winter= pd.Timestamp(f"{param.year}-01-12 00:00")
start_date_summer=pd.Timestamp(f"{param.year}-07-06 00:00")
end_date_summer= pd.Timestamp(f"{param.year}-07-13 00:00")

# france_net.plot_line(start_date_winter, end_date_winter)
# france_net.plot_line(start_date_summer, end_date_summer)
france_net.plot_pie(True)
france_net.plot_pie(False)
france_net.plot_duration_curve()
# france_net.plot_storage(start_date_summer, end_date_summer)
france_net.plot_dispatch(f'{param.year}-07')

print(france_net.network.generators.p_nom_opt)
print(france_net.network.links.p_nom_opt)
print(france_net.network.storage_units.p_nom_opt)
print(france_net.network.stores.e_nom_opt)
print(france_net.network.stores_t.e['Hydrogen Storage'])
print(france_net.network.storage_units_t.p['PHS_b'])

print(france_net.network.buses_t.marginal_price.mean())

# print(france_net.network.carriers)
# print(-france_net.network.global_constraints.mu)
# print(france_net.network.generators.marginal_cost)
# print(france_net.objective_value)
# print(france_net.electricity_price)

france_net.network.storage_units.to_csv("results/storage_without_constraints.csv")

utils.fourier_transform([france_net.network.storage_units_t.p['PHS_b'],
                         france_net.network.storage_units_t.p['PHS_s'],
                         france_net.network.storage_units_t.p['Battery'],
                         france_net.network.generators_t.p['PV'],
                         france_net.network.generators_t.p['Wind Offshore'],
                         france_net.network.generators_t.p['Hydro']]
                         ,colors=[param.colors['PHS_b'], param.colors['PHS_s'], param.colors['Battery'],
                                  param.colors["PV"], param.colors['Wind Offshore'], param.colors['Hydro']])


#print([generator for generator in france_net.network.generators.loc[france_net.network.generators.p_nom_opt !=0].index])
