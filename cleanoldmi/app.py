import json
import os
import boto3
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)
region = os.environ['stackregion']
ssm = boto3.client('ssm', region)


def lambda_handler(event, context):
    logger.info(event['detail']['requestParameters']['terminateWorkspaceRequests'])
    listofws = event['detail']['requestParameters']['terminateWorkspaceRequests']
    for each in range(len(listofws)):
        logger.info(listofws[each]['workspaceId'])
        dsmiinst = ssm.describe_instance_information(
                    Filters=[
                        {
                            'Key': 'tag:workspaceID',
                            'Values': [listofws[each]['workspaceId']]
                        },
                    ],
                
                )
        logger.info('output of desc instance with WS Tag is %s',dsmiinst)
        if len(dsmiinst['InstanceInformationList']) == 0:
            logger.info ('not a managed instance')
        else:
            logger.info ('removing managed instance from ssm %s', dsmiinst['InstanceInformationList'][0]['InstanceId'])
            response = ssm.deregister_managed_instance(
                InstanceId=dsmiinst['InstanceInformationList'][0]['InstanceId']
                    )
            logger.info (response)
        
    