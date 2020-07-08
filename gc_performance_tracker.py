##
## Python program will run on selection
##
## Author: Florian Lungu
## Contact: florian@agourasoftware.com
##
## 06-Apr-2020 initial creation
## 15-Apr-2020 bug fixes and enhancements
## 17-Apr-2020 added hr_stress as secondary field
## 20-Apr-2020 date range fix
## 08-Jul-2020 added drop_duplicates before pandas.pivot
##
import numpy as np
import plotly
import plotly.graph_objs as go
import tempfile
import pathlib
import pandas as pd
import dateutil
import datetime
from datetime import date, timedelta, datetime
#import math #you only need this library if you use math.exp() for CTL

# Title 
athlete = GC.athlete()
athleteName = athlete['name']
chartTitle = "Performance Tracker: " + athleteName
chartSubTitle = "Chart displaying maximum monthly value of: "

# Chart settings (ok to edit this)
ctlDays = 42
power_stress = 'BikeStress'
hr_stress = 'TRIMP_Zonal_Points'
timeRanges = 0, 1200, 600, 300, 60, 10, 1
fieldNames = ['CTL', '20min Pwr', '10min Pwr', '5min Pwr', '1min Pwr', '10sec Pwr', '1sec Pwr']
colors = ['#ff46ac', '#ffa4fd', '#4389ff', '#3ab6ff', '#6688bd', '#a7b96d', 'greenyellow', '#50b329', '#de59da', '#b358ff']
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July','August', 'September', 'October', 'November', 'December']

# Query data
print('py chart code start')
fig = go.Figure()
ctlDates = []
ctlDateTimes = []
ctlVals = []
tssVals = []
filteredDates = []
filteredCTL = []

# Query GC for season metrics or each time range
for i in range(len(fieldNames)):
	if fieldNames[i] == 'CTL':
		dataS = GC.seasonMetrics(all=True, compare=False)
		startDate = dataS['date'][0]
		endDate = dataS['date'][-1]

		# Parse season metrics into all dates between first date and last day
		while startDate < endDate:	
			tssVals.append(0)	
			ctlVals.append(0)
			ctlDates.append(startDate)
			dt = datetime.combine(startDate, datetime.min.time())
			ctlDateTimes.append(dt)
			startDate = startDate + timedelta(days=1)
		
		# Set the total TSS value for each day
		for j in range(len(dataS['date'])):
			for k in range(len(ctlDates)):
				if dataS['date'][j] == ctlDates[k]:
					if dataS[power_stress][j] == 0.0:
						tssVals[k] += dataS[hr_stress][j]
					else:
						tssVals[k] += dataS[power_stress][j]

		# Compute CTL
		ctlY = 0
		for k in range(len(ctlDates)):
			# Option 1: set CTL using formula [Today’s TSS * (1-e^(-1/42)] + {Yesterday’s CTL * (e^(-1/42)]
			# ctlVals[k] = tssVals[k]*(1-math.exp(-1/ctlDays))+ctlY*math.exp(-1/ctlDays)
					
			# Option 2: set CTL using formula Yesterday's CTL + (Today's TSS - Yesterday's CTL)/Time Constant
			ctlVals[k] = ctlY+(tssVals[k]-ctlY)/ctlDays
			ctlY = ctlVals[k]
			
		# filter data
		dataFilter = GC.seasonMetrics(compare=False)
		startDate = dataFilter['date'][0]
		endDate = dataFilter['date'][-1]

		for k in range(len(ctlDates)):
			if ctlDates[k] >= startDate and ctlDates[k] <= endDate:
				filteredDates.append(ctlDateTimes[k])
				filteredCTL.append(ctlVals[k])
			
		dataQ = {'datetime': filteredDates, 'ctl': filteredCTL} 
				
	else:
		dataQ = GC.seasonPeaks(series="power", duration=timeRanges[i])
	
	# Modify the data for charting
	df = pd.DataFrame(dataQ)
	df.columns = ['datetime','maxval']
	df['maxval'] = df['maxval'].round(0)
	df['maxval'] = df['maxval'].astype(int)
	df['maxval'] = df['maxval'].replace({0:np.nan})
	df.index = df['datetime'] 

	df['year'] = pd.DatetimeIndex(df['datetime']).year
	df['month'] = pd.DatetimeIndex(df['datetime']).strftime('%B')
	df['year'] = df['year'].astype(str)
	df['month'] = df['month'].astype(str)
	df['month_year'] = df['month'] + " - " + df['year']

	# Set monthly bests
	resultSet = df.resample('M').max()
	resultSet.set_index(['month_year'])
	resultSet = resultSet.drop_duplicates(['month_year'])
	df_pivoted = resultSet.pivot(index='month', columns='year', values='maxval').reindex(months)

	# Create and style traces
	tColumns = df_pivoted.columns
	rightColor = len(tColumns)-1-(len(colors)*int(len(tColumns)/len(colors)))
	for colName in reversed(tColumns):
		fig.add_trace(go.Scatter(visible=False, x=months, y=df_pivoted[colName], name=colName, line=dict(color=colors[rightColor], width=3)))
		rightColor = rightColor-1
		if rightColor < 0:
			rightColor = len(colors)-1

# Make first trace group visible
for j in range(len(df_pivoted.columns)):
	fig.data[j].visible = True

# Edit the layout
fig.update_layout(title=chartTitle, xaxis_title='Month', yaxis_title='Watts', plot_bgcolor='#343434', paper_bgcolor='#343434', xaxis_gridcolor='rgba(0,0,0,0)', yaxis_gridcolor='#5e5e5e', font_color='white', hovermode='x')

# Create and add slider
steps = []
for i in range(len(fieldNames)):
	step = dict(method="restyle", args=["visible", [False] * len(fig.data)], label=fieldNames[i])
	for j in range(len(df_pivoted.columns)):
		step["args"][1][len(df_pivoted.columns)*i+j] = True
	steps.append(step)

sliders = [dict(active=0, currentvalue={"prefix": chartSubTitle}, pad={"t": 50}, steps=steps)]
fig.update_layout(sliders=sliders)

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Prepare plot
plotly.offline.plot({"data": fig}, auto_open = False, filename=temp_file.name)

# Load plot
GC.webpage(pathlib.Path(temp_file.name).as_uri())

print('py chart code success')