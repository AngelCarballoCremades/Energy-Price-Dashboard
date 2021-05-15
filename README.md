# Energy Price Dashboard

The objective of this project is bringing Mexico's Energy Market  (MEM) information closer to people.

Online dashboard: [www.energia-mexico.org](http://www.energia-mexico.org/) or [Streamlit share](https://share.streamlit.io/angelcarballocremades/energy-price-dashboard/app.py)

## Setup & Run to run locally
1. Install Anacon with python 3.8 or higher (Developed initially in 3.8) (For now Windows only supports streamlit via conda)
2. Open Anaconda Prompt
3. conda create --name venv # Create venv
4. conda activate venv # Activate environment
5. conda install pip # install pip
6. pip install -r requirements.txt # Install required packages
7. streamlit run app.py #Run dashboard file locally
8. Open browser and go to http://localhost:8501/ # Browser should open automatically

## Informatios Source
Information gathered via CENACE web services for [PML](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PML.pdf), [PND](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PEND.pdf), [PSC](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PSC.pdf), [CAEZC](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-CAEZC.pdf) and [CASC](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-CASC.pdf), individual files can be downloaded from here: [PML/PND](https://www.cenace.gob.mx/Paginas/SIM/Reportes/PreciosEnergiaSisMEM.aspx), [PSC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/ServiciosConexosSisMEM.aspx) and [CASC/CAEZC](https://www.cenace.gob.mx/Paginas/SIM/Reportes/CantidadesAsignadasMDA.aspx).


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
        * **Fechas** - Range of date of the information to request. 
            * From February 2017 to Tomorrow. Keep in mind that some NodosP didn't exist in available date range.
            * MTR is available up to today -7 days.
            * MDA is available up to tomorrow.
        * **MDA** and **MTR** markets
            * At least one market must be selected.
    * **Cantidades Asignadas** - Asigned quantities of energy by load zone.
        * **Zona de Carga** 
            * At least one must be selected.
        * **Fechas** - Range of date of the information to request. 
            * From January 2017 to Tomorrow.
            * MDA is available up to tomorrow.
        * **MDA** market
            * For now, only MDA can be selected (MTR will be added soon).
* **Servicios Conexos**
    * **Precios** - Price of electrical reserves.
        * **Zonas de Reserva** 
            * At least one must be selected.
        * **Fechas** - Range of date of the information to request. 
            * From May 2018 to Tomorrow.
            * MTR is available up to today -7 days.
            * MDA is available up to tomorrow.
        * **MDA** and **MTR** markets
            * At least one market must be selected.
    * **Cantidades Asignadas** - Asigned quantities of reserves by zone.
        * **Zonas de Reserva** 
            * At least one must be selected.
        * **Fechas** - Range of date of the information to request. 
            * From May 2018 to Tomorrow.
            * MDA is available up to tomorrow.
        * **MDA** market
            * For now, only MDA can be selected (MTR will be added soon).
    
Once a valid selection is made, information request to CENACE will begin and a progress bar will apear. Depending on the info size, it may take some seconds or up to minutes to finish.

### Central Area
The central area is where graph and plotting options are.

<p align="center">
  <img src=./images/central_top.png/>
  <img src=./images/central_down.png/>
</p>

Here you can choose:
* **Componente de Precio**, **Tipo de Carga** or **Tipo de Reserva** - Energy price component, load type or reserve type to analyze. Depends on selection in sidebar.
    * **Componente de Precio** - Energy component to plot in $/MWh (currency MXN).
    * **Tipo de Carga** - Type of load in MWh.
    * **Tipo de Reserva** - Type of electrical market reserve as defined by CENACE in $/MWh (currency MXN) or MWh.
* **Promedio** or **Valor** - Group info by hour, day or week.
    * **Horario** - Plot info by hourly average.
    * **Diario** - Plot info by daily average (Promedio) or daily sum (Valor).
    * **Semanal** - Plot info by weekly average (Promedio) or daily sum (Valor).
* **Agrupar por** - Plot hourly info by different graph types.
    * **Histórico** - Shows all info requested, no modification made.
    * **Día de la semana** - Plots average of each hour grouped by every day of the week. Takes into account all information requested.
    * **Mes** - Plots average of each hour grouped by month. Takes into account all information requested.
* **Año vs Año** - Makes different lines for every year in selected info.

Every time a selection is made, a new graph will be rendered.

* **Resumen de datos horarios:** - Table showing min, max, average and stdev of hourly values.
* **Primeras 1000 filas de datos:** - Table showing first 1000 rows of hourly info.
* All data can be downloaded via a cvs file with the **Descargar datos** button.

## Future Updates
This are changes or updates planned to be done some time soon.
* Add MTR-MDA button to graph the difference between the two.
* Build a database to gather missing MTR info.

I will always be exploring new visualizations, feel free to ask for something to be added or modified!

Cheers!
