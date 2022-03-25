import json
import os
import boto3
import botocore.exceptions
region = os.environ['stackregion']
ssmclient = boto3.client('ssm', region)

def lambda_handler(event, context):
    print(event)
    wsid = event["queryStringParameters"]['wsid']
    hostname= event["queryStringParameters"]['hostname']
    print ('got the wsid as ',wsid)
    try:
        print('getting instance information')
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
        print('instance list is', instancelist)
        for i in range(len(instancelist['Entities'])):
            print (instancelist['Entities'][i])
            if instancelist['Entities'][i]['Id'] == wsid and instancelist['Entities'][i]['Data']['AWS:InstanceInformation']['Content'][0]['InstanceStatus'] != 'Terminated':
                try:
                    print ('Instance found in inventory and is not terminated hence continuing')
                    response = ssmclient.get_connection_status(
                                Target=wsid
                                )
                    pingstat= response['Status']
                    if  pingstat == 'connected':
                        print("machine is connected")
                        break
                except botocore.exceptions.ClientError as error:
                    print (error)
                    print('error calling instance info')
                    pingstat= "error"
                print ('got ping status response as', pingstat)
            else :
                print('managed instance terminated')
                pingstat= "not_found" 

    except botocore.exceptions.ClientError as error: 
        print (error)
        print('error calling instance info')
        pingstat= "error"
    

    return {
    'statusCode': 200,
    'body': json.dumps({'pingstatus': pingstat})
    }