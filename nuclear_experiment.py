from dispatch_optimization import ExistingBusElectricity
import param
import pandas as pd
import matplotlib.pyplot as plt
import utils
import math

installed_capa = {
    "Nuclear": 61.4*1000/2,
    "PV": 19*1000,
    "Wind Onshore": 21.8*1000,
    "Wind Offshore": 0.8*1000,
    "Hydro": 25.7*1000,
    "OCGT": 3*1000,
    "CCGT": 12.6*1000,
    "TACH2": 0,
    "Nuclear Extension" : 0
}

technologies_france = {
    "Nuclear": {"df": None, "p_min": 61.4*1000/2, "p_max": math.inf},
    "PV": {"df": param.df_solar, "p_min": 19*1000, "p_max": math.inf},
    "Wind Onshore": {"df": param.df_onshorewind, "p_min": 21.8*1000, "p_max": math.inf},
    "Wind Offshore": {"df": param.df_offshorewind, "p_min": 0.8*1000, "p_max": math.inf},
    "Hydro": {"df": param.df_hydro, "p_min": 25.7*1000, "p_max": math.inf},
    "OCGT": {"df": None, "p_min": 3*1000, "p_max": math.inf},
    "CCGT": {"df": None, "p_min": 12.6*1000, "p_max": math.inf},
    "TACH2": {"df": None, "p_min": 0, "p_max": math.inf},
    "Nuclear Extension": {"df": None, "p_min": 0, "p_max": 61.4*1000/2},
}

country = 'FRA'
#france_net = BusElectricity(country, param.year, technologies=param.technologies_france)
france_net = ExistingBusElectricity(country, param.year, technologies=technologies_france, storage_technologies= param.technologies_storage_france, single_node=True)

# Optimize
#france_net.add_co2_constraints(param.co2_limit_2030)
france_net.optimize()
france_net.plot_duration_curve()
start_date_winter=pd.Timestamp(f"{param.year}-01-05 00:00")
end_date_winter= pd.Timestamp(f"{param.year}-01-12 00:00")
start_date_summer=pd.Timestamp(f"{param.year}-07-06 00:00")
end_date_summer= pd.Timestamp(f"{param.year}-07-13 00:00")

# france_net.plot_line(start_date_winter, end_date_winter)
# france_net.plot_line(start_date_summer, end_date_summer)
france_net.plot_pie(True)
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

france_net.network.storage_units.to_csv("results/storage_without_constraints.csv")

utils.fourier_transform([france_net.network.storage_units_t.p['PHS_b'],
                         france_net.network.storage_units_t.p['PHS_s'],
                         france_net.network.storage_units_t.p['Battery'],
                         france_net.network.generators_t.p['PV'],
                         france_net.network.generators_t.p['Wind Offshore'],
                         france_net.network.generators_t.p['Hydro']]
                         ,colors=[param.colors['PHS_b'], param.colors['PHS_s'], param.colors['Battery'],
                                  param.colors["PV"], param.colors['Wind Offshore'], param.colors['Hydro']])

