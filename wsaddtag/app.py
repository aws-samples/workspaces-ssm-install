# This API is invoked to add Tag to the Workspace. The Logon Powershell script after installing 
# and registering the SSM agent on the worksapce, 
# get the managed instanceID and the WS ID and passes that as paramter.
#This script will check the find teh managed instance and add the Tag for it with the WS ID,
# this way we have the Managed instance to WS ID mapping in SSM


import json
import boto3, os
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)

         
def addtagfunc(ssmclient,miid,tagkey,tagvalue):
   try:
     wstag = ssmclient.add_tags_to_resource(
                ResourceType='ManagedInstance',
                ResourceId= miid,
                Tags=[
                    {
                    'Key': tagkey,
                    'Value': tagvalue
                    },
                ]
                )
     
     return ('added_Tag')
   except:
      logger.error ('failed adding tag') 


def lambda_handler(event, context):
    region= os.environ['stackregion']
    ssmclient= boto3.client('ssm', region)
    logger.info(event)
    wsid = event["queryStringParameters"]['wsid']
    miid = event["queryStringParameters"]['miid']
    hostname = event["queryStringParameters"]['hostname']
    username = event["queryStringParameters"]['username']
    directoryid = event["queryStringParameters"]['directoryid']
    region = event["queryStringParameters"]['wsregion']
    baseos= event["queryStringParameters"]['OS']
    nodetype= "AWSWorkspace"
    logger.info ('wsid is %s', wsid)
    addtagfunc(ssmclient,miid,"workspaceID",wsid)
    addtagfunc(ssmclient,miid,"MIID",miid)
    addtagfunc(ssmclient,miid,"username",username)
    addtagfunc(ssmclient,miid,"nodetype",nodetype)
    addtagfunc(ssmclient,miid,"directoryid",directoryid)
    addtagfunc(ssmclient,miid,"wsregion",region)
    addtagfunc(ssmclient,miid,"OS",baseos)
    outval=addtagfunc(ssmclient,miid,"hostname",hostname)
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

