import pandas as pd

# Load data

### CF
df_onshorewind = pd.read_csv('data/onshore_wind_1979-2017.csv', sep=';', index_col = 0)
df_onshorewind.index = pd.to_datetime(df_onshorewind.index)
df_solar = pd.read_csv('data/pv_optimal.csv', sep=';', index_col=0)
df_solar.index = pd.to_datetime(df_solar.index)
df_offshorewind = pd.read_csv('data/offshore_wind_1979-2017.csv', sep=';', index_col=0)
df_offshorewind.index = pd.to_datetime(df_solar.index)
df_hydro = pd.read_csv('data/Hydro_Inflow_FR.csv', sep=',')
df_hydro.index = pd.to_datetime(df_hydro[['Year', 'Month', 'Day']])
df_hydro = df_hydro.resample('h').ffill()
df_hydro['Inflow [GW]'] = df_hydro['Inflow [GWh]']/24 #Hourly value
df_hydro['Inflow pu'] = df_hydro['Inflow [GW]']/df_hydro['Inflow [GW]'].max()

### Costs
costs = pd.read_csv('data/costs.csv', index_col='Technology')

# Plot
colors = {"Nuclear":"#ffe66d",
          "PV":"#ffa96c",
          "Wind Onshore":"#9abb7f",
          "Wind Offshore": "#a3e6de",
          "Hydro":"#349090",
          "OCGT":"#8d5f64",
          "CCGT":"#d1a9a5",
          "TACH2": "#cdd176",
          "Storage1":"#ff6b6b",
          "Storage2":"#1a535c"}