import streamlit as st
import time
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
import plotly.express as px
# from functions import *

def check_nodes(selected_nodes_p, selected_nodes_d):
    if selected_nodes_p == selected_nodes_d:
        st.sidebar.warning('Selecciona un NodoP o NodoP Distribuido')
        st.stop()

def check_markets(mda, mtr):
    if not any([mda, mtr]):
        st.sidebar.warning('Selecciona uno o dos mercados')
        st.stop()

def pack_dates(start_date, end_date, market):
    """Gets days to ask for info and start date, returns appropiate data intervals to assemble APIs url"""
    
    if market == 'MTR' and end_date > date.today()-timedelta(days = 7):
        end_date = date.today()-timedelta(days = 7)

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
        raise ValueError("Node system not found.")

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

def get_urls_to_request(nodes_dict, dates_packed, node_type, market):

    url_frame = {
        'PND':'https://ws01.cenace.gob.mx:8082/SWPEND/SIM/',
        'PML':'https://ws01.cenace.gob.mx:8082/SWPML/SIM/'
        }

    urls_list = []
    # for market in markets:
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

def get_info(urls_list, bar):

    session = FuturesSession(max_workers=20)
    futures=[session.get(u) for u in urls_list]

    dfs = [] # List of missing info data frames

    for i,future in enumerate(as_completed(futures)):
        percentage = i*100//len(urls_list) 
        bar.progress(percentage)

        resp = future.result()
        json_data = resp.json()

        if "status" in json_data.keys():
            if json_data["status"] != "OK":
                print(json_data)
                continue
        else:
            if "Message" in json_data.keys():
                print(json_data)
                continue

        dfs.append(json_to_dataframe(json_data))
        print('.')

    bar.progress(100)

    try:
        df = pd.concat(dfs) # Join downloaded info in one data frame
    except:
        df = None
    
    return df


def json_to_dataframe(json_file):
    """Reads json file, creates a list of nodes DataFrames and concatenates them. After that it cleans/orders the final df and returns it"""
    dfs = []

    for node in json_file['Resultados']:
        dfs.append(pd.DataFrame(node))

    df = pd.concat(dfs) # Join all data frames

    # Clean/order df to same format of existing csv files
    df['Sistema'] = json_file['sistema']
    df['Mercado'] = json_file['proceso']
    df['Fecha'] = df['Valores'].apply(lambda x: x['fecha'])
    df['Hora'] = df['Valores'].apply(lambda x: x['hora'])

    if json_file['nombre'] == 'PEND':
        df['Precio [$/MWh]'] = df['Valores'].apply(lambda x: x['pz']).astype("float")
        df['Componente de Energía [$/MWh]'] = df['Valores'].apply(lambda x: x['pz_ene']).astype("float")
        df['Componente de Pérdidas [$/MWh]'] = df['Valores'].apply(lambda x: x['pz_per']).astype("float")
        df['Componente de Congestión [$/MWh]'] = df['Valores'].apply(lambda x: x['pz_cng']).astype("float")
        df['Nombre del Nodo'] = df['zona_carga'].copy()
        df['Tipo de NodoP'] = "NodoP Distribuido"

    if json_file['nombre'] == 'PML':
        df['Precio [$/MWh]'] = df['Valores'].apply(lambda x: x['pml']).astype("float")
        df['Componente de Energía [$/MWh]'] = df['Valores'].apply(lambda x: x['pml_ene']).astype("float")
        df['Componente de Pérdidas [$/MWh]'] = df['Valores'].apply(lambda x: x['pml_per']).astype("float")
        df['Componente de Congestión [$/MWh]'] = df['Valores'].apply(lambda x: x['pml_cng']).astype("float")
        df['Nombre del Nodo'] = df['clv_nodo'].copy()
        df['Tipo de NodoP'] = "NodoP"

    df = df[['Sistema','Mercado','Fecha','Hora','Nombre del Nodo','Precio [$/MWh]','Componente de Energía [$/MWh]', 'Componente de Pérdidas [$/MWh]','Componente de Congestión [$/MWh]', "Tipo de NodoP"]]
    # print(df)
    return df

def arange_dataframe_for_plot(df):

    df['Hora_g'] = df['Hora'].apply(lambda x: f"0{int(x)-1}" if int(x)-1 < 10 else f"{int(x)-1}")
    df["Fecha_g"] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora_g'] + ':59:59', format="%Y-%m-%d %H:%M:%S")
    df["Nodo-Mercado"] = df["Nombre del Nodo"] + '_' + df['Mercado']
    df.sort_values(by='Fecha_g', axis=0, ascending=True, inplace=True, ignore_index=True)
    return df

def arange_dataframe_for_table(df, component, download = False):

    df_table = df.pivot(index=['Fecha','Hora'], columns='Nodo-Mercado', values=component)
    df_table.columns = df_table.columns.to_series().values
    df_table.reset_index(inplace=True)
    df_table['Hora'] = df_table['Hora'].astype('int')
    df_table.sort_values(by=['Fecha','Hora'], axis=0, ascending=[True,True], inplace=True, ignore_index=True)
    # print(df_table.columns)
    # if not download:
    #     for col in df_table.columns:
    #         if col not in ['Fecha','Hora']:
    #             df_table[col] = df_table[col].astype('int', errors='ignore')

    return df_table

def plot_df(df, component):
    
    fig = px.line(
        data_frame=df, 
        x="Fecha_g", 
        y=component, 
        color='Nodo-Mercado',
        hover_data=['Fecha','Hora', "Nodo-Mercado", component],
        width=900, 
        height=600,
        labels={
            "Fecha_g": "Fecha"
            }
        )
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor = 'rgba(255,255,255,0.6)'
        ),
        hovermode="x"
    )
    fig.update_traces(
        mode="markers+lines",
        hovertemplate=None
        )
    fig.update_xaxes(
        rangeslider_visible=True,
        rangeslider_thickness = 0.09
        )
    fig.update_yaxes(
        fixedrange=False,
        # ticklabelposition="inside top"
    )

    return fig

def main():

    st.set_page_config(page_title="Precios del MEM", layout="wide", initial_sidebar_state="expanded")

    # List of nodes for multiselects
    df = pd.read_csv('nodos2.csv')
    nodes_p = df['CLAVE'].tolist()
    nodes_d = [zona for zona in df['ZONA DE CARGA'].unique().tolist() if zona != "No Aplica"]

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
        print('Press the button')
        st.stop()

    print("Checking data...")
    # One or more nodes and markets must be selected to continue...
    check_nodes(selected_nodes_p, selected_nodes_d)
    check_markets(mda, mtr)

    print("Getting info ready...")
    dates_packed_mda = pack_dates(start_date, end_date, 'MDA')
    dates_packed_mtr = pack_dates(start_date, end_date, 'MTR')
    nodes_d_system = list(map(get_node_system, selected_nodes_d))
    nodes_p_system = list(map(get_node_system, selected_nodes_p))
    
    nodes_d = {
        "SIN": pack_nodes([node[0] for node in nodes_d_system if node[1] == "SIN"], "PND"),
        "BCA": pack_nodes([node[0] for node in nodes_d_system if node[1] == "BCA"], "PND"),
        "BCS": pack_nodes([node[0] for node in nodes_d_system if node[1] == "BCS"], "PND")
    }
    nodes_p = {
        "SIN": pack_nodes([node[0] for node in nodes_p_system if node[1] == "SIN"], "PML"),
        "BCA": pack_nodes([node[0] for node in nodes_p_system if node[1] == "BCA"], "PML"),
        "BCS": pack_nodes([node[0] for node in nodes_p_system if node[1] == "BCS"], "PML")
    }
    # print(nodes_d, nodes_p)
    nodes_p_urls = []
    nodes_d_urls = []

    if mda:
        nodes_p_urls += get_urls_to_request(nodes_p, dates_packed_mda, 'PML', 'MDA')
        nodes_d_urls += get_urls_to_request(nodes_d, dates_packed_mda, 'PND', 'MDA')
    
    if mtr:        
        nodes_p_urls += get_urls_to_request(nodes_p, dates_packed_mtr, 'PML', 'MTR')
        nodes_d_urls += get_urls_to_request(nodes_d, dates_packed_mtr, 'PND', 'MTR')

    # print(nodes_d_urls)
    # print(nodes_p_urls)

    if not len(nodes_d_urls + nodes_p_urls):
        st.sidebar.warning('No hay valores disponibles para las fechas seleccionadas.')
        st.stop()

    print("Requesting...")

    bar = st.sidebar.progress(0)   
    df_requested = get_info(nodes_d_urls + nodes_p_urls, bar) if any([nodes_d_urls,nodes_p_urls])  else None
    time.sleep(0.2)
    bar.empty()  

    components = ['Precio [$/MWh]','Componente de Energía [$/MWh]', 'Componente de Pérdidas [$/MWh]','Componente de Congestión [$/MWh]']
    component = st.selectbox(label='etiqueta', options=components, index=0, key=None, help=None)
    # component = componentes[2]

    print('Plotting...')
    df_plot = arange_dataframe_for_plot(df_requested)
    st.plotly_chart(plot_df(df_plot, component), use_container_width=True)

    print("Making table...")
    df_table = arange_dataframe_for_table(df_requested, component)
    st.dataframe(df_table.style.format({col:"{:,}" for col in df_table.columns if col not in ['Fecha','Hora']}))
    
    print('Done')

if __name__ == "__main__":
    main()