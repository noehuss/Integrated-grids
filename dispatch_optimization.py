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
        self.network.add('Carrier', carrier_name, co2_emissions=CO2_emissions)
        if data_prod is not None:
            CF = data_prod[self.country][[hour.strftime('%Y-%m-%dT%H:%M:%SZ') for hour in self.network.snapshots]]
            self.network.add('Generator', carrier=carrier_name, name=carrier_name, 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost, p_max_pu=CF.values)
        else:
            self.network.add('Generator', carrier=carrier_name, name=carrier_name, 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost/efficiency)

    def add_co2_constraints(self, co2_limit):
        """Add a CO2 constraint, with a co2_limit in tCO2/year"""

        self.network.add("GlobalConstraint",
            "co2_limit",
            type="primary_energy",
            carrier_attribute="co2_emissions",
            sense="<=",
            constant=co2_limit)

    def add_storage(self):
        pass

    def optimize(self):
        self.network.optimize(solver_name='gurobi')
        self.objective_value = self.network.objective/1000000 # in 10^6 €
        self.electricity_price = self.network.objective/self.network.loads_t.p.sum()

    def plot_line(self):
        plt.plot(self.network.loads_t.p['load'][0:96], color='black', label='demand')
        colors=['blue', 'orange', 'brown']
        for i, generator in enumerate(self.network.generators_t.p.columns):
            plt.plot(self.network.generators_t.p[str(generator)][0:96], color=colors[i], label=str(generator))
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

# Load Data
df_onshorewind = pd.read_csv('data/onshore_wind_1979-2017.csv', sep=';', index_col = 0)
df_onshorewind.index = pd.to_datetime(df_onshorewind.index)
df_solar = pd.read_csv('data/pv_optimal.csv', sep=';', index_col=0)
df_solar.index = pd.to_datetime(df_solar.index)

france_net = BusElectricity('FRA', 2015)
# Add onshore wind generator
france_net.add_generator('onshorewind', 910000, 0.033*910000, 0, 30, 1, 0, df_onshorewind)

# Add solar PV generator
france_net.add_generator('solar', 425000, 0.03*425000, 0, 25, 1, 0, df_solar)

# Add OCFT (Open Cycle Gas Turbine) generator
france_net.add_generator('OCGT', 560000, 0.033*560000, 21.6, 25, 0.39, 10)

# Optimize
france_net.optimize()

france_net.plot_line()
france_net.plot_pie()
