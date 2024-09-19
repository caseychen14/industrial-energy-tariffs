#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import ast
import geo2ei
import os


# In[2]:


MONTHS = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}

mixed_type_columns = [3, 5, 11, 28, 362, 392, 397, 402, 407, 412, 417, 437, 442, 447, 452, 457, 472, 477, 482, 492, 497, 502, 507, 517, 522, 527, 532, 542, 547, 552, 557, 562, 567, 572, 577, 582, 587, 592, 597, 602, 607, 612, 617, 622, 627, 632, 637, 642, 647, 652, 655, 668]

dtype_dict = {col: str for col in mixed_type_columns}

openei = pd.read_csv('../data/usurdb.csv', dtype=dtype_dict) #can add null values

openei['sourceparent'] = openei['sourceparent'].fillna('')

#turn into python script maybe turn into a class


# In[3]:


metadata = {
    'eiaid': [],
    'latitude': [],
    'longitude': [],
    'name': [],
    'utility': [],
    'source': []
}


# In[4]:


# create a dictionary of the tariff and then append to a list
# df.concat, make the empty values NaN


# In[5]:


tariff_list = []


# In[6]:


def make_dict():
    data_dict = {
        'utility': [],
        'type': [],
        'assessed': [],
        'period': [],
        'basic_charge_limit (imperial)': [],
        'basic_charge_limit (metric)': [],
        'month_start': [],
        'month_end': [],
        'hour_start': [],
        'hour_end': [],
        'weekday_start': [],
        'weekday_end': [],
        'charge (imperial)': [],
        'charge (metric)': [],
        'units': [],
        'Notes': []
    }
    return data_dict


# In[7]:


def find_consecutive_ranges(lst):
    if not lst:
        return []

    ranges = []
    start = 0

    for i in range(1, len(lst)):
        if lst[i] != lst[start]:
            ranges.append((start, i - 1))
            start = i

    ranges.append((start, len(lst) - 1))

    return ranges


# In[8]:


def process_customer(i):
    data_dict = make_dict()
    data_dict['utility'].append('electricity')
    data_dict['type'].append('customer')
    data_dict['assessed'].append('')
    data_dict['period'].append('')
    data_dict['basic_charge_limit (imperial)'].append('')
    data_dict['basic_charge_limit (metric)'].append('')
    data_dict['month_start'].append('')
    data_dict['month_end'].append('')
    data_dict['hour_start'].append('')
    data_dict['hour_end'].append('')
    data_dict['weekday_start'].append('')
    data_dict['weekday_end'].append('')
    data_dict['charge (imperial)'].append(openei['fixedchargefirstmeter'][i])
    data_dict['charge (metric)'].append(openei['fixedchargefirstmeter'][i])
    data_dict['units'].append('$/month')
    data_dict['Notes'].append(str(openei['source'][i]) + ('\t' + str(openei['sourceparent'][i]) if openei['sourceparent'][i] != '' else ''))
    tariff_list.append(data_dict)


# In[9]:


# make sure to name in period the same if the weekday and weekend charges are the same charge
# add a unit converter to standardize to kW or kWh (pint package for unit handling)
# demand window should be 15 mins (check the demandwindow column) 
# if not 15 mins, put in seperate list
# use period to determine when evaluated
def process_demand(i):
    # processing the array for time intervals

    MONTH_ARRAY = ['flatDemandMonth_jan', 'flatDemandMonth_feb', 'flatDemandMonth_mar', 'flatDemandMonth_apr', 'flatDemandMonth_may', 'flatDemandMonth_jun', 'flatDemandMonth_jul', 'flatDemandMonth_aug', 'flatDemandMonth_sep', 'flatDemandMonth_oct', 'flatDemandMonth_nov', 'flatDemandMonth_dec']
    sched = {}
    for j in range(len(MONTH_ARRAY)):
        sched[j] = (openei[MONTH_ARRAY[j]][i])

    print(type(sched.values()))
    new_list = list(sched.values())
    ranges = find_consecutive_ranges(new_list)
        
    if len(ranges) == 0:
        ranges = [(1, 12)]

    time_index = 0
    tier_index = 0
    charge_limit = 0

    # set a flag var to false if something triggers
    while time_index < len(ranges):
        try:
            # tier_str first to catch ValueErrors from null values in the dataframe
            tier_str = 'flatdemandstructure/period'+ str(int(sched[ranges[time_index][0]])) + '/tier'+ str(tier_index)
            rate = openei[tier_str + 'rate'][i]
        except (ValueError, KeyError):
            return
        
        data_dict = make_dict()
        data_dict['month_start'].append(str(ranges[time_index][0]))
        data_dict['month_end'].append(str(ranges[time_index][1]))
        data_dict['utility'].append('electricity')
        data_dict['type'].append('demand')
        data_dict['assessed'].append('') # figure out if the demand charge is done daily
        data_dict['period'].append('flat' + str(i)) # make sure that if the charge is the same, give the same name to the tariff
        data_dict['basic_charge_limit (imperial)'].append(charge_limit)
        data_dict['basic_charge_limit (metric)'].append(charge_limit)
        data_dict['hour_start'].append('')
        data_dict['hour_end'].append('')
        # Not the case for all structures
        data_dict['weekday_start'].append('0')
        data_dict['weekday_end'].append('6')
        if not np.isnan(openei[tier_str + 'adj'][i]):
            rate += openei[tier_str + 'adj'][i]
            data_dict['Notes'].append(f'adjustment factor of {openei[tier_str + "adj"][i]}')
        else:
            data_dict['Notes'].append('')
        data_dict['charge (imperial)'].append(rate)
        data_dict['charge (metric)'].append(rate)
        data_dict['units'].append('$/' + str(openei['flatdemandunit'][i])) # convert automatically
        tariff_list.append(data_dict)
        


        # contain the try except fwk to setting this string
        max_str = 'flatdemandstructure/period' + str(int(sched[ranges[time_index][0]])) + '/tier'+ str(tier_index) + 'max'
        if not np.isnan(openei[max_str][i]):
            charge_limit = openei[max_str][i]
            tier_index += 1
        else:
            time_index += 1
            tier_index = 0

        


# In[10]:


'''
unpack_array() takes the nested array and processed array in order to generate 
tarriffs which are sensitive to day-by-day variance as well as month variance.

lst is a list of tuples, each tuple representing the start and end month of a
continuous term for which a tarriff is applicable
sched is the unprocessed two-layer nested array with the indexes of tariffs
string is the string that represents the name of the tarriff structure in dataframe
units is the unit for which the tariff measures i.e. kWh, kW, etc.
'''#TODO: remove tariff if the rate is zero
# be very detailed in comment when turning into python script
# check fractional hours, look into whether there is a way to handle/understand how it works
def unpack_array(lst, sched, string, i, units, type, week_start, week_end):
    time_index = 0 ##change to day index
    hour_index = 0
    tier_index = 0
    charge_limit = 0

    hour_list = sched[lst[time_index][0]] # month_lst is the current month looked at
    hour_ranges = find_consecutive_ranges(hour_list) # processed month_lst
    hour = hour_ranges[hour_index][0] #

    # print(f'MONTH_LIST: {hour_list}')
    # print(f'MONTH_FIRST: {hour_list[hour_index]} + here is the type: {type(hour_list[hour_index])}')

    while time_index < len(lst) and hour_index < len(hour_ranges):
        data_dict = make_dict()
        try:
            # tier_str first to catch ValueErrors from null values in the dataframe
            #printing the types of every element of the concatenated tier_str
            tier_str = string + '/period'+ str(hour_list[hour]) + '/tier'+ str(tier_index)
            rate = openei[tier_str + 'rate'][i]
        except (IndexError, ValueError, KeyError):
            break
        data_dict['month_start'].append(str(lst[time_index][0]))
        data_dict['month_end'].append(str(lst[time_index][1]))
        data_dict['utility'].append('electric') #TODO: add to arguments in function prototype # change all electricity to electric
        data_dict['type'].append(type)
        data_dict['assessed'].append('')
        data_dict['period'].append('')
        data_dict['basic_charge_limit (imperial)'].append(charge_limit)
        data_dict['basic_charge_limit (metric)'].append(charge_limit)
        data_dict['hour_start'].append(hour_ranges[hour_index][0])
        data_dict['hour_end'].append(hour_ranges[hour_index][1])
        # Not the case for all structures
        data_dict['weekday_start'].append(week_start)
        data_dict['weekday_end'].append(week_end)
        if not np.isnan(openei[tier_str + 'adj'][i]):
            rate += openei[tier_str + 'adj'][i]
        data_dict['charge (imperial)'].append(rate)
        data_dict['charge (metric)'].append(rate)
        data_dict['units'].append(units)
        data_dict['Notes'].append('')
        tariff_list.append(data_dict)

        max_str = string + '/period' + str(hour_list[hour]) + '/tier'+ str(tier_index) + 'max'
        if not np.isnan(openei[max_str][i]):
            charge_limit = openei[max_str][i]
            tier_index += 1
        elif hour_index < len(hour_ranges) - 1:
            hour_index += 1
            charge_limit = 0
            
        else:
            time_index += 1
            hour_index = 0
        try:
            hour_list = sched[lst[time_index][0]] # month_lst is the current month looked at
            hour_ranges = find_consecutive_ranges(hour_list) # processed month_lst
            hour = hour_ranges[hour_index][0]
        except IndexError:
            break


# In[11]:


def process_TOU(i):
    # check if TOU data available

    
    if pd.isna(openei['demandweekdayschedule'][i]) and pd.isna(openei['demandweekendschedule'][i]):
        return

    weekday_sched = ast.literal_eval(openei['demandweekdayschedule'][i])
    weekend_sched = ast.literal_eval(openei['demandweekendschedule'][i])

    weekday_ranges = find_consecutive_ranges(weekday_sched)
    weekend_ranges = find_consecutive_ranges(weekend_sched)
    #quick n dirty fix here for units
    unpack_array(weekday_ranges, weekday_sched, 'demandratestructure', i, '$/kWh', 'demand', 0, 4)
    unpack_array(weekend_ranges, weekend_sched, 'demandratestructure', i, '$/kWh', 'demand', 5, 6)


# In[12]:


def process_energyStruc(i):
    # check if energy data available
    if pd.isna(openei['energyweekdayschedule'][i]) and pd.isna(openei['energyweekendschedule'][i]):
        return

    weekday_sched = ast.literal_eval(openei['energyweekdayschedule'][i])
    weekend_sched = ast.literal_eval(openei['energyweekendschedule'][i])

    weekday_ranges = find_consecutive_ranges(weekday_sched)
    weekend_ranges = find_consecutive_ranges(weekend_sched)

    # print(f"wd sched: {weekday_sched}, ranges length: {len(weekday_sched)}")
    # print(f"we sched: {weekend_sched}, ranges length: {len(weekend_sched)}")

    # print(f"wd ranges: {weekday_ranges}, ranges length: {len(weekday_ranges)}")
    # print(f"we ranges: {weekend_ranges}, ranges length: {len(weekend_ranges)}")
    unpack_array(weekday_ranges, weekday_sched, 'energyratestructure', i, '$/kWh', 'electricity', 0, 4)
    unpack_array(weekend_ranges, weekend_sched, 'energyratestructure', i, '$/kWh', 'electricity', 5, 6)
    


# In[13]:


# def add_metadata(i):
#     metadata['eiaid'].append(openei['eiaid'][i])
#     metadata['latitude'].append(openei['latitude'][i])
#     metadata['longitude'].append(openei['longitude'][i])
#     metadata['name'].append(openei['name'][i])
#     metadata['utility'].append('electricity')
#     metadata['source'].append(openei['source'][i] + ('\t' + openei['sourceparent'][i] if openei['sourceparent'][i] != '' else ''))
    


# In[14]:


def add_index(i):
    process_customer(i)
    process_demand(i)
    process_TOU(i)
    process_energyStruc(i)


# In[15]:


top_utils = pd.read_excel('../data/table_8.xlsx')
zipcodes = pd.read_csv('../data/merged_zipcodes.csv')
bad_list = ['EDF Energy Services, LLC', 'Tenaska Power Services', 'Withheld', 'Grand River Dam Authority', 'MP2 Energy LLC', 'Vinton Public Power Authority', 'ENGIE Resources LLC', 'AGC Division of APGI Inc', 'Adjustment 2022', 'Adjustment 2022', 'Adjustment 2022', 'WAPA-- Western Area Power Administration', 'Constellation NewEnergy, Inc', 'Adjustment 2022', 'Upper Michigan Energy Resources Corp.', 'Adjustment 2022', 'Adjustment 2022', 'Basin Electric Power Coop', 'Cheyenne Light Fuel & Power', 'Adjustment 2022', 'Adjustment 2022', 'Adjustment 2022', 'Adjustment 2022', 'Adjustment 2022', 'Total Gas & Power North America Inc', 'MidAmerican Energy Services, LLC', 'Adjustment 2022', 'Southern Pioneer Electric Company', 'Adjustment 2022', 'Adjustment 2022', 'Bonneville Power Administration', 'Adjustment 2022', 'Adjustment 2022', 'Adjustment 2022', 'NorthWestern Energy - (SD)', 'Adjustment 2022', 'Adjustment 2022', 'Adjustment 2022', 'Electrical Dist No8 Maricopa', 'Calpine Energy Solutions, LLC', 'BP Energy Company', 'Adjustment 2022', 'Adjustment 2022', 'Adjustment 2022', 'Adjustment 2022', 'Adjustment 2022']
indexes = []
for name in top_utils['Name']:
    matching_rows = zipcodes[zipcodes['utility_name'] == name]
    if matching_rows.empty:
        continue
    eiaid = matching_rows.iloc[0]['eiaid']
    index = openei[openei['eiaid'] == eiaid].index
    #add the index to indexes
    if not index.empty:
        for i in index:
            add_index(i)


# In[40]:


#list of all state abbreviations
states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
missing = []
print(len(states))
i = 0
for i in range(len(states)):
    matching = top_utils[top_utils['State'] == states[i]]
    if matching.empty:
        missing.append(states[i])
    else:
        print(states[i], i)
        i +=1
print(missing)


# In[16]:


# df = pd.DataFrame(data_dict)
# df.to_csv('../data/industrial-energy-tariffs.csv', index=False)


# In[17]:


# make sure to document tests (write doctests/pytests)
add_index(333)

data_frame = pd.DataFrame()
for lst in tariff_list:
    data_frame = pd.concat([data_frame, pd.DataFrame(lst)])
print(data_frame)


# In[20]:


data_frame.to_csv('../data/industrial-energy-tariffs.csv', index=False)


# In[18]:


#remove api key from code and then store in api key in txt (or save as a github action and save as a secret)
url = "https://api.openei.org/utility_rates?version=3&format=csv&limit=3&eia=195&api_key=${{ secrets.API_KEY }}&detail=full"

geo2ei.open_api(url)

new_df = pd.read_csv("../data/openei/utility_rates.csv")


# In[19]:


def merge_zips():
    iou = pd.read_csv("../data/iou_zipcodes_2020.csv")
    non_iou = pd.read_csv("../data/non_iou_zipcodes_2020.csv")
    merged = pd.concat([iou, non_iou], ignore_index=True)
    merged.to_csv("../data/merged_zipcodes.csv")

