"""
Description
   Verify IPv4 and IPv6 ARP.

   If there is any ARP failure, create a list with all the ip addresses that failed ARP and 
   insert the ipv4/ipv6 obj as the first element in the list.

   This code will loop through all created topologies, device groups that are started/enabled, ethernet, for ipv4 and ipv6.

Requirements:
   - Minimum UHD 1.0
   - Python 2.7 and 3+
   - pip install requests
   - pip install ixnetwork_restpy (minimum version 1.0.53)

RestPy Doc:
    https://www.openixia.com/userGuides/restPyDoc

Usage:
   - Enter: python <script>
   
"""

import os, sys, time, traceback
# Import the RestPy module
from ixnetwork_restpy.testplatform.testplatform import TestPlatform
from ixnetwork_restpy.files import Files
from ixnetwork_restpy.assistants.statistics.statviewassistant import StatViewAssistant

uhdIp = '10.36.79.101'
sessionId = 17
username = 'admin'
password = 'admin'

try:
    testPlatform = TestPlatform(uhdIp, log_file_name='restpy.log')

    # Console output verbosity: 'none'|request|request_response
    testPlatform.Trace = 'request_response'

    testPlatform.Authenticate(username, password)
    session = testPlatform.Sessions.find(Id=sessionId)

    uhd = session.Ixnetwork
    
    arpFailedList = []
    for topology in uhd.Topology.find():
        for deviceGroup in topology.DeviceGroup.find():
            # Verify if the device group is enabled/started
            if deviceGroup.Status == 'started':
                for ethernet in deviceGroup.Ethernet.find(): 

                    ipv4Obj = ethernet.Ipv4.find()
                    if ipv4Obj:
                        currentIpObjList = []
                        # Get the index of the arp failure
                        for index, arpFailed in enumerate(ipv4Obj.SessionInfo):
                            if arpFailed == 'resolveMacFailed':
                                # With the index, get the IP address
                                currentIpObjList.append(ipv4Obj.Address.Values[index])

                        if len(currentIpObjList) > 0:
                            currentIpObjList.insert(0, ipv4Obj)
                            arpFailedList.append(currentIpObjList)

                    ipv6Obj = ethernet.Ipv6.find()
                    if ipv6Obj:
                        currentIpObjList = []
                        # Get the index of the arp failure
                        for index, arpFailed in enumerate(ipv6Obj.SessionInfo):
                            if arpFailed == 'resolveMacFailed':
                                # With the index, get the IP address
                                currentIpObjList.append(ipv6Obj.Address.Values[index])

                        if len(currentIpObjList) > 0:
                            currentIpObjList.insert(0, ipv6Obj)
                            arpFailedList.append(currentIpObjList)

    if arpFailedList != []:
        print('\nARP failures:')
        for eachFailure in arpFailedList:
            print('\t', eachFailure)
    
    print('Done')

except Exception as errMsg:
    print('\nError: %s' % traceback.format_exc())
    print('\nrestPy.Exception:', errMsg)
