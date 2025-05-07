import pandas as pd
import utils
# Load data

# CF
df_onshorewind = pd.read_csv(
    'data/onshore_wind_1979-2017.csv', sep=';', index_col=0)
df_onshorewind.index = pd.to_datetime(df_onshorewind.index)
df_solar = pd.read_csv('data/pv_optimal.csv', sep=';', index_col=0)
df_solar.index = pd.to_datetime(df_solar.index)
df_offshorewind = pd.read_csv(
    'data/offshore_wind_1979-2017.csv', sep=';', index_col=0)
df_offshorewind.index = pd.to_datetime(df_solar.index)
df_hydro = pd.read_csv('data/Hydro_Inflow_FR.csv', sep=',')
df_hydro.index = pd.to_datetime(df_hydro[['Year', 'Month', 'Day']])
df_hydro = df_hydro.resample('h').ffill()
df_hydro['Inflow [GW]'] = df_hydro['Inflow [GWh]']/24  # Hourly value
df_hydro['Inflow pu'] = df_hydro['Inflow [GW]']/df_hydro['Inflow [GW]'].max()

demand = pd.read_csv(
    'data/electricity_demand.csv', sep=';', index_col=0)
demand.index = pd.to_datetime(demand.index)
demand = demand['FRA'].loc['2015']
print(demand.sum())

#Hydrogen demand
industrial_data = pd.read_csv('data/Industrial-1-shift Fabricated Metals.csv')
industrial_data['utc_time'] = pd.date_range(start='2015-01-01 00:00:00', end='2015-12-31 23:00:00', freq='H')
industrial_data.index = industrial_data['utc_time']
    #To find the hydrogen demand, we normalize by the total demand over a year, predicted for 2030: 35TWh.
hourly_hydrogen_demand = industrial_data['Power [kW]']*35000000/industrial_data['Power [kW]'].sum() 

### Costs
costs = pd.read_csv('data/costs2030.csv', index_col='Technology')
for key in costs.index:
    costs.loc[key, 'CAPEX'] = utils.cost_conversion(
        costs.loc[key, 'CAPEX'], costs.loc[key, 'Currency year'])
    costs.loc[key, 'FOM'] = utils.cost_conversion(
        costs.loc[key, 'FOM'], costs.loc[key, 'Currency year'])
    costs.loc[key, 'VOM'] = utils.cost_conversion(
        costs.loc[key, 'VOM'], costs.loc[key, 'Currency year'])

# Costs storage
costs_store = pd.read_csv('data/cost_storage2030.csv', index_col='Technology')

#Costs hydrogen
capex_electrolyser = utils.annuity(20, 0.07) * (641000 + 12000)
capex_salt_cavern = utils.annuity(40, 0.07) * (350000 + 2000)
capex_ccgt_H2 = utils.annuity(40, 0.07) * (1100000 + 40000)

### CO2 emissions
#### Regarding the historical emissions of the electrical mix in France, we have:
co2_limit_2019 = 20000000 #tCO2/year
co2_limit_1990 = 45000000 #tCO2/year
co2_limit_2030 = 12000000 #tCO2/year

# Param
# Year simulation
year = 2015

# Technologies
technologies_france = {
    "Nuclear": None,
    "PV": df_solar,
    "Wind Onshore": df_onshorewind,
    "Wind Offshore": df_offshorewind,
    "Hydro": df_hydro,
    "OCGT": None,
    "CCGT": None,
    "TACH2": None,
}

technologies_storage_france = {
    "PHS_s": None,
    "PHS_b": None,
    "Battery": None,
}

# Countries
countries = ['FRA', 'BEL', "DEU", "ITA", "ESP", "GBR"]
country_coords = {
    'FRA': (46.60, 2.50),
    'GBR': (52.35, -1.17),
    'BEL': (50.85, 4.35),
    'DEU': (51.17, 10.45),
    'ITA': (42.83, 12.83),
    'ESP': (40.40, -3.68)
}

technologies_by_country = {}

for country in countries:
    if country == "ITA":
        technologies_by_country[country] = {
            "PV": df_solar,
            "Wind Onshore": df_onshorewind,
            "OCGT": None,
            "CCGT": None,
            "TACH2": None,
        }
    elif country == "BEL":
        technologies_by_country[country] = {
            "Nuclear": None,
            "PV": df_solar,
            "Wind Onshore": df_onshorewind,
            "Wind Offshore": df_offshorewind,
            "OCGT": None,
            "CCGT": None,
            "TACH2": None,
        }
    elif country == "DEU":
        technologies_by_country[country] = {
            "PV": df_solar,
            "Wind Onshore": df_onshorewind,
            "Wind Offshore": df_offshorewind,
            "OCGT": None,
            "CCGT": None,
            "TACH2": None,
        }
    elif country == "ESP":
        technologies_by_country[country] = {
            "Nuclear": None,
            "PV": df_solar,
            "Wind Onshore": df_onshorewind,
            "OCGT": None,
            "CCGT": None,
            "TACH2": None,
        }
    elif country == "GBR":
        technologies_by_country[country] = {
            "Nuclear": None,
            "PV": df_solar,
            "Wind Onshore": df_onshorewind,
            "Wind Offshore": df_offshorewind,
            "OCGT": None,
            "CCGT": None,
            "TACH2": None,
        }
    else:
        technologies_by_country[country] = {
            "Nuclear": None,
            "PV": df_solar,
            "Wind Onshore": df_onshorewind,
            "Wind Offshore": df_offshorewind,
            "Hydro": df_hydro if country == "FRA" else None,
            "OCGT": None,
            "CCGT": None,
            "TACH2": None,
        }
Distance_to_Paris = {
    'GBR': 350,
    'BEL': 265,
    'DEU': 877,
    'ITA': 1100,
    'ESP': 1050
}

# Plot
colors = {"Nuclear": "#ffe66d",
          "PV": "#ffa96c",
          "Wind Onshore": "#9abb7f",
          "Wind Offshore": "#a3e6de",
          "Hydro": "#349090",
          "OCGT": "#8d5f64",
          "CCGT": "#d1a9a5",
          "TACH2": "#cdd176",
          "PHS":"#052F5F",
          "Battery":"#06A77D",
          "tCO2":"#272932",
          "elec":"#AA968A",
          "PHS_s":"#00747A",
          "PHS_b":"#29DCFF",
          "Nuclear Extension" : "#fcba03"}

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