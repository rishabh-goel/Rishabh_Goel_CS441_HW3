import json
import boto3
import re
import datetime

s3 = boto3.client('s3')

GET_RAW_PATH = '/getLogCount'
POST_RAW_PATH = '/postLogCount'
GRPC_RAW_PATH = '/GRPC'
TEST_RAW_PATH = '/test'
regexPattern = re.compile('([a-c][e-g][0-3]|[A-Z][5-9][f-w]){5,15}')

## Method to parse input for GET, POST, GRPC requests
def getInput(methodType, event):
    if methodType=='GET':
        inputTime = event['params']['querystring']['time']
        inputDelta = event['params']['querystring']['delta']
    elif methodType=='POST':
        inputTime = event['body-json']['time']
        inputDelta = event['body-json']['delta']

    #Convert from string to time format
    time = datetime.datetime.strptime(inputTime, '%H:%M:%S')
    delta = datetime.datetime.strptime(inputDelta, '%H:%M:%S')

    #Calculating start time using input time and delta
    st = str(time - delta) + '.000'
    start_time = datetime.datetime.strptime(st, '%H:%M:%S.%f')

    #Calculating end time using input time and delta
    dt1 = datetime.timedelta(hours=time.hour,minutes=time.minute, seconds=time.second)
    dt2 = datetime.timedelta(hours=delta.hour,minutes=delta.minute, seconds=delta.second)
    et = str(dt1 + dt2) + '.000'
    end_time = datetime.datetime.strptime(et, '%H:%M:%S.%f')

    #Reading file from today's date from S3 and convert it to string list
    key = 'LogFileGenerator.'+str(datetime.datetime.today().strftime('%Y-%m-%d'))+'.log'
    print(key)
    data = s3.get_object(Bucket='cs441hw3', Key=key)
    logList = data['Body'].read().decode('utf-8').split('\n')
    logList = list(filter(None, logList))

    return start_time, end_time, logList

## Method to parse input for Test cases
def getTestInput(methodType, event):
    if methodType=='GET':
        inputTime = event['params']['querystring']['time']
        inputDelta = event['params']['querystring']['delta']
    elif methodType=='POST':
        inputTime = event['body-json']['time']
        inputDelta = event['body-json']['delta']

    #Convert from string to time format
    time = datetime.datetime.strptime(inputTime, '%H:%M:%S')
    delta = datetime.datetime.strptime(inputDelta, '%H:%M:%S')

    #Calculating start time using input time and delta
    st = str(time - delta) + '.000'
    start_time = datetime.datetime.strptime(st, '%H:%M:%S.%f')

    #Calculating end time using input time and delta
    dt1 = datetime.timedelta(hours=time.hour,minutes=time.minute, seconds=time.second)
    dt2 = datetime.timedelta(hours=delta.hour,minutes=delta.minute, seconds=delta.second)
    et = str(dt1 + dt2) + '.000'
    end_time = datetime.datetime.strptime(et, '%H:%M:%S.%f')

    #Reading file from S3 and convert it to string list
    key = 'LogFileGenerator.2021-11-02.log'
    print(key)
    data = s3.get_object(Bucket='cs441hw3', Key=key)
    logList = data['Body'].read().decode('utf-8').split('\n')
    logList = list(filter(None, logList))

    return start_time, end_time, logList

## Binary Search program to get indices of start and end time of the required interval from log file
def binarySearch(list, low, high, target):
    if low == high:
        logEntry = list[low].split(" - ")
        logParser = logEntry[0].replace("  ", " ").split(" ")
        logTime = datetime.datetime.strptime(logParser[0], '%H:%M:%S.%f')

        return low if logTime < target else -1

    mid = (high + low) // 2
    logEntry = list[mid].split(" - ")
    logParser = logEntry[0].replace("  ", " ").split(" ")
    logTime = datetime.datetime.strptime(logParser[0], '%H:%M:%S.%f')

    if(target < logTime):
      return binarySearch(list, low, mid, target)

    ret = binarySearch(list, mid+1, high, target)
    return mid if ret == -1 else ret

## Method to extract start and end time of log file
def checkForInterval(logList):
    logEntry = logList[0].split(" - ")
    logParser = logEntry[0].replace("  ", " ").split(" ")
    startLogTime = datetime.datetime.strptime(logParser[0], '%H:%M:%S.%f')

    logEntry = logList[-1].split(" - ")
    print(logList[-1])
    logParser = logEntry[0].replace("  ", " ").split(" ")
    endLogTime = datetime.datetime.strptime(logParser[0], '%H:%M:%S.%f')

    return startLogTime, endLogTime


## Driver method
def lambda_handler(event, context):
    print(event)

    ## GRPC call
    if (event['context']['resource-path'] == GRPC_RAW_PATH):

        start_time, end_time, logList = getInput('GET', event)
        startLogTime, endLogTime = checkForInterval(logList)

        #check if given interval exists in log file
        if(end_time < startLogTime or start_time > endLogTime):
            raise Exception("No Interval found.")
        else:
            return {'Result' : True, 'ResultMsg' : 'Interval Found'}

    ## REST call using GET
    elif(event['context']['resource-path'] == GET_RAW_PATH):

        start_time, end_time, logList = getInput('GET', event)
        startLogTime, endLogTime = checkForInterval(logList)

        #check if given interval exists in log file
        if(end_time < startLogTime or start_time > endLogTime):
            raise Exception("No Interval found.")
        else:
            #calculate number of logs with regex pattern in the given time interval
            start_location = binarySearch(logList, 0, len(logList)-1, start_time) + 1
            end_location = binarySearch(logList, 0, len(logList)-1, end_time)

            print("Start location = " + str(start_location) + ", End Location = " + str(end_location))
            print(logList[start_location])
            print(logList[end_location])

            count = 0

            for idx in range(start_location, end_location+1):
                logEntry = logList[idx].split(" - ")
                if(regexPattern.search(logEntry[1])):
                    count+=1

            return { 'count' : count }

    ## REST call using POST
    elif (event['context']['resource-path'] == POST_RAW_PATH):

        start_time, end_time, logList = getInput('POST', event)
        startLogTime, endLogTime = checkForInterval(logList)

        #check if given interval exists in log file
        if(end_time < startLogTime or start_time > endLogTime):
            raise Exception("No Interval found.")
        else:
            #calculate number of logs with regex pattern in the given time interval
            start_location = binarySearch(logList, 0, len(logList)-1, start_time) + 1
            end_location = binarySearch(logList, 0, len(logList)-1, end_time)

            print("Start location = " + str(start_location) + ", End Location = " + str(end_location))
            print(logList[start_location])
            print(logList[end_location])

            count = 0

            for idx in range(start_location, end_location+1):
                logEntry = logList[idx].split(" - ")
                if(regexPattern.search(logEntry[1])):
                    count+=1

            return { 'count' : count }

    ## REST call for testing using GET
    elif (event['context']['resource-path'] == TEST_RAW_PATH):

        #check if any parameter is missing
        if('time' not in event['params']['querystring'] or 'delta' not in event['params']['querystring']):
            raise Exception("Insufficient Inputs(either Time or Delta)")
        else:
            #calculate number of logs with regex pattern in the given time interval
            start_time, end_time, logList = getTestInput('GET', event)
            startLogTime, endLogTime = checkForInterval(logList)

            if(end_time < startLogTime or start_time > endLogTime):
                raise Exception("No Interval found.")
            else:
                start_location = binarySearch(logList, 0, len(logList)-1, start_time) + 1
                end_location = binarySearch(logList, 0, len(logList)-1, end_time)

                print("Start location = " + str(start_location) + ", End Location = " + str(end_location))
                print(logList[start_location])
                print(logList[end_location])

                count = 0

                for idx in range(start_location, end_location+1):
                    logEntry = logList[idx].split(" - ")
                    if(regexPattern.search(logEntry[1])):
                        count+=1

                return count


