"""
connectToExistingConfig.py

   Connecting to an existing session.


Requirements:
   - Minimum UHD 1.0
   - Python 2.7 and 3+
   - pip install requests
   - pip install ixnetwork_restpy (minimum version 1.0.54)

RestPy Doc:
    https://www.openixia.github.io/ixnetwork_restpy
"""

import os, sys, time, traceback

# Import the RestPy module
from uhd_restpy import SessionAssistant, Files

uhdIp = '10.36.78.190'
sessionId = 1
username = 'admin'
password = 'admin'

try:
    session = SessionAssistant(IpAddress=uhdIp, RestPort=None, UserName=username, Password=password, 
                               SessionName=None, SessionId=sessionId, ApiKey=None, ClearConfig=False, LogLevel='info')

    uhd = session.Ixnetwork
    
    uhd.info("Connected to Session ID {} - Session Name {}".format(session.Session.Id,session.Session.Name))

except Exception as errMsg:
    print('\nError: %s' % traceback.format_exc())
    print('\nrestPy.Exception:', errMsg)
