##
## Python program will run on selection
##
## Author: Florian Lungu
## Contact: florian@agourasoftware.com
##
## 06-04-2020 initial creation
##
import numpy as np
import plotly
import plotly.graph_objs as go
import tempfile
import pathlib
import pandas as pd
import dateutil
import datetime

# Title 
athlete = GC.athlete()
athleteName = athlete['name']
chartTitle = "Power Tracker: " + athleteName

# Time range in seconds (edit this)
timeRanges = 1200, 600, 300, 60, 10, 1
fieldNames = ['20min', '10min', '5min', '1min', '10sec', '1sec']

# Chart settings
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July','August', 'September', 'October', 'November', 'December']
colors = ['#ff46ac', '#ffa4fd', '#4389ff', '#3ab6ff', '#6688bd', '#a7b96d', 'greenyellow', '#339900', '#d44fd0', '#b358ff']

# Query data
print('start code')
fig = go.Figure()
# query gc for each time range
for i in range(len(fieldNames)):
	dataQ = GC.seasonPeaks(filter='Data contains "P"', series="power", duration=timeRanges[i])
	df = pd.DataFrame(dataQ)
	df.columns = ['datetime','bestpower']
	df['bestpower'] = df['bestpower'].round(0)
	df['bestpower'] = df['bestpower'].astype(int)
	df.index = df['datetime'] 

	df['year'] = pd.DatetimeIndex(df['datetime']).year
	df['month'] = pd.DatetimeIndex(df['datetime']).strftime('%B')
	df['year'] = df['year'].astype(str)
	df['month'] = df['month'].astype(str)
	df['month_year'] = df['month'] + " - " + df['year']

	# set monthly bests
	resultSet = df.resample('M').max()
	resultSet.set_index(['month_year'])
	df_pivoted = resultSet.pivot(index='month', columns='year', values='bestpower').reindex(months)

	# Create and style traces
	tColumns = df_pivoted.columns
	y = 0
	z = 0

	for colName in reversed(tColumns):
		fig.add_trace(go.Scatter(visible=False, x=months, y=df_pivoted[colName], name=colName, line=dict(color=colors[z], width=3)))
		y += 1
		z = y
		if y == len(colors):
			z = 0

# Make 1st trace group visible
for j in range(len(df_pivoted.columns)):
	fig.data[j].visible = True

# Edit the layout
fig.update_layout(title=chartTitle, xaxis_title='Month', yaxis_title='Watts', plot_bgcolor='#343434', paper_bgcolor='#343434', xaxis_gridcolor='rgba(0,0,0,0)', yaxis_gridcolor='#5e5e5e', font_color='white')

# Create and add slider
steps = []
for i in range(len(fieldNames)):
	step = dict(method="restyle", args=["visible", [False] * len(fig.data)], label=fieldNames[i])
	for j in range(len(df_pivoted.columns)):
		step["args"][1][len(df_pivoted.columns)*i+j] = True
	steps.append(step)

sliders = [dict(active=0, currentvalue={"prefix": "Display: "}, pad={"t": 50}, steps=steps)]
fig.update_layout(sliders=sliders)

# Define temporary file
temp_file = tempfile.NamedTemporaryFile(mode="w+t", prefix="GC_", suffix=".html", delete=False)

# Prepare plot
plotly.offline.plot({"data": fig}, auto_open = False, filename=temp_file.name)

# Load plot
GC.webpage(pathlib.Path(temp_file.name).as_uri())

print('code success') 