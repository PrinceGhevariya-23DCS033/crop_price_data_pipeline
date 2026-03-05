import pandas as pd
df = pd.read_csv('test_results.csv')
print('=== STATUS BY CROP ===')
summary = df.groupby(['crop','status']).size().unstack(fill_value=0)
for col in ['OK','FAIL','SKIP']:
    if col not in summary.columns:
        summary[col] = 0
summary = summary[['OK','FAIL','SKIP']]
pd.set_option('display.max_rows', 60)
print(summary.to_string())
print()
print('=== OVERALL ===')
print(df['status'].value_counts().to_string())
print()
fails = df[df['status']=='FAIL']
if len(fails) > 0:
    print('=== FAILURES ===')
    for _, r in fails.iterrows():
        print(' ' + str(r['crop']) + ' / ' + str(r['district']) + ': ' + str(r['reason']))
else:
    print('=== NO FAILURES - ALL COMBINATIONS PASS - READY TO UPLOAD! ===')
