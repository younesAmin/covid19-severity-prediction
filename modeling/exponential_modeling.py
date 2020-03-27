import sklearn
import numpy as np
import scipy as sp
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from viz import viz
from bokeh.plotting import figure, show, output_notebook, output_file, save
from functions import merge_data
from sklearn.model_selection import RandomizedSearchCV
import load_data
import copy
import statsmodels.api as sm

def exponential_fit(counts, target_day=np.array([1])): 
    # let target_day=np.array([5]) to predict 5 days in advance, 
    # and target_day=np.array([1, 2, 3, 4, 5]) to generate predictions for 1-5 days in advance 
    
    """
    Parameters:
        counts: array
            each row is the cases/deaths of one county over time
        target_day: array
            for each element {d} in the array, will predict cases/deaths {d} days from the last day in {counts}
    Return:
        array
        predicted cases/deaths for all county, for each day in target_day
    """
    predicted_counts = []
    for i in range(len(counts)):
        ts = counts[i]
        if ts[-1] > 100:
            start = np.where(ts >= 10)[0][0]
        elif ts[-1] >= 1:
            start = np.where(ts >= 1)[0][0]
        else:
            start = len(ts)
        active_day = len(ts) - start # days since 'outbreak'
        if active_day >= 2 and ts[-1] > 5:
            X_train = np.transpose(np.vstack((np.array(range(active_day)), 
                                      np.ones(active_day))))
            m = sm.GLM(ts[start:], X_train,
                       family=sm.families.Poisson())
            m = m.fit()
            X_test = np.transpose(np.vstack((target_day + active_day - 1, 
                                             np.ones(len(target_day)))))
            predicted_counts.append(m.predict(X_test))
        else:
            predicted_counts.append([ts[-1]]*len(target_day)) 
            ## if there are too few data points to fit a curve, return the cases/deaths of current day as predictions for future
                
    return predicted_counts 




def estimate_cases(df, method="exponential", target_day=np.array([1])):
    
    # estimate number of cases using exponential curve
    
    predicted_cases = []
    
    if method == "exponential":
        predicted_cases = exponential_fit(df['cases'].values, target_day=target_day)
    
    df['predicted_cases'] = predicted_cases
    return df
                
    
def estimate_death_rate(df, method="constant"):
    
    predicted_death_rate = []
    
    if method == 'constant':
        for i in range(len(df)):
            predicted_death_rate.append(df['deaths'].values[i][-1]/max(1, df['cases'].values[i][-1]))
            
    df['predicted_death_rate'] = predicted_death_rate
    return df
    
    
def estimate_deaths(df, method="exponential", target_day=np.array([1])):
    
    predicted_deaths = []
    
    if method == 'exponential':
        predicted_deaths = exponential_fit(df['deaths'].values, target_day=target_day)
        
    elif method == 'cases_exponential_rate_constant':
        predicted_cases = np.array(estimate_cases(df, method="exponential")['predicted_cases'])
        predicted_death_rate = np.array(estimate_death_rate(df, method="constant")['predicted_death_rate'])
        predicted_deaths = predicted_cases * predicted_death_rate
        
    df[f'predicted_deaths_{method}'] = predicted_deaths
        
    return df
        
def create_leave_one_day_out_valid(df):
    
    df2 = copy.deepcopy(df)
    days = len(df['deaths'].values[0])
    for i in range(len(df)):
        df2['deaths'].values[i] = df2['deaths'].values[i][0:(days-1)]
        df2['cases'].values[i] = df2['cases'].values[i][0:(days-1)]
    return df2

