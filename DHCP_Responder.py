#!/usr/bin/env python3
# encoding: utf-8

from cortexutils.responder import Responder
from DHCPCallScript import DHCPClass
import DHCPConf
from objdict import ObjDict
import json
import traceback
import sys
import ipaddress

class DHCPResponder(Responder):
  def __init__(self):
    Responder.__init__(self)
    self.ES_api_url1=self.get_param('config.ES_api_url1',None,'Missing ElasticSearch API url1')
    self.ES_api_url2=self.get_param('config.ES_api_url2',None,'Missing ElasticSearch API url2')
    self.ES_api_username=self.get_param('config.ES_api_username',None,'Missing ElasticSearch API username')
    self.ES_api_password=self.get_param('config.ES_api_password',None,'Missing ElasticSearch API password')
    self.thehive_api_url=self.get_param('config.TheHive_api_url',None,'Missing thehive API url')
    self.thehive_api_password=self.get_param('config.TheHive_api_password',None,'Missing TheHive API password')
    self.proxies=self.get_param('config.proxy',None)


  def run(self):
    try:
      Responder.run(self)
      es_api_url1=self.get_param('config.ES_api_url1')
      es_api_url2=self.get_param('config.ES_api_url2')
      es_api_username=self.get_param('config.ES_api_username')
      es_api_password=self.get_param('config.ES_api_password')
      thehive_api_url=self.get_param('config.TheHive_api_url')
      thehive_api_password=self.get_param('config.TheHive_api_password')

      thehive_caseId=self.artifact['data']['case']['id']
      thehive_observableId=self.artifact['data']['id']

      data=ObjDict()
      data.dataType=self.artifact['data']['dataType']
      if(self.artifact['data']['data']):
        data.data=self.artifact['data']['data']

      if('customer' in self.artifact['data']['case']['customFields']):
        data.companyName=self.artifact['data']['case']['customFields']['customer']['string']

      if('autoDHCPEnrichment' in self.artifact['data']['case']['customFields']):
        data.autoEnrichment=self.artifact['data']['case']['customFields']['autoDHCPEnrichment']['boolean']

      if('startTime' in self.artifact['data']['case']['customFields']):
        data.startTime=self.artifact['data']['case']['customFields']['startTime']['date']
      if('endTime' in self.artifact['data']['case']['customFields']):
        data.endTime=self.artifact['data']['case']['customFields']['endTime']['date']

      if (self.artifact['data']['dataType']=='ip'):
        #Check if ip is rfc1918-compliant (a private ip)
        if(not ipaddress.ip_address(self.artifact['data']['data']).is_private):
          self.error('The ip-address does not seem to be a valid rfc1918 address...')

      if self.artifact['data']['dataType'] in ('ip','other','hostname','fqdn'):
        DHCPClassInst=DHCPClass(es_api_url1,es_api_url2,es_api_username,es_api_password,thehive_api_url,thehive_api_password,thehive_caseId,thehive_observableId,data)
        DHCPObj=DHCPClassInst.DHCPCall(es_api_url1,es_api_url2,es_api_username,es_api_password,thehive_api_url,thehive_api_password,thehive_caseId,thehive_observableId,data)
        self.report(DHCPObj)

      else:
        self.error('Invalid DataType, or specified IP is not a valid rfc1918 address...')

    except Exception as ex:
      self.error(traceback.format_exc())


  def operations(self,raw):
#    for tag in DHCPConf.defaultTags:
#      return[self.build_operation('AddTagToArtifact',tag='Elastic:DHCP')]
      return[self.build_operation('AddTagToCase',tag='Elastic:DHCP-enriched')]


if __name__=='__main__':
  DHCPResponder().run()

