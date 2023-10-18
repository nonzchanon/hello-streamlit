# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
from streamlit.logger import get_logger
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pvlib
from pvlib import location
from pvlib import irradiance
from plotly.subplots import make_subplots
#from tzwhere.tzwhere import tzwhere
import folium
from streamlit_folium import folium_static , st_folium
import base64
import requests
from PIL import Image
from io import BytesIO
from geopy.geocoders import Nominatim
import pytz
from pytz import timezone
import sqlite3
import smtplib
from email.mime.text import MIMEText
import datetime


LOGGER = get_logger(__name__)


def run():
# -*- coding: utf-8 -*-



  st.set_page_config(page_title="Solar Energy Estimator Using PVlib", page_icon="☀️",layout="wide")


  #Main Program#---------------------------------------

  st.markdown(
      """
      <div style="background-color:#279119;padding:5px;border-radius:5px">
      <h3 style="color:white;text-align:center;">Solar Energy Estimator PVlib</h3>
      </div>
      """,
      unsafe_allow_html=True,
  )


  st.write('\n')

  all_timezones = pytz.all_timezones
  default_ix=all_timezones.index('Asia/Bangkok')


  # Load module specifications from CSV
  module_df = pd.read_csv('module_data.csv')
  col1,col2,col3=st.columns([0.5,2,0.5])
  # Begin form
  with col2.form(key='my_form'):
      # Get plant capacity from user
      plant_cap = st.number_input("Enter the plant capacity in kW" , value=18218)
      # User inputs
      latitude = st.number_input('Enter latitude',min_value=-90.0, max_value=90.0, value=12.95281634822728) #13.57749372632019
      longitude = st.number_input('Enter longitude',min_value=-180.0, max_value=180.0, value=101.09737136411678) #100.92252171629401
      tz_str = st.selectbox("Select your Time Zone", all_timezones,index=default_ix)
      
      # Let users select a model
      module_selection = st.selectbox("Select a model", options=module_df['Model Name'].unique())
      # Get selected module data
      module = module_df[(module_df['Model Name'] == module_selection)].iloc[0]
      module_efficiency = module['Efficiency'] / 100
      surface_tilt = st.slider('Enter surface tilt',0.0,90.00,20.00,0.10)
      surface_azimuth = st.slider('Enter surface azimuth (180 means facing direct to south)',-180,180,180,1)
      #module_efficiency = st.number_input('Enter module efficiency (%)', min_value=0.0, max_value=100.0, step=0.1, value=21.0, format='%f') / 100
      pr = st.number_input('Enter plant Performance Ratio (%PR)', min_value=0.0, max_value=100.0, step=0.1, value=81.0, format='%f') / 100
      module_watt_peak = module['Watt peak']
      area=module['Area']

      day_ahead = st.number_input('Enter day ahead', min_value=0, max_value=31, step=1, value=7)


      # Every form must have a submit button.
      submitted = st.form_submit_button("Submit")
      

  if submitted:
      total_modules = round(plant_cap / (module_watt_peak / 1000),0)
      plant_capacity=(total_modules*module_watt_peak)/1000
      total_area=area*total_modules
      tz_str=tz_str

      col1,col2=st.columns([1,1])
      with col1:
              # Create a map centered at the input coordinates
          m = folium.Map(location=[latitude, longitude], width='100%', height='100%')
          # Add a marker at the input coordinates
          folium.Marker([latitude, longitude]).add_to(m)
          # Display the map
          folium_static(m)
      
      

      st.write('______________')
      a1,a2,a3=st.columns([0.5,2,0.5])
      a2.header('Sub hourly Solar Irradiation Values')
      st.write('\n')
      m1,m2,m3=st.columns(3)
      
      col1,col2=st.columns(2)
      

      # Get specific energy production for each month using PVLIB
      def calculate_solar_production(latitude, longitude, tz_str, surface_tilt, surface_azimuth, module_efficiency, pr):
          # Define the location
          site = location.Location(latitude, longitude, tz=tz_str)

          # Define a range of dates for one year
          # times = pd.date_range(start='2023-08-01', end='2023-10-01', freq='15min', tz=tz_str)

          # get the current date
          current_date = datetime.datetime.now()

          # add 7 days to the current date
          days_ahead_date = current_date + datetime.timedelta(days=day_ahead)

          times = pd.date_range(start=str(current_date.date()), end=str(days_ahead_date.date()), freq='15MIN', tz=tz_str)

          times = times[:-1]  # remove the last hour

          # Get solar azimuth and zenith to pass to the transposition function
          solar_position = site.get_solarposition(times)

          # Get irradiance data using the DISC model
          irrad_data = site.get_clearsky(times)

          # Calculate POA irradiance
          poa_irrad = irradiance.get_total_irradiance(surface_tilt=surface_tilt, surface_azimuth=surface_azimuth, solar_zenith=solar_position['apparent_zenith'], solar_azimuth=solar_position['azimuth'], dni=irrad_data['dni'], ghi=irrad_data['ghi'], dhi=irrad_data['dhi'])
          
          #st.write(poa_irrad)
          hourly_ghi=(poa_irrad['poa_global']).resample('15MIN').max()
          #max-min values
          max_hourly_ghi=hourly_ghi.max()

          
          m1.metric(label='Max Daily GHI (kW/m\u00b2)',value="{:.2f}".format(max_hourly_ghi))
          
          hourly_ghi=pd.DataFrame({"Daily Solar Irradiation (Wh/m2)": hourly_ghi})
        
          
          col1.write('Daily Solar Irradiation (resolution 15 MIN)')
          col1.write(hourly_ghi)
          
              
          daily_gii = hourly_ghi.resample('D').sum()
          daily_gii=pd.DataFrame(daily_gii)
          daily_gii.columns = ["Daily Solar Irradiation (kWh/m2)"]
          daily_gii = daily_gii.reset_index()
          # Convert the dates to datetime objects & get the month names
          daily_gii['Daily'] = pd.to_datetime(daily_gii['index']).dt.day_name()
          daily_gii = daily_gii.drop(columns=['index'])
          # Make 'Month' column to be the first column
          daily_gii = daily_gii.set_index('Daily').reset_index()
          
          #col2.write('Daily Solar Irradiation')
          #col2.write(daily_gii)
          # Convert irradiance to energy production
          

          fig1 = go.Figure()
          fig1.add_trace(go.Scatter(x=hourly_ghi.index, y=hourly_ghi['Daily Solar Irradiation (Wh/m2)'], mode='lines', name='Daily Solar Irradiation (Wh/m2)'))
          
          # Add titles and labels
          fig1.update_layout(title_text="Solar Irradiation (Wh/m2)")
          fig1.update_xaxes(title_text="Min")
          fig1.update_yaxes(title_text="Irradiation")
          
          col1.plotly_chart(fig1, use_container_width=True)

            
          fig2 = go.Figure()
          fig2.add_trace(go.Bar(
                          x=daily_gii['Daily'],
                          y=daily_gii['Daily Solar Irradiation (kWh/m2)'],
                          name="Daily Solar Irradiation (kWh/m2)",
                          marker_color='indianred'
          ))
          
          fig2.update_layout(title_text='Daily Solar Irradiation (kWh/m2)',
                            xaxis=dict(type='category'))
                  
          
          #col2.plotly_chart(fig2, use_container_width=True)
          
          hourly_production = (poa_irrad['poa_global']) * module_efficiency* pr
          min15_production = hourly_production.resample('15MIN').sum()

          return min15_production
          
      
      min15_production = calculate_solar_production(latitude, longitude, tz_str, surface_tilt, surface_azimuth, module_efficiency, pr)
      energy_df = pd.DataFrame(columns=['Interval', 'Solar Energy Production'])
      
      # st.write('15min Production',min15_production)
      # st.write('totalarea',total_area)
      
      st.write('_________')
      a1,a2=st.columns([0.5,2])
      a2.header('Daily Solar Energy Generation Values')
      st.write('\n')
      m1,m2,m3=st.columns(3)
      col1,col2=st.columns(2)
          

      total_daily_production = min15_production * total_area
      
      m1.metric(label='Max Solar Energy (kW)',value="{:.2f}".format(total_daily_production.max()))

      total_daily_production=pd.DataFrame({"Daily Solar Energy Production (kWh)": total_daily_production})

      col1.write('Daily Solar Energy Production')
      col1.write(total_daily_production)


      total_daily_production.index = min15_production.index.tz_localize(None)
      
      Total_Daily_Energy=total_daily_production.resample('D').sum()
      Total_Daily_Energy=pd.DataFrame(Total_Daily_Energy)
      Total_Daily_Energy.columns=["Daily Solar Energy Production (kWh)"]
      
    
      Total_Daily_Energy = Total_Daily_Energy.reset_index()
      # Convert the dates to datetime objects & get the month names
      Total_Daily_Energy['Daily'] = pd.to_datetime(Total_Daily_Energy['index']).dt.day_name()
      Total_Daily_Energy = Total_Daily_Energy.drop(columns=['index'])
      # Make 'Month' column to be the first column
      Total_Daily_Energy = Total_Daily_Energy.set_index('Daily').reset_index()
      
      # col2.write('Daily Solar Energy Production')
      # col2.write(Total_Daily_Energy)
      




      total_daily_production.index = min15_production.index.tz_localize(None)
      
      total_production=total_daily_production.resample('15MIN').sum()

      
      #Data Visualization#-----------------------------------------
      #Daily Values
      st.write('_________')

      # Create DataFrame for plotting
      
      col1,col2=st.columns(2)

      
      
      # Plotting of daily solar energy
      fig = go.Figure()
      fig.add_trace(go.Scatter(x=total_daily_production.index, y=total_daily_production['Daily Solar Energy Production (kWh)'], mode='lines', name='Solar Energy Production'))
      
      # Add titles and labels
      fig.update_layout(title_text="Daily Solar Energy Production (kWh)")
      fig.update_xaxes(title_text="Date")
      fig.update_yaxes(title_text="Energy")
      
      col1.plotly_chart(fig, use_container_width=True)
      


if __name__ == "__main__":
    run()
