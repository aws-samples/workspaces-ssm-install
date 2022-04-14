# DISCRIPTION:
#This function is used to create SSM activation code to register onprem instance as a managed instance. In this case the
# powershell logon script calls this API sends the workspace ID as a parameter. The below code checks to makes sure if there is no duplicate
#value for the managed insatnce as stale intry, if so it delete and creates a new activation code

import json
import boto3
import os
import logging
from datetime import datetime,timedelta
logger = logging.getLogger()
logger.setLevel(logging.INFO)
regionparam = os.environ['stackregion']
instancerole = os.environ['instancerole']
ssmclient = boto3.client('ssm',regionparam)
delta = timedelta(hours=1)
expiry = datetime.now() + delta


def index(wuser,wsregion,ipadd):
    wsid = ''
    logger.info("Working with region: %s",wsregion)
    ds = boto3.client('ds', region_name=wsregion)
    
    
    try:
        response = ds.describe_directories()
        logger.info("Directory response: %s",response)
        DirectoryID = []
        for i in range(0,len(response['DirectoryDescriptions'])):
                logger.info('Directory loop %s',i)
                DirectoryID=response['DirectoryDescriptions'][i]['DirectoryId']
                logger.info(DirectoryID)
                wsclient = boto3.client('workspaces', region_name=wsregion)
                try:
                    ws = wsclient.describe_workspaces(
                    DirectoryId = DirectoryID,
                    UserName = wuser)
                    wsid = ws['Workspaces'][0]['WorkspaceId']
                    logger.info("Workspace found %s",ws)
                    if ws['Workspaces'][0]['IpAddress'] == ipadd:
                        logger.info("found the worksapce that matches the IP")
                        break
                except Exception as e:
                    #logging all the others as warning
                    logger.error("failed getting workspace %s",e)

                logger.error("Failed getting assinged workspace")
    except Exception as e:
            #logging all the others as warning
            logger.error("Failed getting directory for region")
            wsid= "workspace_not_found"
            wsregion = "Not_found"
            DirectoryID = "Not_found"
    wsout= {'workspaceID': wsid,
                        'Region': wsregion,
                        'DirectoryID': DirectoryID}
    logger.info('wsout return is %s', wsout) 
    return wsout


def getws(username,wsregion,ipadd):
    logger.info('got the user name as %s',username)
    responseout = index(username,wsregion,ipadd)
    if not responseout['workspaceID']:
       return(
        'WS_NOT_FOUND'
        ) 
    return(responseout)


def lambda_handler(event, context):
    logger.info(event)
    hostname = event["queryStringParameters"]['hostname']
    wsusername = event["queryStringParameters"]['username']
    wsregion = event["queryStringParameters"]['region']
    ipadd = event["queryStringParameters"]['ipadd']
    logger.info('got the hostname as %s', hostname)
    instancelist = ssmclient.get_inventory (
        Filters=[
                {
                    'Key': 'AWS:InstanceInformation.ComputerName',
                    'Values': [
                        hostname,
                    ],
                    'Type': 'Equal'
                },
                            ],
            ResultAttributes=[{'TypeName': 'AWS:InstanceInformation'},])
    logger.info(instancelist)
    for Inst in range(0,len(instancelist['Entities'])):
        logger.info (Inst)
        Instid=instancelist['Entities'][Inst]['Id']
        logger.info (Instid)
        if instancelist['Entities'][Inst]['Data']['AWS:InstanceInformation']['Content'][0]['InstanceStatus'] != 'Terminated' :
                associationlist = []
                associationlist = ssmclient.describe_effective_instance_associations(InstanceId=Instid)
                if associationlist['Associations']:
                    logger.info (associationlist)
                    for j in range(0,len(associationlist['Associations'])):
                        logger.info (j)
                        assoc= associationlist['Associations'][j]['AssociationId']
                        logger.info (assoc)
                        delassoc = ssmclient.delete_association(
                        InstanceId=Instid,
                        AssociationId=assoc
                        )
                try:
                    dereg_inst = ssmclient.deregister_managed_instance(InstanceId=Instid)
                except:
                    logger.error ('unable to remove instance %s',Instid)
        else:
            logger.info('instance is terminated so going to next')
    wsid=getws(wsusername,wsregion,ipadd)
    logger.info('got output from getwsfunction as %s', wsid)
    if  wsid['workspaceID'] == "workspace_not_found":
        return {
            'statusCode': 200,
            'body': json.dumps({'activationcode': 'NULL','ActivationId':'NULL', 
            'wsid':wsid['workspaceID']})}
    else:
        activation= ssmclient.create_activation(
        Description='workspace',
        DefaultInstanceName=hostname,
        IamRole= instancerole,
        RegistrationLimit=1,
        ExpirationDate=expiry
        )
        activationcode = activation['ActivationCode']
        logger.info ('the activation code is %s', activationcode)
        return {
        'statusCode': 200,
        'body': json.dumps({'activationcode': activationcode,'ActivationId':activation['ActivationId'], 
        'wsid':wsid['workspaceID'],'DirectoryID':wsid['DirectoryID']})}