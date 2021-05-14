import streamlit as st
from streamlit import caching
import pandas as pd
from datetime import datetime, date, timedelta
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
import plotly.express as px
import base64
import unidecode


week_days = {
    1:"Lunes",
    2:"Martes",
    3:"Miércoles",
    4:"Jueves",
    5:"Viernes",
    6:"Sábado",
    7:"Domingo",
    }

months = {
    1:"Enero",
    2:"Febrero",
    3:"Marzo",
    4:"Abril",
    5:"Mayo",
    6:"Junio",
    7:"Julio",
    8:"Agosto",
    9:"Sept",
    10:"Octubre",
    11:"Noviembre",
    12:"Diciembre"
    }

reservas = {
    'Reserva de regulación secundaria':"Reserva de Regulación Secundaria [$/MWh]",
    'Reserva rodante de 10 minutos':"Reserva Rodante de 10 Minutos [$/MWh]",
    'Reserva no rodante de 10 minutos':"Reserva No Rodante de 10 Minutos [$/MWh]",
    'Reserva rodante suplementaria':"Reserva Rodante Suplementaria [$/MWh]",
    'Reserva no rodante suplementarias':"Reserva No Rodante Suplementaria [$/MWh]"    
}


def welcome_text():
    return """
        #### ¡Hola!

        Este proyecto está hecho para facilitar el análisis de los **precios de energía eléctrica en México**.
        
        Básicamente debes: 
        
        1. **Elegir** las opciones deseadas de la **barra lateral**.
        2. **Esperar** a que la información se descargue y la gráfica aparezca (**Si no la ves, desplázate hacia abajo**).
        3. **Seleccionar** el tipo de **visualización** deseada.
        ####

        A las gráficas se les puede hacer zoom, ocultar trazos, descargar, etc. Revisa todo lo que puedes hacer con ellas [aquí](https://plotly.com/chart-studio-help/zoom-pan-hover-controls/).

        Tengo pensado agregar varias cosas más, visualizaciones, información extra y lo que se me vaya ocurriendo. 

        Si tienes **alguna duda o sugerencia** no dudes en decirme por **[Linkedin](https://www.linkedin.com/in/angelcarballo/)** o **[Github](https://github.com/AngelCarballoCremades/Energy-Price-Dashboard)**.
        
        Espero que este proyecto te sea útil.

        ### Ángel :v:



        """

def instructions_text():
    return """
        
        
        ### Barra lateral

        Selecciona:
        * **Precios de Energia** 
            * **NodosP** y **NodosP Distribuidos** 
                * Por lo menos uno debe ser seleccionado (de cualquier tipo).
            * **Fechas** - Rango de fechas de información a solicitar. 
                * Disponible desde febrero 2017 a mañana. Ten en cuenta que no todos los NodosP han existido en este rango.
                * MTR disponible hasta hoy -7 días.
                * MDA hasta hoy +1 día.
        * **Servicios Conexos**  
            * **Zonas de Reserva**
                * Por lo menos una debe ser seleccionada.
            * **Fechas** - Rango de fechas de información a solicitar. 
                * Disponible desde mayo 2018 a mañana.
                * MTR disponible hasta hoy -7 días.
                * MDA hasta hoy +1 día.
        * **MDA** y **MTR**
            * Por lo menos uno debe ser seleccionado.

        Cuando se ha hecho una selección válida, aparecerá una barra de progreso mientras la información la información es descargada.
        El tiempo que tarde dependerá de la información solicitada.

        ### Área Central

        Opciones a seleccionar:
        * **Componente de Precio** o **Tipo de Reserva** - Componente del PML, PND o tipo de reserva a graficar $/MWh (MXN).
        * **Promedio**
            * **Horario** - Graficar promedio por hora (promedio simple).
            * **Diario** - Graficar promedio por día (promedio simple).
            * **Semanal** - Graficar promedio por semana (promedio simple).
        * **Agrupar por**
            * **Histórico** - Grafica la información sin modificación extra.
            * **Día de la semana** - Grafica el promedio de cada hora para cada día de la semana. Utiliza la información solicitada en la barra lateral.
            * **Mes** - Grafica el promedio de cada hora para cada mes. Utiliza la información solicitada en la barra lateral. 
        * **Año vs Año** - Crea diferentes trazos para cada año dentro de la información solicitada en la barra lateral.

        Cada vez que se hace una selección, una gráfica será creada o modificada.
        
        * **Resumen de datos horarios:** - Tabla mostrando valores estadísticos de los valores horarios.
        * **Primeras 1000 filas de datos:** - Tabla mostrando 100 primeras filas de la información horaria.
        
        Puedes descargar toda la información a un cvs con el botón **Descargar datos**.


        """
@st.cache()
def get_nodes_list():
    "Gets list of NodosP and NodosP Distribuidos in file nodos.csv"
    df = pd.read_csv('nodos.csv')
    nodes_p = df['CLAVE'].tolist()
    nodes_d = [zona for zona in df['ZONA DE CARGA'].unique().tolist() if zona != "No Aplica"]

    nodes_p.sort()
    nodes_d.sort()

    return nodes_p, nodes_d

def check_dates(dates):
    """Checks if dates are selected"""
    if len(dates)!=2:
        st.stop()

def check_nodes(selected_nodes_p, selected_nodes_d):
    """Checks if there is at least a node selected"""
    if selected_nodes_p == selected_nodes_d:
        st.sidebar.warning('Selecciona un NodoP o NodoP Distribuido')
        st.stop()

def check_zones(selected_zones):
    """Checks if there is at least a Zona de Reserva selected"""
    if len(selected_zones) == 0:
        st.sidebar.warning('Selecciona una Zona de Reserva')
        st.stop()

def check_markets(mda, mtr):
    """Checks if there is at least a market selected"""
    if not any([mda, mtr]):
        st.sidebar.warning('Selecciona uno o dos mercados')
        st.stop()

def check_df_requested(df_requested):
    if isinstance(df_requested, bool):
        caching.clear_cache()
        st.sidebar.warning('Error extrayendo datos del CENACE. Inténtalo de nuevo o cambia las fechas solicitadas.')
        st.stop()

def pack_dates(start_date, end_date, market):
    """Gets days to ask for info and start date, returns appropiate data intervals to assemble APIs url"""
    
    # To avoid CENACE error in MTR API last date of MTR API call is limited
    if market == 'MTR' and end_date > date.today()-timedelta(days = 7):
        end_date = date.today()-timedelta(days = 7)

    dates = []
    delta = end_date-start_date
    days = delta.days

    # Pack dates every 7 days.
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
    """This functions pairs a node or zone to it's system. Returns a tuple (Node, System)"""

    df = pd.read_csv('nodos.csv')

    if df[df["CLAVE"] == node].shape[0]:
        system = df[df["CLAVE"] == node]["SISTEMA"].to_list()[0]

    elif df[df["ZONA DE CARGA"] == node].shape[0]:
        system = df[df["ZONA DE CARGA"] == node]["SISTEMA"].to_list()[0]
    
    else:
        raise ValueError("Node system not found.")

    return (node, system)

def pack_nodes(nodes, node_type):
    """Returns a list of lists with nodes, this is done because depending on node type we have a maximum number of nodes per request (PND is 10 max and PML is 20 max)"""
    
    nodes = [node.replace(' ','-') for node in nodes] # Remove spaces from strings

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

def get_nodes_urls(start_date, end_date, selected_nodes_d, selected_nodes_p, mda, mtr):
    """Returns nodes urls to request"""

    dates_packed_mda = pack_dates(start_date, end_date, 'MDA') # Pack dates for API calls
    dates_packed_mtr = pack_dates(start_date, end_date, 'MTR') # Pack dates for API calls
    
    nodes_d_system = list(map(get_node_system, selected_nodes_d)) # Get selected-nodes system
    nodes_p_system = list(map(get_node_system, selected_nodes_p)) # Get selected-nodes system
    
    # Pack nodes depending on system
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
    
    nodes_p_urls = []
    nodes_d_urls = []

    # Get urls from packed nodes and dates, separated by market
    if mda:
        nodes_p_urls += get_urls_to_request(nodes_p, dates_packed_mda, 'PML', 'MDA')
        nodes_d_urls += get_urls_to_request(nodes_d, dates_packed_mda, 'PND', 'MDA')
    
    if mtr:        
        nodes_p_urls += get_urls_to_request(nodes_p, dates_packed_mtr, 'PML', 'MTR')
        nodes_d_urls += get_urls_to_request(nodes_d, dates_packed_mtr, 'PND', 'MTR')

    # If there are no urls to call
    if not len(nodes_d_urls + nodes_p_urls):
        st.sidebar.warning('No hay valores disponibles para las fechas seleccionadas.')
        st.stop()

    return nodes_d_urls + nodes_p_urls

def get_zones_urls(start_date, end_date, selected_zones, mda, mtr):
    """Returns zones urls to request"""


    dates_packed_mda = pack_dates(start_date, end_date, 'MDA') # Pack dates for API calls
    dates_packed_mtr = pack_dates(start_date, end_date, 'MTR') # Pack dates for API calls

    zones = {zone[1:4]:[[zone[1:4]]] for zone in selected_zones} # Pack zoness for function 'get_urls_to_request'

    zones_urls = []

    # Get urls from packed zones and dates, separated by market
    if mda:
        zones_urls += get_urls_to_request(zones, dates_packed_mda, 'PSC', 'MDA')
    
    if mtr:        
        zones_urls += get_urls_to_request(zones, dates_packed_mtr, 'PSC', 'MTR')

    # If there are no urls to call
    if not len(zones_urls):
        st.sidebar.warning('No hay valores disponibles para las fechas seleccionadas.')
        st.stop()

    return zones_urls, zones

def get_urls_to_request(nodes_dict, dates_packed, node_type, market):
    """Assemble API calls urls for PMLs, PNDs and PSC"""

    url_frame = {
        'PND':'https://ws01.cenace.gob.mx:8082/SWPEND/SIM/',
        'PML':'https://ws01.cenace.gob.mx:8082/SWPML/SIM/',
        'PSC':'https://ws01.cenace.gob.mx:8082/SWPSC/SIM/'
        }

    urls_list = []
    
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


@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)#(hash_funcs={streamlit.delta_generator.DeltaGenerator: bar_hash_func})
def get_info(urls_list):
    """Makes API calls for every url provided and returns a DataFrame with clean information."""

    # Create loading bar in sidebar
    bar_string = st.sidebar.text('Cargando...')
    bar = st.sidebar.progress(0)

    # Initialize futures session
    session = FuturesSession(max_workers=20)
    futures=[session.get(u) for u in urls_list]

    dfs = [] # List of info data frames

    for i,future in enumerate(as_completed(futures)):

        percentage = i*100//len(urls_list) # Update loading bar progress
        bar.progress(percentage)

        resp = future.result() # Url response
        json_data = resp.json() # Get response json

        # checks for response status, expected 'OK' status
        if "status" in json_data.keys():
            if json_data["status"] != "OK": # If response != 'OK' don't append response. Usualy happens when there is no data available for nodes/date selected.
                print(json_data)
                continue
        else:
            # When there is an error on CENACE's side (Usually in MTR API) there is a 'message' key in json response. If it's true entire process is cancelled (False is returned).
            if "Message" in json_data.keys():
                print(json_data)
                print(resp.request.url)
                return False

        dfs.append(json_to_dataframe(json_data)) # Convert json to DataFrame and append to DataFrames'list
        # print('.')

    bar.progress(100) # Process is complete
        
    try:
        df = pd.concat(dfs) # Join downloaded info in one DataFrame
    except:
        df = None
    
    df.reset_index(drop=True, inplace=True)
    
    # Eliminate progress bar
    bar_string.empty()
    bar.empty()

    return df


def json_to_dataframe(json_file):
    """Reads json file, creates a list of nodes DataFrames and concatenates them. After that, it cleans/orders the final df and returns it"""
    
    dfs = []

    # Separate every node response and join in one DataFrame
    for node in json_file['Resultados']:
        dfs.append(pd.DataFrame(node))

    df = pd.concat(dfs) # Join all DataFrame

    # Order all data into one same structure.
    df['Sistema'] = json_file['sistema']
    df['Mercado'] = json_file['proceso']
    df['Fecha'] = df['Valores'].apply(lambda x: x['fecha'])
    df['Hora'] = df['Valores'].apply(lambda x: x['hora'])

    if json_file['nombre'] == 'PSC':
        df['Nombre del Nodo'] = df['clv_zona_reserva']
        df['Reserva'] = df['Valores'].apply(lambda x: x['tipo_res'])
        df['Precio'] = df['Valores'].apply(lambda x: x['pres']).astype("float")
        df = df[['Sistema','Mercado','Nombre del Nodo','Fecha','Hora','Reserva','Precio']]
        df = df.set_index(['Sistema','Mercado','Nombre del Nodo','Fecha','Hora','Reserva']).unstack().reset_index()
        df.columns = [col[0] if col[1]=='' else reservas[col[1]] for col in df.columns]
        
        return df
    
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

    return df


def check_for_23_or_25_hours(df_requested):
    """Check for 25 or 23 hour days, works still missing in this function"""
    df = df_requested[df_requested['Hora'] != '25']
    # index_25 = df_requested[df_requested['Hora'] == '25'].index.to_list()
    # print(index_25)

    return df

def arange_dataframe_for_plot(df, avg_option, agg_option, group):
    """Modifies dataframe to plot desired information, changes output depending on average, aggregation and group option"""
    
    def use_avg_option(df, avg_option, agg_option, group):
        """Modifies dataframe to plot desired avg_option"""

        if agg_option == "Día de la semana":
            df['Hora_g'] = df['Hora'].apply(lambda x: f"0{int(x)-1}" if int(x)-1 < 10 else f"{int(x)-1}")
            df["Fecha_g"] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora_g'] + ':59:59', format="%Y-%m-%d %H:%M:%S")
            df['Día de la semana'] = df['Fecha_g'].apply(lambda x: str(x.isocalendar()[2]))

            if group:
                df["Año"] = df['Fecha_g'].dt.year
                df["Nodo-Mercado"] = df['Año'].apply(str) + "_" + df['Mercado'] + '_' + df["Nombre del Nodo"]
                df = df.groupby(['Nodo-Mercado','Día de la semana','Hora_g']).mean()
            
            else:
                df["Nodo-Mercado"] = df['Mercado'] + '_' + df["Nombre del Nodo"]
                df = df.groupby(['Nodo-Mercado','Día de la semana','Hora_g']).mean()                   

            df.reset_index(inplace=True)
            df['Segundo'] = df['Hora_g'].apply(lambda x: str(int(x)+1) if int(x)>8 else f"0{int(x)+1}")
            df['Día-Hora'] = pd.to_datetime("2021-03-0" + df['Día de la semana'] + " " + df['Hora_g'] + ":59:" + df['Segundo'], format="%Y-%m-%d %H:%M:%S")
            df.sort_values(by='Día-Hora', axis=0, ascending=True, inplace=True, ignore_index=True)
            return df

        elif agg_option == "Mes":
            df['Hora_g'] = df['Hora'].apply(lambda x: f"0{int(x)-1}" if int(x)-1 < 10 else f"{int(x)-1}")
            df["Fecha_g"] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora_g'] + ':59:59', format="%Y-%m-%d %H:%M:%S")
            df['Mes'] = df['Fecha_g'].dt.month
            
            if group:
                df["Año"] = df['Fecha_g'].dt.year
                df["Nodo-Mercado"] = df['Año'].apply(str) + "_" + df['Mercado'] + '_' + df["Nombre del Nodo"]
                
            else:
                df["Nodo-Mercado"] = df['Mercado'] + '_' + df["Nombre del Nodo"]
                
            df = df.groupby(['Nodo-Mercado','Mes','Hora_g']).mean()
            df.reset_index(inplace=True)
            df['Mes'] = df['Mes'].apply(lambda x: str(int(x)) if int(x)>9 else f"0{int(x)}")
            df['Segundo'] = df['Hora_g'].apply(lambda x: str(int(x)+1) if int(x)>8 else f"0{int(x)+1}")
            df['Mes-Hora'] = pd.to_datetime("2021-03-" + df['Mes'] + " " + df['Hora_g'] + ":59:" + df['Segundo'], format="%Y-%m-%d %H:%M:%S")
            df.sort_values(by='Mes-Hora', axis=0, ascending=True, inplace=True, ignore_index=True)
            return df
        
        elif avg_option == "Horario":
            df['Hora_g'] = df['Hora'].apply(lambda x: f"0{int(x)-1}" if int(x)-1 < 10 else f"{int(x)-1}")
            df["Fecha_g"] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora_g'] + ':59:59', format="%Y-%m-%d %H:%M:%S")
            df["Año"] = df['Fecha_g'].dt.year
            df.sort_values(by='Fecha_g', axis=0, ascending=True, inplace=True, ignore_index=True)
            return df
        
        elif avg_option == "Diario":
            df = df.groupby(['Sistema','Mercado','Nombre del Nodo','Fecha']).mean()
            df.reset_index(inplace=True)
            df["Fecha_g"] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d")
            df.sort_values(by='Fecha_g', axis=0, ascending=True, inplace=True, ignore_index=True)
            df["Año"] = df['Fecha_g'].dt.year
            return df

        elif avg_option == "Semanal":
            df["Fecha"] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d")
            df['Año-Semana'] = df['Fecha'].apply(lambda x: ".".join([str(x.isocalendar()[0]), str(x.isocalendar()[1]) if x.isocalendar()[1] > 9 else f"0{str(x.isocalendar()[1])}" ]))
            df = df.groupby(['Sistema','Mercado','Nombre del Nodo','Año-Semana']).mean()
            df.reset_index(inplace=True)
            df.sort_values(by=['Año-Semana'], axis=0, ascending=True, inplace=True, ignore_index=True)
            return df

    def group_by_year(df,group, avg_option, agg_option):
        """Modifies dataframe to plot yaer vs year"""
        if agg_option in ["Día de la semana","Mes"]:
            return df

        elif not group:
            df["Nodo-Mercado"] = df['Mercado'] + '_' + df["Nombre del Nodo"]
            return df
            
        else:
            if avg_option == "Horario":
                # df = df[(df['Fecha_g'] > '2013-01-01') & (df['date'] < '2013-02-01')]
                df['Fecha_g'] = df['Fecha_g'].apply(lambda x: x.replace(year = 2020))
                # df["Fecha_g"] = df['Fecha_g'].dt.strftime('%m-%d %H:%M:%S')
                df["Nodo-Mercado"] = df["Año"].apply(str) + "_" + df['Mercado'] + "_" + df["Nombre del Nodo"] 
                return df
                
            elif avg_option == "Diario":
                df['Fecha_g'] = df['Fecha_g'].apply(lambda x: x.replace(year = 2020))
                # df["Fecha_g"] = df['Fecha_g'].dt.strftime('%m-%d %H:%M:%S')
                df["Nodo-Mercado"] = df["Año"].apply(str) + "_" + df['Mercado'] + "_" + df["Nombre del Nodo"] 
                return df

            elif avg_option == "Semanal":
                df["Año"] = df['Año-Semana'].apply(lambda x: x[:4])
                df["Semana"] = df['Año-Semana'].apply(lambda x: x[-2:])
                df.sort_values(by=['Semana'], axis=0, ascending=True, inplace=True, ignore_index=True)
                df["Nodo-Mercado"] = df["Año"] + "_" + df['Mercado'] + "_" + df["Nombre del Nodo"]
                return df
        

    # print(df)
    df = use_avg_option(df, avg_option, agg_option, group)
    # print(df)
    df = group_by_year(df, group, avg_option, agg_option)
    # print(df)

    return df

st.cache()
def arange_dataframe_for_table(df, component, download = False):
    """Modifies original df to show in table."""
    
    df["Nodo-Mercado"] = df['Mercado'] + '_' + df["Nombre del Nodo"] 
    df_table = df.pivot(index=['Fecha','Hora'], columns='Nodo-Mercado', values=component)
    df_table.columns = df_table.columns.to_series().values
    df_table.reset_index(inplace=True)
    df_table['Hora'] = df_table['Hora'].astype('int')
    df_table.sort_values(by=['Fecha','Hora'], axis=0, ascending=[True,True], inplace=True, ignore_index=True)

    return df_table

def arange_dataframe_for_info_table(df, component, group):
    """Obtains statistical measurements from original dataframe."""

    df["Fecha_g"] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d")
    df['Hora'] = df['Hora'].astype('int')
    df["Año"] = df['Fecha_g'].dt.year

    if group:
        df["Nodo-Mercado"] = df["Año"].apply(str) + "_" + df['Mercado'] + "_" + df["Nombre del Nodo"] 
    
    else:
        df["Nodo-Mercado"] = df['Mercado'] + "_" + df["Nombre del Nodo"]

    df = df.pivot(index=['Fecha','Hora'], columns='Nodo-Mercado', values=component)

    df = df.describe().T[['min','max','mean','std']]

    df.reset_index(inplace=True)
    df.columns = ['','Mínimo','Máximo','Promedio','Desviación Est.']

    if group:
        df['nodo'] = df[''].apply(lambda x: x[9:])
        df['mercado'] = df[''].apply(lambda x: x[5:8])
        df['año'] = df[''].apply(lambda x: x[:4])
        df.sort_values(by=['nodo','mercado','año'], axis=0, ascending=True, inplace=True, ignore_index=True)

    else:
        df['nodo'] = df[''].apply(lambda x: x[4:])
        df['mercado'] = df[''].apply(lambda x: x[:3])

        df.sort_values(by=['nodo','mercado'], axis=0, ascending=True, inplace=True, ignore_index=True)

    df = df.round(2)
    df = df[['','Mínimo','Máximo','Promedio','Desviación Est.']]

    return df



def plot_df(df, component, avg_option, agg_option, group):
    """Generates plot depending on selected options"""

    if agg_option == "Día de la semana":
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
        fig.update_layout(
            xaxis_tickformat = '%a (%S)')
        
        # Add vertical lines and day-of-week names
        for i in range(1,7): 
            fig.add_vline(x=datetime(year=2021, month=3, day=i+1, hour=0, minute=30), line_width=1)
        for i in range(1,8):
            fig.add_vrect(x0=f"2021-03-{i+1} 00:30", x1=f"2021-03-{i+1} 00:30", annotation_text=week_days[i], annotation_position="bottom right", fillcolor="green", opacity=0, line_width=0)

    elif agg_option == "Mes":
        fig = px.line(
            data_frame=df, 
            x="Mes-Hora", 
            y=component, 
            color='Nodo-Mercado',
            hover_data=['Mes-Hora', "Nodo-Mercado", component],
            width=900, 
            height=600,
            labels={
                "Mes-Hora": ""
                }
            )
        fig.update_layout(
            xaxis_tickformat = '%d (%S)')

        # Add vertical lines and month names
        for i in range(1,12): 
            fig.add_vline(x=datetime(year=2021, month=3, day=i+1, hour=0, minute=30), line_width=1)
        for i in range(1,13):
            fig.add_vrect(x0=f"2021-03-{i+1} 00:30", x1=f"2021-03-{i+1} 00:30", annotation_text=months[i], annotation_position="bottom right", fillcolor="green", opacity=0, line_width=0)
            # print(i, months[i], f"2021-03-{i} 00:30 2021-03-{i+1} 00:30")

    
    elif avg_option == 'Semanal':
        if group:
            fig = px.line(
                data_frame=df, 
                x="Semana", 
                y=component, 
                color='Nodo-Mercado',
                hover_data=['Año-Semana', "Nodo-Mercado", component],
                width=900, 
                height=600,
                labels={
                    "Semana": ""
                    }
                )
        else:
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

    elif group:
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
            xaxis_tickformat = '%b-%d')

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

    # Position legend and remove it's title
    fig.update_layout(
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor = 'rgba(255,255,255,0.6)',
            title_text=''
        ),
        hovermode="x"
    )
    fig.update_traces(
        mode="lines",#"markers+lines",
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

@st.cache()
def get_table_download_link(df,dates, component, info, markets):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    # Extra info to show in file name
    if isinstance(info, int):
        info = f"{info}_nodos"
    else:
        info = ("_").join(info)
    
    # Selected markets to show in file name
    markets_info = []
    if markets[0]:
        markets_info.append("MDA")
    if markets[1]:
        markets_info.append("MTR")

    file_name_header = unidecode.unidecode(component[:-8]).replace(' ',"_") # Remove special characters ó, í, á, etc from file name
    file_name = f"{file_name_header}_{info}_{('_').join(markets_info)}_{dates[0].strftime('%Y_%m_%d')}_{dates[1].strftime('%Y_%m_%d')}.csv"
    
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{file_name}">Descargar datos</a>'
    return href

def main():

    # Set page title, icon, layout wide (more used space in central area) and sidebar initial state
    st.set_page_config(page_title="Energía México", page_icon='logo.png', layout="wide", initial_sidebar_state="expanded")
    
    # Central area header
    col1, col2, = st.beta_columns([1,9])
    
    col1.image("logo.png")
    col2.write("# Energía México")
    col2.markdown("Un proyecto de [Ángel Carballo](https://www.linkedin.com/in/angelcarballo/)")

    # Welcome message
    welcome = st.beta_expander(label="Bienvenida", expanded=True)
    with welcome:
        st.write(welcome_text())
        st.write("")
    
    # Instructions message
    instructions = st.beta_expander(label="Instrucciones", expanded=False)
    with instructions:
        st.write(instructions_text())


    st.write("###") # Vertical space

    # Type of info to analyze
    selected_data = st.sidebar.radio(label='Selecciona la opción deseada:',options=['Precios de Energía','Servicios Conexos'], index=0, key=None)
    st.sidebar.write("#")
    st.sidebar.write("#")

    # Precios de Energía Selected
    if selected_data == 'Precios de Energía':

        # List of nodes for multiselects
        nodes_p, nodes_d = get_nodes_list()

        # Dates for date_input creation and delimitation
        max_date = date.today()+timedelta(days=1)
        min_date = datetime(2017, 2, 1)
        today = date.today()
        start_date = today-timedelta(days=30)
        end_date = today-timedelta(days=15)

        # Nodes multiselect
        selected_nodes_p = st.sidebar.multiselect('NodosP',nodes_p)
        selected_nodes_d = st.sidebar.multiselect('NodosP Distribuidos',nodes_d)

        # Date picker
        dates = st.sidebar.date_input('Fechas', max_value=max_date, min_value=min_date, value=(start_date, end_date))

        # MDA and MTR checkboxes
        col1, col2, *_ = st.sidebar.beta_columns(4)
        with col1:
            mda = st.checkbox('MDA', value=False)
        with col2:
            mtr = st.checkbox('MTR', value=False)

        print("Checking data...")

        # Check selected options        
        check_dates(dates)
        check_nodes(selected_nodes_p, selected_nodes_d)
        check_markets(mda, mtr)
        
        print("Getting info ready...")
        start_date, end_date = dates # Unpack date range
        
        # Create urls (API calls) to request using selected options
        nodes_urls = get_nodes_urls(start_date, end_date, selected_nodes_d, selected_nodes_p, mda, mtr)
        
        print("Requesting...")
        df_requested = get_info(nodes_urls) # Request created urls

        # Check for error in request
        check_df_requested(df_requested)
        
        # Deal with 23 and 25 hour days
        df_requested_clean = check_for_23_or_25_hours(df_requested)

        # Plotting options
        components = ['Precio Total [$/MWh]','Componente de Energía [$/MWh]', 'Componente de Pérdidas [$/MWh]','Componente de Congestión [$/MWh]']
        avg_options = ["Horario", "Diario", "Semanal"]
        agg_options = ["Histórico","Día de la semana", "Mes"]
    
        col1, col2, col3, col4 = st.beta_columns([2,1,1,1])
        component = col1.selectbox(label = "Componente de Precio",options=components, index=0, key=None, help="Componente de PML o PND a graficar.")
        avg_option = col2.selectbox("Promedio", avg_options, 0, help = "Grafica el valor promedio por hora, día o semana (promedios simples).")
        agg_option = col3.selectbox("Agrupar por", agg_options, 0)
        col4.write("####") # Vertical space
        group = col4.checkbox('Año vs Año', value=False, help = "Separa información por año.")    

        with st.spinner(text='Generando gráfica y tabla.'):
            
            print('Plotting...')
            # Create DataFrame for plot and create plot
            df_plot = arange_dataframe_for_plot(df_requested_clean.copy(), avg_option, agg_option, group)
            st.plotly_chart(plot_df(df_plot, component, avg_option, agg_option, group), use_container_width=True)#use_column_width=True

            print("Making info table...")
            # Create DataFrame for info table and display info table
            df_info_table = arange_dataframe_for_info_table(df_requested.copy(), component, group)
            st.markdown("""Resumen de datos horarios:""")
            st.dataframe(df_info_table.style.format({col:"{:,}" for col in df_info_table.columns if col not in ['']}).applymap(lambda x: 'color: red' if x < 0 else 'color: black', subset=['Mínimo','Máximo','Promedio','Desviación Est.']))

            st.markdown("") # Vertical space
            st.markdown("")

            print("Making table...")
            # Create dataframe for table and display table
            df_table = arange_dataframe_for_table(df_requested.copy(), component)
            st.markdown("""Primeras 1000 filas de datos:""")
            st.dataframe(df_table.iloc[:1000].style.format({col:"{:,}" for col in df_table.columns if col not in ['Fecha','Hora']}).applymap(lambda x: 'color: red' if x < 0 else 'color: black', subset=[col for col in df_table.columns if col not in ['Fecha','Hora']]))
            
            # Download link
            st.markdown(get_table_download_link(df_table, dates, component, info=len(selected_nodes_d+selected_nodes_p), markets=[mda,mtr]), unsafe_allow_html=True)

    if selected_data == 'Servicios Conexos':
        
        # Dates for date_input creation and delimitation
        max_date = date.today()+timedelta(days=1)
        min_date = datetime(2018, 5, 24)
        today = date.today()
        start_date = today-timedelta(days=30)
        end_date = today-timedelta(days=15)

        # Nodes multiselect
        selected_zones = st.sidebar.multiselect('Zonas de Reserva',['(SIN) Nacional','(BCA) Baja California','(BCS) Baja California Sur'])

        # Date picker
        dates = st.sidebar.date_input('Fechas', max_value=max_date, min_value=min_date, value=(start_date, end_date))

        # MDA and MTR checkboxes
        col1, col2, *_ = st.sidebar.beta_columns(4)
        with col1:
            mda = st.checkbox('MDA', value=False)
        with col2:
            mtr = st.checkbox('MTR', value=False)     
        
        print("Checking data...")

        # Check selected options
        check_dates(dates)
        check_zones(selected_zones)
        check_markets(mda, mtr)

        print("Getting info ready...")
        start_date, end_date = dates # Unpack date range

        # Create urls (API calls) to request using selected options
        zones_urls, zones = get_zones_urls(start_date, end_date, selected_zones, mda, mtr)

        print("Requesting...")
        df_requested = get_info(zones_urls) # Request created urls

        # Check for error in request
        check_df_requested(df_requested)
        
        # Deal with 23 and 25 hour days
        df_requested_clean = check_for_23_or_25_hours(df_requested)

        # Plotting options
        components = list(reservas.values())
        avg_options = ["Horario", "Diario", "Semanal"]
        agg_options = ["Histórico","Día de la semana", "Mes"]
    
        col1, col2, col3, col4 = st.beta_columns([2,1,1,1])
        component = col1.selectbox(label = "Tipo de Reserva",options=components, index=0, key=None)
        avg_option = col2.selectbox("Promedio", avg_options, 0, help = "Grafica el valor promedio por hora, día o semana (promedios simples).")
        agg_option = col3.selectbox("Agrupar por", agg_options, 0)
        col4.write("####") # Vertical space
        group = col4.checkbox('Año vs Año', value=False, help = "Separa información por año.")    

        with st.spinner(text='Generando gráfica y tabla.'):

            print('Plotting...')
            # Create DataFrame for plot and create plot
            df_plot = arange_dataframe_for_plot(df_requested_clean.copy(), avg_option, agg_option, group)
            st.plotly_chart(plot_df(df_plot, component, avg_option, agg_option, group), use_container_width=True)#use_column_width=True

            print("Making info table...")
            # Create DataFrame for info table and display info table
            df_info_table = arange_dataframe_for_info_table(df_requested.copy(), component, group)
            st.markdown("""Resumen de datos horarios:""")
            st.dataframe(df_info_table.style.format({col:"{:,}" for col in df_info_table.columns if col not in ['']}).applymap(lambda x: 'color: red' if x < 0 else 'color: black', subset=['Mínimo','Máximo','Promedio','Desviación Est.']))

            st.markdown("") # Vertical space
            st.markdown("")

            print("Making table...")
            # Create dataframe for table and display table
            df_table = arange_dataframe_for_table(df_requested.copy(), component)
            st.markdown("""Primeras 1000 filas de datos:""")
            st.dataframe(df_table.iloc[:1000].style.format({col:"{:,}" for col in df_table.columns if col not in ['Fecha','Hora']}).applymap(lambda x: 'color: red' if x < 0 else 'color: black', subset=[col for col in df_table.columns if col not in ['Fecha','Hora']]))

            # Download link
            st.markdown(get_table_download_link(df_table,dates, component, info=list(zones.keys()), markets=[mda,mtr]), unsafe_allow_html=True)
        
    print('Done')

if __name__ == "__main__":
    main()