import pandas as pd

mixed_type_columns = [3, 5, 28, 362, 392, 397, 402, 407, 412, 417, 437, 442, 447, 452, 457, 472, 477, 482, 492, 497, 502, 507, 517, 522, 527, 532, 542, 547, 552, 557, 562, 567, 572, 577, 582, 587, 592, 597, 602, 607, 612, 617, 622, 627, 632, 637, 642, 647, 652, 655, 668]

dtype_dict = {col: str for col in mixed_type_columns}

openei_dummy = pd.read_csv('/Users/caseychens/Documents/stanford/summer24/we3/data/OpenEI data/91761.csv', dtype=dtype_dict)

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

pd.head()