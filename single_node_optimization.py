from dispatch_optimization import BusElectricity
import param
import pandas as pd

france_net = BusElectricity('FRA', param.year, technologies=param.technologies_france)

# Optimize
france_net.optimize()

#france_net.plot_duration_curve()
start_date_winter=pd.Timestamp(f"{param.year}-01-01 00:00")
end_date_winter= pd.Timestamp(f"{param.year}-01-08 00:00")
start_date_summer=pd.Timestamp(f"{param.year}-07-01 00:00")
end_date_summer= pd.Timestamp(f"{param.year}-07-08 00:00")

france_net.plot_line(start_date_winter, end_date_winter)
france_net.plot_line(start_date_summer, end_date_summer)
france_net.plot_pie()
france_net.plot_duration_curve()
#france_net.plot_storage()
france_net.plot_dispatch(f'{param.year}-01')

print(france_net.network.generators)
print(france_net.network.carriers)
print(-france_net.network.global_constraints.mu)
print(france_net.network.generators.marginal_cost)

print([generator for generator in france_net.network.generators.loc[france_net.network.generators.p_nom_opt !=0].index])