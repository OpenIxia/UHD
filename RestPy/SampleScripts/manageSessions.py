"""
manageSessions.py

   Connect to UHD
      - View or delete open sessions

Requirements:
   - Minimum UHD 1.0
   - Python 2.7 and 3+
   - pip install requests
   - pip install ixnetwork_restpy (minimum version 1.0.53)

RestPy Doc:
    https://www.openixia.com/userGuides/restPyDoc
"""

import os, sys, traceback

# Import the RestPy module
from ixnetwork_restpy.testplatform.testplatform import TestPlatform

uhdIp = '10.36.79.101'
apiServerPort = 443
username = 'admin'
password = 'admin'

try:
    testPlatform = TestPlatform(uhdIp, rest_port=apiServerPort)

    # Display debug loggings
    testPlatform.Trace = 'request_response'
    
    # authenticate with username and password
    testPlatform.Authenticate(username, password)

    # Show all open sessions
    for session in testPlatform.Sessions.find():
        print(session)

    # Delete a particular session ID
    #testPlatform.Sessions.find(Id=11).remove()
    
    testPlatform.Sessions.find(Id=1).remove()

except Exception as errMsg:
    print('\n%s' % traceback.format_exc(None, errMsg))
