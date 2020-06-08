"""
loadConfigFile.py:

   Tested with two back-2-back UHD ports

   - Connect to the API server
   - Load a saved config file
   - Optional: Assign ports or use the ports that are in the saved config file.
   - Start all protocols
   - Verify all protocols
   - Start traffic 
   - Get Traffic Item
   - Get Flow Statistics stats


Requirements:
   - Minimum UHD 1.0
   - Python 2.7 and 3+
   - pip install requests
   - (optional) pip install tabulate
   - pip install ixnetwork_restpy (minimum version 1.0.53)
   
RestPy Doc:
    https://www.openixia.github.io/ixnetwork_restpy

Usage:
   - Enter: python <script>
"""

import json, sys, os, traceback

try:
    from tabulate import tabulate

    # function to print a sta view in a table format
    def printStat(statView, transpose=True):
        data = statView.Rows.RawData
        columnCaptions=statView.ColumnHeaders
        cheader = columnCaptions[:]
        rows = []
        for row in data:
            tmp = [row[columnCaptions.index(col)] for col in cheader]
            rows.append(tmp[:])

        if transpose:
            # transpose the table
            rows.insert(0,cheader)
            rows = list(zip(*rows))
            cheader = []           

        print(tabulate(rows,headers=cheader,tablefmt="psql"))
except:
    pass

# Import the RestPy module
from ixnetwork_restpy import SessionAssistant, Files

uhdIp = '10.36.79.101'
portList = ['localuhd/1','localuhd/2']
username = 'admin'
password = 'admin'

sessionName = os.path.splitext(os.path.basename(__file__))[0]

# debugMode=True:  Leave the session opened for debugging.
# debugMode=False: Remove the session when the script is done.
debugMode = False

# Forcefully take port ownership if the portList are owned by other users.
forceTakePortOwnership = True

configFile = 'ospf.ixncfg'


try:
    # LogLevel: none, info, warning, request, request_response, all
    session = SessionAssistant(IpAddress=uhdIp, RestPort=None, UserName=username, Password=password, 
                               SessionName=sessionName, SessionId=None, ApiKey=None,
                               ClearConfig=True, LogLevel='info', LogFilename='uhd_restpy.log')

    uhd = session.Ixnetwork
    uhd.info("Session ID/Session Name: {} {}".format(session.Session.Id,session.Session.Name))

    uhd.info('Loading config file: {0}'.format(configFile))
    uhd.LoadConfig(Files(configFile, local_file=True))

    uhd.info('Assigning Ports to vPorts')
    connected_ports = uhd.AssignPorts(portList,uhd.Vport.find(),True)

    uhd.info('Assigning vPorts to topolgy')
    vportxpathlist = ['/vport[%d]' % d for d in range(1,len(portList)+1)]
    topology = [{"vports": vportxpathlist[::2],"xpath": "/topology[1]"},{"vports": vportxpathlist[1::2],"xpath": "/topology[2]"}]
    uhd.ResourceManager.ImportConfig(json.dumps(topology), False)

    uhd.StartAllProtocols(Arg1='sync')

    uhd.info('Verify protocol sessions\n')
    protocolSummary = session.StatViewAssistant('Protocols Summary')
    protocolSummary.CheckCondition('Sessions Not Started', protocolSummary.EQUAL, 0)
    protocolSummary.CheckCondition('Sessions Down', protocolSummary.EQUAL, 0)
    uhd.info('Protocols Summary')
    if 'tabulate' in sys.modules:
        printStat(protocolSummary)
    else:
        uhd.info(protocolSummary)

    # Get the Traffic Item name for getting Traffic Item statistics.
    trafficItem = uhd.Traffic.TrafficItem.find()[0]

    trafficItem.Generate()
    uhd.Traffic.Apply()
    uhd.Traffic.StartStatelessTrafficBlocking()

    trafficItemStatistics = session.StatViewAssistant('Traffic Item Statistics')

    # StatViewAssistant could also filter by REGEX, LESS_THAN, GREATER_THAN, EQUAL. 
    # Examples:
    #    trafficItemStatistics.AddRowFilter('Port Name', trafficItemStatistics.REGEX, '^Port 1$')
    #    trafficItemStatistics.AddRowFilter('Tx Frames', trafficItemStatistics.GREATER_THAN, "5000")

    uhd.info('Traffic Item Statistics')
    if 'tabulate' in sys.modules:
        printStat(trafficItemStatistics)
    else:
        uhd.info(trafficItemStatistics)

    # Get the statistic values
    txFrames = trafficItemStatistics.Rows['Tx Frames']
    rxFrames = trafficItemStatistics.Rows['Rx Frames']
    uhd.info('\nTraffic Item Stats:\n\tTxFrames: {}  RxFrames: {}\n'.format(txFrames, rxFrames))

    uhd.Traffic.StopStatelessTrafficBlocking()

    if debugMode == False:
        session.Session.remove()

except Exception as errMsg:
    print('\n%s' % traceback.format_exc())
    if debugMode and 'session' in locals():
        session.remove()





