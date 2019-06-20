# ElasticSearch-Cortex_Responder

This is my attempt at enriching events in TheHive, with information from ElasticSearch.

## Short intro

This responder was made with the purpose of helping correlate ip-addresses with hostnames in a large infrastructure, using dynamic DHCP.

Besides being able to fetch the relevant log-entries form our DHCP-logs in Elastic, This responder is also able to perform automatic enrichment of the event, Meaning, that the responder can create new observables, containing relevant info in the message-field.


###Prerequisites

When implementing this responder the following should be implemented in TheHive:
    Datatype: hostname      (fqdn could be used instead as it already exist in TheHive, but this would require a few small changes to the responder)
    CustomField: customer   (used to define which ElasticSearch-index should be searched.)
    CustomField: startTime  (Used to define the start of the time-period you want logs from. Default is datetime.now - 24hours)
    CustomField: endTime    (Used to define the end of the time-period you want logs from. Default is datetime.now)


Furthermore your DHCP logs should adhere to the Elastic-Common-Schema.








