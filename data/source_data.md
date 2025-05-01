# Project

The idea of the project is to evaluate the optimal production mix for France, ignoring the existing mix but considering the fixed and marginal costs of new plants. 

Inspired by the existing mix in France, we considered the following technologies of production:*Nuclear
- PV: large-roof
- Wind onshore and "fixed" offshore
- Hydro
- CCGT
- OCGT
- TACH2

# Sources
We mainly took our values for France in the Futurs Energétiques 2050, a prospective study realized by RTE, the French TSO. To reflect the current mix in France, we chose the data for 2020, in the reference scenario. All our selected values are in the file `costs.csv`. 

Columns:
- Technology: Technology name of the power plant
- CAPEX: In EUR/MW
- fixed OPEX: In EUR/MW/year
- marginal cost: In EUR/MWh of produced electricity
- Lifetime: Expected lifetime of the technology
- Efficiency: [0, 1], efficiency of the technology 
- CO2 emissions: Direct CO2 emissions in tCO2/MWh_th

For the storage, the selected values are in the file 'costs_storage.csv'
Columns:
- Technology: Technology name of the power plant
- Max capacity: In MW
- CAPEX power: in EUR/MW
- CAPEX energy: in EUR/MWh
- OPEX fixed power: in EUR/MW/year
- OPEX fixed energy: in EUR/MWh/year
- Marginal cost: in EUR/MWh of produced electricity
- lifetime: Expected lifetime of the technology in years
- efficiency: [0, 1], efficiency of the technology. We make the assumption that efficiency_store = efficiency_dispatch = efficiency. The round trip efficiency is thus efficiency * efficiency.
- CO2 emissions: Direct CO2 emissions in tCO2/MWh_th
- Energy Power ratio: number of hours where the storage system can ideally store/discharge at full capacity.

## Technologies
### Nuclear
Data are from the report Futurs Energétiques 2050, of the French TSO RTE. The costs and values considered are the ones for the EPR of Flamanville, commissionned in 2024. The reference hypothesis was considered.

### PV
We considered the values given in the report Futurs Energétiques 2050 from RTE, for new large-roof solar panels(rather than PV fields) in 2020. We are only considering large-roof PV and not other types of PV

### Wind onshore
We also considered the values given in the report from RTE, with the reference prices for new wind turbines in 2020

### Wind offshore "fixed"
We also considered the values given in the report from RTE, with the reference prices for new wind turbines in 2020. Only "fixed" offshore has been taken into account, as "floating" offshore is much more expensive than "fixed" according to RTE analysis.

### Hydro
For hydro, we again took RTE values, however, we considered a maximum potential of 40 GW in France, that can't be exceeded due to geographical constraints 

### CCGT and OCGT
For these data, we didn't  rely on the RTE report. Indeed, in their simulation, RTE only consider existing conventional generators. As they aim at targetting the zero-emissions of the electric system by 2050, they don't plan to buy new conventional units (explaining thus the absence of data)
We considered data from PyPSA: Technology-data.

### TACH2

## The CO2 constraints
Regarding the CO2-constraints, we took the historical emissions for France in the report of RTE.

### Storage
Major Energy Storage Characteristics by Technology
(Deloitte, 2015)


- Max capa: MW
- Capex power
- Capex energy
- Opex fixed power
- Opex fixed energy
- Marginal cost
- Lifetime: year
- Efficiency: %
- CO2 emissions
- Energy power ratio