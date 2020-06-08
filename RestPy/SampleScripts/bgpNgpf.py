"""
bgpNgpf.py:

   Tested with two back-2-back Ixia ports...

   - Connect to the API server
   - Assign ports:
        - If variable forceTakePortOwnership is True, take over the ports if they're owned by another user.
        - If variable forceTakePortOwnership if False, abort test.
   - Configure two Topology Groups: IPv4/BGP
   - Configure Network Group for each topology for route advertising
   - Configure a Traffic Item
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

import json, sys, os, time, traceback
from ixnetwork_restpy import SessionAssistant

try:
    from tabulate import tabulate

    # function to print a stat view in a table format
    def printStat(statView, transpose=True):
        data = statView.Rows.RawData
        columnCaptions = statView.ColumnHeaders
        cheader = columnCaptions[:]
        rows = []

        for row in data:
            tmp = [row[columnCaptions.index(col)] for col in cheader]
            rows.append(tmp[:])

        if transpose:
            # transpose the table
            rows.insert(0,cheader)
            rows = list(zip(*rows))
            cheader=[]
            
        print(tabulate(rows,headers=cheader,tablefmt="psql"))
except:
    pass

uhdIp = '10.36.79.101'
username = 'admin'
password = 'admin'

portList = ['localuhd/1','localuhd/2']

sessionName = os.path.splitext(os.path.basename(__file__))[0]

# debugMode=True:  Leave the session opened for debugging.
# debugMode=False: Remove the session when the script is done.
debugMode = True

# Forcefully take port ownership if the portList are owned by other users.
forceTakePortOwnership = True

# Test Variables
protocolTimeout = 60

try:
    # LogLevel: none, info, warning, request, request_response, all

    session = SessionAssistant(IpAddress=uhdIp, RestPort=None, UserName=username, Password=password, 
                               SessionName=sessionName, SessionId=None, ApiKey=None,
                               ClearConfig=True, LogLevel='info', LogFilename='uhd_restpy.log')

    uhd = session.Ixnetwork
    uhd.info("Session ID/Session Name: {} {}".format(session.Session.Id,session.Session.Name))

    uhd.info('Adding Required Virtual Ports')
    vports = [ { 'xpath': '/vport[%d]' %i, 'name': 'Port_%d' %i} for i in range(1,len(portList)+1)]
    uhd.ResourceManager.ImportConfig(json.dumps(vports), False)
    
    uhd.info('Assigning Ports')
    connected_ports = uhd.AssignPorts(portList, uhd.Vport.find(), forceTakePortOwnership)
    
    uhd.info('Creating Topology Group 1')
    topology1 = uhd.Topology.add(Name='Topo1', Vports=uhd.Vport.find(Name='^Port_1$'))
    deviceGroup1 = topology1.DeviceGroup.add(Name='DG1', Multiplier='1')
    ethernet1 = deviceGroup1.Ethernet.add(Name='Eth1')
    ethernet1.Mac.Increment(start_value='00:01:01:01:00:01', step_value='00:00:00:00:00:01')
    ethernet1.EnableVlans.Single(True)

    uhd.info('Configuring vlanID')
    vlanObj = ethernet1.Vlan.find()[0].VlanId.Increment(start_value=103, step_value=0)

    uhd.info('Configuring IPv4')
    ipv4 = ethernet1.Ipv4.add(Name='Ipv4')
    ipv4.Address.Increment(start_value='1.1.1.1', step_value='0.0.0.1')
    ipv4.GatewayIp.Increment(start_value='1.1.1.2', step_value='0.0.0.0')

    uhd.info('Configuring BgpIpv4Peer 1')
    bgp1 = ipv4.BgpIpv4Peer.add(Name='Bgp1')
    bgp1.DutIp.Increment(start_value='1.1.1.2', step_value='0.0.0.0')
    bgp1.Type.Single('internal')
    bgp1.LocalAs2Bytes.Increment(start_value=101, step_value=0)

    uhd.info('Configuring Network Group 1')
    networkGroup1 = deviceGroup1.NetworkGroup.add(Name='BGP-Routes1', Multiplier='100')
    ipv4PrefixPool = networkGroup1.Ipv4PrefixPools.add(NumberOfAddresses='1')
    ipv4PrefixPool.NetworkAddress.Increment(start_value='10.10.0.1', step_value='0.0.0.1')
    ipv4PrefixPool.PrefixLength.Single(32)

    uhd.info('Creating Topology Group 2')
    topology2 = uhd.Topology.add(Name='Topo2', Vports=uhd.Vport.find(Name='^Port_2$'))
    deviceGroup2 = topology2.DeviceGroup.add(Name='DG2', Multiplier='1')

    ethernet2 = deviceGroup2.Ethernet.add(Name='Eth2')
    ethernet2.Mac.Increment(start_value='00:01:01:02:00:01', step_value='00:00:00:00:00:01')
    ethernet2.EnableVlans.Single(True)

    uhd.info('Configuring vlanID')
    vlanObj = ethernet2.Vlan.find()[0].VlanId.Increment(start_value=103, step_value=0)

    uhd.info('Configuring IPv4 2')
    ipv4 = ethernet2.Ipv4.add(Name='Ipv4-2')
    ipv4.Address.Increment(start_value='1.1.1.2', step_value='0.0.0.1')
    ipv4.GatewayIp.Increment(start_value='1.1.1.1', step_value='0.0.0.0')

    uhd.info('Configuring BgpIpv4Peer 2')
    bgp2 = ipv4.BgpIpv4Peer.add(Name='Bgp2')
    bgp2.DutIp.Increment(start_value='1.1.1.1', step_value='0.0.0.0')
    bgp2.Type.Single('internal')
    bgp2.LocalAs2Bytes.Increment(start_value=101, step_value=0)

    uhd.info('Configuring Network Group 2')
    networkGroup2 = deviceGroup2.NetworkGroup.add(Name='BGP-Routes2', Multiplier='100')
    ipv4PrefixPool = networkGroup2.Ipv4PrefixPools.add(NumberOfAddresses='1')
    ipv4PrefixPool.NetworkAddress.Increment(start_value='20.20.0.1', step_value='0.0.0.1')
    ipv4PrefixPool.PrefixLength.Single(32)

    uhd.StartAllProtocols(Arg1='sync')
    
    i = 0
    while i < protocolTimeout:
        sessionStatusLists = [protocolObj.refresh().SessionStatus for protocolObj in [bgp1,bgp2]]
        sessionsStatusList = [s for l in sessionStatusLists for s in l]
        if len(set(sessionsStatusList)) == 1 and sessionsStatusList[0] == 'up':
            uhd.info('{} protocol sessions are up'.format(','.join([p.DescriptiveName for p in [bgp1,bgp2]])))
            break

        time.sleep(1)
        i += 1

    if i == protocolTimeout:
        uhd.error('FAIL Session up status not reached in {} secs'.format(protocolTimeout))
        exit()

    uhd.info('Verify protocol sessions\n')
    protocolSummary = session.StatViewAssistant('Protocols Summary')
    protocolSummary.CheckCondition('Sessions Not Started', protocolSummary.EQUAL, 0)
    protocolSummary.CheckCondition('Sessions Down', protocolSummary.EQUAL, 0)
    uhd.info('Protocols Summary')

    if 'tabulate' in sys.modules:
        printStat(protocolSummary)
    else:
        uhd.info(protocolSummary)

    uhd.info('Create Traffic Item')
    trafficItem = uhd.Traffic.TrafficItem.add(Name='BGP Traffic', BiDirectional=False, TrafficType='ipv4')

    uhd.info('Add endpoint flow group')
    trafficItem.EndpointSet.add(Sources=topology1, Destinations=topology2)

    # Note: A Traffic Item could have multiple EndpointSets (Flow groups).
    #       Therefore, ConfigElement is a list.
    uhd.info('Configuring config elements')
    configElement = trafficItem.ConfigElement.find()[0]
    configElement.FrameRate.update(Type='percentLineRate', Rate=50)
    configElement.FrameRateDistribution.PortDistribution = 'splitRateEvenly'
    configElement.FrameSize.FixedSize = 128
    trafficItem.Tracking.find()[0].TrackBy = ['flowGroup0']

    trafficItem.Generate()
    uhd.Traffic.Apply()
    uhd.Traffic.StartStatelessTrafficBlocking()

    flowStatistics = session.StatViewAssistant('Flow Statistics')

    # StatViewAssistant could also filter by REGEX, LESS_THAN, GREATER_THAN, EQUAL. 
    # Examples:
    #    flowStatistics.AddRowFilter('Port Name', flowStatistics.REGEX, '^Port 1$')
    #    flowStatistics.AddRowFilter('Tx Frames', flowStatistics.GREATER_THAN, "5000")
    uhd.info('Flow Statistics')
    if 'tabulate' in sys.modules:
        printStat(flowStatistics)
    else:
        uhd.info(flowStatistics)

    if debugMode == False:
        session.Session.remove()

except Exception as errMsg:
    print('\n%s' % traceback.format_exc(None, errMsg))
    if debugMode == False and 'session' in locals():
        session.Session.remove()




