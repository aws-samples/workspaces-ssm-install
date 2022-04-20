import json
from operator import truediv
import os
import boto3
from botocore.config import Config
import sys,ast
from ldap3 import Server, Connection, NTLM, ALL
import logging
from botoful import Query
config = Config(
   retries = {
      'max_attempts': 20,
      'mode': 'adaptive'
   }
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
region = os.environ['stackregion']
ldapserv = os.environ['ldapserv']
basedn = os.environ['basedn']
ldapdomain = os.environ['domain']
ldapname = os.environ['user']
secretname = os.environ['secretname']
ddbtable= os.environ['ddbtable']
ldapuser = ldapdomain +'\\'+ldapname
ssmclient = boto3.client('ssm', region,config=config)
sec = boto3.client('secretsmanager',region,config=config)
dynamodb = boto3.resource('dynamodb', region,config=config)
table = dynamodb.Table(ddbtable)
querytable = Query(table=ddbtable)

def getadgroups(miid,username):
    logger.info('getting ad group for user %s', username)
    get_secret_val = sec.get_secret_value(
            SecretId = secretname
        )
    serchstring = "(&(objectclass=user)(sAMAccountName=" + username + "))"
    server = Server(ldapserv, get_info=ALL)
    conn = Connection(server, user=ldapuser, password=get_secret_val['SecretString'], authentication=NTLM, auto_bind=True)
    if conn.result["description"] != "success":
        logger.error("Error connecting to the LDAP with the service account")
        return False
    else:
        conn.search(basedn,serchstring, attributes=['memberOf'])
        response = json.loads(conn.response_to_json())
        logger.info(response)
        return response
                               
def addtagfunc(miid, tags_list):
    try:
        wstag = ssmclient.add_tags_to_resource(ResourceType='ManagedInstance',
                    ResourceId= miid,
                    Tags= tags_list )
        logger.info(wstag) 
        return('added_Tag')
    except:
       logger.error('failed adding tag') 

def removeADgrouptags(miid):
    removekeyarray=[]
    listtag = ssmclient.list_tags_for_resource(
    ResourceType='ManagedInstance',
    ResourceId = miid)
    removekeyarray = []
    for tags in range(len(listtag['TagList'])):
        if listtag['TagList'][tags]['Key'].startswith('ADGroup'):
            removekeyarray.append(listtag['TagList'][tags]['Key']) 
        elif listtag['TagList'][tags]['Key'] == 'directoryid':
            directoryid=listtag['TagList'][tags]['Value']
        else:    
            continue
    logger.info('got the tags to remove as %s ',removekeyarray)
    if len(removekeyarray) != 0:
            removekeyaction = ssmclient.remove_tags_from_resource(
                ResourceType='ManagedInstance',
                ResourceId=miid,
                TagKeys=removekeyarray
                )
            logger.info('Removed tags %s',removekeyaction)
    return directoryid

def searchiteminddb(username,directoryid):
    result = querytable.key(Username= username, DirectoryID= directoryid).execute(dynamodb)
    if result.items:
        return True
    else:
        return False
    
def addgrouptagtoddb(username,directoryid,tags_list):
    logger.info ('adding group tag to dynamotable')
    items = {
        'Username': username,
        'DirectoryID': directoryid,
        'ADGroupTags':tags_list
            }
    table.put_item(Item=items)

def addbasetagtoddb(miid,username,directoryid):
    logger.info('Adding Base Tags')
    basetagkeylist=[]
    basetagvaluelist =[]
    listtag = ssmclient.list_tags_for_resource(
    ResourceType='ManagedInstance',
    ResourceId = miid)
    if len(listtag['TagList']) !=0 :
        for tags in range(len(listtag['TagList'])):
            basetagkeylist.append(listtag['TagList'][tags]['Key'])
            basetagvaluelist.append(listtag['TagList'][tags]['Key'])
        basetaglist=dict(zip(basetagkeylist,basetagvaluelist))
        table.update_item(
        Key={
             'Username': username,
            'DirectoryID': directoryid,
            },
        UpdateExpression="set BaseTag = :g",
        ExpressionAttributeValues={
                ':g': basetaglist
            },
        ReturnValues="UPDATED_NEW"
        )
        
            
    
    
    
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
            groupoutput=getadgroups(mangdinst,username)['entries'][0]['attributes']['memberOf']
            if groupoutput:
                directoryid=removeADgrouptags(mangdinst)
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
                addgrouptagresut=addtagfunc( mangdinst,tags_list)
                if addgrouptagresut == 'added_Tag':
                    if searchiteminddb(username,directoryid):
                        logger.info('Instance found in Dynamotable')
                        addgrouptagtoddb(username,directoryid,tags_list)
                    else:
                        logger.info('Instance not found in dynamotable')
                        addbasetagtoddb(username,directoryid,tags_list)
                        addgrouptagtoddb(username,directoryid,tags_list)
                        
                    
   
           
           
    
    
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


