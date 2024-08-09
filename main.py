import datetime
import requests
import csv
import threading

def generateMonthCSVFile(days, csvName, url, cookie, securityHeaders):
    current_time = datetime.datetime.now()
    dateFormatCurrent = str(current_time.day) + "/" + str(current_time.month) + "/" + str(current_time.year)

    a_date = datetime.date(current_time.year, current_time.month, current_time.day)
    days = datetime.timedelta(days)

    new_date = a_date - days
    dateFormatNew = str(new_date.day) + "/" + str(new_date.month) + "/" + str(new_date.year)


    req = url + "/Search/ExportEntries?searchrequest=%7B%22DataPagingCriteria%22:%7B%22ResultItemsStartIndex%22:0,%22ResultItemsCount%22:15%7D,%22EvaluatedPersonEntrySearchCriteria%22:%7B%22EntryDateTimeMax%22:%22" + dateFormatCurrent + "%2023:59:59%22,%22EntryDateTimeMin%22:%22" + dateFormatNew + "%22,%22HighLevelResult%22:null,%22PersonEntryMetaDatas%22:[],%22ScanReason%22:null,%22AdditionalDataFilters%22:null,%22DecisionOrigin%22:null,%22KeywordSearchCriteria%22:%7B%22KeywordValue%22:null,%22KeywordValueForReference%22:null%7D,%22AdditionalDataNames%22:[%22BranchCode%22,%22UserName%22,%22CustomerNumber%22,%22IsMarkedForSecondLineReview%22,%22IsCommited%22,%22IsExported%22,%22ManualFaceMatchResult%22,%22AutomatedFaceMatchResult%22,%22LivenessFinalResult%22,%22LivenessFramesNumber%22,%22LivenessActionsNumber%22,%22LivenessActionTimeout%22,%22LivenessNumberOfSelfie%22,%22LivenessJumpsAllowed%22,%22LivenessPassedFrames%22,%22Site%22,%22Location%22]%7D,%22UserId%22:null%7D"

    payload = {}
    headers = {
        'Authorization': cookie,
        'Cookie': securityHeaders
    }
    response = requests.request("GET", req, headers=headers, data=payload)
    if response.status_code != 200:
        with open(csvName, 'w') as out:
            out.write("")
    else:
        with open(csvName, 'w') as out:
            out.write(response.text)

def getCookie(url, username, password):
    url = url + "/token"
    payload = "username=" + username + "&password=" + password + "&grant_type=password&area=scanning"

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    cookie = response.json().get("access_token")

    test = (response.headers.get("Set-Cookie"))

    newTest = test.split(",")

    csrf = ""
    vis = ""
    incap = ""
    token = ""

    for x in newTest:
        if "csrf" in x:
            csrf = x
        if "visid" in x:
            vis = x
        if "incap_ses" in x:
            incap = x
        if (x[1] == 't' and x[2] == 'o') or (x[0] == 't' and x[1] == 'o'):
            token = x

    csrf = csrf.split(';')[0].replace(" ", "")
    vis = vis.split(';')[0].replace(" ", "")
    incap = incap.split(';')[0].replace(" ", "")
    token = token.split(';')[0].replace(" ", "")

    if len(vis) > 1:
        securityHeaders = csrf + ';' + incap + ';' + token + ';' + vis
    else:
        securityHeaders = csrf + ';' + incap + ';' + token


    return [cookie, securityHeaders]

def getJourneyIDsFromCSV():
    with open(csvName, newline='') as csvfile:
        reader = csv.reader(csvfile)

        for row in reader:
            if row:
                journeyIDs.append(row[0])
    journeyIDs.pop(0) #Delete Header

def getFullCSV():
    data_array = []

    # Open the CSV file and read data into the array
    with open(csvName, mode='r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            data_array.append(row)

    return (data_array)

def getRetrieveResponse(journeyID):
    try:
        newURL = url + "/journey/get?journeyID=" + journeyID
        payload = {}
        headers = {
            'Cookie': cookie + '; ' + securityHeaders,
            'Content-Type': 'application/json'
        }
        response = requests.request("GET", newURL, headers=headers, data=payload)
        return response
    except Exception as e:
        print(e)

def process_chunk(data_chunk):
    for row in data_chunk:
        journeyID = row[0]
        responseDetails = getRetrieveResponse(journeyID)
        customerNumber = "null"
        location = "null"

        try:
            if responseDetails.status_code == 200:
                response_json = responseDetails.json()
                additional_data = response_json.get("AdditionalData")
                for item in additional_data:
                    if item.get("Name") == "CustomerNumber":
                        customerNumber = item.get("Value")
                    if item.get("Name") == "Location":
                        location = item.get("Value")
                row[-1] = location
                row.append(customerNumber)
        except Exception as e:
            print(f"An error occurred: {e}")

def chunk_data(data, num_chunks):
    for i in range(0, len(data), num_chunks):
        yield data[i:i + num_chunks]


# MAIN SEQUENCE

days = 1
csvName = "ALC_CSV_OUTPUT_WITH_CUSTOMER_NUMBER.csv"
url = "https://prod.idscan.cloud/idscanenterprisesvc"
user = "ALC_Sup2"
passw = ""

content = getCookie(url, user, passw)
cookie = content[0]
securityHeaders = content[1]
generateMonthCSVFile(days, csvName, url, cookie, securityHeaders)
journeyIDs = []
getJourneyIDsFromCSV()
csvDataFull = getFullCSV()
csvDataFull[0].append("CustomerNumber")
num_threads = 4 # Please only keep to 4 :)
chunks = list(chunk_data(csvDataFull, len(csvDataFull) // num_threads))
threads = []
for i in range(num_threads):
    thread = threading.Thread(target=process_chunk, args=(chunks[i],))
    thread.start()
    threads.append(thread)
for thread in threads:
    thread.join()

print("All tasks completed.")


output_file_path = ('ALC_CSV_OUTPUT_WITH_CUSTOMER_NUMBER_OUTPUT.csv')

with open(output_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    for row in csvDataFull:
        writer.writerow(row)

print(f"Data has been written to {output_file_path}")









