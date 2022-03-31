import json
import os
import boto3
from ldap3 import Server, Connection, NTLM, ALL
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def addtagfunc(ssmclient, miid, tagkey, tagvalue):
    try:
        wstag = ssmclient.add_tags_to_resource(ResourceType='ManagedInstance',
                    ResourceId= miid,
                    Tags=[{'Key': tagkey,
                    'Value': tagvalue },])
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
    grouparray = []
    region = os.environ['stackregion']
    ldapserv = os.environ['ldapserv']
    basedn = os.environ['basedn']
    ldapdomain = os.environ['domain']
    ldapname = os.environ['user']
    ldapuser = ldapdomain +'\\'+ldapname
    ssmclient = boto3.client('ssm', region)
    sec = boto3.client(service_name='secretsmanager',region_name='us-east-1')
    logger.info(event)
    miid = event["queryStringParameters"]['miid']
    username = event["queryStringParameters"]['username']
    logger.info('user is %s', username)
    get_secret_val = sec.get_secret_value(
            SecretId = 'adpasswd'
        )
    removeADgrouptags(ssmclient,miid)
    serchstring = "(&(objectclass=user)(sAMAccountName=" + username + "))"
    server = Server(ldapserv, get_info=ALL)
    conn = Connection(server, user=ldapuser, password=get_secret_val['SecretString'], authentication=NTLM, auto_bind=True)
    conn.search(basedn,serchstring, attributes=['memberOf'])
    response = json.loads(conn.response_to_json())
    logger.info(response)
    groupname = []
    
    
    for item in range(len(response['entries'][0]['attributes']['memberOf'])):
        membervalues = response['entries'][0]['attributes']['memberOf'][item].split(",")[0]
        groupname = membervalues.split('=')
        logger.info(groupname[1])
        tagkey = 'ADGroup_'+ groupname[1]
        outval = addtagfunc(ssmclient,miid,tagkey,'ADGROUP')
        grouparray.append(groupname[1])
    logger.info('list if groups is %s',grouparray)
    
    
    if outval != 'added_Tag':
        return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "issue_Adding_tag"
        }),
            }

    else:
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "added_tags"
            }),
                }


