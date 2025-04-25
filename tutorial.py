import pypsa
import pandas as pd
import matplotlib.pyplot as plt

network = pypsa.Network()
hours_in_2015 = pd.date_range('2015-01-01 00:00Z',
                              '2015-12-31 23:00Z',
                              freq='h')

network.set_snapshots(hours_in_2015.values)

network.add("Bus", 
            "electricity bus")

# Load electricity demand data
df_elec = pd.read_csv('data/electricity_demand.csv', sep=';', index_col=0) #in MWh
df_elec.index = pd.to_datetime(df_elec.index) #change index to datetime
country = 'DNK'

# Add load to the bus
network.add("Load", 
            "load",
            bus="electricity bus",
            p_set=df_elec[country].values)

print(network.loads_t.p_set)

def annuity(n, r):
    """ Calculate the annuity factor for an asset with 
    lifetime n years and discount rate  r """

    if r>0:
        return r/(1.-1./(1.+r)**n)
    else:
        return 1/n
    
# Add the different carriers, only gas emits CO2
network.add('Carrier', 'gas', co2_emissions=0.19) # in t_CO2/MWh_th
network.add('Carrier', 'onshorewind')
network.add('Carrier', 'solar')

# Add onshore wind generator
df_onshorewind = pd.read_csv('data/onshore_wind_1979-2017.csv', sep=';', index_col = 0)
df_onshorewind.index = pd.to_datetime(df_onshorewind.index)
CF_wind = df_onshorewind[country][[hour.strftime('%Y-%m-%dT%H:%M:%SZ') for hour in network.snapshots]]
capital_cost_onshorewind = annuity(30, 0.07)*910000*(1+0.033) #in €/MW
network.add('Generator', 'onshorewind', bus='electricity bus',
            p_nom_extendable=True, carrier='onshorewind',
            capital_cost = capital_cost_onshorewind,
            marginal_cost = 0,
            p_max_pu = CF_wind.values)

# Add solar PV generator
df_solar = pd.read_csv('data/pv_optimal.csv', sep=';', index_col=0)
df_solar.index = pd.to_datetime(df_solar.index)
CF_solar = df_solar[country][[hour.strftime("%Y-%m-%dT%H:%M:%SZ") for hour in network.snapshots]]
capital_cost_solar = annuity(25,0.07)*425000*(1+0.03) # in €/MW
network.add('Generator', 'solar', bus='electricity bus',
            p_nom_extendable=True, carrier='solar',
            capital_cost = capital_cost_solar,
            marginal_cost = 0,
            p_max_pu = CF_solar.values)

# Add OCFT (Open Cycle Gas Turbine) generator
capital_cost_OCGT = annuity(25,0.07)*560000*(1+0.033) # in €/MW
fuel_cost = 21.6 # in €/MWh_th
efficiency = 0.39 # MWh_elec/MWh_th
marginal_cost_OCGT = fuel_cost/efficiency # in €/MWh_el
network.add('Generator', 'OCGT',
            bus='electricity bus',
            p_nom_extendable=True,
            carrier='gas',
            capital_cost=capital_cost_OCGT,
            marginal_cost=marginal_cost_OCGT)


network.optimize(solver_name='gurobi')
print(network.objective/1000000) #in 10^6 €
print(network.objective/network.loads_t.p.sum()) # EUR/MWh
print(network.generators.p_nom_opt) # in MW

plt.plot(network.loads_t.p['load'][0:96], color='black', label='demand')
plt.plot(network.generators_t.p['onshorewind'][0:96], color='blue', label='onshore wind')
plt.plot(network.generators_t.p['solar'][0:96], color='orange', label='solar')
plt.plot(network.generators_t.p['OCGT'][0:96], color='brown', label='gas (OCGT)')
plt.legend(fancybox=True, loc='best')
plt.show()

labels = ['onshore wind',
          'solar',
          'gas (OCGT)']
sizes = [network.generators_t.p['onshorewind'].sum(),
         network.generators_t.p['solar'].sum(),
         network.generators_t.p['OCGT'].sum()]

colors=['blue', 'orange', 'brown']

plt.pie(sizes,
        colors=colors,
        labels=labels,
        wedgeprops={'linewidth':0})
plt.axis('equal')

plt.title('Electricity mix', y=1.07)
plt.show()

network.generators['p_nom_opt']