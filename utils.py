import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

def annuity(n, r):
    """ Calculate the annuity factor for an asset with 
    lifetime n years and discount rate  r """

    if r>0:
        return r/(1.-1./(1.+r)**n)
    else:
        return 1/n

def cost_conversion(cost, year_from, year_to=2020, inflation=1.02):
    """Convert cost from year_from to year_to using inflation data. 
    Inflation: float, ex: Inflation of 2%: 1.02
    """
    years = year_to - year_from
    return cost * (inflation ** years)

def fourier_transform(list_data:list[pd.Series], colors:list[str]):
    max_columns = 3
    columns = min(len(list_data), max_columns)
    rows = math.ceil(len(list_data)/max_columns)
    fig, ax = plt.subplots(rows, columns, sharey=True)
    for i, data  in enumerate(list_data):
        column = i%max_columns 
        row = math.ceil((i+1)/max_columns) - 1   
        index = (row, column) if rows > 1 else column
        t_sampling=1 # sampling rate, 1 data per hour
        x = np.arange(1,8761, t_sampling) 
        y = data
        n = len(x)
        y_fft = np.fft.fft(y)/n #n for normalization    
        frq = np.arange(0,1/t_sampling,1/(t_sampling*n))        
        period = np.array([1/f for f in frq]) 
        ax[index].semilogx(period[1:n//2],
                    abs(y_fft[1:n//2])/np.max(abs(y_fft[1:n//2])), 
                    color=colors[i],
                    linewidth=2, label=data.name)  
        ax[index].set(xlabel='cycling period (hours)')
        #We add lines indicating day, week, month
        ax[index].axvline(x=24, color='lightgrey', linestyle='--')
        ax[index].axvline(x=24*7, color='lightgrey', linestyle='--')
        ax[index].axvline(x=24*30, color='lightgrey', linestyle='--')
        ax[index].axvline(x=8760, color='lightgrey', linestyle='--') 
        ax[index].text(26, 0.95, 'day', horizontalalignment='left', color='dimgrey', fontsize=9)
        ax[index].text(24*7+20, 0.95, 'week', horizontalalignment='left', color='dimgrey', fontsize=9)
        ax[index].text(24*30+20, 0.95, 'month', horizontalalignment='left', color='dimgrey', fontsize=9)
        ax[index].legend()
    plt.show()