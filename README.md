# Energy Price Dashboard

The objective of this project is bringing Mexico's Energy Market  (MEM) information closer to people.

Online dashboard: [www.energia-mexico.org](http://www.energia-mexico.org/) or [Streamlit share](https://share.streamlit.io/angelcarballocremades/energy-price-dashboard/app.py)

## Setup & Run to run locally
1. Install Anaconda with python 3.8 or higher (Developed initially in 3.8) (For now Windows only supports Streamlit via conda)
2. Open Anaconda Prompt
3. conda create --name venv # Create venv
4. conda activate venv # Activate environment
5. conda install pip # install pip
6. pip install -r requirements.txt # Install required packages
7. streamlit run app.py #Run dashboard file locally
8. Open browser and go to http://localhost:8501/ # Browser should open automatically
9. For now, non-CENACE APIs need to be disabled

## Informatios Source
Information gathered via CENACE web services for [PML](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PML.pdf), [PND](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PEND.pdf), [PSC](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PSC.pdf), [CAEZC](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-CAEZC.pdf) and [CASC](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-CASC.pdf).
Information gathered via private (for now) [APIs from this repo](https://github.com/AngelCarballoCremades/CENACE-RDS-API) for [EDREZC](https://github.com/AngelCarballoCremades/CENACE-RDS-API/tree/main/SWEDREZC), [PDEZC](https://github.com/AngelCarballoCremades/CENACE-RDS-API/tree/main/SWPDEZC), [EGTT](https://github.com/AngelCarballoCremades/CENACE-RDS-API/tree/main/SWEGTT) y [PGI](https://github.com/AngelCarballoCremades/CENACE-RDS-API/tree/main/SWPGI).
Individual files can be downloaded from here: [PML/PND](https://www.cenace.gob.mx/Paginas/SIM/Reportes/PreciosEnergiaSisMEM.aspx), [PSC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/ServiciosConexosSisMEM.aspx), [CASC/CAEZC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/CantidadesAsignadasMDA.aspx), [EDREZC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/EstimacionDemandaReal.aspx) (Por Retiros), [PDEZC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/PronosticosDemanda.aspx) (AUGC/Por Retiros), [EGTT](https://www.cenace.gob.mx/Paginas/SIM/Reportes/EnergiaGeneradaTipoTec.aspx) (Liquidación 0) and [PGI](https://www.cenace.gob.mx/Paginas/SIM/Reportes/H_PronosticosGeneracion.aspx?N=245&opc=divCssPronosticosGen&site=Pron%C3%B3sticos%20de%20Generaci%C3%B3n%20Intermitente&tipoArch=C&tipoUni=ALL&tipo=All&nombrenodop=).


## Dashboard
The dashboard is made with [Streamlit](https://streamlit.io/). 
The app is divided in 2: sidebar and central area.

### Sidebar
The sidebar is where the information to request is selected.

<p align="center">
  <img src=./images/sidebar.png/>
  <img src=./images/sidebar2.png/>
</p>

Here you can choose:
* **Energía eléctrica**
    * **Precios** - Price of electricity.
        * **NodosP** and **NodosP Distribuidos** 
            * At least one must be selected from any type.
        * **Fechas** - Date range of information to request. 
            * From February 2017 to Tomorrow. Keep in mind that some NodosP didn't exist in available date range.
            * MTR is available up to today -7 days.
            * MDA is available up to tomorrow.
        * **MDA** and **MTR** markets
            * At least one market must be selected.
    * **Cantidades Asignadas** - Asigned quantities of energy by load zone.
        * **Zona de Carga** 
            * At least one must be selected.
        * **Fechas** - Date range of information to request. 
            * From January 2017 to Tomorrow.
            * MDA is available up to tomorrow.
        * **MDA** market
            * Must be selected.
    * **Demanda** - Energy consumption by load zone.
        * **Zona de Carga** 
            * At least one must be selected.
        * **Fechas** - Date range of information to request. 
            * MDA from January 2018 to Tomorrow.
            * MTR from January 2018 to Today - 15 days.
                * I'm working on the automatic update.
            * MDA-AUGC from January 10th 2019 to Today - 4 months (aprox).
                * I'm working on the automatic update.
        * **MDA, MDA-AUGC** and **MTR** markets
            * **MDA** - Consumption data from AU-MDA model, energy buying offers (Cantidades Asignadas).
            * **MDA-AUGC** - CENACE's consumption forecast from AU-GC model.
            * **MTR** - Estimated real consumption.
    * **Generación** - Energy generation by technology type.
        * **MDA-Intermitentes** y **MTR**
            * **MDA-Intermitentes** - Renewable energy generation forecast.
            * **MTR** - Energy generation by technology type.
                * **Sistema**
                    * Select one.
        * **Fechas** - Date range of information to request. 
            * MDA-Intermitentes from January 2018 to Tomorrow.
                * I'm working on the automatic update.
            * MTR from January 2018 to Today - 1 or -2 months.
                * I'm working on the automatic update.
* **Servicios Conexos**
    * **Precios** - Price of electrical reserves.
        * **Zonas de Reserva** 
            * At least one must be selected.
        * **Fechas** - Date range of information to request. 
            * From May 2018 to Tomorrow.
            * MTR is available up to today -7 days.
            * MDA is available up to tomorrow.
        * **MDA** and **MTR** markets
            * At least one market must be selected.
    * **Cantidades Asignadas** - Asigned quantities of reserves by zone.
        * **Zonas de Reserva** 
            * At least one must be selected.
        * **Fechas** - Date range of information to request. 
            * From May 2018 to Tomorrow.
            * MDA is available up to tomorrow.
        * **MDA** market
            * Must be selected.
    
Once a valid selection is made, information request to CENACE will begin and a progress bar will apear. Depending on the info size, it may take some seconds or up to minutes to finish.

### Central Area
The central area is where graph and plotting options are.

<p align="center">
  <img src=./images/central_top.png/>
  <img src=./images/central_down.png/>
</p>

Here you can choose:
* **Componente de Precio**, **Tipo de Carga**, **Energía** or **Tipo de Reserva** - Energy price component, load type, total energy or reserve type to analyze. Depends on selection in sidebar.
    * **Componente de Precio** - Energy component to plot in $/MWh (currency MXN).
    * **Tipo de Carga** - Type of load in MWh.
    * **Energía** - Energy in MWh
    * **Tipo de Reserva** - Type of electrical market reserve as defined by CENACE in $/MWh (currency MXN) or MWh.
* **Valores a graficar:** - Group info by hour, day, week, day of week or month.
    * **Horario** - Plot info by hourly average.
    * **Diario** - Plot info by daily average (Promedio) or daily sum (Valor).
    * **Semanal** - Plot info by weekly average (Promedio) or daily sum (Valor).
    * **Promedio Horario por Día de la semana** - Plots average of each hour grouped by every day of the week. Takes into account all information requested.
    * **Promedio Horario por Mes** - Plots average of each hour grouped by month. Takes into account all information requested.
* **Año vs Año** - Makes different lines for every year in selected info.
* **Gráficas de Generación de Energía**
    * **Area plot** - Same functionality as first plot in terms of data agrupation and plotting.
        * **Porcentaje** - Plots energy generated percentage by technology type.
    * **Donut plot** - Percentage of energy generated by technology in selected dates.
        * **Total de Energía** - Sum of generated energy in selected dates.

Every time a selection is made, a new graph will be rendered.

* **Resumen de datos horarios:** - Table showing min, max, average and stdev of hourly values.
* **Primeras 1000 filas de datos:** - Table showing first 1000 rows of hourly info.
* All data can be downloaded via a cvs file with the **Descargar datos** button.

## Future Updates
This are changes or updates planned to be done some time soon.
* Add MTR-MDA button to graph the difference between the two.
* Build a APIs and add info to DB to gather missing info.
* Add generation by technology info.

I will always be exploring new visualizations, feel free to ask for something to be added or modified!

Cheers!
