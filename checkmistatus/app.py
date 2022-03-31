import json
import os
import boto3
import botocore.exceptions
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)
region = os.environ['stackregion']
ssmclient = boto3.client('ssm',region)


def lambda_handler(event, context):
    logger.info(event)
    wsid = event["queryStringParameters"]['wsid']
    hostname = event["queryStringParameters"]['hostname']
    logger.info('got the wsid as %s', wsid)
    
    
    try:
        logger.info('getting instance information')
        instancelist = ssmclient.get_inventory(
        Filters = [
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
        logger.info('instance list is %s', instancelist)
    
    
        if len(instancelist['Entities']) == 0 :
            logger.info ( 'The instance list is empty, so the machine thinks its managed but its not')
            pingstat= "not_found" 
            return
            {
            'statusCode': 200,
            'body': json.dumps({'pingstatus': pingstat})
            }
        else:
            for i in range(len(instancelist['Entities'])):
                logger.info('%s count instance is %s', i, instancelist['Entities'][i])
                if instancelist['Entities'][i]['Id'] == wsid and instancelist['Entities'][i]['Data']['AWS:InstanceInformation']['Content'][0]['InstanceStatus'] != 'Terminated':
                    try:
                        logger.info ('%s Instance found in inventory and is not terminated hence continuing')
                        response = ssmclient.get_connection_status(
                                    Target=wsid
                                    )
                        pingstat = response['Status']
                        if  pingstat == 'connected':
                            logger.info("machine is connected %")
                            break
                    except botocore.exceptions.ClientError as error:
                        logger.info (error)
                        logger.error('%s error calling instance info')
                        pingstat= "error"
                    logger.info ('%s got ping status response as', pingstat)
                else :
                    logger.info('%s managed instance terminated')
                    pingstat= "not_found" 


    except botocore.exceptions.ClientError as error: 
        logger.error (error)
        logger.error('error calling instance info')
        pingstat= "error"
    

    return {
    'statusCode': 200,
    'body': json.dumps({'pingstatus': pingstat})
            }