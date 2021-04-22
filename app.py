import streamlit as st
import time
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
import plotly.express as px
import base64
# from functions import *
# 

def check_dates(dates):
    if len(dates)!=2:
        st.stop()

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

# def bar_hash_func(bar):
#     return bar.progress

@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)#(hash_funcs={streamlit.delta_generator.DeltaGenerator: bar_hash_func})
def get_info(urls_list):

    bar = st.sidebar.progress(0)
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
    time.sleep(0.5)
    bar.empty()

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
        df['Precio Total [$/MWh]'] = df['Valores'].apply(lambda x: x['pz']).astype("float")
        df['Componente de Energía [$/MWh]'] = df['Valores'].apply(lambda x: x['pz_ene']).astype("float")
        df['Componente de Pérdidas [$/MWh]'] = df['Valores'].apply(lambda x: x['pz_per']).astype("float")
        df['Componente de Congestión [$/MWh]'] = df['Valores'].apply(lambda x: x['pz_cng']).astype("float")
        df['Nombre del Nodo'] = df['zona_carga'].copy()

    if json_file['nombre'] == 'PML':
        df['Precio Total [$/MWh]'] = df['Valores'].apply(lambda x: x['pml']).astype("float")
        df['Componente de Energía [$/MWh]'] = df['Valores'].apply(lambda x: x['pml_ene']).astype("float")
        df['Componente de Pérdidas [$/MWh]'] = df['Valores'].apply(lambda x: x['pml_per']).astype("float")
        df['Componente de Congestión [$/MWh]'] = df['Valores'].apply(lambda x: x['pml_cng']).astype("float")
        df['Nombre del Nodo'] = df['clv_nodo'].copy()

    df = df[['Sistema','Mercado','Fecha','Hora','Nombre del Nodo','Precio Total [$/MWh]','Componente de Energía [$/MWh]', 'Componente de Pérdidas [$/MWh]','Componente de Congestión [$/MWh]']]
    # print(df)
    return df

def get_agg_options(avg_option):
    # avg_options = ["Horario", "Diario", "Semanal"]
    if avg_option == "Horario":
        return ["Histórico","Día de la semana", "Mes"]
    if avg_option == "Diario":
        return ["Histórico"]
    if avg_option == "Semanal":
        return ["Histórico"]


def arange_dataframe_for_plot(df, avg_option, agg_option, group):
    
    def use_avg_option(df, avg_option, agg_option):

        if avg_option == "Horario":
            if agg_option == "Histórico":
                df['Hora_g'] = df['Hora'].apply(lambda x: f"0{int(x)-1}" if int(x)-1 < 10 else f"{int(x)-1}")
                df["Fecha_g"] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora_g'] + ':59:59', format="%Y-%m-%d %H:%M:%S")
                df.sort_values(by='Fecha_g', axis=0, ascending=True, inplace=True, ignore_index=True)
                return df
            
            elif agg_option == "Día de la semana":
                df['Hora_g'] = df['Hora'].apply(lambda x: f"0{int(x)-1}" if int(x)-1 < 10 else f"{int(x)-1}")
                df["Fecha_g"] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora_g'] + ':59:59', format="%Y-%m-%d %H:%M:%S")
                df['Día de la semana'] = df['Fecha_g'].apply(lambda x: str(x.isocalendar()[2]))
                df['Hora'] = df['Hora'].apply(lambda x: x if int(x)>9 else f'0{x}')
                df['Día-Hora'] = df['Día de la semana'] + "_" + df['Hora']
                # print(df.T)
                df = df.groupby(['Sistema','Mercado','Nombre del Nodo','Día-Hora']).mean()
                df.reset_index(inplace=True)
                # print(df.T)
                df.sort_values(by='Día-Hora', axis=0, ascending=True, inplace=True, ignore_index=True)
                return df

            elif agg_option == "Mes":
                pass

        elif avg_option == "Diario":
            df = df.groupby(['Sistema','Mercado','Nombre del Nodo','Fecha']).mean()
            df.reset_index(inplace=True)
            df["Fecha_g"] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d")
            df.sort_values(by='Fecha_g', axis=0, ascending=True, inplace=True, ignore_index=True)
            return df

        elif avg_option == "Semanal":
            df["Fecha"] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d")
            df['Año-Semana'] = df['Fecha'].apply(lambda x: ".".join([str(x.isocalendar()[0]), str(x.isocalendar()[1]) if x.isocalendar()[1] > 9 else f"0{str(x.isocalendar()[1])}" ]))
            # df['Año'] = df['Fecha'].apply(lambda x: x.isocalendar()[0])
            # st.dataframe(df[['Año-Semana','Fecha']])#.sort_values(by=['Semana','Fecha'], axis=0, ascending=True))
            df = df.groupby(['Sistema','Mercado','Nombre del Nodo','Año-Semana']).mean()
            df.reset_index(inplace=True)
            df.sort_values(by=['Año-Semana'], axis=0, ascending=True, inplace=True, ignore_index=True)
            # df["Fecha_g"] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d")
            return df

    df = df[df['Hora'] != '25']
    df = use_avg_option(df, avg_option, agg_option)
    # print(df)
    
    df["Nodo-Mercado"] = df['Mercado'] + '_' + df["Nombre del Nodo"] 
    
    return df

def arange_dataframe_for_table(df, component, download = False):

    print(df)
    df["Nodo-Mercado"] = df['Mercado'] + '_' + df["Nombre del Nodo"] 
    df_table = df.pivot(index=['Fecha','Hora'], columns='Nodo-Mercado', values=component)
    df_table.columns = df_table.columns.to_series().values
    df_table.reset_index(inplace=True)
    df_table['Hora'] = df_table['Hora'].astype('int')
    df_table.sort_values(by=['Fecha','Hora'], axis=0, ascending=[True,True], inplace=True, ignore_index=True)

    return df_table

def plot_df(df, component, avg_option, agg_option):
    
    if avg_option == 'Semanal':
        fig = px.line(
            data_frame=df, 
            x="Año-Semana", 
            y=component, 
            color='Nodo-Mercado',
            hover_data=['Año-Semana', "Nodo-Mercado", component],
            width=900, 
            height=600,
            labels={
                "Año-Semana": ""
                }
            )
    
    elif avg_option == "Horario" and agg_option == "Día de la semana":
        fig = px.line(
            data_frame=df, 
            x="Día-Hora", 
            y=component, 
            color='Nodo-Mercado',
            hover_data=['Día-Hora', "Nodo-Mercado", component],
            width=900, 
            height=600,
            labels={
                "Día-Hora": ""
                }
            )

    else:
        fig = px.line(
            data_frame=df, 
            x="Fecha_g", 
            y=component, 
            color='Nodo-Mercado',
            hover_data=['Fecha', "Nodo-Mercado", component],
            width=900, 
            height=600,
            labels={
                "Fecha_g": ""
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
        fixedrange=False
    )

    return fig

def get_table_download_link(df,dates):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    file_name = f"energy_prices_{dates[0].strftime('%Y_%m_%d')}_{dates[1].strftime('%Y_%m_%d')}.csv"
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}" download="{file_name}">Descargar tabla</a>'
    return href

def main():

    st.set_page_config(page_title="Precios del MEM", layout="wide", initial_sidebar_state="expanded")
    
    components = ['Precio Total [$/MWh]','Componente de Energía [$/MWh]', 'Componente de Pérdidas [$/MWh]','Componente de Congestión [$/MWh]']

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

    # Check selected options
    print("Checking data...")
    
    check_dates(dates)
    check_nodes(selected_nodes_p, selected_nodes_d)
    check_markets(mda, mtr)
    start_date, end_date = dates

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

    if not len(nodes_d_urls + nodes_p_urls):
        st.sidebar.warning('No hay valores disponibles para las fechas seleccionadas.')
        st.stop()

    print("Requesting...")

   
    df_requested = get_info(nodes_d_urls + nodes_p_urls) if any([nodes_d_urls,nodes_p_urls])  else None
    # print(df_requested)

    col1, col2, col3, col4 = st.beta_columns([2,1,1,1])
    component = col1.selectbox(label = "Componente de Precio",options=components, index=0, key=None, help=None)
    
    avg_option = col2.selectbox("Promedio", ["Horario", "Diario", "Semanal"], 0)
    agg_option = col3.selectbox("Agrupar por", get_agg_options(avg_option), 0)
    col4.subheader('')
    group = col4.checkbox('Comparar Periodos', value=False)    

    print('Plotting...')
    df_plot = arange_dataframe_for_plot(df_requested.copy(), avg_option, agg_option, group)
    st.plotly_chart(plot_df(df_plot, component, avg_option, agg_option), use_container_width=True)#use_column_width=True

    print("Making table...")
    df_table = arange_dataframe_for_table(df_requested.copy(), component)
    st.markdown(get_table_download_link(df_table,dates), unsafe_allow_html=True)
    st.dataframe(df_table.style.format({col:"{:,}" for col in df_table.columns if col not in ['Fecha','Hora']}))
    
    print('Done')

if __name__ == "__main__":
    main()