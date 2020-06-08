"""
vxlanNgpf.py:

   Tested with two back-2-back UHD ports

   - Connect to UHDs
   - Configure license server IP
   - Assign ports:
        - If variable forceTakePortOwnership is True, take over the ports if they're owned by another user.
        - If variable forceTakePortOwnership if False, abort test.
   - Configure two Topology Groups: vxLAN/IPv4
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
    https://www.openixia.com/userGuides/restPyDoc

Usage:
   - Enter: python <script>

"""

import json, sys, os, time, traceback

try:
    from tabulate import tabulate
    
    # function to print a sta view in a table format
    def printStat(statView, transpose=True):
        data = statView.Rows.RawData
        columnCaptions = statView.ColumnHeaders
        cheader = columnCaptions[:]
        rows=[]
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
from ixnetwork_restpy import SessionAssistant

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

    uhd.info('\tConfiguring vlanID')
    vlanObj = ethernet1.Vlan.find()[0].VlanId.Increment(start_value=103, step_value=0)

    uhd.info('Configuring IPv4')
    ipv4 = ethernet1.Ipv4.add(Name='Ipv4-1')
    ipv4.Address.Increment(start_value='100.1.1.1', step_value='0.0.0.1')
    ipv4.GatewayIp.Increment(start_value='100.1.3.1', step_value='0.0.0.1')
    ipv4.Prefix.Single(16)

    uhd.info('Configuring VxLAN')
    vxlan1 = ipv4.Vxlan.add(Name='VxLAN-1')
    vxlan1.Vni.Increment(start_value=1008, step_value=2)
    vxlan1.Ipv4_multicast.Increment(start_value='225.8.0.1', step_value='0.0.0.1')

    uhd.info('Create Device Group for VxLAN')
    vxlanDeviceGroup1 = deviceGroup1.DeviceGroup.add(Name='VxLAN-DG', Multiplier=1)

    uhd.info('Create Ethernet for VxLAN')
    vxlanEthernet1 = vxlanDeviceGroup1.Ethernet.add(Name='VxLAN-Ethernet')
    vxlanEthernet1.Mac.Increment(start_value='00:01:11:00:00:001', step_value='00:00:00:00:00:01')
    vxlanEthernet1.EnableVlans.Single(True)

    vxlanEthernet1.Vlan.find()[0].VlanId.Increment(start_value=101, step_value=0)

    uhd.info('Create IPv4 for VxLAN')
    vxlanIpv4 = vxlanEthernet1.Ipv4.add(Name='VxLAN-IPv4')
    vxlanIpv4.Address.Increment(start_value='10.1.1.1', step_value='0.0.0.0')
    vxlanIpv4.GatewayIp.Increment(start_value='10.1.3.1', step_value='0.0.0.0')
    vxlanIpv4.Prefix.Single(16)
    vxlanIpv4.ResolveGateway.Single(True)

    uhd.info('Creating Topology Group 2')
    # assignPorts() has created a list of vports based on the amount of your portList.
    topology2 = uhd.Topology.add(Name='Topo2', Vports=uhd.Vport.find(Name='^Port_2$'))
    deviceGroup2 = topology2.DeviceGroup.add(Name='MyDG2', Multiplier='1')

    ethernet2 = deviceGroup2.Ethernet.add(Name='Eth2')
    ethernet2.Mac.Increment(start_value='00:01:01:02:00:01', step_value='00:00:00:00:00:01')
    ethernet2.EnableVlans.Single(True)

    uhd.info('Configuring vlanID')
    vlanObj = ethernet2.Vlan.find()[0].VlanId.Increment(start_value=103, step_value=0)

    uhd.info('Configuring IPv4')
    ipv4 = ethernet2.Ipv4.add(Name='Ipv4-2')
    ipv4.Address.Increment(start_value='100.1.3.1', step_value='0.0.0.1')
    ipv4.GatewayIp.Increment(start_value='100.1.1.1', step_value='0.0.0.1')
    ipv4.Prefix.Single(24)

    uhd.info('Configuring VxLAN')
    vxlan2 = ipv4.Vxlan.add(Name='VxLAN-2')
    vxlan2.Vni.Increment(start_value=1008, step_value=1)
    vxlan2.Ipv4_multicast.Increment(start_value='225.8.0.1', step_value='0.0.0.0')

    uhd.info('Create Device Group for VxLAN')
    vxlanDeviceGroup2 = deviceGroup2.DeviceGroup.add(Name='VxLAN-DG', Multiplier=1)

    uhd.info('Create Ethernet for VxLAN')
    vxlanEthernet2 = vxlanDeviceGroup2.Ethernet.add(Name='VxLAN-Ethernet')
    vxlanEthernet2.Mac.Increment(start_value='00:01:22:00:00:001', step_value='00:00:00:00:00:01')
    vxlanEthernet2.EnableVlans.Single(True)

    vxlanEthernet2.Vlan.find()[0].VlanId.Increment(start_value=101, step_value=0)

    uhd.info('Create IPv4 for VxLAN')
    vxlanIpv4 = vxlanEthernet2.Ipv4.add(Name='VxLAN-IPv4-2')
    vxlanIpv4.Address.Increment(start_value='10.1.3.1', step_value='0.0.0.0')
    vxlanIpv4.GatewayIp.Increment(start_value='10.1.1.1', step_value='0.0.0.0')
    vxlanIpv4.Prefix.Single(16)
    vxlanIpv4.ResolveGateway.Single(True)

    uhd.StartAllProtocols(Arg1='sync')

    uhd.info('Verify protocol sessions')
    protocolSummary = session.StatViewAssistant('Protocols Summary')
    protocolSummary.CheckCondition('Sessions Not Started', protocolSummary.EQUAL, 0)
    protocolSummary.CheckCondition('Sessions Down', protocolSummary.EQUAL, 0)
    uhd.info('Protocols Summary')
    if 'tabulate' in sys.modules:
        printStat(protocolSummary)
    else:
        uhd.info(protocolSummary)

    uhd.info('Create Traffic Item')
    trafficItem = uhd.Traffic.TrafficItem.add(Name='VxLAN traffic', BiDirectional=False, TrafficType='ipv4')

    uhd.info('Add flow group')
    trafficItem.EndpointSet.add(Sources=topology1, Destinations=topology2)

    # Note: A Traffic Item could have multiple EndpointSets (Flow groups).
    #       Therefore, ConfigElement is a list.
    uhd.info('\tConfiguring config elements')
    configElement = trafficItem.ConfigElement.find()[0]
    configElement.FrameRate.update(Type='percentLineRate', Rate=50)
    configElement.TransmissionControl.update(Type='fixedFrameCount', FrameCount=10000)
    configElement.FrameRateDistribution.PortDistribution = 'splitRateEvenly'
    configElement.FrameSize.FixedSize = 128
    trafficItem.Tracking.find()[0].TrackBy = ['flowGroup0']

    trafficItem.Generate()
    uhd.Traffic.Apply()
    uhd.Traffic.Start()

    flowStatistics = session.StatViewAssistant('Flow Statistics')

    # StatViewAssistant could also filter by regex, LESS_THAN, GREATER_THAN, EQUAL. 
    # Examples:
    #    flowStatistics.AddRowFilter('Port Name', flowStatistics.REGEX, '^Port 1$')
    #    flowStatistics.AddRowFilter('Tx Frames', flowStatistics.LESS_THAN, "50000")

    uhd.info('Flow Statistics')
    if 'tabulate' in sys.modules:
        printStat(flowStatistics)
    else:
        uhd.info(flowStatistics)

    if debugMode == False:
        session.Session.remove()

except Exception as errMsg:
    print('\n%s' % traceback.format_exc())
    if debugMode == False and 'session' in locals():
        session.Session.remove()



