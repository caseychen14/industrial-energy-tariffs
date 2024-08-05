import pandas as pd

df = pd.read_excel('../data/flight.xls')

sorted_df = df.sort_values(by='GHG QUANTITY (METRIC TONS CO2e)', ascending=False)

top_2500 = sorted_df.head(2500)

top_2500.to_excel('top_2500_ghg.xlsx', index=False)

