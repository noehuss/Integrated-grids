import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import utils

class BusElectricity():
    def __init__(self, country:str, year:int):
        self.country = country
        self.year = year
        self.name = f'{country} electriciy'
        self.network = pypsa.Network()
        hours_in_year = pd.date_range(f'{self.year}-01-01 00:00Z',
                              f'{self.year}-12-31 23:00Z',
                              freq='h')
        self.network.set_snapshots(hours_in_year.values)
        self.network.add('Bus', self.name)
        # Load electricity demand data
        df_elec = pd.read_csv('data/electricity_demand.csv', sep=';', index_col=0) #in MWh
        df_elec.index = pd.to_datetime(df_elec.index) #change index to datetime
        # Add load to the bus
        self.network.add("Load", 
            "load",
            bus=self.name,
            p_set=df_elec[self.country].values)
        
        self.objective_value = 0
        self.electricity_price = 0
        

    def add_generator(self, technology_name:str, capex:float, opex_fixed:float ,marginal_cost:float, lifetime:int, efficiency:float, CO2_emissions:float, data_prod=None):
        """
        Add a generator in our network object.
        """
        annualized_cost = utils.annuity(lifetime, 0.07)*capex*(1+opex_fixed/capex)
        carrier_name = technology_name
        self.network.add('Carrier', carrier_name, co2_emissions=CO2_emissions, overwrite = True)
        if data_prod is not None:
            if technology_name == 'Hydro':
                P_max = data_prod['Inflow [GWh]'][[hour.strftime('%Y-%m-%dT%H:%M:%SZ') for hour in self.network.snapshots]]
                self.network.add('Generator', carrier=carrier_name, name=carrier_name, 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost, p_max=P_max.values)
            else:
                CF = data_prod[self.country][[hour.strftime('%Y-%m-%dT%H:%M:%SZ') for hour in self.network.snapshots]]
                self.network.add('Generator', carrier=carrier_name, name=carrier_name, 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost, p_max_pu=CF.values)
        else:
            self.network.add('Generator', carrier=carrier_name, name=carrier_name, 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost/efficiency)

    def add_co2_constraints(self, year):
        """Add a CO2 constraint, with a co2_limit in tCO2/year"""
        #Regarding the historical emissions of the electrical mix in France, we have:
        co2_limit_2019 = 20000000 #tCO2/year
        co2_limit_1990 = 45000000 #tCO2/year
        if year == 1990:
            co2_limit = co2_limit_1990
        co2_limit = co2_limit_2019

        self.network.add("GlobalConstraint",
            "co2_limit",
            type="primary_energy",
            carrier_attribute="co2_emissions",
            sense="<=",
            constant=co2_limit)

    def add_storage(self, technology_name: str, capex_pow: float, capex_en: float, opex_fixed_pow:float, opex_fixed_en:float, marginal_cost: float, lifetime: int, efficiency: float, CO2_emissions: float, energy_power_ratio: int):
        carrier_name = technology_name
        self.network.add('Carrier', carrier_name, co2_emissions = CO2_emissions)
        annualized_cost = utils.annuity(lifetime, 0.07)*(capex_en*energy_power_ratio + capex_pow + opex_fixed_en*energy_power_ratio + opex_fixed_pow)

        self.network.add('StorageUnit', technology_name, 
                         carrier = technology_name, bus = self.name, p_nom_extendable = True, 
                         capital_cost = annualized_cost, marginal_cost = marginal_cost/efficiency,
                         cyclic_state_of_charge=True, max_hours = energy_power_ratio, 
                         efficiency_store = efficiency, efficiency_dispatch = efficiency,)
        
    def optimize(self):
        self.network.optimize(solver_name='gurobi')
        self.objective_value = self.network.objective/1000000 # in 10^6 € (or M€)
        self.electricity_price = self.network.objective/self.network.loads_t.p.sum()

    def plot_line(self):
        plt.plot(self.network.loads_t.p['load'][0:96], color='black', label='demand')
        colors=['blue', 'orange', 'brown']
        for i, generator in enumerate(self.network.generators_t.p.columns):
            plt.plot(self.network.generators_t.p[str(generator)][0:96], color=colors[i], label=str(generator))
        plt.legend(fancybox=True, loc='best')
        plt.show()
    
    def plot_storage(self):
        colors = ['yellow']
        for i, storage_unit in enumerate(self.network.storage_units_t.p.columns):
            plt.plot(self.network.storage_units_t.p[str(storage_unit)][0:96], color = colors[i], label = str(storage_unit))
        plt.legend(fancybox=True, loc='best')
        plt.show()

    def plot_pie(self):
        labels = [str(generator) for generator in self.network.generators_t.p.columns]
        sizes = [self.network.generators_t.p[generator].sum() for generator in self.network.generators_t.p.columns]
        colors=['blue', 'orange', 'brown']
        plt.pie(sizes,
                colors=colors,
                labels=labels,
                wedgeprops={'linewidth':0})
        plt.axis('equal')

        plt.title('Electricity mix', y=1.07)
        plt.show()

    def plot_dispatch(self, time):
        p_by_gen = self.network.generators_t.p.div(1e3)

        if not self.network.storage_units.empty:
            sto = self.network.storage_units_t.p.div(1e3)
            p_by_gen = pd.concat([p_by_gen, sto], axis =1)
        
        fig, ax = plt.subplots(figsize=(6, 3))

        p_by_gen.where(p_by_gen > 0).loc[f'{time}'].plot.area(ax=ax, linewidth = 0)

        charge = p_by_gen.where(p_by_gen < 0).dropna(how="all", axis=1).loc[time]

        if not charge.empty:
            charge.plot.area(ax=ax, linewidth = 0)
        
        self.network.loads_t.p_set.sum(axis=1).loc[time].div(1e3).plot(ax=ax, c="k", linewidth = 1)

        plt.legend(loc=(0.7, 0))
        ax.set_ylabel("GW")
        ax.set_ylim(-200, 200)
        plt.title (f'Optimal dispatch {time}')
        plt.show()



# Load Data
df_onshorewind = pd.read_csv('data/onshore_wind_1979-2017.csv', sep=';', index_col = 0)
df_onshorewind.index = pd.to_datetime(df_onshorewind.index)
df_solar = pd.read_csv('data/pv_optimal.csv', sep=';', index_col=0)
df_solar.index = pd.to_datetime(df_solar.index)
df_offshorewind = pd.read_csv('data/offshore_wind_1979-2017.csv', sep=';', index_col=0)
df_offshorewind.index = pd.to_datetime(df_solar.index)
df_hydro = pd.read_csv('data/Hydro_Inflow_FR.csv', sep=',')
df_hydro.index = pd.to_datetime(df_hydro[['Year', 'Month', 'Day']])
df_hydro = df_hydro.resample('h').ffill()
df_hydro['Inflow [GWh]'] = df_hydro['Inflow [GWh]']/24 #Hourly value

costs = pd.read_csv('data/costs.csv')

france_net = BusElectricity('FRA', 2015)

# Add onshore wind generator
france_net.add_generator('onshorewind', 910000, 0.033*910000, 0, 30, 1, 0, df_onshorewind)

# Add solar PV generator
france_net.add_generator('solar', 425000, 0.03*425000, 0, 25, 1, 0, df_solar)

# Add OCFT (Open Cycle Gas Turbine) generator
france_net.add_generator('OCGT', 560000, 0.033*560000, 21.6, 25, 0.39, 10)

#Add a storage unit (same as exercise session 9)
france_net.add_storage('Battery', 24678, 12894, 0, 0, 0, 20, 0.96, 0, 2)

# Optimize
france_net.optimize()

#france_net.plot_line()
#france_net.plot_pie()
#france_net.plot_storage()
france_net.plot_dispatch('2015-11')
