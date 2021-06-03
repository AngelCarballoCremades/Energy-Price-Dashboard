import streamlit as st
from streamlit import caching
import pandas as pd
from datetime import datetime, date, timedelta
import requests
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed
import plotly.express as px
import base64
import unidecode
import os


API_URL = os.environ["API_URL"]


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

# configuration dict to modify texts and options

analysis_options = {
    "Energía Eléctrica":{
        "Precios":{
            "max_date":date.today()+timedelta(days=1), # Max date in date selector
            "min_date":datetime(2017, 2, 1), # Min date in date selector
            "start_date":date.today()-timedelta(days=30), # Initial date selected
            "end_date":date.today()-timedelta(days=15), # final date initially selected
            "markets":["MDA","MTR"], # Markets checkboxes options
            "mean_or_sum":"mean", # MWh == sum, $/MWh == mean
            "component":{
                "options":["Precio Total [$/MWh]","Componente de Energía [$/MWh]", "Componente de Pérdidas [$/MWh]","Componente de Congestión [$/MWh]"], # Component dropdown options
                "title":"Componente de Precios:", # Component dropdown title
                "help":"Componente de precios a graficar."  # Component dropdown help
            },
            "plot_options":{
                "title":"Valores a graficar:", # Plot_options dropdown title
                "help":"Grafica el valor promedio por hora, día, semana, promedio de cada hora por día de la semana o promedio de cada hora por mes." # Plot_options dropdown help
            }
        },
        "Cantidades Asignadas":{
            "max_date":date.today()+timedelta(days=1),
            "min_date":datetime(2017, 1, 1),
            "start_date":date.today()-timedelta(days=30), # Initial date selected
            "end_date":date.today()-timedelta(days=15), # final date initially selected
            "markets":["MDA"],
            "mean_or_sum":"sum",
            "component":{
                "options":["Total de Cargas [MWh]","Cargas Directamente Modeladas [MWh]","Cargas Indirectamente Modeladas [MWh]"],
                "title":"Tipo de carga a graficar:",
                "help":"Cargas directamente modeladas, indirectamente modeladas o ambas (suma)"
            },
            "plot_options":{
                "title":"Valores a graficar:",
                "help":"Grafica el valor total (suma) por hora, día, semana, promedio de cada hora por día de la semana o promedio de cada hora por mes."
            }
        },
        "Demanda":{
            "max_date":date.today()+timedelta(days=1),
            "min_date":datetime(2018, 1, 1),
            "start_date":date.today()-timedelta(days=180), # Initial date selected
            "end_date":date.today()-timedelta(days=165), # final date initially selected
            "markets":["MDA","MDA-AUGC","MTR"],
            "mean_or_sum":"sum",
            "component":{
                "options":["Energía [MWh]"],
                "title":"Valor a graficar:",
                "help":"Energía total"
            },
            "plot_options":{
                "title":"Valores a graficar",
                "help":"Grafica el valor total (suma) por hora, día, semana, promedio de cada hora por día de la semana o promedio de cada hora por mes."
            }
        },
        "Generación":{
            "max_date":date.today()+timedelta(days=1),
            "min_date":datetime(2018, 1, 1),
            "start_date":date.today()-timedelta(days=180), # Initial date selected
            "end_date":date.today()-timedelta(days=165), # final date initially selected
            "markets":["MDA-Intermitentes","MTR"],
            "mean_or_sum":"sum",
            "component":{
                "options":["Energía [MWh]"],
                "title":"Valor a graficar:",
                "help":"Generación de energía por tipo de tecnología"
            },
            "plot_options":{
                "title":"Valores a graficar",
                "help":"Grafica el valor total (suma) por hora, día, semana, promedio de cada hora por día de la semana o promedio de cada hora por mes."
            },
            "second_plot_options":{
                "title":"Valores a graficar:",
                "help":"Grafica el valor total (suma) por hora, día, semana, promedio de cada hora por día de la semana o promedio de cada hora por mes.",
                "options":["Horario","Diario", "Semanal","Promedio Horario por Día de la Semana", "Promedio Horario por Mes"]
            }
        }
    },
    "Servicios Conexos":{
        "Precios":{
            "max_date":date.today()+timedelta(days=1),
            "min_date":datetime(2018, 5, 24),
            "start_date":date.today()-timedelta(days=30), # Initial date selected
            "end_date":date.today()-timedelta(days=15), # final date initially selected
            "markets":["MDA","MTR"],
            "mean_or_sum":"mean",
            "component":{
                "options":["Reserva de Regulación Secundaria [$/MWh]","Reserva Rodante de 10 Minutos [$/MWh]","Reserva No Rodante de 10 Minutos [$/MWh]","Reserva Rodante Suplementaria [$/MWh]","Reserva No Rodante Suplementaria [$/MWh]"],
                "title":"Tipo de Reserva a graficar:",
                "help":"Tipo de Reserva a graficar."
            },
            "plot_options":{
                "title":"Valores a graficar:",
                "help":"Grafica el valor promedio por hora, día, semana, promedio de cada hora por día de la semana o promedio de cada hora por mes."
            }
        },
        "Cantidades Asignadas":{
            "max_date":date.today()+timedelta(days=1),
            "min_date":datetime(2018, 5, 24),
            "start_date":date.today()-timedelta(days=30), # Initial date selected
            "end_date":date.today()-timedelta(days=15), # final date initially selected
            "markets":["MDA"],
            "mean_or_sum":"sum",
            "component":{
                "options":["Reserva de Regulación Secundaria [MWh]","Reserva Rodante de 10 Minutos [MWh]","Reserva No Rodante de 10 Minutos [MWh]","Reserva Suplementaria [MWh]"],
                "title":"Tipo de Reserva a graficar:",
                "help":"Tipo de Reserva a graficar"
            },
            "plot_options":{
                "title":"Valores a graficar:",
                "help":"Grafica el valor total (suma) por hora, día, semana, promedio de cada hora por día de la semana o promedio de cada hora por mes."
            }
        }
    }
}

reservas = {
    "Reserva de regulación secundaria":"Reserva de Regulación Secundaria [$/MWh]",
    "Reserva rodante de 10 minutos":"Reserva Rodante de 10 Minutos [$/MWh]",
    "Reserva no rodante de 10 minutos":"Reserva No Rodante de 10 Minutos [$/MWh]",
    "Reserva rodante suplementaria":"Reserva Rodante Suplementaria [$/MWh]",
    "Reserva no rodante suplementarias":"Reserva No Rodante Suplementaria [$/MWh]"    
}


def welcome_text():
    return """
        #### ¡Hola!

        Este proyecto está hecho para facilitar el acceso y análisis de la información del **Mercado Eléctrico Mayorista** mexicano.
        
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
        * **Energía Eléctrica** 
            * **Precios** - Precio de energía
                * **NodosP** y **NodosP Distribuidos** 
                    * Por lo menos uno debe ser seleccionado (de cualquier tipo).
                * **Fechas** - Rango de fechas de información a solicitar. 
                    * Disponible desde febrero 2017 a mañana. Ten en cuenta que no todos los NodosP han existido en este rango.
                    * MTR disponible hasta hoy -7 días.
                    * MDA hasta hoy +1 día.
                * **MDA** y **MTR**
                    * Por lo menos uno debe ser seleccionado.
            * **Cantidades Asignadas** - Cantidades asignadas de energía por Zona de Carga en el MDA.
                * **Zonas de Carga**
                    * Por lo menos uno debe ser seleccionado.
                * **Fechas** - Rango de fechas de información a solicitar. 
                    * Disponible desde enero 2017 a mañana.
                    * MDA hasta hoy +1 día.
                * **MDA**
                    * Debe estar seleccionado.
            * **Demanda** - Demanda de energía por Zona de Carga.
                * **Zonas de Carga**
                    * Por lo menos uno debe ser seleccionado.
                * **Fechas** - Rango de fechas de información a solicitar. 
                    * MDA disponible desde enero 2018 a mañana.
                    * MTR disponible desde enero 2018 a hoy-15 días.
                        * Estoy trabajando en la actualización automática de los datos.
                    * MDA-AUGC disponible desde el 10 de enero del 2019 a hoy-4 meses.
                        * Estoy trabajando en la actualización automática de los datos.
                * **MDA, MDA-AUGC** y **MTR**
                    * **MDA** - Demanda de energía del modelo AU-MDA, ofertas de compra de energía (Cantidades Asignadas).
                    * **MDA-AUGC** - Pronóstico de demanda de energía del modelo AU-GC
                    * **MTR** - Estimación de demanda real de energía
            * **Generación** - Generación de energía por tipo de tecnología.
                * **MDA-Intermitentes** y **MTR**
                    * **MDA-Intermitentes** - Pronóstico de generación de energía intermitente
                    * **MTR** - Energía generada por tipo de tecnología
                * **Sistema**
                    * En MDA-Intermitentes selecciona el deseado.
                * **Fechas** - Rango de fechas de información a solicitar. 
                    * MDA-Intermitentes disponible desde enero 2018 a mañana.
                        * Estoy trabajando en la actualización automática de los datos.
                    * MTR disponible desde enero 2018 a hoy-1 o -2 meses.
                        * Estoy trabajando en la actualización automática de los datos.
        * **Servicios Conexos**  
            * **Precios** - Precio de Servicios conexos por tipo de reserva.
                * **Zonas de Reserva**
                    * Por lo menos una debe ser seleccionada.
                * **Fechas** - Rango de fechas de información a solicitar. 
                    * Disponible desde mayo 2018 a mañana.
                    * MTR disponible hasta hoy -7 días.
                    * MDA hasta hoy +1 día.
                * **MDA** y **MTR**
                    * Por lo menos uno debe ser seleccionado.
            * **Cantidades Asignadas** - Cantidades asignadas de reservas en el MDA.
                * **Zonas de Reserva**
                    * Por lo menos uno debe ser seleccionado.
                * **Fechas** - Rango de fechas de información a solicitar. 
                    * Disponible desde mayo 2018 a mañana.
                    * MDA hasta hoy +1 día.
                * **MDA**
                    * Debe estar seleccionado.
            

        Cuando se ha hecho una selección válida, aparecerá una barra de progreso mientras la información la información es descargada.
        El tiempo que tarde dependerá de la información solicitada.

        ### Área Central

        Opciones a seleccionar:
        * **Componente de Precio**, **Tipo de Carga**, **Energía** o **Tipo de Reserva** - Componente del PML, PND, tipo de carga, energía o reserva a graficar.
        * **Promedio** o **Valor**
            * **Horario** - Graficar promedio por hora (promedio simple).
            * **Diario** - Graficar promedio por día (promedio simple) o suma del total asignado en el día.
            * **Semanal** - Graficar promedio por semana (promedio simple) o suma del total asignado en la semana.
            * **Promedio Horario por Día de la Semana** - Grafica el promedio de cada hora para cada día de la Semana. Utiliza la información solicitada en la barra lateral.
            * **Promedio Horario por Mes** - Grafica el promedio de cada hora para cada mes. Utiliza la información solicitada en la barra lateral. 
        * **Año vs Año** - Crea diferentes trazos para cada año dentro de la información solicitada en la barra lateral.
        * **Gráficas de Generación de Energía**
            * **Gráfico de área** - Misma funcionalidad que la gráfica anterior en temas de selección de datos a agrupar.
                * **Porcentaje** - Grafica el porcentaje de generación por tecnología con base en el 100% generado (normaliza información de 0 a 1 por hora, día o semana).
            * **Gráfico de dona** - Porcentaje de energía por tipo de energía del rango de fechas solicitado
                * **Total de Energía** - Total (suma) de energía generada en el rango de fechas solicitado.
        * Tablas
            * **Resumen de datos horarios:** - Tabla mostrando valores estadísticos de los valores horarios.
            * **Primeras 1000 filas de datos:** - Tabla mostrando 1000 primeras filas de la información horaria.
        
        Puedes descargar toda la información a un cvs con el botón **Descargar datos**.

        Información decargada a través de los servicios web del CENACE: [PML](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PML.pdf), [PND](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PEND.pdf), [PSC](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PSC.pdf), [CAEZC](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-CAEZC.pdf) y [CASC](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-CASC.pdf).
        
        Información descargada a través de [API privada](https://github.com/AngelCarballoCremades/CENACE-RDS-API) (por ahora): [EDREZC](https://github.com/AngelCarballoCremades/CENACE-RDS-API/tree/main/SWEDREZC), [PDEZC](https://github.com/AngelCarballoCremades/CENACE-RDS-API/tree/main/SWPDEZC), [EGTT](https://github.com/AngelCarballoCremades/CENACE-RDS-API/tree/main/SWEGTT) y [PGI](https://github.com/AngelCarballoCremades/CENACE-RDS-API/tree/main/SWPGI).
        
        Los archivos oficiales pueden ser descargados aquí: [PML/PND](https://www.cenace.gob.mx/Paginas/SIM/Reportes/PreciosEnergiaSisMEM.aspx), [PSC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/ServiciosConexosSisMEM.aspx), [CASC/CAEZC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/CantidadesAsignadasMDA.aspx), [EDREZC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/EstimacionDemandaReal.aspx) (Por Retiros), [PDEZC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/PronosticosDemanda.aspx) (AUGC/Por Retiros), [EGTT](https://www.cenace.gob.mx/Paginas/SIM/Reportes/EnergiaGeneradaTipoTec.aspx) (Liquidación 0) y [PGI](https://www.cenace.gob.mx/Paginas/SIM/Reportes/H_PronosticosGeneracion.aspx?N=245&opc=divCssPronosticosGen&site=Pron%C3%B3sticos%20de%20Generaci%C3%B3n%20Intermitente&tipoArch=C&tipoUni=ALL&tipo=All&nombrenodop=).


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

def check_nodes_zones(selected):
    """Checks if there is at least a node selected"""
    if not selected:
        st.sidebar.warning('Selecciona un Nodo')    
        st.stop()

def check_markets(markets):
    """Checks if there is at least a market selected"""
    if not any(markets):
        st.sidebar.warning('Selecciona un mercado.')
        st.stop()

def check_df_requested(df_requested):
    if isinstance(df_requested, bool):
        caching.clear_cache()
        st.sidebar.warning('Error extrayendo datos del CENACE. Inténtalo de nuevo o cambia las fechas solicitadas.')
        st.stop()


def pack_dates(start_date, end_date, market = "", limit_dates=True):
    """Gets days to ask for info and start date, returns appropiate data intervals to assemble APIs url"""
    
    # For open source APIs date interval for resquest is bigger
    date_interval = 200 if not limit_dates else 7
        
    # To avoid CENACE error in MTR API last date of MTR API call is limited
    if market == 'MTR' and end_date > date.today()-timedelta(days = 7):
        end_date = date.today()-timedelta(days = 7)

    dates = []
    delta = end_date-start_date
    days = delta.days

    # Pack dates every 'date_interval' days.
    while days >= 0:

        if days >= date_interval:
            last_date = start_date + timedelta(days = date_interval-1)
            dates.append( [str(start_date),str(last_date)] )
            start_date = last_date + timedelta(days = 1)
            days -= date_interval

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

def get_nodes_urls(start_date, end_date, selected_nodes_d, selected_nodes_p, mda, mtr=False):
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

def get_nodes_p_urls(start_date, end_date, selected_nodes_d, mda, mda_augc=False, mtr=False, ):
    """Returns nodes urls to request"""

    dates_packed_mda = pack_dates(start_date, end_date, 'MDA') # Pack dates for API calls
    dates_packed_mda_augc = pack_dates(start_date, end_date, 'MDA-AUGC',limit_dates=False) # Pack dates for API calls
    dates_packed_mtr = pack_dates(start_date, end_date, 'MTR',limit_dates=False) # Pack dates for API calls
    
    nodes_d_system = list(map(get_node_system, selected_nodes_d)) # Get selected-nodes system
    
    # Pack nodes depending on system. Leave 'PND', same 10 node limit in url.
    nodes_d = {
        "SIN": pack_nodes([node[0] for node in nodes_d_system if node[1] == "SIN"], "PND"),
        "BCA": pack_nodes([node[0] for node in nodes_d_system if node[1] == "BCA"], "PND"),
        "BCS": pack_nodes([node[0] for node in nodes_d_system if node[1] == "BCS"], "PND")
    }
    
    nodes_urls = []

    # Get urls from packed nodes and dates, separated by market
    if mda:
        nodes_urls += get_urls_to_request(nodes_d, dates_packed_mda, 'CAEZC', 'MDA')
    if mda_augc:
        nodes_urls += get_urls_to_request(nodes_d, dates_packed_mda_augc, 'PDEZC', 'MDA-AUGC')
    if mtr:
        nodes_urls += get_urls_to_request(nodes_d, dates_packed_mtr, 'EDREZC', 'MTR')
    
    # If there are no urls to call
    if not len(nodes_urls):
        st.sidebar.warning('No hay valores disponibles para las fechas seleccionadas.')
        st.stop()

    return nodes_urls

def get_zones_urls(start_date, end_date, selected_zones, info_type, mda, mtr=False):
    """Returns zones urls to request"""


    dates_packed_mda = pack_dates(start_date, end_date, 'MDA') # Pack dates for API calls
    dates_packed_mtr = pack_dates(start_date, end_date, 'MTR') # Pack dates for API calls

    zones = {zone[1:4]:[[zone[1:4]]] for zone in selected_zones} # Pack zoness for function 'get_urls_to_request'

    zones_urls = []

    # Get urls from packed zones and dates, separated by market
    if mda:
        zones_urls += get_urls_to_request(zones, dates_packed_mda, info_type, 'MDA')
    
    if mtr:        
        zones_urls += get_urls_to_request(zones, dates_packed_mtr, info_type, 'MTR')

    # If there are no urls to call
    if not len(zones_urls):
        st.sidebar.warning('No hay valores disponibles para las fechas seleccionadas.')
        st.stop()

    return zones_urls, zones


def get_generation_urls(start_date, end_date, generation_type, system="SEN"):
    """Returns generation urls to request"""
    
    dates_packed = pack_dates(start_date, end_date, market=None,limit_dates=False)

    # Get urls from desired information
    if generation_type == "MDA-Intermitentes":
        urls = get_urls_to_request(False, dates_packed, "PGI", "MDA", system)
    elif generation_type == "MTR":
        urls = get_urls_to_request(False, dates_packed, "EGTT", "MTR", system)

    # If there are no urls to call
    if not len(urls):
        st.sidebar.warning('No hay valores disponibles para las fechas seleccionadas.')
        st.stop()

    return urls


def check_consumption_dfs(df):
    """"""
    # CAEZC does not have a column named Energía, it is named Total de Cargas
    if "Energía [MWh]" not in df.columns:
        df["Energía [MWh]"] = df["Total de Cargas [MWh]"]
        df.drop(columns=["Cargas Directamente Modeladas [MWh]","Cargas Indirectamente Modeladas [MWh]","Total de Cargas [MWh]"], inplace=True)
        return df
    
    else:
        return df


def get_urls_to_request(nodes_dict, dates_packed, info_type, market, system = None):
    """Assemble API calls urls for PMLs, PNDs and PSC"""

    url_frame = {
        "PND":"https://ws01.cenace.gob.mx:8082/SWPEND/SIM/",
        "PML":"https://ws01.cenace.gob.mx:8082/SWPML/SIM/",
        "PSC":"https://ws01.cenace.gob.mx:8082/SWPSC/SIM/",
        "CAEZC":"https://ws01.cenace.gob.mx:8082/SWCAEZC/SIM/",
        "CASC":"https://ws01.cenace.gob.mx:8082/SWCASC/SIM/",
        "EDREZC":f"{API_URL}SWEDREZC/",
        "PDEZC":f"{API_URL}SWPDEZC/",
        "EGTT":f"{API_URL}SWEGTT/",
        "PGI":f"{API_URL}SWPGI/"
        }

    urls_list = []

    if not nodes_dict:
        for dates in dates_packed:
            # Select correct API base
            url = url_frame[info_type]

            # Building request url with data provided
            url_complete = f"{url}{system}/{market}/{dates[0][:4]}/{dates[0][5:7]}/{dates[0][8:]}/{dates[1][:4]}/{dates[1][5:7]}/{dates[1][8:]}/JSON"
            urls_list.append(url_complete)
        
        return urls_list
    
    for system, nodes_packed in nodes_dict.items():
        if not len(nodes_packed[0]): 
            continue
        
        for node_group in nodes_packed:
            for dates in dates_packed:
                nodes_string = ",".join(node_group)

                # Select correct API base
                url = url_frame[info_type]

                # Building request url with data provided
                url_complete = f"{url}{system}/{market}/{nodes_string}/{dates[0][:4]}/{dates[0][5:7]}/{dates[0][8:]}/{dates[1][:4]}/{dates[1][5:7]}/{dates[1][8:]}/JSON"

                urls_list.append(url_complete)

    return urls_list


@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)#(hash_funcs={streamlit.delta_generator.DeltaGenerator: bar_hash_func})
def get_info(urls_list, selected_subdata):
    """Makes API calls for every url provided and returns a DataFrame with clean information."""

    # Create loading bar in sidebar
    bar_string = st.sidebar.text("Cargando...")
    bar = st.sidebar.progress(0)

    # Initialize futures session
    session = FuturesSession(max_workers=20)
    futures=[session.get(u) for u in urls_list]

    dfs = [] # List of info data frames

    for i,future in enumerate(as_completed(futures)):

        percentage = i*100//len(urls_list) # Update loading bar progress
        bar.progress(percentage)

        resp = future.result() # Url response
        try:
            json_data = resp.json() # Get response json
        except:
            print(resp.content)
            raise ValueError(f'Error extraño, respuesta: {resp.content}')

        # Check for bad responses
        for _ in range(10):

            if "status" in json_data.keys(): 
                break # Good response

            # When there is an error on CENACE's side (Usually in MTR API) there is a 'message' key in json response. If it's true entire process is cancelled (False is returned).
            elif "Message" in json_data.keys():
                    print(json_data)
                    print(resp.request.url)
                    print("Requesting again...")
                    resp = requests.get(resp.request.url)
                    json_data = resp.json() # Get response json
                    
        if "Message" in json_data.keys() or "message"in json_data.keys():
            print(json_data)
            print(resp.request.url)
            return False

        # checks for response status, expected 'OK' status
        if json_data["status"] != "OK": # If response != 'OK' don't append response. Usualy happens when there is no data available for nodes/date selected.
            print(json_data)
            continue

        dfs.append(json_to_dataframe(json_data)) # Convert json to DataFrame and append to DataFrames'list

    bar.progress(100) # Process is complete
        
    try:
        if selected_subdata == "Demanda":
            dfs = map(check_consumption_dfs, dfs)

        df = pd.concat(dfs) # Join downloaded info in one DataFrame
    except:
        df = None
    
    # If there are no values with selected data
    if isinstance(df,type(None)):
        bar_string.empty()
        bar.empty()
        st.sidebar.warning('No hay valores disponibles para las opciones seleccionadas.')
        caching.clear_cache()
        st.stop()

    df.reset_index(drop=True, inplace=True)
    
    # Eliminate progress bar
    bar_string.empty()
    bar.empty()

    return df


def json_to_dataframe(json_file):
    """Reads json file, creates a list of nodes DataFrames and concatenates them. After that, it cleans/orders the final df and returns it"""
    
    dfs = []

    # Separate every node response and join in one DataFrame
    for node in json_file["Resultados"]:
        dfs.append(pd.DataFrame(node))

    df = pd.concat(dfs) # Join all DataFrame
    
    # Order all data into one same structure.
    df["Sistema"] = json_file["sistema"]
    df["Mercado"] = json_file["proceso"]
    df["Fecha"] = df["Valores"].apply(lambda x: x["fecha"])
    df["Hora"] = df["Valores"].apply(lambda x: x["hora"])

    if json_file["nombre"] in ["Energía Generada por Tipo de Tecnología","Pronóstico de Generación Intermitente"]:
        df["Nombre del Nodo"] = df["tecnologia"]
        df["Energía [MWh]"] = df["Valores"].apply(lambda x: x["energia"]).astype("float")
        df = df[["Sistema","Mercado","Nombre del Nodo","Fecha","Hora","Energía [MWh]"]]

        return df

    elif json_file["nombre"] == "Pronóstico de Demanda de Energía por Zona de Carga":
        df["Nombre del Nodo"] = df["zona_carga"]
        df["Energía [MWh]"] = df["Valores"].apply(lambda x: x["energia"]).astype("float")
        df = df[["Sistema","Mercado","Nombre del Nodo","Fecha","Hora","Energía [MWh]"]]
        
        return df

    elif json_file["nombre"] == "Estimación de la Demanda Real de Energía por Zona de Carga":
        df["Nombre del Nodo"] = df["zona_carga"]
        df["Energía [MWh]"] = df["Valores"].apply(lambda x: x["energia"]).astype("float")
        df = df[["Sistema","Mercado","Nombre del Nodo","Fecha","Hora","Energía [MWh]"]]
        
        return df

    elif json_file["nombre"] == "PSC":
        df["Nombre del Nodo"] = df["clv_zona_reserva"]
        df["Reserva"] = df["Valores"].apply(lambda x: x["tipo_res"])
        df["Precio"] = df["Valores"].apply(lambda x: x["pres"]).astype("float")
        df = df[["Sistema","Mercado","Nombre del Nodo","Fecha","Hora","Reserva","Precio"]]
        df = df.set_index(["Sistema","Mercado","Nombre del Nodo","Fecha","Hora","Reserva"]).unstack().reset_index()
        df.columns = [col[0] if col[1]=="" else reservas[col[1]] for col in df.columns]
        
        return df
    
    elif json_file["nombre"] == "Cantidades Asignadas de Energía de Zona de Carga":
        df["Nombre del Nodo"] = df["zona_carga"]
        df["Cargas Directamente Modeladas [MWh]"] = df["Valores"].apply(lambda x: x["demanda_mdo_nodales"]).astype("float")
        df["Cargas Indirectamente Modeladas [MWh]"] = df["Valores"].apply(lambda x: x["demanda_pml_zonales"]).astype("float")
        df["Total de Cargas [MWh]"] = df["Valores"].apply(lambda x: x["total_cargas"]).astype("float")
        df = df[["Sistema","Mercado","Nombre del Nodo","Fecha","Hora","Cargas Directamente Modeladas [MWh]","Cargas Indirectamente Modeladas [MWh]","Total de Cargas [MWh]"]]
        
        return df
    
    elif json_file["nombre"] == "Cant. Asignadas Servicios Conexos":
        df["Nombre del Nodo"] = df["zona_reserva"]
        df["Reserva de Regulación Secundaria [MWh]"] = df["Valores"].apply(lambda x: x["res_reg"]).astype("float")
        df["Reserva Rodante de 10 Minutos [MWh]"] = df["Valores"].apply(lambda x: x["res_rod_10"]).astype("float")
        df["Reserva No Rodante de 10 Minutos [MWh]"] = df["Valores"].apply(lambda x: x["res_10"]).astype("float")
        df["Reserva Suplementaria [MWh]"] = df["Valores"].apply(lambda x: x["res_sup"]).astype("float")
        df = df[["Sistema","Mercado","Nombre del Nodo","Fecha","Hora","Reserva de Regulación Secundaria [MWh]","Reserva Rodante de 10 Minutos [MWh]","Reserva No Rodante de 10 Minutos [MWh]","Reserva Suplementaria [MWh]"]]
        
        return df
    
    elif json_file["nombre"] == "PEND":
        df["Precio Total [$/MWh]"] = df["Valores"].apply(lambda x: x["pz"]).astype("float")
        df["Componente de Energía [$/MWh]"] = df["Valores"].apply(lambda x: x["pz_ene"]).astype("float")
        df["Componente de Pérdidas [$/MWh]"] = df["Valores"].apply(lambda x: x["pz_per"]).astype("float")
        df["Componente de Congestión [$/MWh]"] = df["Valores"].apply(lambda x: x["pz_cng"]).astype("float")
        df["Nombre del Nodo"] = df["zona_carga"].copy()

    elif json_file["nombre"] == "PML":
        df["Precio Total [$/MWh]"] = df["Valores"].apply(lambda x: x["pml"]).astype("float")
        df["Componente de Energía [$/MWh]"] = df["Valores"].apply(lambda x: x["pml_ene"]).astype("float")
        df["Componente de Pérdidas [$/MWh]"] = df["Valores"].apply(lambda x: x["pml_per"]).astype("float")
        df["Componente de Congestión [$/MWh]"] = df["Valores"].apply(lambda x: x["pml_cng"]).astype("float")
        df["Nombre del Nodo"] = df["clv_nodo"].copy()

    df = df[["Sistema","Mercado","Fecha","Hora","Nombre del Nodo","Precio Total [$/MWh]","Componente de Energía [$/MWh]", "Componente de Pérdidas [$/MWh]","Componente de Congestión [$/MWh]"]]

    return df


def check_for_23_or_25_hours(df_requested):
    """Check for 25 or 23 hour days, works still missing in this function"""
    df = df_requested[df_requested['Hora'] != '25']

    return df


def arange_dataframe_for_plot(df, plot_option, group, mean_or_sum, percentage=False):
    """Modifies dataframe to plot desired information, changes output depending on plot and group option"""
    
    def use_plot_option(df, plot_option, group, mean_or_sum):
        """Modifies dataframe to plot desired plot_option"""

        if plot_option == "Promedio Horario por Día de la Semana":
            df['Hora_g'] = df['Hora'].apply(lambda x: f"0{int(x)-1}" if int(x)-1 < 10 else f"{int(x)-1}")
            df["Fecha_g"] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora_g'] + ':59:59', format="%Y-%m-%d %H:%M:%S")
            df['Día de la Semana'] = df['Fecha_g'].apply(lambda x: str(x.isocalendar()[2]))

            if group:
                df["Año"] = df['Fecha_g'].dt.year
                df["Nodo-Mercado"] = df['Año'].apply(str) + "_" + df['Mercado'] + '_' + df["Nombre del Nodo"]
                df = df.groupby(['Nodo-Mercado','Día de la Semana','Hora_g']).mean()
            
            else:
                df["Nodo-Mercado"] = df['Mercado'] + '_' + df["Nombre del Nodo"]
                df = df.groupby(['Nodo-Mercado','Día de la Semana','Hora_g']).mean()                   

            df.reset_index(inplace=True)
            df['Segundo'] = df['Hora_g'].apply(lambda x: str(int(x)+1) if int(x)>8 else f"0{int(x)+1}")
            df['Día-Hora'] = pd.to_datetime("2021-03-0" + df['Día de la Semana'] + " " + df['Hora_g'] + ":59:" + df['Segundo'], format="%Y-%m-%d %H:%M:%S")
            df.sort_values(by='Día-Hora', axis=0, ascending=True, inplace=True, ignore_index=True)
            return df

        elif plot_option == "Promedio Horario por Mes":
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
        
        elif plot_option == "Horario":
            df['Hora_g'] = df['Hora'].apply(lambda x: f"0{int(x)-1}" if int(x)-1 < 10 else f"{int(x)-1}")
            df["Fecha_g"] = pd.to_datetime(df['Fecha'] + ' ' + df['Hora_g'] + ':59:59', format="%Y-%m-%d %H:%M:%S")
            df["Año"] = df['Fecha_g'].dt.year
            df.sort_values(by='Fecha_g', axis=0, ascending=True, inplace=True, ignore_index=True)
            return df
        
        elif plot_option == "Diario":
            if mean_or_sum == 'mean':
                df = df.groupby(['Sistema','Mercado','Nombre del Nodo','Fecha']).mean()
            elif mean_or_sum == 'sum':
                df = df.groupby(['Sistema','Mercado','Nombre del Nodo','Fecha']).sum()
            
            df.reset_index(inplace=True)
            df["Fecha_g"] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d")
            df.sort_values(by='Fecha_g', axis=0, ascending=True, inplace=True, ignore_index=True)
            df["Año"] = df['Fecha_g'].dt.year
            return df

        elif plot_option == "Semanal":
            df["Fecha"] = pd.to_datetime(df['Fecha'], format="%Y-%m-%d")
            df['Año-Semana'] = df['Fecha'].apply(lambda x: ".".join([str(x.isocalendar()[0]), str(x.isocalendar()[1]) if x.isocalendar()[1] > 9 else f"0{str(x.isocalendar()[1])}" ]))
            
            if mean_or_sum == 'mean':
                df = df.groupby(['Sistema','Mercado','Nombre del Nodo','Año-Semana']).mean()
            elif mean_or_sum == 'sum':
                df = df.groupby(['Sistema','Mercado','Nombre del Nodo','Año-Semana']).sum()

            df.reset_index(inplace=True)
            df.sort_values(by=['Año-Semana'], axis=0, ascending=True, inplace=True, ignore_index=True)
            return df

    def group_by_year(df,group, plot_option):
        """Modifies dataframe to plot yaer vs year"""
        if plot_option in ["Promedio Horario por Día de la Semana","Promedio Horario por Mes"]:
            return df

        elif not group:
            df["Nodo-Mercado"] = df['Mercado'] + '_' + df["Nombre del Nodo"]
            return df
            
        else:
            if plot_option == "Horario":
                # df = df[(df['Fecha_g'] > '2013-01-01') & (df['date'] < '2013-02-01')]
                df['Fecha_g'] = df['Fecha_g'].apply(lambda x: x.replace(year = 2020))
                # df["Fecha_g"] = df['Fecha_g'].dt.strftime('%m-%d %H:%M:%S')
                df["Nodo-Mercado"] = df["Año"].apply(str) + "_" + df['Mercado'] + "_" + df["Nombre del Nodo"] 
                return df
                
            elif plot_option == "Diario":
                df['Fecha_g'] = df['Fecha_g'].apply(lambda x: x.replace(year = 2020))
                # df["Fecha_g"] = df['Fecha_g'].dt.strftime('%m-%d %H:%M:%S')
                df["Nodo-Mercado"] = df["Año"].apply(str) + "_" + df['Mercado'] + "_" + df["Nombre del Nodo"] 
                return df

            elif plot_option == "Semanal":
                df["Año"] = df['Año-Semana'].apply(lambda x: x[:4])
                df["Semana"] = df['Año-Semana'].apply(lambda x: x[-2:])
                df.sort_values(by=['Semana'], axis=0, ascending=True, inplace=True, ignore_index=True)
                df["Nodo-Mercado"] = df["Año"] + "_" + df['Mercado'] + "_" + df["Nombre del Nodo"]
                return df
        
    def use_percentage(df, percentage):
        
        if not percentage:
            return df

        cols = df.columns

        # Hourly graph
        if "Fecha_g" in cols and "Hora_g" in cols:
            df.set_index("Fecha_g", inplace=True)
            df["Energía [%]"] = df["Energía [MWh]"].div(df.resample('H')["Energía [MWh]"].transform("sum")).multiply(100).round(3)
        
        # Daily graph
        elif "Fecha_g" in cols:
            df.set_index("Fecha_g", inplace=True)
            df["Energía [%]"] = df["Energía [MWh]"].div(df.resample('D')["Energía [MWh]"].transform("sum")).multiply(100).round(3)
        
        # Weekly graph
        elif "Año-Semana" in cols:            
            df["Energía [%]"] = df[["Año-Semana","Energía [MWh]"]].groupby("Año-Semana").transform(lambda x: x / x.sum()).multiply(100).round(3)
            df.set_index("Año-Semana", inplace=True)

        # Day-of-week graph
        elif "Día-Hora" in cols:
            df.set_index("Día-Hora", inplace=True)
            df["Energía [%]"] = df["Energía [MWh]"].div(df.resample('H')["Energía [MWh]"].transform("sum")).multiply(100).round(3)

        # Month graph
        elif "Mes-Hora" in cols:
            df.set_index("Mes-Hora", inplace=True)
            df["Energía [%]"] = df["Energía [MWh]"].div(df.resample('H')["Energía [MWh]"].transform("sum")).multiply(100).round(3)
        
        df.reset_index(inplace=True)

        return df

    df = use_plot_option(df, plot_option, group, mean_or_sum)
    df = group_by_year(df, group, plot_option)
    df = use_percentage(df, percentage)
    return df


@st.cache(show_spinner=False)
def arange_dataframe_for_table(df, component, download = False):
    """Modifies original df to show in table."""
    
    df["Nodo-Mercado"] = df['Mercado'] + '_' + df["Nombre del Nodo"] 
    df_table = df.pivot(index=['Fecha','Hora'], columns='Nodo-Mercado', values=component)
    df_table.columns = df_table.columns.to_series().values
    df_table.reset_index(inplace=True)
    df_table['Hora'] = df_table['Hora'].astype('int')
    df_table.sort_values(by=['Fecha','Hora'], axis=0, ascending=[True,True], inplace=True, ignore_index=True)

    return df_table


@st.cache(show_spinner=False)
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


@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)
def plot_df(df, component, plot_option, group):
    """Generates plot depending on selected options"""

    if plot_option == "Promedio Horario por Día de la Semana":
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

    elif plot_option == "Promedio Horario por Mes":
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
    
    elif plot_option == 'Semanal':
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


@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)
def plot_generation(df, plot_option, component):
    """Generates area plot depending on selected options"""

    if plot_option == "Promedio Horario por Día de la Semana":
        fig = px.area(
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

    elif plot_option == "Promedio Horario por Mes":
        fig = px.area(
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
    
    elif plot_option == 'Semanal':
    
        fig = px.area(
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

    else:
        fig = px.area(
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

@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)
def plot_generation_pie(df, component = "Energía [MWh]"):
    """Plot generation gonut plot with total energy in the middle"""

    total_energy = f"""Total de Energía:<br>{round(df["Energía [MWh]"].sum()/1000000,2)} TWh"""

    fig = px.pie(df, values=component, names="Nodo-Mercado", hole=0.8)

    # Add annotations in the center of the donut
    fig.update_layout(
    annotations=[dict(text=total_energy, x=0.5, y=0.5, font_size=20, showarrow=False)])
    
    return fig

@st.cache()
def get_table_download_link(df,dates, component):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """

    component_title = ''
    for s in component:
        if s == '[':
            break
        else:
            component_title += s

    file_name_header = unidecode.unidecode(component_title[:-1]).replace(' ',"_") # Remove special characters ó, í, á, etc from file name
    file_name = f"{file_name_header}_{dates[0].strftime('%Y_%m_%d')}_{dates[1].strftime('%Y_%m_%d')}.csv"
    
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
    selected_data = st.sidebar.radio(label='Selecciona la opción deseada:',options=[*analysis_options], index=0, key=None)
    st.sidebar.write("#")

    selected_subdata = st.sidebar.radio(label=f'Información de {selected_data}:',options=[*analysis_options[selected_data]], index=0, key=None)
    st.sidebar.write("#")
        

    # Dates for date_input creation and delimitation
    max_date = analysis_options[selected_data][selected_subdata]["max_date"]
    min_date = analysis_options[selected_data][selected_subdata]["min_date"]
    start_date = analysis_options[selected_data][selected_subdata]["start_date"]
    end_date = analysis_options[selected_data][selected_subdata]["end_date"]

    # Markets checkboxes options
    market_options = analysis_options[selected_data][selected_subdata]["markets"]

    if selected_data == "Energía Eléctrica":

        # List of nodes for multiselects
        nodes_p, nodes_d = get_nodes_list()
        
        # Nodes multiselect
        if selected_subdata == "Precios":
            selected_nodes_p = st.sidebar.multiselect('NodosP',nodes_p)
            selected_nodes_d = st.sidebar.multiselect('NodosP Distribuidos',nodes_d)
            selected = len(selected_nodes_d+selected_nodes_p)>0 # Is there any node selected?

        elif selected_subdata in ["Cantidades Asignadas","Demanda"]:
            selected_nodes_d = st.sidebar.multiselect('Zonas de Carga',nodes_d)
            selected = len(selected_nodes_d)>0 # Is there any node selected?

        elif selected_subdata == "Generación":
            # Generation info selector, only allowed one
            generation_type = st.sidebar.radio(label="Tipo de información:", options=market_options)
            selected = True

            # MDa can be selected by systems, only one can be selected
            if generation_type == "MDA-Intermitentes":
                system = st.sidebar.selectbox('Sistema',['(SIN) Nacional','(BCA) Baja California','(BCS) Baja California Sur'])[1:4]
            else:
                system = "SEN"

    elif selected_data == "Servicios Conexos":
        
        # Zones multiselect
        selected_zones = st.sidebar.multiselect('Zonas de Reserva',['(SIN) Nacional','(BCA) Baja California','(BCS) Baja California Sur'])
        selected = len(selected_zones)>0 # Is there any zone selected?
        

    # Date picker
    dates = st.sidebar.date_input('Fechas', max_value=max_date, min_value=min_date, value=(start_date, end_date))
    
    # For multiple market selections
    if selected_subdata not in ["Generación"]:
        markets = []
        for market in market_options:
            markets.append(st.sidebar.checkbox(market, value=False))

        check_markets(markets)

    # Check selected options        
    check_dates(dates)
    check_nodes_zones(selected)
    
    start_date, end_date = dates # Unpack date range
    mean_or_sum = analysis_options[selected_data][selected_subdata]["mean_or_sum"]

    # Create urls (API calls) to request using selected options    
    if selected_data == "Energía Eléctrica":
        
        if selected_subdata == "Precios":
            urls = get_nodes_urls(start_date, end_date, selected_nodes_d, selected_nodes_p, *markets)        

        elif selected_subdata in ["Cantidades Asignadas","Demanda"]:
            urls = get_nodes_p_urls(start_date, end_date, selected_nodes_d, *markets)

        elif selected_subdata == "Generación":
            urls = get_generation_urls(start_date, end_date, generation_type, system)

    elif selected_data == "Servicios Conexos":

        if selected_subdata == "Precios":
            urls, zones = get_zones_urls(start_date, end_date, selected_zones, 'PSC', *markets)

        elif selected_subdata == "Cantidades Asignadas":
            urls, zones = get_zones_urls(start_date, end_date, selected_zones, 'CASC', *markets)


    print("Requesting...")
    df_requested = get_info(urls, selected_subdata) # Request created urls

    # Check for error in request
    check_df_requested(df_requested)
    
    # Deal with 23 and 25 hour days
    df_requested_clean = check_for_23_or_25_hours(df_requested)

    # Plotting options
    components = analysis_options[selected_data][selected_subdata]["component"]["options"]
    plot_options = ["Horario", "Diario", "Semanal","Promedio Horario por Día de la Semana", "Promedio Horario por Mes"]
    
    col1, col2, col3 = st.beta_columns([2,2,1])
    component = col1.selectbox(label = analysis_options[selected_data][selected_subdata]["component"]["title"],options=components, index=0, key=None, help=analysis_options[selected_data][selected_subdata]["component"]["help"])
    plot_option = col2.selectbox(analysis_options[selected_data][selected_subdata]["plot_options"]["title"], plot_options, 0, help = analysis_options[selected_data][selected_subdata]["plot_options"]["help"])
    col3.write("####") # Vertical space
    group = col3.checkbox('Año vs Año', value=False, help = "Separa información por año.")    

    with st.spinner(text='Generando gráfica y tabla.'):
        
        print('Plotting...')
        # Create DataFrame for plot and create plot
        df_plot = arange_dataframe_for_plot(df_requested_clean.copy(), plot_option, group, mean_or_sum = mean_or_sum)
        st.plotly_chart(plot_df(df_plot, component, plot_option, group), use_container_width=True)#use_column_width=True

        # Extra plots for generation info
        if selected_subdata == "Generación":
            
            # Aggregation of information and percentage selector
            col1, col2 = st.beta_columns([5,2])
            
            second_plot_option = col1.selectbox(analysis_options[selected_data][selected_subdata]["second_plot_options"]["title"], analysis_options[selected_data][selected_subdata]["second_plot_options"]["options"], 1, help = analysis_options[selected_data][selected_subdata]["second_plot_options"]["help"])
            col2.write("####") # Vertical space
            percentage = col2.checkbox('Porcentajes', value=False, help = "Analiza el porcentaje del total generado.")

            # In case percentage is selected, change column units to '%'
            second_plot_component = "Energía [%]" if percentage else "Energía [MWh]"

            # Plotting generation graph
            df_generation_plot = arange_dataframe_for_plot(df_requested_clean.copy(), second_plot_option, group=False, mean_or_sum = mean_or_sum, percentage = percentage)
            st.plotly_chart(plot_generation(df_generation_plot, second_plot_option, second_plot_component), use_container_width=True)
            
            # Plotting donut graph
            df_generation_plot = arange_dataframe_for_plot(df_requested_clean.copy(), plot_option="Diario", group=False, mean_or_sum = mean_or_sum)
            st.plotly_chart(plot_generation_pie(df_generation_plot), use_container_width=True)

        # Create DataFrame for info table and display info table
        df_info_table = arange_dataframe_for_info_table(df_requested.copy(), component, group)
        st.markdown("""Resumen de datos horarios:""")
        st.dataframe(df_info_table.style.format({col:"{:,}" for col in df_info_table.columns if col not in ['']}).applymap(lambda x: 'color: red' if x < 0 else 'color: black', subset=['Mínimo','Máximo','Promedio','Desviación Est.']))

        st.markdown("") # Vertical space
        st.markdown("")

        # Create dataframe for table and display table
        df_table = arange_dataframe_for_table(df_requested.copy(), component)
        st.markdown("""Primeras 1000 filas de datos:""")
        st.dataframe(df_table.iloc[:1000].style.format({col:"{:,}" for col in df_table.columns if col not in ['Fecha','Hora']}).applymap(lambda x: 'color: red' if x < 0 else 'color: black', subset=[col for col in df_table.columns if col not in ['Fecha','Hora']]))
        
        # Download link
        st.markdown(get_table_download_link(df_table, dates, component), unsafe_allow_html=True)
        
    print('Done')

if __name__ == "__main__":
    main()