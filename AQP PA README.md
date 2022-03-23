# Backorder resolution forecast accuracy 

## Summary
This code was created to process backorder data and asses whether the forecasted availability dates for the SKUs on backorder are accurate. It uses raw data to create a table that shows both the forecasted availability communicated to the customer and the true date of availability.

## Content of the project
The following things are needed to use this code:
- raw data in a .csv file having the same layout as the first table bellow (the column names should be identical)
- backorder.py


## What does this code do?
The input is a table like this:


| SKU         | DataDate   | Qty      | Availability | NetUSD |
| ----------- | ---------- |----------| ------------ | ------ |
| 0000EL00004 | 01/03/2021 |59.00     | NaN          | 50.74  |
| 0000EL00287 | 04/03/2021 |21.55     | 26/02/2021   | 394.23 |
| ...         | ...        |...       | ...          | ...    |

Each row corresponds to a day when a sku was on backorder. Availability is the date when the planner thinks the sku will be available again.

The output is a table like this:

| sku         | date_BO_initiated | forecasted_availability | last_date_BO | first_date_available |
| ----------- | ----------------- |------------------------ | ------------ | -------------------- |
| 0000EL00004 | 01/28/2019        |02/01/2019               | 01/28/2019   | 01/29/2019           |
| 0000EL00287 | 01/28/2019        |01/25/2019               | 02/14/2019   | 02/15/2019           |
| ...         | ...               |...                      | ...          | ...                  |

Each row corresponds to a period when a sku was on backorder without interuption from date_BO_initiated to last_date_BO. "forecasted_availability" is the date when the planner thinks the sku will be available again.

## Requirement

Python and the following libraries are needed to run the code:
- pandas
- pickle
- sys
- argparse
- os

## How to use the code?

There is a file backorder.py can be run in two modes :
 1) Using historic data containing entries with multiple dates (note that the program assumes that there is at least one backorder entry on each business day + saturdays)
 2) Updates the output generated in mode 1 using individual files with one day's data in each file

### Mode 1 Running the code for the first time

A command prompt with python and the required libraries installed should be opened in the location of the file . The following command should be run:
python backorder.py --historical -i <path to csv file>
This will create three files "output.csv", "backorder_archive.pkl" and "input.csv" required for mode 2.

### Mode 2 Adding one day of data at a time

To add on day of at a time the following line should be run in a command prompt opened in the same folder as the file backorder.py:
python backorder.py --path_today <path to csv file with data for the next date>
By default the program will use the input.csv, backorder_archive.pkl and output.csv files located in the same folder as backorder.py. If the files have different names or are located elsewhere, the path should be specified thus:
python backorder.py --path_today <path to csv file with data for the next date> --path_input <path to csv file with input data> --path_backorder_archive <path to pkl file with backorder archive> --path_output <path to csv file with output data>
If there are mutliple files with daily data, one can update the output with all of them at once by simply listing them in the following way:
python backorder.py --path_today <path to csv file with data for the next date> <path to 2-nd csv file with daily data > <path to 3-rd csv file with daily data> ... <path to n-th csv file with daily data>


### Expected Behaviour

The expected behaviour is that the code creates/overwrites the following files: "output.csv", "backorder_archive.pkl" and "input.csv"

## Authors

This script was created by Viktor Crettenand (viktor.crettenand@bd.com).