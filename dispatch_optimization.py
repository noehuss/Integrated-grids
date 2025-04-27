import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import utils
import param

class BusElectricity():
    def __init__(self, country:str, year:int, technologies):
        self.country = country
        self.year = year
        self.name = f'{country} electriciy'
        self.network = pypsa.Network()
        hours_in_year = pd.date_range(f'{self.year}-01-01 00:00Z',
                              f'{self.year}-12-31 23:00Z',
                              freq='h')
        hours_in_year = hours_in_year[~((hours_in_year.month == 2) & (hours_in_year.day == 29))]
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

        for key, df in technologies.items():
            self.add_generator(key, param.costs.loc[key, 'CAPEX'], param.costs.loc[key, 'FOM'],
                            param.costs.loc[key, 'VOM'], param.costs.loc[key, 'Fuel'], param.costs.loc[key, 'Lifetime'],
                            param.costs.loc[key, 'Efficiency'], param.costs.loc[key, 'CO2'], df)

        

    def add_generator(self, technology_name:str, capex:float, opex_fixed:float ,opex_variable: float, fuel_cost:float, lifetime:int, efficiency:float, CO2_emissions:float, data_prod=None):
        """
        Add a generator in our network object.
        """
        annualized_cost = utils.annuity(lifetime, 0.07)*capex*(1+opex_fixed/capex)
        marginal_cost = opex_variable + fuel_cost/efficiency
        carrier_name = technology_name
        self.network.add('Carrier', carrier_name, co2_emissions=CO2_emissions, overwrite = True)
        if data_prod is not None:
            if technology_name == 'Hydro':
                P_max_pu = data_prod['Inflow pu'][[hour.strftime('2010-%m-%d %H:%M:%S') for hour in self.network.snapshots]]
                self.network.add('Generator', carrier=carrier_name, name=carrier_name, 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost, p_max_pu=P_max_pu.values, p_nom_max = 1000*data_prod['Inflow [GW]'].max())
            else:
                CF = data_prod[self.country][[hour.strftime('%Y-%m-%dT%H:%M:%SZ') for hour in self.network.snapshots]]
                self.network.add('Generator', carrier=carrier_name, name=carrier_name, 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost, p_max_pu=CF.values)
        else:
            self.network.add('Generator', carrier=carrier_name, name=carrier_name, 
                         bus = self.name, p_nom_extendable = True, capital_cost=annualized_cost, 
                         marginal_cost=marginal_cost, efficiency=efficiency)

    def add_co2_constraints(self, co2_limit:float):
        """Add a CO2 constraint, with a co2_limit in tCO2/year"""
        self.network.add("GlobalConstraint",
            "co2_limit",
            #type="primary_energy",
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
                         efficiency_store = efficiency, efficiency_dispatch = efficiency)
        
    def optimize(self):
        self.network.optimize(solver_name='gurobi')
        self.objective_value = self.network.objective/1000000 # in 10^6 € (or M€)
        self.electricity_price = self.network.objective/self.network.loads_t.p.sum()

    def plot_line(self, start_date, end_date):
        origin = pd.Timestamp(f"{self.year}-01-01 00:00")
        start_index= int((start_date-origin).total_seconds()/3600)
        end_index= int((end_date-origin).total_seconds()/3600)
        plt.plot(self.network.loads_t.p['load'][start_index:end_index], color='black', label='Demand')
        producers = [generator for generator in self.network.generators.loc[self.network.generators.p_nom_opt !=0].index]
        for i, generator in enumerate(producers):
            plt.plot(self.network.generators_t.p[str(generator)][start_index:end_index], label=str(generator), color=param.colors[str(generator)])
        plt.legend(fancybox=True, loc='best')
        plt.xlabel('Time')
        plt.ylabel('Electricity production (MWh)')
        plt.grid(linewidth='0.4', linestyle='--')
        #plt.title('Electricity production dispatch')
        plt.show()
    
    def plot_storage(self,start_date, end_date):
        origin = pd.Timestamp(f"{self.year}-01-01 00:00")
        start_index= int((start_date-origin).total_seconds()/3600)
        end_index= int((end_date-origin).total_seconds()/3600)
        colors = ['yellow']
        for i, storage_unit in enumerate(self.network.storage_units_t.p.columns):
            plt.plot(self.network.storage_units_t.p[str(storage_unit)][start_index:end_index], color = colors[i], label = str(storage_unit))
        plt.legend(fancybox=True, loc='best')
        plt.show()

    def plot_pie(self):
        labels = [generator for generator in self.network.generators.loc[self.network.generators.p_nom_opt !=0].index]
        sizes = [self.network.generators_t.p[generator].sum() for generator in labels]
        colors = [param.colors[generator] for generator in labels]
        plt.pie(sizes,
                colors=colors,
                labels=labels,
                autopct=lambda pct: f"{pct:.1f}%",
                wedgeprops={'linewidth':0})
        plt.axis('equal')

        #plt.title('Electricity mix', y=1.07)
        plt.show()

    def plot_duration_curve(self):
        fig, (ax1, ax2) = plt.subplots(1, 2)
        producers = [generator for generator in self.network.generators.loc[self.network.generators.p_nom_opt !=0].index]
        for i, generator in enumerate(producers):
            ax1.plot(self.network.generators_t.p[str(generator)].sort_values(ascending=False,ignore_index=True),
                     color=param.colors[str(generator)],
                     label=str(generator))
            cf = self.network.generators_t.p[str(generator)].sort_values(ascending=False,ignore_index=True)/self.network.generators.p_nom_opt[generator]
            ax2.plot(cf, color=param.colors[str(generator)],
                     label=str(generator))
        ax1.legend(fancybox=True, loc='best')
        ax1.set(xlabel='Hours', ylabel='Electricity production (MW)')
        ax1.grid(linewidth='0.4', linestyle='--')
        ax2.legend(fancybox=True, loc='best')
        ax2.set(xlabel='Hours', ylabel='Capacity factor')
        ax2.grid(linewidth='0.4', linestyle='--')
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
        #ax.set_ylim(-200, 200)
        plt.title (f'Optimal dispatch {time}')
        plt.show()

    def return_production_mix(self) -> pd.DataFrame:
        return self.network.generators_t.p.sum()
    
    def return_capacity_mix(self) -> pd.DataFrame:
        return self.network.generators.p_nom_opt


france_net = BusElectricity('FRA', param.year, technologies=param.technologies_france)


# Add CO2 constraints
# france_net.add_co2_constraints(param.co2_limit_2019)

# Add a storage unit (same as exercise session 9)
# france_net.add_storage('Battery', 24678, 12894, 0, 0, 0, 20, 0.96, 0, 2)

# # Optimize
# france_net.optimize()

# #france_net.plot_duration_curve()
# start_date_winter=pd.Timestamp(f"{param.year}-01-01 00:00")
# end_date_winter= pd.Timestamp(f"{param.year}-01-08 00:00")
# start_date_summer=pd.Timestamp(f"{param.year}-07-01 00:00")
# end_date_summer= pd.Timestamp(f"{param.year}-07-08 00:00")

# france_net.plot_line(start_date_winter, end_date_winter)
# france_net.plot_line(start_date_summer, end_date_summer)
# france_net.plot_pie()
# #france_net.plot_storage()
# #france_net.plot_dispatch(f'{year}-01')

# print(france_net.network.generators)
# print(france_net.network.carriers)
# print(-france_net.network.global_constraints.mu)
# print(france_net.network.generators.marginal_cost)

# print([generator for generator in france_net.network.generators.loc[france_net.network.generators.p_nom_opt !=0].index])

