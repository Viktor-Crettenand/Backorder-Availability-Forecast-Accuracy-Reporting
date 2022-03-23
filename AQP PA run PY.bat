REM AQP BO PA daily execution code, VC&CD 2021-06-03
REM
REM
REM process steps
REM 1 call python
REM 2 pass AQP PA backorder.py code from D drive location
REM 3 pass location of input daily CSV file which is exported from BO access database at ~08:20 CET
REM 4 pass location of output Archive CSV file which contains the complete history of all backorder events in scope
REM 5 pass location of holding pkl file which contains all of the WIP backorders, i.e. a backorder which has started but not yet finished; backorders in this list are either added to the Archive and subsequent Tracking files once complete or are discarded if they do not exist on a Wednesday as that is the SLA for SC PA input
REM 6 pass location of output Tracking CSV file which contains the core output data and the Tuple which is the concatenated list of dates and change events
REM
REM
REM this is the code...
py "D:\Python\AQP PA backorder.py" --path_today "\\eubelbfs00\CRMReportingOpenhub_D\ID_EMEA\excel\staging\User Apps\SC_Backorders\BO_AQP_PA_RC.csv" --path_input "\\bdx.com\group\GBR35\SC optimization\Power BI source files\AQP_BO_Archive.csv" --path_backorder_archive "\\bdx.com\group\GBR35\SC optimization\Power BI source files\backorder_archive.pkl" --path_output "\\bdx.com\group\GBR35\SC optimization\Power BI source files\AQP_BO_AvailabilityTracking.csv"