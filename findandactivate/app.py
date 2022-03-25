# DISCRIPTION:
#This function is used to create SSM activation code to register onprem instance as a managed instance. In this case the
# powershell logon script calls this API sends the workspace ID as a parameter. The below code checks to makes sure if there is no duplicate
#value for the managed insatnce as stale intry, if so it delete and creates a new activation code

import json
import boto3
import os
regionparam = os.environ['stackregion']
instancerole = os.environ['instancerole']
ssmclient = boto3.client('ssm',regionparam)

def index(wuser,wsregion,ipadd):
    wsid=''
    #regions = [region['RegionName'] for region in ec2.describe_regions()['Regions']]
    #print(regions)
    #regions = ["us-east-2","us-east-1","us-west-1","us-west-2","ap-south-1","ap-northeast-2","ap-southeast-1","ap-southeast-2","ap-northeast-1","ca-central-1","eu-central-1","eu-west-1","eu-west-2","sa-east-1","us-gov-west-1"]
    #for region in regions:
    print ("Working with region:",wsregion)
    ds = boto3.client('ds', region_name=wsregion)
    try:
        response = ds.describe_directories()
        print ("Directory response:",response)
        DirectoryID=[]
        for i in range(0,len(response['DirectoryDescriptions'])):
                print('Directory loop',i)
                DirectoryID=response['DirectoryDescriptions'][i]['DirectoryId']
                print (DirectoryID)
                wsclient = boto3.client('workspaces', region_name=wsregion)
                try:
                    ws = wsclient.describe_workspaces(
                    DirectoryId= DirectoryID,
                    UserName=wuser)
                    wsid= ws['Workspaces'][0]['WorkspaceId']
                    print ("Workspace found",ws)
                except Exception as e:
                    #logging all the others as warning
                    print ("failed getting workspace",e)
                if ws['Workspaces'][0]['IpAddress'] == ipadd:
                    print ("found the worksapce that matches the IP")
                    break
                print ("Failed getting assinged workspace")        
    except Exception as e:
            #logging all the others as warning
            print ("Failed getting directory for region")
            wsid= "workspace_not_found"
            wsregion = "Not_found"
            DirectoryID = "Not_found"
    wsout= {'workspaceID': wsid,
                        'Region': wsregion,
                        'DirectoryID': DirectoryID}
    print('wsout return is', wsout) 
    return wsout

def getws(username,wsregion,ipadd):
    print(username)
    responseout = index(username,wsregion,ipadd)
    if not responseout['workspaceID']:
       return(
        'WS_NOT_FOUND'
        ) 
    return(responseout)


def lambda_handler(event, context):
    print(event)
    hostname = event["queryStringParameters"]['hostname']
    wsusername = event["queryStringParameters"]['username']
    wsregion = event["queryStringParameters"]['region']
    ipadd = event["queryStringParameters"]['ipadd']
    print ('got the hostname as',hostname)
    instancelist = ssmclient.get_inventory(
        Filters=[
                {
                    'Key': 'AWS:InstanceInformation.ComputerName',
                    'Values': [
                        hostname,
                    ],
                    'Type': 'Equal'
                },
                            ],
            ResultAttributes=[
                {
                    'TypeName': 'AWS:InstanceInformation'
                },
                  ])
    print (instancelist)
    for iw in range(0,len(instancelist['Entities'])):
        print (iw)
        Instid=instancelist['Entities'][iw]['Id']
        print (Instid)
        if instancelist['Entities'][iw]['Data']['AWS:InstanceInformation']['Content'][0]['InstanceStatus'] != 'Terminated' :
                associationlist=[]
                associationlist = ssmclient.describe_effective_instance_associations(
                InstanceId=Instid
                )
                if associationlist['Associations']:
                    print (associationlist)
                    for j in range(0,len(associationlist['Associations'])):
                        print (j)
                        assoc= associationlist['Associations'][j]['AssociationId']
                        print (assoc)
                        delassoc = ssmclient.delete_association(
                        Name='string',
                        InstanceId=Instid,
                        AssociationId=assoc
                        )
                try:
                    dereg_inst = ssmclient.deregister_managed_instance(InstanceId=Instid)
                except:
                    print ('unable to remove instance',Instid)
        else:
            print('instance is terminated so going to next')
    wsid=getws(wsusername,wsregion,ipadd)
    print('got output from getwsfunction as', wsid)
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
        RegistrationLimit=1
        )
        activationcode = activation['ActivationCode']
        print ('the activation code is', activationcode)
        return {
        'statusCode': 200,
        'body': json.dumps({'activationcode': activationcode,'ActivationId':activation['ActivationId'], 
        'wsid':wsid['workspaceID'],'DirectoryID':wsid['DirectoryID']})}