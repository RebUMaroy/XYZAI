# library imports
import pandas as pd
from IPython.display import display

# function Defination
def get_duration(itemDesc):
    if itemDesc == 'annual subscription':
        return 12
    elif itemDesc == 'monthly subscription' or itemDesc == 'calendar purchase':
        return 0

def get_monthly(amount, itemDesc, curr, dateStart):
    if itemDesc == 'annual subscription':
        # take date only
        curr = str(curr)[:10]
        # only apply revenue starting from the next month
        if curr == dateStart:
            return 0
        return amount/12
    elif itemDesc == 'monthly subscription' or itemDesc == 'calendar purchase':
        return amount


# import file
df = pd.read_csv(r".\xyz-billing.csv", sep=',')

# format date as yyyy-mm-dd into start date
df['dateStart'] = pd.to_datetime(df.date, dayfirst = True)
df['dateStart'] = df['dateStart'].dt.strftime('%Y-%m-%d')

# Create column month duration
df['duration'] = df['itemDescription'].apply(get_duration)
df['duration'] = df['duration'].astype(int)
df['dateEnd'] =  pd.to_datetime(df.dateStart) + df['duration'].astype('timedelta64[M]')

# add column monthEnd (current month) and convert to datetime format
df['monthEnd'] = df.apply(lambda row: pd.date_range(row['dateStart'], row['dateEnd'], freq='M'), axis=1)
df_t = df.explode('monthEnd')
df_t['monthEnd'] = pd.to_datetime(df_t.monthEnd)

# monthlyAmount, annual subscription only start applying from the next month
df_t['MonthlyAmount'] = df_t.apply(lambda x: get_monthly(x.amount, x.itemDescription, x.monthEnd, x.dateStart), axis=1)

# clean up interim columns
df_t = df_t.drop(columns=['dateStart', 'duration'])

# # chceck reaccuring amount is correct
# for index, row in df_t.where(df_t.customerID == 'customer1').iterrows():
#     print(row)
# check full df
# display(df_t)


###################################################
##################### Answers #####################
###################################################

# q1 
# excluding calandar purchase, set date range
df1 = df_t.where(((df_t.itemDescription == 'annual subscription') | (df_t.itemDescription == 'monthly subscription')) & (df_t.monthEnd < '2022-07-01')) \
    .groupby('monthEnd')['MonthlyAmount'].sum().to_frame('MRR').reset_index()
df1['MRR'] = pd.to_numeric(df1['MRR']).astype(int)
df1['monthEnd'] = df1['monthEnd'].dt.strftime('%Y-%m')
df1 = df1.rename(columns={'monthEnd':'month'})
display(df1)


# ---------------------------
# q2 
# calculate separately and combine in one df
# Subcription MRR growth rate
df2_s = df_t.where(((df_t.itemDescription == 'annual subscription') | (df_t.itemDescription == 'monthly subscription')) & (df_t.monthEnd < '2022-07-01')) \
    .groupby('monthEnd')['MonthlyAmount'].sum().pct_change().to_frame('MRRGrowthRate').reset_index()
df2_s['MRRGrowthRate'] = df2_s['MRRGrowthRate'].map(lambda x: '{:.2%}'.format(x))
# print(df2_Sub)

# calendar purchase growth rate
df2_c = df_t.where(df_t.itemDescription == "calendar purchase").groupby('monthEnd')['MonthlyAmount'] \
    .sum().pct_change().to_frame('CalendarGrowthRate').reset_index()
df2_c['CalendarGrowthRate'] = df2_c['CalendarGrowthRate'].map(lambda x: '{:.2%}'.format(x))
# print(df2_Cal)

# dr = pd.date_range(start='2021-01-31', end='2022-06-30', freq='M')
df2 = pd.merge(df2_s, df2_c, how="outer", on=['monthEnd'])
df2['monthEnd'] = df2['monthEnd'].dt.strftime('%Y-%m')
df2 = df2.rename(columns={'monthEnd':'month'})
display(df2)


# ---------------------------
# q3
# get items of interest
df3 = df_t.where((df_t.itemDescription == 'annual subscription')|(df_t.itemDescription == 'monthly subscription')).dropna(how="all").reset_index().drop(columns=['index'])

# extract customer and month when they paid
paidCount = {}
for index, row in df3.iterrows():
    if row['customerID'] not in paidCount:
        paidCount[row['customerID']] = []
    if row['MonthlyAmount'] > 0:
        paidCount[row['customerID']].append(row['monthEnd'].strftime('%Y-%m'))

# get the reporting range
monthRange = pd.date_range('2021-11-30', '2022-03-31', freq='M')
monthRange = monthRange.strftime('%Y-%m')

# count churns for each month
churnCount = {}
rowCount = monthRange.shape[0]
for ind in range(rowCount-1):
    churnCount[monthRange[ind+1]] = 0
    for cust in paidCount.keys():
        if monthRange[ind]  in paidCount[cust] and monthRange[ind+1] not in paidCount[cust]:
            churnCount[monthRange[ind+1]] += 1
result = {'Month':churnCount.keys(), 'churnCount':churnCount.values()}
df3 = pd.DataFrame.from_dict(result)
display(df3)



# export table into a full table format
df1.to_csv('.\question1.csv', index=False)  
df2.to_csv('.\question2.csv', index=False)  
df3.to_csv('.\question3.csv', index=False)  

