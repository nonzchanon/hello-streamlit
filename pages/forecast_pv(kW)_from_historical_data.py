from streamlit.logger import get_logger
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime 
# from sklearn.preprocessing import StandardScaler

import warnings
import pandas as pd
import numpy as np
import streamlit as st
warnings.filterwarnings('ignore', message='DataFrame is highly fragmented', category=pd.errors.PerformanceWarning)
import joblib
# Your code that produces the warning



def pv_data():
    # Filter out the specific PerformanceWarning

    # read uacj data 18/10/2023
    uacj_data_current = pd.read_csv('./workspaces/hello-streamlit/pages/data/Curve_UACJ solar_20231019121210.csv' , skiprows=1)
    # uacj_data_current = uacj_data_current.sort_values(by='Time')
    uacj_data_current.rename(columns={
    'Meteo Station5(08224)/Temp. (PV module)(℃)' : 'PV_module_temp(c)',
    'Meteo Station5(08224)/Ambient Temperature(℃)' : 'Ambient_temp(c)',
    'Meteo Station5(08224)/Ambient Humidity(%RH)' : 'Ambient_humidity(%RH)',
    'Meteo Station5(08224)/Atmospheric Pressure(hPa)' : 'Atmosperic_pressure(hpa)',
    'Meteo Station5(08224)/Wind Angle(°)' : 'Wind_angle',
    'Meteo Station5(08224)/Wind Speed(m/s)' : 'Wind_speed(m/s)',
    'UACJ solar(46372)/Inverter AC Power(kW)' : 'PV(kW)' ,
    'Meteo Station5(08224)/Slope Transient Irradiation(W/㎡)' : 'radiation(W/m2)',
    }
    , inplace=True)
    uacj_data_current['radiation(W/m2)'][uacj_data_current['radiation(W/m2)'] == '--'] = 0

    for i in uacj_data_current.columns.tolist():
        uacj_data_current[i][uacj_data_current[i] == '--'] = np.NaN

    for i in uacj_data_current.columns.tolist():
        if i != 'Time' :
            uacj_data_current[i] = pd.to_numeric(uacj_data_current[i])
            
    uacj_data_current['Time'] = pd.to_datetime(uacj_data_current['Time'] , errors='coerce')
    uacj_data_current = uacj_data_current.sort_values(by='Time' , ascending=True)
    uacj_data_current.dropna(inplace=True)

    return uacj_data_current


def gbr_models():
    loaded_model = joblib.load('./workspaces/hello-streamlit/pages/models/chained_gbr_model.joblib')
    return loaded_model



def window_input_output(input_length : int , output_length : int , data: pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    i = 1
    while i < input_length:
        for col in ['PV_module_temp(c)', 'Ambient_temp(c)', 'Ambient_humidity(%RH)', 'Atmosperic_pressure(hpa)', 'Wind_angle', 'Wind_speed(m/s)', 'radiation(W/m2)']:
            df[f'x_{col}_shifted_{i}_x'] = df[col].shift(-i)
        i += 1

    j = 0
    while j < output_length:
        df[f'y_{j}'] = df['PV(kW)'].shift(-output_length-j)
        j += 1
    df = df.dropna(axis= 0)
    return df



def predict(models , data):
    # scaler = StandardScaler()

    seq_df = window_input_output(24, 12, data)

    X_cols = [col for col in seq_df.columns if col.startswith('x')]

    # y_cols = [col for col in seq_df.columns if col.startswith('y')]

    data_to_forecast = seq_df[X_cols].values
    # data_to_forecast_scaled = scaler.fit_transform( data_to_forecast)
    result = models.predict(np.expand_dims(data_to_forecast[-1],axis=0))[0]

    # result = models.predict(np.expand_dims(data_to_forecast[-1],axis=0))[0]

    return result



gbr_chain_models = gbr_models()
st.write(gbr_chain_models)

# df_current_pv = pv_data()
# st.write(df_current_pv)
# pv_chart_data = pd.DataFrame( df_current_pv[['PV(kW)' , 'Time']], columns=["PV(kW)" , "Time"]  )
# pv_chart_data['Time'] = pd.to_datetime(pv_chart_data['Time'] , errors='coerce')
# pv_chart_data = pv_chart_data.set_index('Time')


# datetime_forecast = pd.date_range(start=df_current_pv['Time'].iloc[-1] + pd.Timedelta(hours=1), freq='5MIN', periods=12)
# datetime_forecast_df = pd.DataFrame( datetime_forecast , columns=[ "Time"] )
# datetime_forecast_df['Forecast_PV(kW)'] = np.random.randint(14000 , size = len(datetime_forecast))
# datetime_forecast_df['Time'] = pd.to_datetime(datetime_forecast_df['Time'] , errors='coerce')
# datetime_forecast_df = datetime_forecast_df.set_index('Time')
# st.write(datetime_forecast_df)


# st.area_chart(pv_chart_data)
# st.area_chart(datetime_forecast_df)

import datetime

################################################################################

df = pd.DataFrame({"Time":[1]})

start_date = st.date_input('Enter start date', value=datetime.datetime(2023,10,17))
start_time = st.time_input('Enter start time', datetime.time(8, 45 , 00))

start_datetime = datetime.datetime.combine(start_date, start_time)

df["DateTime"] = [start_datetime + datetime.timedelta(seconds=time) for time in df["Time"]]

df["DateTime"] = [date.strftime("%d/%m/%Y %H:%M:%S") for date in df["DateTime"]]

df = df.drop(columns=["Time"])

st.write('Start Date: ', df['DateTime'].iloc[-1])

################################################################################


df_current_pv_based = pv_data()
df_current_pv = df_current_pv_based[df_current_pv_based['Time'] <= df['DateTime'].iloc[0]]
st.write(df_current_pv_based)

pv_chart_data = pd.DataFrame(df_current_pv[['PV(kW)' , 'Time']], columns=["PV(kW)" , "Time"])
pv_chart_data['Time'] = pd.to_datetime(pv_chart_data['Time'], errors='coerce')
pv_chart_data = pv_chart_data.set_index('Time')



####################### forecast ######################

datetime_forecast = pd.date_range(start=df_current_pv['Time'].iloc[-1] + pd.Timedelta(hours=0 , minutes=5), freq='5MIN', periods=12)
datetime_forecast_df = pd.DataFrame(datetime_forecast, columns=["Time"])
datetime_forecast_df['Time'] = pd.to_datetime(datetime_forecast_df['Time'], errors='coerce')

# datetime_forecast_df['Forecast_PV(kW)'] = np.random.randint(14000, size=len(datetime_forecast))

forecasting_result = predict(gbr_chain_models , df_current_pv)
st.write('------')
st.write('\n')
st.write('Forecasts_PV(kW)')
datetime_forecast_df['Forecasts_PV(kW)'] = forecasting_result
st.write('\n')

datetime_forecast_df = datetime_forecast_df.set_index('Time')

# Combine both data frames
combined_data = pd.concat([pv_chart_data, datetime_forecast_df], axis=0)
# Plotting combined data
st.area_chart(combined_data , color=["#E35335", "#ADD8E6"])

### Actual Pv(kW) ###
st.write('Actual PV(kW)')
st.write('\n')

# df['DateTime'] = pd.to_datetime(df['DateTime'])
# Now you can perform operations with Timedelta
# end_time = df['DateTime'].iloc[0] + pd.Timedelta(minutes=5*12)

df_current_pv_based = df_current_pv_based.set_index('Time')

end_actual = df_current_pv['Time'].iloc[-1] +  pd.Timedelta(hours=1) 
end_actual_df = df_current_pv_based[df_current_pv_based.index <= end_actual]
# st.write( df_current_pv_based[df_current_pv_based.index <= end_actual])
st.area_chart(end_actual_df['PV(kW)'])


