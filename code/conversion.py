import pandas as pd
import numpy as np
import ast

MONTHS = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
openei = pd.read_csv('../data/usurdb.csv', low_memory=False)

def make_meta():
    metadata = {
        'eiaid': '',
        'name': '',
        'label': '',
        'utility': '',
        'source': '',
        'zipcode': '',
        'state': '',
        'city': '',
        'county': ''
    }
    return metadata



def make_dict():
    data_dict = {
        'label': '',
        'utility': '',
        'type': '',
        'assessed': '',
        'period': '',
        'basic_charge_limit (imperial)': '',
        'basic_charge_limit (metric)': '',
        'month_start': '',
        'month_end': '',
        'hour_start': '',
        'hour_end': '',
        'weekday_start': '',
        'weekday_end': '',
        'charge (imperial)': '',
        'charge (metric)': '',
        'units': '',
        'Notes': ''
    }
    return data_dict

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

def process_customer(i, tariff):
    data_dict = make_dict()
    data_dict['label'] = (openei['label'][i])
    data_dict['utility'] = ('electric')
    data_dict['type'] = ('customer')
    data_dict['assessed'] = ('')
    data_dict['period'] = ('')
    data_dict['basic_charge_limit (imperial)'] = ('')
    data_dict['basic_charge_limit (metric)'] = ('')
    data_dict['month_start'] = ('')
    data_dict['month_end'] = ('')
    data_dict['hour_start'] = ('')
    data_dict['hour_end'] = ('')
    data_dict['weekday_start'] = ('')
    data_dict['weekday_end'] = ('')
    data_dict['charge (imperial)'] = (openei['fixedchargefirstmeter'][i])
    data_dict['charge (metric)'] = (openei['fixedchargefirstmeter'][i])
    data_dict['units'] = ('$/month')
    data_dict['Notes'] = (str(openei['source'][i]) + ('\t' + str(openei['sourceparent'][i]) if openei['sourceparent'][i] != '' else ''))
    tariff.append(data_dict)

def process_demand(i, tariff):
    # processing the array for time intervals

    MONTH_ARRAY = ['flatDemandMonth_jan', 'flatDemandMonth_feb', 'flatDemandMonth_mar', 'flatDemandMonth_apr', 'flatDemandMonth_may', 'flatDemandMonth_jun', 'flatDemandMonth_jul', 'flatDemandMonth_aug', 'flatDemandMonth_sep', 'flatDemandMonth_oct', 'flatDemandMonth_nov', 'flatDemandMonth_dec']
    sched = {}
    for j in range(len(MONTH_ARRAY)):
        sched[j] = (openei[MONTH_ARRAY[j]][i])
    new_list = list(sched.values())
    ranges = find_consecutive_ranges(new_list)
        
    if len(ranges) == 0:
        ranges = [(1, 12)]

    time_index = 0
    tier_index = 0
    charge_limit = 0

    while time_index < len(ranges):
        try:
            # tier_str first to catch ValueErrors from null values in the dataframe
            tier_str = 'flatdemandstructure/period'+ str(int(sched[ranges[time_index][0]])) + '/tier'+ str(tier_index)
            rate = openei[tier_str + 'rate'][i]
        except (ValueError, KeyError):
            return
        
        data_dict = make_dict()
        data_dict['label'] = (openei['label'][i])
        data_dict['month_start'] = (str(ranges[time_index][0]))
        data_dict['month_end'] = (str(ranges[time_index][1]))
        data_dict['utility'] = ('electric')
        data_dict['type'] = ('demand')
        data_dict['assessed'] = ('')
        data_dict['period'] = ('flat ' + str(i))
        data_dict['basic_charge_limit (imperial)'] = (charge_limit)
        data_dict['basic_charge_limit (metric)'] = (charge_limit)
        data_dict['hour_start'] = ('')
        data_dict['hour_end'] = ('')
        data_dict['weekday_start'] = ('0')
        data_dict['weekday_end'] = ('6')
        if not np.isnan(openei[tier_str + 'adj'][i]):
            rate += openei[tier_str + 'adj'][i]
            data_dict['Notes'] = (f'adjustment factor of {openei[tier_str + "adj"][i]}') 
        else:
            data_dict['Notes'] = ('')
        data_dict['charge (imperial)'] = (rate)
        data_dict['charge (metric)'] = (rate)
        data_dict['units'] = ('$/' + str(openei['flatdemandunit'][i]))
        tariff.append(data_dict)
        


        # contain the try except fwk to setting this string
        max_str = 'flatdemandstructure/period' + str(int(sched[ranges[time_index][0]])) + '/tier'+ str(tier_index) + 'max'
        if not np.isnan(openei[max_str][i]):
            charge_limit = openei[max_str][i]
            tier_index += 1
        else:
            time_index += 1
            tier_index = 0

def unpack_array(lst, sched, string, i, units, type, week_start, week_end, tariff):
    day_index = 0
    hour_index = 0
    tier_index = 0
    charge_limit = 0

    hour_list = sched[lst[day_index][0]] # month_lst is the current month looked at
    hour_ranges = find_consecutive_ranges(hour_list) # processed month_lst
    hour = hour_ranges[hour_index][0] #

    while day_index < len(lst) and hour_index < len(hour_ranges):
        data_dict = make_dict()
        try:
            # tier_str first to catch ValueErrors from null values in the dataframe
            tier_str = string + '/period'+ str(hour_list[hour]) + '/tier'+ str(tier_index)
            rate = openei[tier_str + 'rate'][i]
        except (IndexError, ValueError, KeyError):
            break
        data_dict['label'] = (str(openei['label'][i]))
        data_dict['month_start'] = (str(lst[day_index][0]))
        data_dict['month_end'] = (str(lst[day_index][1]))
        data_dict['utility'] = ('electric')
        data_dict['type'] = (type)
        data_dict['assessed'] = ('')
        data_dict['period'] = ('')
        data_dict['basic_charge_limit (imperial)'] = (charge_limit)
        data_dict['basic_charge_limit (metric)'] = (charge_limit)
        data_dict['hour_start'] = (hour_ranges[hour_index][0])
        data_dict['hour_end'] = (hour_ranges[hour_index][1])
        # Not the case for all structures
        data_dict['weekday_start'] = (week_start)
        data_dict['weekday_end'] = (week_end)
        if not np.isnan(openei[tier_str + 'adj'][i]):
            rate += openei[tier_str + 'adj'][i]
        data_dict['charge (imperial)'] = (rate)
        data_dict['charge (metric)'] = (rate)
        data_dict['units'] = (units)
        data_dict['Notes'] = ('')
        tariff.append(data_dict)

        max_str = string + '/period' + str(hour_list[hour]) + '/tier'+ str(tier_index) + 'max'
        if not np.isnan(openei[max_str][i]):
            charge_limit = openei[max_str][i]
            tier_index += 1
        elif hour_index < len(hour_ranges) - 1:
            hour_index += 1
            charge_limit = 0
            
        else:
            day_index += 1
            hour_index = 0
        try:
            hour_list = sched[lst[day_index][0]] # month_lst is the current month looked at
            hour_ranges = find_consecutive_ranges(hour_list) # processed month_lst
            hour = hour_ranges[hour_index][0]
        except IndexError:
            break

def process_TOU(i, tariff):
    # check if TOU data available
    if pd.isna(openei['demandweekdayschedule'][i]) and pd.isna(openei['demandweekendschedule'][i]):
        return

    weekday_sched = ast.literal_eval(openei['demandweekdayschedule'][i])
    weekend_sched = ast.literal_eval(openei['demandweekendschedule'][i])

    weekday_ranges = find_consecutive_ranges(weekday_sched)
    weekend_ranges = find_consecutive_ranges(weekend_sched)

    unpack_array(weekday_ranges, weekday_sched, 'demandratestructure', i, '$/kW', 'demand', 0, 4, tariff)
    unpack_array(weekend_ranges, weekend_sched, 'demandratestructure', i, '$/kW', 'demand', 5, 6, tariff)

def process_energyStruc(i, tariff):
    # check if energy data available
    if pd.isna(openei['energyweekdayschedule'][i]) and pd.isna(openei['energyweekendschedule'][i]):
        return

    weekday_sched = ast.literal_eval(openei['energyweekdayschedule'][i])
    weekend_sched = ast.literal_eval(openei['energyweekendschedule'][i])

    weekday_ranges = find_consecutive_ranges(weekday_sched)
    weekend_ranges = find_consecutive_ranges(weekend_sched)

    unpack_array(weekday_ranges, weekday_sched, 'energyratestructure', i, '$/kWh', 'electric', 0, 4, tariff)
    unpack_array(weekend_ranges, weekend_sched, 'energyratestructure', i, '$/kWh', 'electric', 5, 6, tariff)
    


def sector_filter(i, filter):
    if openei['sector'][i] == filter:
        return True
    return False

def add_metadata(i, zipcodes, metadata_list):
    metadata = make_meta()
    metadata['eiaid'] = openei['eiaid'][i]
    metadata['name'] = (openei['name'][i])
    metadata['label'] = (openei['label'][i])
    metadata['utility'] = (openei['utility'][i])
    metadata['source'] = (openei['source'][i])
    i_zips = zipcodes[zipcodes['eiaid'] == openei['eiaid'].iloc[i]]
    metadata['zipcode'] = (i_zips['zip'].iloc[0])
    metadata['state'] = (zipcodes.loc[zipcodes['eiaid'] == openei['eiaid'][i], 'state'].values[0])
    metadata_list.append(metadata)
    # put in city county, state
    


def add_index(i,tariff_list, zipcodes, metadata_list):
    tariff = []
    process_customer(i, tariff)
    process_demand(i, tariff)
    process_TOU(i, tariff)
    process_energyStruc(i, tariff)
    add_metadata(i, zipcodes, metadata_list)
    tariff_list.append(tariff)
    

def main():
    top_utils = pd.read_excel('../data/table_8.xlsx')
    zipcodes = pd.read_csv('../data/merged_zipcodes.csv')

    openei['sourceparent'] = openei['sourceparent'].fillna('')

    metadata_list = []
    tariff_list = []
    zips = pd.DataFrame()

    for name in top_utils['Name']:
        matching_rows = zipcodes[zipcodes['utility_name'] == name]
        if matching_rows.empty:
            continue
        zips = pd.concat([zips, matching_rows])
        eiaid = matching_rows.iloc[0]['eiaid']
        index = openei[openei['eiaid'] == eiaid].index
        #add the index to indexes
        if not index.empty:
            for i in index:
                if sector_filter(i, 'Industrial'):
                    add_index(i, tariff_list, zipcodes, metadata_list)




    for lst in tariff_list:
        lst_df = pd.DataFrame(lst)
        label = lst_df['label'][0]
        lst_df.to_csv(f'../tariffs/tariff_{label}.csv', index=False)

    metadata_df = pd.DataFrame(metadata_list)
    metadata_df.to_csv('../data/metadata.csv', index=False)

if __name__=="__main__":
    main()
