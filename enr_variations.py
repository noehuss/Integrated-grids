import pandas as pd
import param
import matplotlib.pyplot as plt

country='FRA'

hours_in_year = pd.date_range(f'{param.year}-01-01 00:00Z',
                              f'{param.year}-12-31 23:00Z',
                              freq='h')
plt.plot(param.df_offshorewind.loc[hours_in_year, country].sort_values(ascending=False,ignore_index=True),
                     color=param.colors["Wind Offshore"],
                     label="Wind Offshore")
plt.plot(param.df_onshorewind.loc[hours_in_year, country].sort_values(ascending=False,ignore_index=True),
                     color=param.colors["Wind Onshore"],
                     label="Wind Onshore")
plt.plot(param.df_solar.loc[hours_in_year, country].sort_values(ascending=False,ignore_index=True),
                     color=param.colors["PV"],
                     label="PV")
plt.plot(param.df_hydro.loc[pd.date_range(f'2010-01-01 00:00',
                              f'2010-12-31 23:00',
                              freq='h'), 'Inflow pu'].sort_values(ascending=False,ignore_index=True),
                     color=param.colors["Hydro"],
                     label="Hydro")

plt.xlabel('Hours')
plt.ylabel('Capacity factor')
plt.grid(linewidth='0.4', linestyle='--')
plt.legend()
plt.show()

annual_mean_pv = param.df_solar[country].resample('YE').mean()
annual_mean_wind_onshore  = param.df_onshorewind[country].resample('YE').mean()
annual_mean_wind_offshore  = param.df_offshorewind[country].resample('YE').mean()
annual_mean_hydro = param.df_hydro['Inflow pu'].resample('YE').mean()


fig, (ax1, ax2, ax3, ax4) = plt.subplots(4,1, sharex=True)
ax1.plot(annual_mean_pv, label='PV', color=param.colors["PV"])
ax1.grid(linewidth='0.4', linestyle='--')
ax1.legend()
# add text box for the statistics
stats = (f'$\\mu$: {annual_mean_pv.mean():.2f}\n'
            f'$\\sigma_n$: {100*annual_mean_pv.std()/annual_mean_pv.mean():.1f} %')
bbox = dict(boxstyle='round', fc='whitesmoke', ec=param.colors["PV"], alpha=0.5)
ax1.text(0.9, 0.17, stats, fontsize=9, bbox=bbox,
        transform=ax1.transAxes, horizontalalignment='left')

ax2.plot(annual_mean_wind_onshore, color=param.colors["Wind Onshore"], label="Wind Onshore")
ax2.grid(linewidth='0.4', linestyle='--')
ax2.legend()
# add text box for the statistics
stats = (f'$\\mu$: {annual_mean_wind_onshore.mean():.2f}\n'
            f'$\\sigma_n$: {100*annual_mean_wind_onshore.std()/annual_mean_wind_onshore.mean():.1f} %')
bbox = dict(boxstyle='round', fc='whitesmoke', ec=param.colors["Wind Onshore"], alpha=0.5)
ax2.text(0.9, 0.17, stats, fontsize=9, bbox=bbox,
        transform=ax2.transAxes, horizontalalignment='left')

ax3.plot(annual_mean_wind_offshore, color=param.colors["Wind Offshore"], label="Wind Offshore")
ax3.grid(linewidth='0.4', linestyle='--')
ax3.legend()
# add text box for the statistics
stats = (f'$\\mu$: {annual_mean_wind_offshore.mean():.2f}\n'
            f'$\\sigma_n$: {100*annual_mean_wind_offshore.std()/annual_mean_wind_offshore.mean():.1f} %')
bbox = dict(boxstyle='round', fc='whitesmoke', ec=param.colors["Wind Offshore"], alpha=0.5)
ax3.text(0.9, 0.17, stats, fontsize=9, bbox=bbox,
        transform=ax3.transAxes, horizontalalignment='left')

ax4.plot(annual_mean_hydro, color=param.colors["Hydro"], label="Hydro")
ax4.grid(linewidth='0.4', linestyle='--')
ax4.legend()
# add text box for the statistics
stats = (f'$\\mu$: {annual_mean_hydro.mean():.2f}\n'
            f'$\\sigma_n$: {100*annual_mean_hydro.std()/annual_mean_hydro.mean():.1f} %')
bbox = dict(boxstyle='round', fc='whitesmoke', ec=param.colors["Hydro"], alpha=0.5)
ax4.text(0.9, 0.17, stats, fontsize=9, bbox=bbox,
        transform=ax4.transAxes, horizontalalignment='left')

plt.show()