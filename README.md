# Energy Price Dashboard

The objective of this project is bringing Mexico's Energy Market  (MEM) information closer to people. The main focus here is **Energy Price** and it's components.

Online dashboard:    *...Not ready yet...*

## Setup & Run to run locally
1. Install Anacon with python 3.8 or higher (Developed initially in 3.8) (Windows only supports streamlit via conda)
2. Open Anaconda Prompt
2. conda create --name venv --file requirements.txt # Create venv and install packages
3. streamlit run app.py #Run dashboard file locally
4. Open browser and go to http://localhost:8501/ # Browser should open automatically

## Informatios Source
Information gathered via CENACE web services for [PML](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PML.pdf) and [PND](https://www.cenace.gob.mx/DocsMEM/2020-01-14%20Manual%20T%C3%A9cnico%20SW-PEND.pdf), individual files can be downloaded from [here](https://www.cenace.gob.mx/Paginas/SIM/Reportes/PreciosEnergiaSisMEM.aspx).


## Dashboard
The dashboard is made with [Streamlit](https://streamlit.io/). 
The app is divided in 2: sidebar and central area.

### Sidebar
The sidebar is where the information to request is placed.

<p align="center">
  <img src=sidebar.png/>
</p>

Here you can choose:
* **NodosP** and **NodosP Distribuidos** 
    * At least one must be selected from any type.
* **Fechas** - Range of date of the information to request. 
    * From February 2017 to Tomorrow. Keep in mind that some NodosP didn't exist in available date range.
    * MTR is available up to today -7 days.
    * MDA is available up to tomorrow.
* **MDA** and **MTR** markets
    * At least one must be selected.

Once a valid selection is made, information request to CENACE will begin and a progress bar will apear. Depending on the dates and NodosP selected, it may take some seconds or up to minutes to finish.

### Central Area
The central area is where graph and plotting options are.

<p align="center">
  <img src=central_top.png/>
  <img src=central_down.png/>
</p>

Here you can choose:
* **Componente de Precio** - Energy component to plot in $/MWh (currency MXN).
    * **Precio Total** - Total energy price.
    * **Componente de Energía** - Energy component.
    * **Componente de Pérdidas** - Losses component.
    * **Componente de Congestión** - Congestion component.
* **Promedio** - Group info by hour, day or week.
    * **Horario** - Plot info by hourly average.
    * **Diario** - Plot info by daily average.
    * **Semanal** - Plot info by weekly average.
* **Agrupar por** - Plot hourly info by different graph types.
    * **Histórico** - Shows all info requested, no modification made.
    * **Día de la semana** - Plots average of each hour grouped by every day of the week. Takes into account all information requested.
        * Only works with **Promedio**-**Horario** selected.
    * **Mes** - Plots average of each hour grouped by month. Takes into account all information requested.
        * Only works with **Promedio**-**Horario** selected.
* **Año vs Año** - Makes different lines for every year in selected info.
    * Only works with **Agrupar por**-**Histórico** selected.

Every time a selection is made, a new graph will be rendered (if selection is valid).
There is a table at the bottom showing original requested data, it only changes whith information requested.
All data can be downloaded via a cvs file with the **Descargar tabla completa** button.

## Future Updates
This are changes or updates planned to be done some time soon.
* Add MTR-MDA button to graph the difference between the two.
* Add table showing avg, std, min, max, and interesting information of data.

I will always be exploring new visualizations, feel free to ask for something to be added or modified!

Cheers!