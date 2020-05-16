##
## Python program will run on selection
##
## Author: Florian Lungu
## Contact: florian@agourasoftware.com
##
## 20-Apr-2020 initial creation
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
# import math #you only need this library if you use math.exp() for CTL

# Title 
athlete = GC.athlete()
athleteName = athlete['name']
chartTitle = "Performance Management Chart (PMC): " + athleteName

# Chart settings (ok to edit this)
ctlDays = 42
atlDays = 7
power_stress = 'BikeStress'
hr_stress = 'TRIMP_Zonal_Points'
showColumns = ['CTL', 'ATL', 'TSB']
colors = ['#ff46ac', '#4389ff', '#ffa4fd']

# Query data
print('py chart code start')
fig = go.Figure()
ctlDates = []
ctlDateTimes = []
ctlVals = []
atlVals = []
tssVals = []
filteredDates = []
filteredCTL = []
filteredATL = []
filteredTSB = []

# Query GC for season metrics
dataS = GC.seasonMetrics(all=True, compare=False)
startDate = dataS['date'][0]
endDate = dataS['date'][-1]

# Parse season metrics into all dates between first date and last day
while startDate <= endDate:	
	tssVals.append(0)	
	ctlVals.append(0)
	atlVals.append(0)
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

# Compute CTL & ATL
ctlY = 0
atlY = 0
for k in range(len(ctlDates)):
	# Option 1: set CTL using formula [Today’s TSS * (1-e^(-1/42)] + {Yesterday’s CTL * (e^(-1/42)]
	# ctlVals[k] = round(tssVals[k]*(1-math.exp(-1/ctlDays))+ctlY*math.exp(-1/ctlDays))
					
	# Option 2: set CTL using formula Yesterday's CTL + (Today's TSS - Yesterday's CTL)/Time Constant
	ctlVals[k] = ctlY+(tssVals[k]-ctlY)/ctlDays
	atlVals[k] = atlY+(tssVals[k]-atlY)/atlDays
	ctlY = ctlVals[k]
	atlY = atlVals[k]

# filter data
dataFilter = GC.seasonMetrics(compare=False)
if dataFilter['date'][-1] + timedelta(days=1) == date.today():
	startDate = dataFilter['date'][0] + timedelta(days=1)
	endDate = dataFilter['date'][-1] + timedelta(days=1)
else:
	startDate = dataFilter['date'][0]
	endDate = dataFilter['date'][-1]

for k in range(len(ctlDates)):
	if ctlDates[k] >= startDate and ctlDates[k] <= endDate:
		filteredDates.append(ctlDateTimes[k])
		filteredCTL.append(round(ctlVals[k],0))
		filteredATL.append(round(atlVals[k],0))
		if k == 0:
			filteredTSB.append(0)
		else:
			filteredTSB.append(round(ctlVals[k-1],0)-round(atlVals[k-1],0))
			
dataQ = {'datetime': filteredDates, 'ctl': filteredCTL, 'atl': filteredATL, 'tsb': filteredTSB} 
	
# Modify the data for charting
df = pd.DataFrame(dataQ)
df.columns = ['datetime', 'CTL', 'ATL', 'TSB']
df.index = df['datetime'] 

# Create and style traces
for k in range(len(showColumns)):
	fig.add_trace(go.Scatter(visible=True, x=filteredDates, y=df[showColumns[k]], name=showColumns[k], line=dict(color=colors[k], width=1)))
	
# Edit the layout
fig.update_layout(title=chartTitle, xaxis_title='Date', yaxis_title='Points', plot_bgcolor='#343434', paper_bgcolor='#343434', xaxis_gridcolor='rgba(0,0,0,0)', yaxis_gridcolor='#5e5e5e', font_color='white', hovermode='x')

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Prepare plot
plotly.offline.plot({"data": fig}, auto_open = False, filename=temp_file.name)

# Load plot
GC.webpage(pathlib.Path(temp_file.name).as_uri())

print('py chart code success')