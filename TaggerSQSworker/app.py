import json
import os
import boto3
import sys,ast
from ldap3 import Server, Connection, NTLM, ALL
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
region = os.environ['stackregion']
ldapserv = os.environ['ldapserv']
basedn = os.environ['basedn']
ldapdomain = os.environ['domain']
ldapname = os.environ['user']
secretname = os.environ['secretname']
ldapuser = ldapdomain +'\\'+ldapname
ssmclient = boto3.client('ssm', region)
sec = boto3.client(service_name='secretsmanager',region_name=region)

def getadgroups(miid,username):
    logger.info('user is %s', username)
    get_secret_val = sec.get_secret_value(
            SecretId = secretname
        )
    serchstring = "(&(objectclass=user)(sAMAccountName=" + username + "))"
    server = Server(ldapserv, get_info=ALL)
    conn = Connection(server, user=ldapuser, password=get_secret_val['SecretString'], authentication=NTLM, auto_bind=True)
    conn.search(basedn,serchstring, attributes=['memberOf'])
    response = json.loads(conn.response_to_json())
    logger.info(response)
    return response
    
                
                
def addtagfunc(ssmclient, miid, tags_list):
    try:
        wstag = ssmclient.add_tags_to_resource(ResourceType='ManagedInstance',
                    ResourceId= miid,
                    Tags= tags_list )
        logger.info(wstag) 
        return('added_Tag')
    except:
       logger.error('failed adding tag') 


def removeADgrouptags(ssmclient,miid):
    removekeyarray=[]
    listtag = ssmclient.list_tags_for_resource(
    ResourceType='ManagedInstance',
    ResourceId = miid)
    removekeyarray = []
    for tags in range(len(listtag['TagList'])):
        if listtag['TagList'][tags]['Key'].startswith('ADGroup'):
            removekeyarray.append(listtag['TagList'][tags]['Key']) 
        else:
            continue
    logger.info('got the tags to remove as %s ',removekeyarray)
    if len(removekeyarray) == 0:
        for eachkey in removekeyarray:
            removekeyaction = ssmclient.remove_tags_from_resource(
                ResourceType='ManagedInstance',
                ResourceId=miid,
                TagKeys=[str(eachkey)]
                )
            logger.info('Removed tags %s',removekeyaction)

def lambda_handler(event, context):
    logger.info('starting worker lambda function')

    logger.info('input event %s',event)
    for record in event['Records']:
        payload = record["body"]
        logger.info('payload is %s', payload)
        payloadlist= ast.literal_eval(payload)
        for username, mangdinst in payloadlist:
            logger.info('user is %s',username)
            logger.info('instance is %s', mangdinst)
            removeADgrouptags(ssmclient,mangdinst)
            groupoutput=getadgroups(mangdinst,username)['entries'][0]['attributes']['memberOf']
            if groupoutput:
                tags_list = []
                
                for item in range(len(groupoutput)):
                    values = {}
                    membervalues = groupoutput[item].split(",")[0]
                    groupname = membervalues.split('=')
                    logger.info(groupname[1])
                    values['Key'] = 'ADGroup_'+ groupname[1]
                    values['Value'] = "ADGROUP"
                    tags_list.append(values)
                    logger.info('list opg group tags to be added is  %s',tags_list)
                addtagfunc(ssmclient, mangdinst,tags_list)
   
           
           
    
    
    # if outval != 'added_Tag':
    #     return {
    #     "statusCode": 200,
    #     "body": json.dumps({
    #         "message": "issue_Adding_tag"
    #     }),
    #         }

    # else:
    #     return {
    #         "statusCode": 200,
    #         "body": json.dumps({
    #             "message": "added_tags"
    #         }),
    #             }


