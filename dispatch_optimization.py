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
        hours_in_year = pd.date_range(f'{self.year}01-01 00:00Z',
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
        if data_prod:
            CF = data_prod[self.country][[hour.strftime('%Y-%m-%dT%H:%M:%SZ') for hour in self.network.snapshots]]
            self.network.add('Generator', carrier=carrier_name, name=f'{self.country}_{technology_name}', 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost, efficiency=efficiency, p_max_pu=CF.values)
        else:
            self.network.add('Generator', carrier=carrier_name, name=f'{self.country}_{technology_name}', 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost, efficiency=efficiency)

    def add_co2_constraints(self):
        pass

    def add_storage(self):
        pass



    def optimize(self):
        self.network.optimize(solver_name='gurobi')
        self.objective_value = self.network.objective/1000000 # in 10^6 €
        self.electricity_price = self.network.objective/self.network.loads_t.p.sum()



# plt.plot(network.loads_t.p['load'][0:96], color='black', label='demand')
# plt.plot(network.generators_t.p['onshorewind'][0:96], color='blue', label='onshore wind')
# plt.plot(network.generators_t.p['solar'][0:96], color='orange', label='solar')
# plt.plot(network.generators_t.p['OCGT'][0:96], color='brown', label='gas (OCGT)')
# plt.legend(fancybox=True, loc='best')
# plt.show()

# labels = ['onshore wind',
#           'solar',
#           'gas (OCGT)']
# sizes = [network.generators_t.p['onshorewind'].sum(),
#          network.generators_t.p['solar'].sum(),
#          network.generators_t.p['OCGT'].sum()]

# colors=['blue', 'orange', 'brown']

# plt.pie(sizes,
#         colors=colors,
#         labels=labels,
#         wedgeprops={'linewidth':0})
# plt.axis('equal')

# plt.title('France electricity mix', y=1.07)
# plt.show()