import streamlit as st
import time
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
from functions import *

def check_nodes(selected_nodes_p, selected_nodes_d):
    if selected_nodes_p == selected_nodes_d:
        st.sidebar.warning('Selecciona un NodoP o NodoP Distribuido')
        st.stop()

def check_markets(mda, mtr):
    if not any([mda, mtr]):
        st.sidebar.warning('Selecciona uno o dos mercados')
        st.stop()

def pack_dates(start_date, end_date):
    """Gets days to ask for info and start date, returns appropiate data intervals to assemble APIs url"""
    dates = []
    delta = end_date-start_date
    days = delta.days

    while days >= 0:

        if days >= 7:
            last_date = start_date + timedelta(days = 6)
            dates.append( [str(start_date),str(last_date)] )
            start_date = last_date + timedelta(days = 1)
            days -= 7

        else:
            last_date = end_date
            dates.append( [str(start_date),str(last_date)] )
            days = -1

    return dates

def get_node_system(node):
    """This functions pairs a node or zone to it's system"""
    df = pd.read_csv('nodos2.csv')

    if df[df["CLAVE"] == node].shape[0]:
        system = df[df["CLAVE"] == node]["SISTEMA"].to_list()[0]

    elif df[df["ZONA DE CARGA"] == node].shape[0]:
        system = df[df["ZONA DE CARGA"] == node]["SISTEMA"].to_list()[0]
    
    else:
        raise

    return (node, system)

def pack_nodes(nodes, node_type):
    """Returns a list of lists with nodes, this is done because depending on node type we have a maximum number of nodes per request ()PND is 10 max and PML is 20 max. PML missing"""
    nodes = [node.replace(' ','-') for node in nodes]

    size_limit = 10 if node_type == 'PND' else 20

    nodos_api = []
    while True:
        if len(nodes) > size_limit:
            nodos_api.append(nodes[:size_limit])
            nodes = nodes[size_limit:]
        else:
            nodos_api.append(nodes)
            break

    return nodos_api

def get_urls_to_request(nodes_dict, dates_packed, node_type, markets):

    urls_list = []
    for market in markets:
        for system, nodes_packed in nodes_dict.items():
            if not len(nodes_packed[0]): 
                continue
            
            for node_group in nodes_packed:
                for dates in dates_packed:
                    nodes_string = ','.join(node_group)

                    # Select correct API base
                    url = url_frame[node_type]

                    # Building request url with data provided
                    url_complete = f'{url}{system}/{market}/{nodes_string}/{dates[0][:4]}/{dates[0][5:7]}/{dates[0][8:]}/{dates[1][:4]}/{dates[1][5:7]}/{dates[1][8:]}/JSON'

                    urls_list.append(url_complete)

    return urls_list

# def check_data(json_data, date_interval):

#     if json_data['status'] == 'OK':

#         first_date = json_data['Resultados'][0]['Valores'][0]['fecha']
#         last_date = json_data['Resultados'][0]['Valores'][-1]['fecha']

#         if [first_date,last_date] != date_interval:
#             print(f'---Got data up to {last_date}, missing {date_interval[1]}---')

#         return True

#     else:
#         if json_data['status'] == 'ZERO RESULTS':
#             print(f'---No data availabe for dates {first_date} to {last_date}---')
#         else:
#             print(f"---Data status not 'OK': {json_data['status']}---")

#         return False

def json_to_dataframe(json_file):
    """Reads json file, creates a list of nodes DataFrames and concatenates them. After that it cleans/orders the final df and returns it"""
    dfs = []

    for node in json_file['Resultados']:
        dfs.append(pd.DataFrame(node))

    df = pd.concat(dfs) # Join all data frames

    # Clean/order df to same format of existing csv files
    df['Sistema'] = json_file['Sistema']
    df['Mercado'] = json_file['proceso']
    df['Fecha'] = df['Valores'].apply(lambda x: x['fecha'])
    df['Hora'] = df['Valores'].apply(lambda x: x['hora'])

    if json_file['nombre'] == 'PEND':
        df['Precio [$/MWh]'] = df['Valores'].apply(lambda x: x['pz'])
        df['Componente de Energía [$/MWh]'] = df['Valores'].apply(lambda x: x['pz_ene'])
        df['Componente de Pérdidas [$/MWh]'] = df['Valores'].apply(lambda x: x['pz_per'])
        df['Componente de Congestión [$/MWh]'] = df['Valores'].apply(lambda x: x['pz_cng'])
        df['Clave o Nombre'] = df['zona_carga'].copy()
        df['Tipo de NodoP'] = "NodoP Distribuido"

    if json_file['nombre'] == 'PML':
        df['Precio [$/MWh]'] = df['Valores'].apply(lambda x: x['pml'])
        df['Componente de Energía [$/MWh]'] = df['Valores'].apply(lambda x: x['pml_ene'])
        df['Componente de Pérdidas [$/MWh]'] = df['Valores'].apply(lambda x: x['pml_per'])
        df['Componente de Congestión [$/MWh]'] = df['Valores'].apply(lambda x: x['pml_cng'])
        df['Clave o Nombre'] = df['clv_nodo'].copy()
        df['Tipo de NodoP'] = "NodoP"

    df = df[['Sistema','Mercado','Fecha','Hora','Clave o Nombre','Precio [$/MWh]','Componente de Energía [$/MWh]', 'Componente de Pérdidas [$/MWh]','Componente de Congestión [$/MWh]', "Tipo de NodoP"]]
    return df

def main():

    # List of nodes for multiselects
    df = pd.read_csv('nodos2.csv')
    nodes_p = df['CLAVE'].tolist()
    nodes_d = df['ZONA DE CARGA'].unique().tolist()

    # Dates for date_input creation and delimitation
    max_date = date.today()+timedelta(days=1)
    min_date = datetime(2016, 1, 1)
    today = date.today()
    start_date = date.today()-timedelta(days=15)

    # Nodes multiselect
    selected_nodes_p = st.sidebar.multiselect('NodosP',nodes_p)
    selected_nodes_d = st.sidebar.multiselect('NodosP Distribuidos',nodes_d)

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
    check_nodes(selected_nodes_p, selected_nodes_d)
    check_markets(mda, mtr)

    dates_packed = pack_dates(start_date, end_date)
    nodes_d_system = list(map(get_node_system, selected_nodes_d))
    nodes_p_system = list(map(get_node_system, selected_nodes_p))

    nodes_d = {
        "SIN": pack_nodes([node[0] for node in nodes_d_system if node[1] == "SIN"], "PND"),
        "BCA": pack_nodes([node[0] for node in nodes_d_system if node[1] == "BCA"], "PND"),
        "BCS": pack_nodes([node[0] for node in nodes_d_system if node[1] == "bcs"], "PND")
    }
    nodes_p = {
        "SIN": pack_nodes([node[0] for node in nodes_p_system if node[1] == "SIN"], "PML"),
        "BCA": pack_nodes([node[0] for node in nodes_p_system if node[1] == "BCA"], "PML"),
        "BCS": pack_nodes([node[0] for node in nodes_p_system if node[1] == "bcs"], "PML")
    }
    
    # print(nodes_p)
    # print(nodes_d)
    # print(nodes_p.items())
    # print(nodes_d.items())

    markets = ['MDA', 'MTR'] if mda and mtr else ['MDA'] if mda else ['MTR']

    nodes_p_urls = get_urls_to_request(nodes_p, dates_packed, 'PML', markets)
    nodes_d_urls = get_urls_to_request(nodes_d, dates_packed, 'PND', markets)

    print(nodes_p_urls)
    print(nodes_d_urls)

    # print('\n')

    session = FuturesSession(max_workers=20)
    futures=[session.get(u) for u in urls_list]

    dfs = [] # List of missing info data frames

    for future in as_completed(futures):

        resp = future.result()
        json_data = resp.json()
        
        if json_data["status"] != "OK":
            continue

        dfs.append(json_to_dataframe(json_data))
        print('.')

    df = pd.concat(dfs) # Join downloaded info in one data frame

    


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


if __name__ == "__main__":
    main()