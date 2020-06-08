"""
loadQuickTest.py:

   Tested with two back-2-back UHD ports

   - Connect to UHD API server
   - Loads a saved Quick Test config file.
     This script will run all the created Quick Tests in the saved config file one after another and
     retrieve all of the csv result files with a timestamp on them so they don't overwrite your existing
     result files.

   - Optional: Assign ports or use the ports that are in the saved config file.
   - Start all protocols
   - Verify all protocols
   - Start traffic 
   - Monitor Quick Test 
   - Copy Quick Test CSV result files
   - Copy PDF test result. This only for Windows. 
 

Supports Web Quick Test also. Set applicationType = 'quicktest'

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

import json, sys, os, re, time, datetime, traceback

try:
    from tabulate import tabulate
    # function to print a sta view in a table format
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

# Defaults to ixnrest for UHD.  
# The type for UHD Quick Test is 'quicktest'.  
applicationType = 'quicktest'

debugMode = False

# Forcefully take port ownership if the portList are owned by other users.
forceTakePortOwnership = True

# The full path to the Quick Test config file
configFile = 'ngpfQuickTest2ports_8.50.ixncfg'

# Where to copy the csv and pdf result files in Windows.
windowsDestinationFolder = 'c:\\Results' 

# If running this script on a Linux, where do you want to put the csv and pdf result files
linuxDestinationFolder = os.getcwd()


class Timestamp:
    """
    Get timestamp for the result files.
    """
    def now(self):
        self._get = datetime.datetime.now().strftime('%H%M%S')

    @property
    def get(self):
        return self._get


def addTimestampToFile(rfcTest, filename):
    """
    Add a timestamp to a file to avoid overwriting existing files.
    Replace default PDF file name Test_Report to the Quick Test RFC test name.

    If a path is included, it will yank out the file from the path.
    """
    currentTimestamp = timestamp.get
    if '\\' in filename:
        filename = filename.split('\\')[-1]

    if '/' in filename:
        filename = filename.split('/')[-1]

    newFilename = filename.split('.')[0]
    newFileExtension = filename.split('.')[1]
    newFileWithTimestamp = '{}_{}.{}'.format(rfcTest, currentTimestamp,  newFileExtension)
    return newFileWithTimestamp

    uhdVersion = uhd.Globals.BuildNumber
    match = re.match('([0-9]+)\.[^ ]+ *', ixNetworkVersion)
    ixNetworkVersion = int(match.group(1))

    if ixNetworkVersion >= 8:
        timer = 10
        for counter in range(1,timer+1):
            currentActions = quickTestHandle.Results.CurrentActions

            uhd.info('\n\ngetQuickTestCurrentAction:\n')
            for eachCurrentAction in quickTestHandle.Results.CurrentActions:
                uhd.info('\t{}'.format(eachCurrentAction['arg2']))

            uhd.info('\n')

            if counter < timer and currentActions == []:
                uhd.info('\n\ngetQuickTestCurrentAction is empty. Waiting %s/%s\n\n' % (counter, timer))
                time.sleep(1)
                continue

            if counter < timer and currentActions != []:
                break

            if counter == timer and currentActions == []:
                raise Exception('\n\ngetQuickTestCurrentActions: Has no action')

        return currentActions[-1]['arg2']
    else:
        return quickTestHandle.Results.Progress

def getQuickTestCurrentAction(quickTestHandle):
    """
    Get the Quick Test current progress.
    """
    timer = 10
    for counter in range(1,timer+1):
        currentActions = quickTestHandle.Results.CurrentActions

        uhd.info('\n\ngetQuickTestCurrentAction:\n')
        for eachCurrentAction in quickTestHandle.Results.CurrentActions:
            uhd.info('\t{}'.format(eachCurrentAction['arg2']))

        uhd.info('\n')

        if counter < timer and currentActions == []:
            uhd.info('\n\ngetQuickTestCurrentAction is empty. Waiting %s/%s\n\n' % (counter, timer))
            time.sleep(1)
            continue

        if counter < timer and currentActions != []:
            break

        if counter == timer and currentActions == []:
            raise Exception('\n\ngetQuickTestCurrentActions: Has no action')

    return currentActions[-1]['arg2']


def verifyQuickTestInitialization(quickTestHandle):
    """
    Verify quick test initialization stages.
    """
    for timer in range(1,30+1):
        currentAction = getQuickTestCurrentAction(quickTestHandle)
        uhd.info('\n\nverifyQuickTestInitialization currentAction: {}\n'.format(currentAction))
        if currentAction == 'TestEnded':
            raise Exception('VerifyQuickTestInitialization: QuickTest failed during initialization: {}'.format(quickTestHandle.Results.Status))

        if timer < 30 and currentAction == 'None':
            uhd.info('\n\nverifyQuickTestInitialization CurrentState = %s\n\tWaiting %s/30 seconds to change state\n' % (currentAction, timer))
            time.sleep(1)
            continue
        else:
            break

        if timer == 20 and currentAction == 'None':
            raise Exception('\n\nQuick Test is stuck.')

    successStatusList = ['TransmittingComplete', 'TransmittingFrames', 'WaitingForStats', 'CollectingStats', 'TestEnded']
    quickTestApplyStates = ['InitializingTest', 'ApplyFlowGroups', 'SetupStatisticsCollection']
    ixNetworkVersion = uhd.Globals.BuildNumber
    match = re.match('([0-9]+)\.[^ ]+ *', ixNetworkVersion)
    ixNetworkVersion = int(match.group(1))

    applyQuickTestCounter = 120
    for counter in range(1,applyQuickTestCounter+1):
        currentAction = getQuickTestCurrentAction(quickTestHandle)
        uhd.info('\n\nverifyQuickTestInitialization: CurrentState: %s  Expecting: TransmittingFrames\n\tWaiting %s/%s seconds\n' % (currentAction, counter, applyQuickTestCounter))
     
        if currentAction == 'TestEnded':
            raise Exception('\n\nVerifyQuickTestInitialization: QuickTest failed!!: {}'.format(quickTestHandle.Results.Status))

        if currentAction == None:
            currentAction = 'ApplyingAndInitializing'


        if counter < applyQuickTestCounter and currentAction not in successStatusList:
            time.sleep(1)
            continue

        if counter < applyQuickTestCounter and currentAction in successStatusList:
            uhd.info('\n\nVerifyQuickTestInitialization is done applying configuration and has started transmitting frames\n')
            break


        if counter == applyQuickTestCounter:
            if ixNetworkVersion >= 8 and currentAction not in successStatusList:
                if currentAction == 'ApplyFlowGroups':
                    uhd.info('\n\nVerifyQuickTestInitialization: IxNetwork is stuck on Applying Flow Groups. You need to go to the session to FORCE QUIT it.\n')

                raise Exception('\n\nVerifyQuickTestInitialization is stuck on %s. Waited %s/%s seconds' % (
                        currentAction, counter, applyQuickTestCounter))

            if ixNetworkVersion < 8 and currentAction != 'Trial':
                raise Exception('\n\nVerifyQuickTestInitialization is stuck on %s. Waited %s/%s seconds' % (
                        currentAction, counter, applyQuickTestCounter))

def monitorQuickTestRunningProgress(quickTestHandle, getProgressInterval=10):
    """
    Description
        monitor the Quick Test running progress.

    Parameters
        quickTestHandle: /api/v1/sessions/{id}/ixnetwork/quickTest/rfc2544throughput/{id}
    """
    isRunningBreakFlag = 0
    trafficStartedFlag = 0
    waitForRunningProgressCounter = 0
    counter = 1
    connectionFailureCounter = 0
    maxRetries = 10

    while True:
        # This while loop was implemented because sometimes there could be failure to connect to the 
        # API server.  It could be caused by many various issues not related to IxNetwork.
        # Going to retry doing GETs up to 10 times.
        connectedToApiServerFlag = False

        while True:
            try:
                isRunning = quickTestHandle.Results.IsRunning
                currentRunningProgress = quickTestHandle.Results.Progress
                print('\nmonitorQuickTestRunningProgress: isRuning:', isRunning)
                break
            except:
                uhd.debug('\n\nmonitorQuickTestRunningProgress: Failed to connect to API server {}/{} times\n'.format(connectionFailureCounter, maxRetries))
                if connectionFailureCounter == maxRetries:
                    raise Exception('\n\nmonitorQuickTestRunningProgress: Giving up trying to connecto the the API server after {} attempts\n'.format(maxRetries))

                if connectionFailureCounter <= maxRetries:
                    connectionFailureCounter += 1
                    time.sleep(3)
                    continue

        uhd.info('\n\nmonitorQuickTestRunningProgress: isRunning: {}  CurrentRunningProgress: {}\n'.format(isRunning, currentRunningProgress))

        if isRunning == True:
            if bool(re.match('^Trial.*', currentRunningProgress)) == False:
                if waitForRunningProgressCounter < 40:
                    uhd.info('\n\nmonitorQuickTestRunningProgress: Waiting for trial runs {0}/30 seconds\n'.format(waitForRunningProgressCounter))
                    waitForRunningProgressCounter += 1
                    time.sleep(1)

                if waitForRunningProgressCounter == 40:
                    raise Exception('\n\nmonitorQuickTestRunningProgress: isRunning=True. QT is running, but no quick test iteration stats showing after 40 seconds.')
            else:
                # The test is running fine.  Keep running until isRunning == False.
                trafficStartedFlag = 1
                time.sleep(getProgressInterval)
                continue
        else:
            if trafficStartedFlag == 1:
                # We only care about traffic not running in the beginning.
                # If traffic ran and stopped, then break out.
                uhd.info('\n\nmonitorQuickTestRunningProgress: isRunning=False. Quick Test ran and is complete\n\n')
                return True

            if trafficStartedFlag == 0 and isRunningBreakFlag < 40:
                uhd.info('\n\nmonitorQuickTestRunningProgress: isRunning=False. QT did not run yet. Wait {0}/40 seconds\n\n'.format(isRunningBreakFlag))
                isRunningBreakFlag += 1
                time.sleep(1)
                continue

            if trafficStartedFlag == 0 and isRunningBreakFlag == 40:
                raise Exception('\n\nmonitorQuickTestRunningProgress: Quick Test failed to start:: {}'.format(quickTestHandle.Results.Status))

def copyApiServerFileToLocalLinux(apiServerPathAndFileName, localPath, prependFilename=None, localPathOs='linux', includeTimestamp=False):
    """
    Description
        Copy files from UHD API Server to a local Linux filesystem.
        The source path could be any path in the API server.
        The filename to be copied will remain the same filename unless you set renameDestinationFile to something else.
        You could also append a timestamp for the destination file so the result files won't be overwritten.

    Parameters
        apiServerPathAndFileName: (str): The full path and filename to retrieve from UHD API server.
        localPath: (str): The Linux local filesystem path without the filename. Ex: /home/hgee/Results.
        prependFilename: (str): The rfc test name.  Ex: rfc2544throughput
        localPathOs: (str): The destination's OS.  linux or windows.
        includeTimestamp: (bool):  If False, each time you copy the same file will be overwritten.

    Example:
       apiServerPathAndFileName =  '/root/.local/share/Ixia/IxNetwork/data/result/DP.Rfc2544Tput/10694b39-6a8a-4e70-b1cd-52ec756910c3/Run0005/portMap.csv'
       localPath = '/home/hgee/portMap.csv'
    """
    if '/' in apiServerPathAndFileName:
        fileName = apiServerPathAndFileName.split('/')[-1]

    if '\\' in apiServerPathAndFileName:
        fileName = apiServerPathAndFileName.split('\\')[-1]

    fileName = fileName.replace(' ', '_')

    if includeTimestamp:
        fileName = addTimestampToFile(prependFilename, fileName)

    if localPathOs == 'linux':
        destinationPath = '{}/{}'.format(localPath, fileName)

    if localPathOs == 'windows':
        destinationPath = '{}\\{}'.format(localPath, fileName)

    uhd.info('\nCopying file from API server:{} -> {}'.format(apiServerPathAndFileName, destinationPath))
    session.Session.DownloadFile(apiServerPathAndFileName, destinationPath)

def getQuickTestCsvFiles(quickTestHandle, copyToPath, csvFile='all', rfcTest=None, includeTimestamp=False):
    """
    Description
        Copy Quick Test CSV result files to a specified path on either Windows or Linux.
        Note: Currently only supports copying from Windows.
              Copy from Linux is coming in November.

    quickTestHandle: The Quick Test handle.
    copyToPath: The destination path to copy to.
                If copy to Windows: Ex:  c:\\Results\\Path
                If copy to Linux:   Ex:  /home/user1/results/path

    csvFile: A list of CSV files to get: 'all', one or more CSV files to get:
             AggregateResults.csv, iteration.csv, results.csv, logFile.txt
    rfcTest: Ex: rfc2544throughput
    includeTimestamp: To append a timestamp on the result file.
    """
    resultsPath = quickTestHandle.Results.ResultPath
    uhd.info('\n\ngetQuickTestCsvFiles: %s\n' % resultsPath)

    if csvFile == 'all':
        getCsvFiles = ['AggregateResults.csv', 'iteration.csv', 'results.csv', 'logFile.txt']
    else:
        if type(csvFile) is not list:
            getCsvFiles = [csvFile]
        else:
            getCsvFiles = csvFile

    for eachCsvFile in getCsvFiles:
        linuxSource = resultsPath+'/{0}'.format(eachCsvFile)

        # Copy from UHD API server to Local Linux client filesystem.
        try:
            uhd.info('\n\nCopying file from UHD API server:{} to local Linux: {}\n'.format(linuxSource, eachCsvFile))
            copyApiServerFileToLocalLinux(linuxSource, copyToPath, prependFilename=rfcTest, localPathOs='linux', includeTimestamp=includeTimestamp)
        except Exception as errMsg:
            uhd.warn('\n\ncopyApiServerFileToLocalLinux ERROR: {}\n'.format(errMsg))

def verifyNgpfIsLayer3(topologyName):
    """
    Verify if the configuration has NGPF and if it is, verify if it is layer 3
    in order to know whether to start all protocols or not.
    """
    result = uhd.Topology.find(topologyName).DeviceGroup.find().Ethernet.find().Ipv4.find()
    try:
        print('\n\nTopology isLayer3: {}\n'.format(result.href))
        isLayer3 = True
    except: 
        result = uhd.Topology.find(topologyName).DeviceGroup.find().Ethernet.find().Ipv6.find()
        try:
            print('\n\nTopology isLayer3: {}\n'.format(result.href))
            isLayer3 = True
        except:
            isLayer3 = False
            print('\n\nTopology isLayer3: False\n')

    return isLayer3


try:
    # LogLevel: none, info, warning, request, request_response, all
    session = SessionAssistant(IpAddress=uhdIp, RestPort=None, UserName=username, Password=password, 
                               SessionName=sessionName, SessionId=None, ApiKey=None,
                               ClearConfig=True, LogLevel='info', LogFilename='uhd_restpy.log')

    uhd = session.Ixnetwork
    uhd.info("Session ID/Session Name: {} {}".format(session.Session.Id,session.Session.Name))

    uhd.LoadConfig(Files(configFile, local_file=True))

    # Assign ports
    uhd.info('Assigning Ports')
    connected_ports = uhd.AssignPorts(portList,uhd.Vport.find(),True)

    if verifyNgpfIsLayer3:
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

    # Create a timestamp for test result files.
    # To append a timestamp in the CSV result files so existing result files won't get overwritten.
    timestamp = Timestamp()

    # These are all the RFC tests to search for in the saved config file.
    for rfcTest in [uhd.QuickTest.Rfc2544frameLoss.find(),
                    uhd.QuickTest.Rfc2544throughput.find(),
                    uhd.QuickTest.Rfc2544back2back.find(),
                    ]:

        if not rfcTest:
            # If the loaded QT config file doesn't have rfcTest created, then skip it.
            continue
       
        for quickTestHandle in rfcTest:
            quickTestName = quickTestHandle.Name
            uhd.info('\n\nQuickTestHandle: {}\n'.format(quickTestHandle))
            match = re.search('/api/.*/quickTest/(.*)/[0-9]+', quickTestHandle.href)
            rfc = match.group(1)
            rfcTest = '{}_{}'.format(rfc, quickTestName)
            uhd.info('\n\nExecuting Quick Test: {}\n'.format(rfcTest))

            quickTestHandle.Apply()
            quickTestHandle.Start()
            verifyQuickTestInitialization(quickTestHandle)
            monitorQuickTestRunningProgress(quickTestHandle)

            timestamp.now()

            # Copy CSV  to local linux filesystem
            getQuickTestCsvFiles(quickTestHandle, copyToPath=linuxDestinationFolder, rfcTest=rfcTest, includeTimestamp=True)

            try:
                pdfFile = quickTestHandle.GenerateReport()
                destPdfTestResult = addTimestampToFile(rfcTest=rfcTest, filename=pdfFile)
                uhd.info('Copying PDF results to: {}'.format(linuxDestinationFolder+destPdfTestResult))
                session.Session.DownloadFile(pdfFile, linuxDestinationFolder+'/'+destPdfTestResult)
            except:
                # If using UHD API server, a PDF result file is not supported for all rfc tests.
                uhd.warn('\n\nPDF for {} is not supported\n'.format(rfc))


            # Examples to show how to stop and remove a quick test.
            # Uncomment one or both if you want to use them.
            #quickTestHandle.Stop()
            #quickTestHandle.remove()

    if debugMode == False:
        session.Session.remove()

except Exception as errMsg:
    print('\n%s' % traceback.format_exc())
    if debugMode == False and 'session' in locals():
        session.Session.remove()





