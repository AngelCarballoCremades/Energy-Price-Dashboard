import os
import sys
import time
import pandas as pd
import json
from datetime import date, timedelta
from requests_futures.sessions import FuturesSession
from concurrent.futures import as_completed


# Data and system to be downloaded
systems = ['BCA','BCS','SIN']
node_types = ['PND','PML']
markets = ['MDA','MTR']

# APIs url
url_frame = {'PND':'https://ws01.cenace.gob.mx:8082/SWPEND/SIM/',
             'PML':'https://ws01.cenace.gob.mx:8082/SWPML/SIM/'} # Agregar al final los parámetros un '/'


# def get_unique_nodes(cursor, system, node_type, market = 'MTR'):

#     table_name = '{}_{}_{}'.format(system, node_type, market)

#     if node_type == 'PML':
#         node_column = 'clave_nodo'
#     elif node_type == 'PND':
#         node_column = 'zona_de_carga'

#     cursor.execute("""SELECT {} FROM {}
#             WHERE fecha = (SELECT MAX(fecha) FROM {}) AND
#             hora = 24;""".format(node_column, table_name, table_name))

#     return cursor.fetchall()


# def get_last_date(cursor, system, node_type, market):

#     cursor.execute("""SELECT MAX(fecha) FROM {}_{}_{};""".format(system, node_type, market))
#     return cursor.fetchall()[0][0]


# def missing_dates(last_date, market):
#     """Returns first date to ask info for depending on df's last date detected and type of market, also returns days of info to be asked for"""
#     today = date.today()

#     start_date = last_date + timedelta(days = 1) # Date to start asking for (last_date plus 1 day)

#     # MDA is available from today +1
#     if market == 'MDA':
#         date_needed = today + timedelta(days = 1)

#     # MTR is available from today -7
#     elif market == 'MTR':
#         date_needed = today - timedelta(days = 7)

#     days = (date_needed - last_date).days # Total days needed to update

#     if days > 0:
#         print(f'Last date on record is {last_date}, there are {days} days missing until {date_needed}.')

#     return days, start_date











def pack_values(df):

    large_list = []
    small_list = []
    for row in df.values.tolist():
        row[0] = f"'{row[0]}'"
        row[1] = f"'{row[1]}'"
        row[2] = f"'{row[2]}'"
        row[4] = f"'{row[4]}'"

        small_list.append(','.join(row))

        if len(small_list) == 1000:
            large_list.append(f"({'),('.join(small_list)})")
            small_list = []


    if not large_list:
        large_list.append(f"({'),('.join(small_list)})")
        small_list = []

    return large_list


# def insert_into_table(cursor, system, node_type, market, values):

#     for i in range(len(values)):
#         print('.', end='')
#         sys.stdout.flush()

#         cursor.execute("""INSERT INTO {}_{}_{} VALUES {};""".format(system.lower(), node_type.lower(), market.lower(), values[i]))

#     print('Done.')



def get_data(nodos_p, nodos_d, mda, mtr, start_date, end_date):

    # conn = pg2.connect(**postgres_password(), database='cenace')
    # cursor = conn.cursor()
    session = FuturesSession(max_workers=20)

    for node_type in node_types:
        for system in systems:

            # print(f'{system}-{node_type}')
            # print('Getting list of nodes...')

            # Node list to upload from sql database
            nodes = get_unique_nodes(cursor, system, node_type)

            # Prepare nodes for API requests
            nodes_packed = pack_nodes(nodes, node_type)

            for market in markets:

                print(f'{market} - Looking for last date...')

                last_date = get_last_date(cursor, system, node_type, market)
                days, start_date = missing_dates(last_date, market)
                dates_packed = pack_dates(days, start_date)

                if len(dates_packed):

                    valid_values = True

                    for date_interval in dates_packed:

                        urls_list = get_urls_to_request(nodes_packed, date_interval, system, node_type, market)

                        print(f'{len(urls_list)} Requests', end='')
                        sys.stdout.flush()

                        futures=[session.get(u) for u in urls_list]

                        dfs = [] # List of missing info data frames

                        for future in as_completed(futures):

                            resp = future.result()
                            json_data = resp.json()
                            valid_values = check_data(json_data, date_interval)

                            if not valid_values:
                                break

                            dfs.append(json_to_dataframe(json_data))
                            print('.', end='')
                            sys.stdout.flush()

                        if not valid_values:
                            break

                        print('Done')

                        df = pd.concat(dfs) # Join downloaded info in one data frame

                        values = pack_values(df)

                        print(f'Uploading data from {date_interval[0]} to {date_interval[1]}', end='')
                        sys.stdout.flush()

                        insert_into_table(cursor, system, node_type, market, values)

                        conn.commit()

                    print(f'{system}-{node_type}-{market} up to date\n')

                #If there are no updates to be made...
                else:
                    print(f'{system}-{node_type}-{market} up to date\n')

    print('.....................DONE.....................')

#     conn.commit()
#     conn.close()

# if __name__ == '__main__':
#     main()