import streamlit as st
import time
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from functions import *

def check_nodes(selected_nodos_p, selected_nodos_d):
    if selected_nodos_p == selected_nodos_d:
        st.sidebar.warning('Selecciona un NodoP o NodoP Distribuido')
        st.stop()

def check_markets(mda, mtr):
    if not any([mda, mtr]):
        st.sidebar.warning('Selecciona uno o dos mercados')
        st.stop()



# List of nodes for multiselects
df = pd.read_csv('nodos.csv')
nodos_p = df['CLAVE'].tolist()
nodos_d = df['ZONA DE CARGA'].unique().tolist()

# Dates for date_input creation and delimitation
max_date = date.today()+timedelta(days=1)
min_date = datetime(2016, 1, 1)
today = date.today()
start_date = date.today()-timedelta(days=15)

# Nodes multiselect
selected_nodos_p = st.sidebar.multiselect('NodosP',nodos_p)
selected_nodos_d = st.sidebar.multiselect('NodosP Distribuidos',nodos_d)

# Date picker
dates = st.sidebar.date_input('Fechas', max_value=max_date, min_value=min_date, value=(start_date, today))

# MDA and MTR checkboxes
col1, col2, *_ = st.sidebar.beta_columns(4)
with col1:
    mda = st.checkbox('MDA', value=False)
with col2:
    mtr = st.checkbox('MTR', value=False)

# Graph button
button_pressed = st.sidebar.button('Graficar')

# wait until a date range is selected
if len(dates)!=2:
    st.stop()

start_date, end_date = dates


if not button_pressed:
    st.stop()

# One or more nodes and markets must be selected to continue...
check_nodes(selected_nodos_p, selected_nodos_d)
check_markets(mda, mtr)


dates_packed = pack_dates(start_date, end_date)
nodos_p_packed = pack_nodes(selected_nodos_p,'PML')
nodos_d_packed = pack_nodes(selected_nodos_d,'PND')

if mda:
    if nodos_p_packed != [[]]:
        urls_nodos_p_mda = get_urls_to_request(nodos_p_packed, dates_packed, 'PML', 'MDA')
    else:
        urls_nodos_p_mda = []

    if nodos_d_packed != [[]]:
        urls_nodos_d_mda = get_urls_to_request(nodos_d_packed, dates_packed, 'PND', 'MDA')
    else:
        urls_nodos_d_mda = []

    print(urls_nodos_p_mda)
    print(urls_nodos_d_mda)

if mtr:
    if nodos_p_packed != [[]]:
        urls_nodos_p_mtr = get_urls_to_request(nodos_p_packed, dates_packed, 'PML', 'MTR')
    else:
        urls_nodos_p_mtr = []

    if nodos_d_packed != [[]]:
        urls_nodos_d_mtr = get_urls_to_request(nodos_d_packed, dates_packed, 'PND', 'MTR')
    else:
        urls_nodos_d_mtr = []

    print(urls_nodos_p_mtr)
    print(urls_nodos_d_mtr)


print()







# st.header('Charts')
# col1 , col2, col3, col4 = st.beta_columns(4)
# symbol = col1.text_input ('Enter Symbol','AMZN')
# start = col2.date_input ('Start', datetime.strptime('2020-1-1', '%Y-%m-%d'))
# end = col3.date_input('End')


# progress_bar = st.sidebar.progress(0)
# status_text = st.sidebar.empty()
# last_rows = np.random.randn(1, 1)
# chart = st.line_chart(last_rows)

# for i in range(1, 101):
#     new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
#     status_text.text("%i%% Complete" % i)
#     chart.add_rows(new_rows)
#     progress_bar.progress(i)
#     last_rows = new_rows
#     time.sleep(0.05)

# progress_bar.empty()