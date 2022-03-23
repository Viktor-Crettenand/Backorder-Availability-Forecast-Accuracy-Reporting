from numpy.lib.type_check import real
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import pickle
import sys
import argparse
import os

def append_output(yesterday, today, output):
    '''Adds resolved backorders to output'''
    resolved = yesterday.merge(today, on=['sku'], how='left')
    # This creates a DataFrame with both yesterday's and today's columns. 
    # It only keeps rows which sku is in yesterday since it is set to do a left merge
    resolved = resolved[resolved.date.isnull()] # Since the resolved backorders are those that existed yesterday but don't exist today, we filter out the backorders that still exist today
    resolved = resolved[resolved.forecasts.apply(lambda x: bool(x))] # filters out entries where the "forecasts" column of "resolved" contains empty lists because we don't want to keep those
    try:
        resolved = resolved[['date_BO_started', 'forecasts', 'max_value', 'last_date', 'last_forecast', 'date_last_forecast', 'supp_situ_x']]
        # Selects the wanted columns. We want date_x and forecasted_availability_x which come from the "yesterday" DataFrame because that is the day on which the backorder was resolved
        resolved.rename({'last_date': 'last_date_BO', 'supp_situ_x': 'supp_situ'}, axis='columns', inplace=True) # rename the columns
        output = output.append(resolved) # append the dataframe to output
        #print(resolved)
    except:
        pass
    return output

def process(row, num_date_limite = 10):
    '''This function is used on a row of a DataFrame with the columns "date", "forecasted_availability", "forecasts",  to append a tupple to a list if some conditions are met. We want to append the tupple (date_y, forecasted_availability_y) if "forecasted_availability_y" '''
    is_wednesday = row.date.isoweekday() == 3 # planners have to enter data on Tuesdays but the data is reported on the next day i.e. on Wednesday
    is_first_day = row.date == row.date_BO_started # checks if it's the first date of back order
    forecast_different = row.last_forecast != row.forecasted_availability # Note that if both sides are NaN this will return True because NaN isn't equal to NaN. But that's not what we want. If a forecasted availability is NaN repetedly we consider the forecasted availability to stay the same. 
    # To remedy to this we calculate "current_and_previous_forecasted_availability_is_nan" to detect when the forecasted availability was NaN and stayed NaN.
    try:
        current_and_previous_forecasted_availability_is_nan = pd.isnull(row.forecasts[-1][1]) & pd.isnull(row.forecasted_availability) # this row will fail to run if the list in the "forecasts" column is empty" because accessing the first element of an empty list generates an error
    except:
        current_and_previous_forecasted_availability_is_nan = False # if an error is thrown that means that the list in the "forecasts" column is empty. That means row.forecasted_availability is the first forecast. In this case we set to False.
    if (len(row.forecasts)>0) & forecast_different & (len(row.forecasts) < (num_date_limite - 1)) & (not current_and_previous_forecasted_availability_is_nan):
        row.forecasts.append((row.date, row.forecasted_availability, row.supp_situ_y, format(int(row.usd_value), '09d'), format(row.root_y,'02d')))
    elif (len(row.forecasts)<1) & is_wednesday & (not is_first_day):
        row.forecasts.append((row.date, row.forecasted_availability, row.supp_situ_y, format(int(row.usd_value), '09d'), format(row.root_y,'02d')))

def update_backorder_archive(yesterday, today):
    '''Adds new backorders to "yesterday" and removes backorders that are not backorders anymore'''
    merged = yesterday.merge(today, on=['sku'], how='right')
    # This creates a DataFrame with both yesterday's and today's columns.
    # It only keeps rows which sku is in today since it is set to do a right merge 
    merged['date_BO_started'] = merged.apply(lambda row: row.date if pd.isnull(row.date_BO_started) else row.date_BO_started, axis=1)
    # if the backorder already existed yesterday then yesterday date is used, if the backorder didn't exist yesterday then yesterday's date in NaN and the we use today's date, today's date is "date_y", yesterday's date is "date_x"
    merged.loc[merged.forecasts.isnull(),'forecasts'] = merged.forecasts.loc[merged.forecasts.isnull()].apply(lambda x: []) # replace NaN by empty lists in column "forecasts"
    merged.apply(lambda row: process(row), axis=1) # applies the function "process" to each row, "process" has the decision rules of which forecasted availability should be appended to the list in the "forecasts" column
    # This is done because if a backorder has an empty list it means it has no forecasted availability date. We choose to disregard those entries because they are of no interest for our usecase.
    merged['max_value'] = merged.apply(lambda row: max([x for x in [row.max_value, row.usd_value] if not pd.isnull(x)]), axis=1) # create a column with the max of the usd_value between yesterday and today
    merged.loc[:, 'last_date'] = merged.loc[:, 'date']
    merged.loc[:, 'date_last_forecast'] = merged.apply(lambda row: row.date_last_forecast if (row.forecasted_availability == row.last_forecast) else row.date, axis=1) # This is the last date on which the forecast changed.
    merged.loc[:, 'last_forecast'] = merged.loc[:,'forecasted_availability']
    # the row last_date keeps the latest date that the order is on BO
    #print(merged)
    backorder_archive = merged[['date_BO_started', 'forecasts', 'max_value', 'last_date', 'last_forecast', 'date_last_forecast', 'supp_situ_y', 'root_y']] # select the wanted columns
    #print(backorder_archive)
    backorder_archive.rename({'supp_situ_y': 'supp_situ', 'root_y': 'root'}, axis='columns', inplace=True)
    return backorder_archive

def clean(data, hour_minute_second=False):
    data.rename({'SKU': 'sku', 'DataDate': 'date', 'Qty': 'qty', 'Availability': 'forecasted_availability', 'NetUSD': 'usd_value', 'SuppSitu': 'supp_situ', 'RootCause':'root'}, axis='columns', inplace=True)
    data = data[data['qty']>0 & (~data['qty'].isnull())]
    if hour_minute_second:
        data.date = pd.to_datetime(data.date, format='%d/%m/%Y %H:%M:%S')
        data.forecasted_availability = pd.to_datetime(data.forecasted_availability, format='%d/%m/%Y %H:%M:%S')
    else:
        data.date = pd.to_datetime(data.date, format='%d/%m/%Y')
        data.forecasted_availability = pd.to_datetime(data.forecasted_availability, format='%d/%m/%Y')
    data.sort_values('date', inplace=True)
    data.drop_duplicates(inplace=True)
    data.set_index('sku', inplace=True)
    data.loc[:, 'supp_situ'] = data.supp_situ.apply(lambda x: '_' if not (( x=='N' ) or (x=='S') or (x=='X')) else x )
    #print(data)
    return data

def daily_job(path_today, path_output='output.csv', path_backorder_archive='backorder_archive.pkl', path_input='input.csv'):
#def daily_job(path_today, path_output, path_backorder_archive, path_input):
    '''This function updates backorder_archive and output from the data of the next day. The "output" can be given either as a path to a csv file or directly a DataFrame. "backorder_archive" can be given as a path to a pickle file or as a DataFrame.'''
    today = clean(pd.read_csv(path_today), True)
    absolute_dir = os.path.dirname(path_output)
    os.chdir(absolute_dir)
    if isinstance(path_output, str):
        output = pd.read_csv(path_output, index_col='sku', parse_dates=[1, 4, 5, 6, 9]) # , 
        # when importing a .csv file, the format might not be the same as it was before exporting it. 
        # Here the index is set to be the sku and the columns 1, 4, 5, 6, 9 are parsed to make the DataFrame have the same format as before it was exported to csv
    else:
        output = path_output # this allows to use this function directly with objects instead of with paths to files
    if isinstance(path_backorder_archive, str):
        with open(path_backorder_archive, 'rb') as f:
            backorder_archive = pickle.load(f)
    else:
        backorder_archive = path_backorder_archive # this allows to use this function directly with objects instead of with paths to files
    #print(output)
    #print(today)
    if today.date[0] < output.first_date_available.sort_values()[-1]:
        print('Todays dates ('+ str(today.date[0]) + ') is earlier than the latest date in the output (' + str(output.first_date_available.sort_values()[-1]) + \
        '). \n If you rerun the program with past days it will change the output in unwanted ways. \n Would you like to continue?''')
        val = 'something'
        while (val != 'Y') & (val != 'y') & (val != 'N') & (val != 'n'):
            val = input("Type Y to continue and N to abort: ")
            if (val=='N') | (val=='n'):
                sys.exit()
    output = append_output(backorder_archive, today, output)
    backorder_archive = update_backorder_archive(backorder_archive, today)
    output.loc[output.first_date_available.isnull(), 'forecasts'] = output.loc[output.first_date_available.isnull(), 'forecasts'].apply(lambda list_: [(element[0], 'Not a number nor a numberrrrrr', element[2], element[3], element[4]) if pd.isnull(element[1]) else element for element in list_]) 
    # replace NaN by string in list in the "forecasts" column. This is done to make the data processing easier in PowerBI
    output.loc[output.first_date_available.isnull(), 'first_date_available'] = today.date[0] # the rows added to output don't yet have a value for 'first_date_available'. This line assigns it.
    absolute_filename = os.path.basename(path_output)
#    output.to_csv('output.csv')
    output.to_csv(absolute_filename)
    with open('backorder_archive.pkl', 'wb') as f:
        pickle.dump(backorder_archive, f)
    updated_input = update_input(path_today, path_input)
    return output, backorder_archive, updated_input

def update_input(path_today, path_input='input.csv'):
    input_ = pd.read_csv(path_input, index_col='sku', parse_dates=[1, 3])
    today = clean(pd.read_csv(path_today),True)
    updated_input = pd.concat([input_, today], axis=0)
    absolute_filename = os.path.basename(path_input)
#    updated_input.to_csv('input.csv')
    updated_input.to_csv(absolute_filename)
    return updated_input

def historical_job(input_path):
    data = pd.read_csv(input_path)
    data = clean(data)
    #print(data)
    #dates = list(data.date.unique())
    dates = list(map(pd.Timestamp, list(data.date.unique())))
    # -------------------------------this section initializes output and backorder_archive in the right format-------------------------
    output = pd.DataFrame(columns=['date_BO_started', 'forecasts', 'max_value', 'last_date_BO', 'last_forecast', 'date_last_forecast', 'supp_situ', 'RootCause'])
    output.index.name = 'sku'
    backorder_archive = data[(data.date == dates[0]) & (~data.forecasted_availability.isnull())] # initialize backorder archive with the entries made on the first date in the dataset
    backorder_archive.loc[:, 'date_BO_started'] = backorder_archive.loc[:, 'date']
    backorder_archive.loc[:, 'date_last_forecast'] = backorder_archive.loc[:, 'date']
    backorder_archive['forecasts'] = [[] for _ in range(len(backorder_archive.index))]
    # since the first date: "dates[0]" isn't a Tuesday we disregard the forecasted availabilities and initialize with empty lists
    backorder_archive.drop(['qty'], axis=1, inplace=True)
    backorder_archive.rename({'forecasted_availability': 'last_forecast', 'date': 'last_date', 'usd_value': 'max_value', 'SuppSitu': 'supp_situ'}, axis='columns', inplace=True)
    backorder_archive.loc[:, 'supp_situ'] = backorder_archive.supp_situ.apply(lambda x: '_' if (not (( x=='N' ) or (x=='S') or (x=='X'))) else x)
    #print(output)
    #print(backorder_archive)
    # --------------------------------This section loops through all days and updates the output-----------------------------
    print('Working on day 1 of ', str(len(dates)))
    for day_number, current_day in enumerate(dates[1:len(dates)]):
        if (day_number + 1)%100 == 0: print('Working on day ', str(day_number + 1), ' of ', str(len(dates)))
        today = data[data.date == current_day]
        output = append_output(backorder_archive, today, output)
        backorder_archive = update_backorder_archive(backorder_archive, today)
    print('Working on day ', str(len(dates)),' of ', str(len(dates)))
    # ----------------------------------------------------------------------------------------------------------------------------
    print('Creating first date available column')
    output['first_date_available'] = output.last_date_BO.apply(lambda x: dates[list(dates).index(x)+1]) # Adding a column with the first date of availability
    print('Sorting rows according to BO start date')
    output.sort_values('date_BO_started', inplace=True) # Sorting output by date_BO_initiated
    print('Replacing NaN by string "Not a number nor a numberrrrrr"')
    output.loc[:, 'forecasts'] = output.forecasts.apply(lambda list_: [(element[0], 'Not a number nor a numberrrrrr', element[2], element[3], element[4]) if pd.isnull(element[1]) else element for element in list_])
    # output.loc[:, 'forecasts'] = output.forecasts.apply(lambda list_: [(element[0], 'Not a number nor a numberrrrrr') if pd.isnull(element[1]) else element for element in list_]) 
    # replace NaN by string in list in the "forecasts" column. This is done to make the data processing easier in PowerBI
    print('Saving files')
    dir_path = os.getcwd() # get working directory path
    if not os.path.exists(os.path.join(dir_path, 'BO_python_code_output_files')):
        os.makedirs(os.path.join(dir_path, 'BO_python_code_output_files'))
    output.to_csv(os.path.join(dir_path, 'BO_python_code_output_files', 'output.csv')) # create csv file containing the results
    data.to_csv(os.path.join(dir_path, 'BO_python_code_output_files', 'input.csv')) # create csv file containing the cleaned raw data this will be refered to as "input"
    with open(os.path.join(dir_path, 'BO_python_code_output_files', 'backorder_archive.pkl'), 'wb') as f:
        pickle.dump(backorder_archive, f)
    print('Done')


def main(arg):
    print('Program started')
    if arg.historical:
        print(arg)
        print(arg.path_input[0])
        historical_job(arg.path_input[0])
    else:
        for num, path_today in enumerate(arg.path_today):
            daily_job(path_today, arg.path_output, arg.path_backorder_archive, arg.path_input)
            print('Successfully updated output with file ', path_today)
            print(str(num+1), ' run completed out of ', str(len(arg.path_today)))
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Some description')
    parser.add_argument('-o', '--path_output', action='store', metavar='Path_Output', 
                    help='The path of the csv file with the previous output data', default='output.csv')  # nargs=1, removed
    parser.add_argument('-b', '--path_backorder_archive', action='store', metavar='Path_Backorder_Archive', 
                    help='The path of the csv file with the backorder archive data', default='backorder_archive.pkl') # nargs=1, removed
    parser.add_argument('-i', '--path_input', action='store', metavar='Path_Input',
                    help='The path of the csv file with the input data', default='input.csv') # nargs=1, removed
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--historical', action='store_true', help='Flag to run program with historical data')
    group.add_argument('-t', '--path_today', action='store', metavar='Path_Today', nargs='+', help='The path of the csv file with today\'s data', dest='path_today')
    arg = parser.parse_args()
    main(arg)