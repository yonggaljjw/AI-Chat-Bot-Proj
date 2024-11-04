import pandas as pd
df = pd.read_csv("./fsc_announcements_extract.csv")
print(df.isna().sum())