import pypsa
import pandas as pd
import matplotlib.pyplot as plt
import utils
import param
import cartopy.crs as ccrs
import cartopy.feature as cf
import numpy as np


class BusElectricity():
    def __init__(self, country: str, year: int, technologies, storage_technologies=None, network=pypsa.Network(), single_node: bool = True):
        self.country = country
        self.year = year
        self.name = f'{country} electriciy'
        self.network = network
        self.single_node = single_node
        hours_in_year = pd.date_range(f'{self.year}-01-01 00:00Z',
                                      f'{self.year}-12-31 23:00Z',
                                      freq='h')
        hours_in_year = hours_in_year[~(
            (hours_in_year.month == 2) & (hours_in_year.day == 29))]
        self.network.set_snapshots(hours_in_year.values)
        self.network.add(
            'Bus', self.name, y=param.country_coords[country][0], x=param.country_coords[country][1],)
        # Load electricity demand data
        df_elec = pd.read_csv('data/electricity_demand.csv',
                              sep=';', index_col=0)  # in MWh
        df_elec.index = pd.to_datetime(
            df_elec.index)  # change index to datetime
        # Add load to the bus
        self.network.add("Load",
                         f"{self.country} load",
                         bus=self.name,
                         p_set=df_elec[self.country].values)

        self.objective_value = 0
        self.electricity_price = 0
        self.technologies = technologies
        self.populate_generators()
        if storage_technologies:
            self.storage_technologies = storage_technologies
            self.populate_storage()

    def populate_generators(self):
        for key, df in self.technologies.items():
            self.add_generator(key, param.costs.loc[key, 'CAPEX'], param.costs.loc[key, 'FOM'],
                               param.costs.loc[key, 'VOM'], param.costs.loc[key,'Fuel'], param.costs.loc[key, 'Lifetime'],
                               param.costs.loc[key, 'Efficiency'], param.costs.loc[key, 'CO2'], df)
    def populate_storage(self):
        for key, df in self.storage_technologies.items():
            self.add_storage(key, param.costs_store.loc[key, 'Max capacity'], 
                            param.costs_store.loc[key, 'CAPEX power'], param.costs_store.loc[key, 'CAPEX energy'], 
                            param.costs_store.loc[key, 'OPEX fixed power'], param.costs_store.loc[key, 'OPEX fixed energy'], 
                            param.costs_store.loc[key, 'Marginal cost'], param.costs_store.loc[key, 'lifetime'], 
                            param.costs_store.loc[key, 'efficiency'], param.costs_store.loc[key, 'CO2 emissions'],
                            param.costs_store.loc[key, 'Energy power ratio'])
        

    def add_generator(self, technology_name: str, capex: float, opex_fixed: float, opex_variable: float, fuel_cost: float, lifetime: int, efficiency: float, CO2_emissions: float, data_prod=None):
        """
        Add a generator in our network object.
        """
        annualized_cost = utils.annuity(
            lifetime, 0.07)*capex*(1+opex_fixed/capex)
        marginal_cost = opex_variable + fuel_cost/efficiency
        carrier_name = technology_name
        self.network.add('Carrier', carrier_name,
                         co2_emissions=CO2_emissions, overwrite=True)
        generator_name = technology_name if self.single_node else f"{self.country} {technology_name}"

        if data_prod is not None:
            if technology_name == 'Hydro':
                P_max_pu = data_prod['Inflow pu'][[hour.strftime(
                    '2010-%m-%d %H:%M:%S') for hour in self.network.snapshots]]
                self.network.add('Generator', carrier=carrier_name, name=generator_name,
                                 bus=self.name, p_nom_extendable=True, capital_cost=annualized_cost,
                                 marginal_cost=marginal_cost, p_max_pu=P_max_pu.values, p_nom_max=1000*data_prod['Inflow [GW]'].max())
            else:
                CF = data_prod[self.country][[hour.strftime(
                    '%Y-%m-%dT%H:%M:%SZ') for hour in self.network.snapshots]]
                self.network.add('Generator', carrier=carrier_name, name=generator_name,
                                 bus=self.name, p_nom_extendable=True, capital_cost=annualized_cost,
                                 marginal_cost=marginal_cost, p_max_pu=CF.values)
        else:
            self.network.add('Generator', carrier=carrier_name, name=generator_name,
                             bus=self.name, p_nom_extendable=True, capital_cost=annualized_cost,
                             marginal_cost=marginal_cost, efficiency=efficiency)

    def add_bus(self) -> pypsa.Network:
        return self.network

    def add_co2_constraints(self, co2_limit: float):
        """Add a CO2 constraint, with a co2_limit in tCO2/year"""
        self.network.add("GlobalConstraint",
                         "co2_limit",
                         # type="primary_energy",
                         carrier_attribute="co2_emissions",
                         sense="<=",
                         constant=co2_limit)
    
    def add_sector(self, sector_name: str, demand, storage: bool = False, bidirectional: bool = False):
        self.network.add('Bus', f'FR {sector_name}', carrier = sector_name)
        self.network.add('Load', f'{sector_name} demand', bus = f'FR {sector_name}', p_set = demand)

        if sector_name == 'Hydrogen':
            capex_electrolyser = param.capex_electrolyser
            self.network.add('Link', 'Electrolyser', 
                             bus0 = self.name, bus1 = f'FR {sector_name}', 
                             carrier = 'electrolysis', 
                             p_nom_extendable = True, efficiency = 0.7,
                             capital_cost = capex_electrolyser)
            if storage:
                capex_store = param.capex_salt_cavern
                self.network.add('Store', 'Hydrogen Storage', 
                             bus = f'FR {sector_name}', 
                             e_nom_extendable = True, e_initial = 0, 
                             capital_cost = capex_store)
                
            if bidirectional:
                CCGTH2_capex = param.capex_ccgt_H2
                self.network.add('Link', 'CCGT H2', 
                                 bus0 = f'FR {sector_name}', bus1 = self.name, 
                                 carrier = 'CCGT H2',
                                 p_nom_extendable = True, efficiency = 0.45,
                                 capital_cost = CCGTH2_capex)
    
    def plot_electrolysis(self, start_date, end_date):
        origin = pd.Timestamp(f"{self.year}-01-01 00:00")
        start_index = int((start_date-origin).total_seconds()/3600)
        end_index = int((end_date-origin).total_seconds()/3600)

        # Calculate the difference between electrolysis production and hydrogen demand
        net_hydrogen = -self.network.links_t.p1['Electrolyser'][start_index:end_index] - param.hourly_hydrogen_demand[start_index:end_index]

        # Create the figure and axes
        fig, ax1 = plt.subplots(figsize=(10, 6))
        ax2 = ax1.twinx()

        # Plot electrolysis production and hydrogen demand difference
        ax1.plot(net_hydrogen, label='Net Hydrogen (Electrolysis - Demand)', color='blue', linestyle='-', linewidth=2)
        ax1.fill_between(net_hydrogen.index, 0, net_hydrogen, where=(net_hydrogen > 0), color='blue', alpha=0.2, label='Excess Hydrogen')

        # Plot hydrogen storage evolution
        ax2.plot(self.network.stores_t.e['Hydrogen Storage'][start_date:end_date], label='Hydrogen Storage', color='orange', linestyle='--', linewidth=2, marker='o')

        # Customize the axes
        ax1.set_xlabel('Time', fontsize=12)
        ax1.set_ylabel('Net Hydrogen (MW)', fontsize=12, color='blue')
        ax2.set_ylabel('Hydrogen Storage (MWh)', fontsize=12, color='orange')

        # Add legends
        ax1.legend(loc='upper left', fontsize=10, fancybox=True)
        ax2.legend(loc='upper right', fontsize=10, fancybox=True)

        # Add grid and improve layout
        ax1.grid(linewidth=0.4, linestyle='--', alpha=0.7)
        #plt.title('Hydrogen Electrolysis and Storage Dynamics', fontsize=14, fontweight='bold')
        plt.tight_layout()

        # Show the plot
        plt.show()
        start_index = int((start_date-origin).total_seconds()/3600)
        end_index = int((end_date-origin).total_seconds()/3600)
        
    
    def plot_electrolysis_storage(self, start_date, end_date):
        plt.plot(self.network.stores_t.e['Hydrogen Storage'].loc[start_date:end_date], label='Hydrogen storage', color = 'blue')
        plt.legend(fancybox = 'True', loc = 'best')
        plt.xlabel('Time')
        plt.ylabel('Hydrogen storage')
        plt.grid(linewidth='0.4', linestyle='--')
        plt.show()



    def add_storage(self, technology_name: str, max_cap: float, capex_pow: float, capex_en: float, opex_fixed_pow: float, opex_fixed_en: float, marginal_cost: float, lifetime: int, efficiency: float, CO2_emissions: float, energy_power_ratio: int):
        carrier_name = technology_name
        self.network.add('Carrier', carrier_name, co2_emissions=CO2_emissions)
        annualized_cost = utils.annuity(lifetime, 0.07)*(
            capex_en*energy_power_ratio + capex_pow + opex_fixed_en*energy_power_ratio + opex_fixed_pow)

        storage_name = technology_name if self.single_node else f"{self.country} {technology_name}"

        if max_cap > 500000:
            self.network.add('StorageUnit', storage_name,
                             carrier=technology_name, bus=self.name, p_nom_extendable=True,
                             capital_cost=annualized_cost, marginal_cost=marginal_cost/efficiency,
                             cyclic_state_of_charge=True, max_hours=energy_power_ratio,
                             efficiency_store=efficiency, efficiency_dispatch=efficiency)

        else:
            self.network.add('StorageUnit', storage_name,
                             carrier=technology_name, bus=self.name, p_nom_extendable=True, p_nom_max=max_cap,
                             capital_cost=annualized_cost, marginal_cost=marginal_cost/efficiency,
                             cyclic_state_of_charge=True, max_hours=energy_power_ratio,
                             efficiency_store=efficiency, efficiency_dispatch=efficiency)

    def optimize(self):
        self.network.optimize(solver_name='gurobi')
        self.objective_value = self.network.objective / \
            1000000  # in 10^6 € (or M€)
        self.electricity_price = (self.network.objective/self.network.loads_t.p.sum())[0]

    def plot_line(self, start_date, end_date):
        origin = pd.Timestamp(f"{self.year}-01-01 00:00")
        start_index = int((start_date-origin).total_seconds()/3600)
        end_index = int((end_date-origin).total_seconds()/3600)
        plt.plot(
            self.network.loads_t.p[f'{self.country} load'][start_index:end_index], color='black', label='Demand')
        producers = [
            generator for generator in self.network.generators.loc[self.network.generators.p_nom_opt != 0].index]
        for i, generator in enumerate(producers):
            plt.plot(self.network.generators_t.p[str(generator)][start_index:end_index], label=str(
                generator), color=param.colors[str(generator)])
        plt.legend(fancybox=True, loc='best')
        plt.xlabel('Time')
        plt.ylabel('Electricity production (MWh)')
        plt.grid(linewidth='0.4', linestyle='--')
        # plt.title('Electricity production dispatch')
        plt.show()

    def plot_storage(self, start_date, end_date):
        origin = pd.Timestamp(f"{self.year}-01-01 00:00")
        start_index = int((start_date-origin).total_seconds()/3600)
        end_index = int((end_date-origin).total_seconds()/3600)
        plt.figure()
        for i, storage_unit in enumerate(self.network.storage_units_t.p.columns):
            plt.plot(self.network.storage_units_t.p[str(
                storage_unit)][start_index:end_index], color=param.colors[str(storage_unit)], label=str(storage_unit))
        plt.legend(fancybox=True, loc='best')
        plt.show()

    def plot_pie(self, production: bool = True):
        labels = [
            generator for generator in self.network.generators.loc[self.network.generators.p_nom_opt != 0].index]
        if production:
            sizes = [self.network.generators_t.p[generator].sum()
                     for generator in labels]
        else:
            sizes = [self.network.generators.p_nom_opt[generator]
                     for generator in labels]
        colors = [param.colors[generator] for generator in labels]
        plt.pie(sizes,
                colors=colors,
                labels=labels,
                autopct=lambda pct: f"{pct:.1f}%",
                wedgeprops={'linewidth': 0})
        plt.axis('equal')

        # plt.title('Electricity mix', y=1.07)
        plt.show()

    def plot_duration_curve(self):
        fig, (ax1, ax2) = plt.subplots(1, 2)
        producers = [
            generator for generator in self.network.generators.loc[self.network.generators.p_nom_opt != 0].index]
        for i, generator in enumerate(producers):
            ax1.plot(self.network.generators_t.p[str(generator)].sort_values(ascending=False, ignore_index=True),
                     color=param.colors[str(generator)],
                     label=str(generator))
            cf = self.network.generators_t.p[str(generator)].sort_values(
                ascending=False, ignore_index=True)/self.network.generators.p_nom_opt[generator]
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
        print(p_by_gen)
        if not self.network.storage_units.empty:
            sto = self.network.storage_units_t.p.div(1e3)
            p_by_gen = pd.concat([p_by_gen, sto], axis=1)

        fig, ax = plt.subplots(figsize=(6, 3))

        gen = p_by_gen.where(p_by_gen >= 0).loc[f'{time}']
        print(gen)
        labels_p = [str(generator) for generator in gen.columns]
        colors_p = [param.colors[generator] for generator in gen.columns]
        ax.stackplot(gen.index, gen.T, colors=colors_p, labels=labels_p)

        charge = p_by_gen.where(p_by_gen < 0).dropna(
            how="all", axis=1).loc[time]

        if not charge.empty:
            labels_ch = [str(storage) for storage in charge.columns]
            colors_ch = [param.colors[storage] for storage in charge.columns]
            ax.stackplot(charge.index, charge.T, colors=colors_ch)
        
        load = self.network.loads_t.p_set.sum(axis=1).loc[time].div(1e3)
        ax.plot(load, label='Load', color='black')
        # self.network.loads_t.p_set.sum(axis=1).loc[time].div(1e3).plot(ax=ax, c="k", linewidth = 1)

        plt.legend()
        ax.set_ylabel("GW")
        # ax.set_ylim(-200, 200)
        plt.title(f'Optimal dispatch {time}')
        plt.show()

    def return_production_mix(self) -> pd.DataFrame:
        return self.network.generators_t.p.sum()

    def return_capacity_mix(self) -> pd.DataFrame:
        return self.network.generators.p_nom_opt


class ExistingBusElectricity(BusElectricity):
    def populate_generators(self):
        for key, dict in self.technologies.items():
            self.add_generator(key, param.costs.loc[key, 'CAPEX'], param.costs.loc[key, 'FOM'],
                            param.costs.loc[key, 'VOM'], param.costs.loc[key, 'Fuel'], param.costs.loc[key, 'Lifetime'],
                            param.costs.loc[key, 'Efficiency'], param.costs.loc[key, 'CO2'], p_min=dict['p_min'], p_max=dict['p_max'], data_prod=dict['df'])

    def add_generator(self, technology_name, capex, opex_fixed, opex_variable, fuel_cost, lifetime, efficiency, CO2_emissions, p_min, p_max, data_prod=None):
        """
        Add a generator in our network object.
        """
        annualized_cost = utils.annuity(
            lifetime, 0.07)*capex*(1+opex_fixed/capex)
        marginal_cost = opex_variable + fuel_cost/efficiency
        carrier_name = technology_name
        self.network.add('Carrier', carrier_name,
                         co2_emissions=CO2_emissions, overwrite=True)
        generator_name = technology_name if self.single_node else f"{self.country} {technology_name}"
        print(data_prod)
        if data_prod is not None:
            if technology_name == 'Hydro':
                P_max_pu = data_prod['Inflow pu'][[hour.strftime(
                    '2010-%m-%d %H:%M:%S') for hour in self.network.snapshots]]
                p_max = max(p_min, 1000*data_prod['Inflow [GW]'].max())
                self.network.add('Generator', carrier=carrier_name, name=generator_name,
                                 bus=self.name, p_nom_extendable=True, capital_cost=annualized_cost,
                                 marginal_cost=marginal_cost, p_max_pu=P_max_pu.values, p_nom_max=p_max, p_nom_min=p_min)
            else:
                CF = data_prod[self.country][[hour.strftime(
                    '%Y-%m-%dT%H:%M:%SZ') for hour in self.network.snapshots]]
                self.network.add('Generator', carrier=carrier_name, name=generator_name,
                                 bus=self.name, p_nom_extendable=True, capital_cost=annualized_cost,
                                 marginal_cost=marginal_cost, p_max_pu=CF.values, p_nom_min = p_min, p_nom_max=p_max)
        else:
            self.network.add('Generator', carrier=carrier_name, name=generator_name,
                             bus=self.name, p_nom_extendable=True, capital_cost=annualized_cost,
                             marginal_cost=marginal_cost, efficiency=efficiency, p_nom_min = p_min, p_nom_max=p_max)

class NetworkElectricity():
    def __init__(self, year: int):
        self.network = pypsa.Network()
        self.year = year

    def add_country(self, country_name, technologies):
        self.network = BusElectricity(
            country=country_name, year=self.year, technologies=technologies, single_node=False).add_bus()

    def add_line(self, country0: str, country1: str, capacity: float, reactance: float, resistance: float, capital_cost: float, extendable: bool):
        self.network.add('Line', f"{country0}-{country1}",
                         bus0=f'{country0} electriciy',
                         bus1=f'{country1} electriciy',
                         s_nom=capacity,
                         x=reactance,
                         r=resistance,
                         capital_cost=capital_cost,
                         s_nom_extendable=extendable,
                         overwrite=True)

    def add_co2_constraints(self, co2_limit: float):
        """Add a CO2 constraint, with a co2_limit in tCO2/year"""
        self.co2_limit = co2_limit
        self.network.add("GlobalConstraint",
                         "co2_limit",
                         # type="primary_energy",
                         carrier_attribute="co2_emissions",
                         sense="<=",
                         constant=co2_limit)

    def optimize(self):
        self.network.optimize(solver_name='gurobi')
        # self.objective_value = self.network.objective/1000000 # in 10^6 € (or M€)
        # self.electricity_price = self.network.objective/self.network.loads_t.p.sum()

    def generation(self):
        print(self.network.generators_t.p.sum(axis=0).groupby(
            [self.network.generators.bus, self.network.generators.carrier]).sum().div(1e6).round(1))

    def plot(self):
        self.network.plot(bus_sizes=1, margin=1)
        plt.show()

    def energy(self):
        print(self.network.lines_t.p0.abs().sum(axis=0))

    def energy_dir(self):
        flows = self.network.lines_t.p0.sum(axis=0)
        for line_name, flow in flows.items():
            bus0 = self.network.lines.loc[line_name, "bus0"]
            bus1 = self.network.lines.loc[line_name, "bus1"]
            direction = f"{bus0} → {bus1}" if flow > 0 else f"{bus1} → {bus0}"
            print(f"{line_name}: {(flow):.2f} MWh, Direction: {direction}")

    def line_capacity(self):
        print(self.network.lines.s_nom_opt)

    def return_production_mix(self):
        production = self.network.generators_t.p
        carriers = self.network.generators.carrier
        production_mix = pd.DataFrame(index=production.index)
        for carrier in carriers.unique():
            generators_of_carrier = carriers[carriers == carrier].index
            production_mix[carrier] = production[generators_of_carrier].sum(axis=1)
        return production_mix

    def plot_map(self):
        # Setup map projection
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={
                               'projection': ccrs.PlateCarree()})

        # Add map features
        ax.add_feature(cf.BORDERS, linestyle=':')
        ax.add_feature(cf.COASTLINE)

        # Ensure buses have a 'country' column
        self.network.buses['country'] = self.network.buses.index.str.split(
        ).str[0]

        techs = ['CCGT', 'OCGT', 'Nuclear', 'PV',
                 'Wind Offshore', 'Wind Onshore', 'Hydro', 'TACH2']

        # Prepare generation data
        gen_mix = self.network.generators.copy()
        gen_mix['country'] = gen_mix.bus.map(
            lambda x: self.network.buses.loc[x, 'country'])
        gen_mix["p_nom_opt"] = gen_mix["p_nom_opt"]/1e3
        generation_sum = self.network.generators_t.p.sum().div(1e6)
        grouped = gen_mix.groupby(['country', 'carrier'])

        gen = {
            country: {
                tech: generation_sum[gen_mix[(gen_mix.country == country) & (
                    gen_mix.carrier == tech)].index].sum()
                for tech in techs
            }
            for country in self.network.buses.country.unique()
        }

        # Calculate transmitted energy for each line
        transmitted_energy = self.network.lines_t.p0.abs().sum(axis=0)
        average_flow = self.network.lines_t.p0.mean(axis=0)
        capacity_lines = self.network.lines.s_nom_opt

        # Normalize transmitted energy for color mapping
        energy_norm = plt.Normalize(
            transmitted_energy.min(), transmitted_energy.max())
        cmap = plt.cm.viridis

        # Draw transmission lines
        for i, line in self.network.lines.iterrows():
            bus0 = self.network.buses.loc[line.bus0]
            bus1 = self.network.buses.loc[line.bus1]
            x0, y0 = bus0.x, bus0.y
            x1, y1 = bus1.x, bus1.y

            flow = average_flow[i]
            energy = transmitted_energy[i]
            capacity = capacity_lines[i]
            width = capacity / 3e3  # scale appropriately
            print("energy: ", energy, "   width: ",
                  width, "    Capacity", capacity)

            if flow >= 0:
                x_start, y_start = x0, y0
                x_end, y_end = x1, y1
            else:
                x_start, y_start = x1, y1
                x_end, y_end = x0, y0

            # Plot the full transmission line as a plain line
            ax.plot([x0, x1], [y0, y1],
                    color=cmap(energy_norm(energy)), linewidth=width,
                    transform=ccrs.PlateCarree(), zorder=1)

            # Midpoint of the line
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2

            # Arrow at the middle of the line in the right direction
            mx, my = (x_start + x_end) / 2, (y_start + y_end) / 2
            dx, dy = x_end - x_start, y_end - y_start
            euclidian_norm = (dx**2 + dy**2)**0.5
            dx /= euclidian_norm
            dy /= euclidian_norm

            # Arrow length
            arrow_len = 0.01  # degrees or scaled appropriately
            ax.arrow(mx - dx * arrow_len / 2, my - dy * arrow_len / 2,
                     dx * arrow_len, dy * arrow_len,
                     head_width=width/5, head_length=width/6,
                     fc=cmap(energy_norm(energy)), ec=cmap(energy_norm(energy)),
                     transform=ccrs.PlateCarree(), zorder=2)

        # Plot pie charts per country
        for country, tech_mix in gen.items():
            total = sum(tech_mix.values())
            if total == 0:
                continue

            fracs = [v / total for v in tech_mix.values()]
            tech_labels = list(tech_mix.keys())
            tech_colors = [param.colors[t] for t in tech_labels]

            lat, lon = param.country_coords[country]
            ax.pie(fracs, colors=tech_colors, radius=np.sqrt(
                total) / 15, center=(lon, lat))

        # Set the extent to focus on Western Europe
        ax.set_extent([-11, 18, 36, 57])  # Western Europe

        # Add legend
        legend_patches = [plt.Line2D(
            [0], [0], color=param.colors[tech], lw=4, label=tech) for tech in techs]
        plt.legend(handles=legend_patches,
                   title="Technologies", loc='upper left')

        # Add colorbar for energy transmitted
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=energy_norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation='vertical', pad=0.01)
        cbar.set_label('Transmitted Energy')

        plt.show()


# france_net = BusElectricity('FRA', param.year, technologies=param.technologies_france)
# Countries = ['FRA', 'BEL', 'DEU']
# Europe_net = NetworkElectricity(param.year)

# for country in Countries:
#     Europe_net.add_country(country, technologies=param.technologies_france)
#     if country != "FRA":
#         Europe_net.add_line("FRA", country, 0, 1, 1, 0, False)

# Europe_net.optimize()

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
