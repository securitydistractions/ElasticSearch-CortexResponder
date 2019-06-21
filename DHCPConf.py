import datetime

port=9200
ssl_cert_path='<PATH_TO_CERT>'    #<-------SHOULD BE CHANGED TO REFLECT ENVIRONMENT

defaultStartTS=datetime.datetime.now() - datetime.timedelta(days=1)
defaultEndTS=datetime.datetime.now()
defaultStart=int(round(defaultStartTS.timestamp()*1000))
defaultEnd=int(round(defaultEndTS.timestamp()*1000))

#Below value represents the default time-difference we use for elasticsearch searching (The value represents number of seconds in 24 hours).
defaultTimeframe=86400
#Below value represents the maximum time-difference we allow for elasticsearch searching (The value represents number of seconds in a week).
max_Timeframe=604800

defaultCompanyIndex='misc:*-custom-dhcp-*'
companyIndex={
  'Undefined customer (Must be changed)':'misc:*-custom-dhcp-*',    #<-------SHOULD BE CHANGED TO REFLECT ENVIRONMENT
  '<CUSTOMER1>':'misc:<CUSTOMER1>-custom-dhcp-*',    #<-------SHOULD BE CHANGED TO REFLECT ENVIRONMENT
  '<CUSTOMER2>':'misc:<CUSTOMER2>-custom-dhcp-*',    #<-------SHOULD BE CHANGED TO REFLECT ENVIRONMENT
  '<CUSTOMER3>':'misc:<CUSTOMER3>-custom-dhcp-*',    #<-------SHOULD BE CHANGED TO REFLECT ENVIRONMENT
  '<CUSTOMER4>':'misc:<CUSTOMER4>-custom-dhcp-*',    #<-------SHOULD BE CHANGED TO REFLECT ENVIRONMENT
  '<CUSTOMER5>':'misc:<CUSTOMER5>-custom-dhcp-*'}    #<-------SHOULD BE CHANGED TO REFLECT ENVIRONMENT

defaultTlp=2
defaultIoc=False
defaultTags=['DHCPEnriched']

DHCPdatatypeIndex={
  'ip':'source.ip',
  'fqdn':'host.fqdn',
  'hostname':'host.name',
  'other':'host.name'
}

def qs_builder(_datatype,_data,_gte,_lte):
  rbody={"query":{"bool":{"must":[
        {"match_phrase":
          {DHCPdatatypeIndex[_datatype]:
          {"query":_data}}},
        {"bool":{"should":[
          {"match_phrase":{"event.action":"Renew"}},
          {"match_phrase":{"event.action":"Assign"}}],
          "minimum_should_match":1}},
        {"range":{"@timestamp":{"gte":_gte,"lte":_lte,"format":"epoch_millis"}}}]}}}
  return rbody


#-----------------------Experimental DNS Feature.....--------------------------------
#DNSdatatypeIndex={
#  'ip':'log_ip',
#  'fqdn':'log_fqdn',
#  'hostname':'log_host',
#}

#def DNS-qs_builder():
#  rbody={"query":{"bool":{"must":[
#        {"match_phrase":
#        {DNSdatatypeIndex[_datatype]:
#        {"query":_data}}},
#        {"range":{"@timestamp":{"gte":_gte,"lte":_lte,"format":"epoch_millis"}}}]}}}
#  return rbody

def msgStrBuilder(eventAction, sourceIp, hostname, ts):
  msgStr='DHCP-{0} {1} TO {2} AT {3} \n\n'.format(eventAction, sourceIp, hostname, ts)
  return msgStr
