import json
import requests
import DHCPConf
from objdict import ObjDict
from operator import itemgetter
from elasticsearch import Elasticsearch
from ssl import create_default_context
from thehive4py.api import TheHiveApi
from thehive4py.models import Case, CaseObservable

class DHCPClass:
  def __init__(self, es_api_url1, es_api_url2, es_api_username, es_api_password, thehive_api_url, thehive_api_password, thehive_caseId, thehive_observableId, searchObj):
    self._es_api_url1=es_api_url1
    self._es_api_url2=es_api_url2
    self._es_api_username=es_api_username
    self._es_api_password=es_api_password
    self._thehive_api_url=thehive_api_url
    self._thehive_api_password=thehive_api_password
    self._thehive_caseId=thehive_caseId
    self._thehive_observableId=thehive_observableId
    self.searchObj=searchObj


  def DHCPCall(self, es_api_url1, es_api_url2, es_api_username, es_api_password, thehive_api_url, thehive_api_password, thehive_caseId, thehive_observableId, searchObj):

    context=create_default_context(cafile=DHCPConf.ssl_cert_path)
    client = Elasticsearch([es_api_url1,es_api_url2],http_auth=(es_api_username,es_api_password),scheme="https",port=DHCPConf.port,ssl_context=context)

    #Initialize variables to default values in case they do not exist in searchObj
    startTS=DHCPConf.defaultStart
    endTS=DHCPConf.defaultEnd
    indexName=DHCPConf.defaultCompanyIndex

    #Check the timeStamps in searchObj and if they exist, overwrite the default time-period to the timeperiod in searchObj
    if hasattr(searchObj, 'startTime') and hasattr(searchObj, 'endTime'):
      #Check that the timestamps are set correctly (that startTime is lower than endTime), and if not, switch them around
#      if (searchObj.startTime < searchObj.endTime) and (searchObj.endTime-searchObj.startTime < DHCPConf.max_Timeframe):
      if (searchObj.startTime < searchObj.endTime):
        startTS=searchObj.startTime
        endTS=searchObj.endTime
      else:
        startTS=searchObj.endTime
        endTS=searchObj.startTime

    elif hasattr(searchObj, 'startTime'):
      startTS=searchObj.startTime
      if (startTS+DHCPConf.defaultTimeframe > DHCPConf.defaultEnd):
        endTS=DHCPConf.defaultEnd
      else:
        endTS=startTS+DHCPConf.defaultTimeframe

    elif hasattr(searchObj, 'endTime'):
      endTS=searchObj.endTime
      startTS=endTS-DHCPConf.defaultTimeframe


    #Check that companyName exists, and if it does, set which index to search (otherwise, per default, all DHCP logs will be searched)
    if hasattr(searchObj, 'companyName'):
      indexName=DHCPConf.companyIndex[searchObj.companyName]

    # Collect relevant logs from ElasticSearch...
    rbody={}
    if hasattr(searchObj, 'dataType'):
      if searchObj.dataType in ('ip','fqdn','hostname','other'):
        rbody=DHCPConf.qs_builder(searchObj.dataType,str(searchObj.data),startTS,endTS)

      response=client.search(index=indexName,body=rbody)
      containerObj=ObjDict()

      # Check if ElasticSearch returned any log-entries
      if(response['hits']['total']==0):
        containerObj.Error='Search gave no valid results'
        return containerObj

      # If ElasticSearch returned any log-entries, filter out all irrelevant info, and return the rest as a cronological report
      else:
        hostList=[]
        ipList=[]
        obj1=[]


        for hit in response['hits']['hits']:
          for k,v in hit.items():
            if(k=='_source'):
              obj2={}
              for sk,sv in v.items():
                if(sk=='host'):
                  for ssk,ssv in sv.items():
                    if(ssk=='name'):
                      hostList.append(str(ssv))
                if(sk=='source'):
                  for ssk,ssv in sv.items():
                    if(ssk=='ip'):
                      ipList.append(str(ssv))
                if(sk=='@timestamp' or sk=='host' or sk=='event' or sk=='source'):
                  obj2.update({sk:sv})
              obj1.append(obj2)

        sortedList=sorted(obj1,key=itemgetter('@timestamp'))
        containerObj.result=sortedList

        # Check whether the responder should perform auto-enrichment on the case.
        # If set to false, the responder will be limited to returning a simple cortex report.
        # If set to true, the responder will create new observables, add tags, and edit the messagefield of the observable.
        if hasattr(searchObj, 'autoEnrichment'):
          if(searchObj.autoEnrichment==True):
            if searchObj.dataType=='ip':
              DHCPClass.hiveupdate(thehive_api_url, thehive_api_password, thehive_caseId, thehive_observableId, set(hostList), sortedList, 'hostname')

            if searchObj.dataType in ('other','hostname','fqdn'):
              DHCPClass.hiveupdate(thehive_api_url, thehive_api_password, thehive_caseId, thehive_observableId, set(ipList), sortedList, 'ip')

        # Return the Cortex-Report
        return containerObj



  #Used to update TheHive case via TheHive4py
  def hiveupdate(thehive_api_url, thehive_api_password, thehive_caseId, thehive_observableId, artifactList, sortedList, dt):

    api=TheHiveApi(thehive_api_url,thehive_api_password,cert=DHCPConf.ssl_cert_path)
    curlMsgString=''
    testString=''

    # Build the message-String for the original observable (The one that the responder was run on)
    for entry in sortedList:
      if (dt=='hostname'):
        testString=str(entry['host']['name'] + ':')
      elif(dt=='ip'):
        testString=str(entry['source']['ip'] + ':')

      if(testString not in curlMsgString):
        curlMsgString+='{0} \n\n'.format(testString)
      curlMsgString+='    {0}'.format(DHCPConf.msgStrBuilder(str(entry['event']['action']),
                                                             str(entry['source']['ip']),
                                                             str(entry['host']['hostname']),
                                                             str(entry['@timestamp'])))

    # Build message-String, and create a new observable per entry in artifactList
    for artifact in artifactList:
      msgString=''
      for entry in sortedList:
        if(dt=='hostname'):
          testString=str(entry['host']['name'])
        elif(dt=='ip'):
          testString=str(entry['host']['name'])

        if(testString==artifact):
          msgString+=DHCPConf.msgStrBuilder(str(entry['event']['action']),
                                             str(entry['source']['ip']),
                                             str(entry['host']['hostname']),
                                             str(entry['@timestamp']))

      domain=CaseObservable(dataType=dt,data=str(artifact),tlp=DHCPConf.defaultTlp,ioc=DHCPConf.defaultIoc,tags=DHCPConf.defaultTags,message=msgString)
      response=api.create_case_observable(thehive_caseId,domain)


    # Because it is not possible to edit existing observables through TheHive4py,
    # We edit the original observable (the one that started the DHCP_Responder),
    # through a HTTP.Patch call:
    headers={'Authorization': 'Bearer {0}'.format(thehive_api_password)}
    data={'message':curlMsgString}
    urlString='{0}/api/case/artifact/{1}'.format(thehive_api_url,thehive_observableId)

    response=requests.patch(urlString, headers=headers, data=data, verify=DHCPConf.ssl_cert_path)

