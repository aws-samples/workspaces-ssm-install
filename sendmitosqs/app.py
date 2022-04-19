#import json
import os
import boto3
#import sys
import logging
region = os.environ['stackregion']
SqsQueue= os.environ['SQS']
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ssm = boto3.client('ssm', region)
sqs = boto3.client('sqs',region)
def desc_instance():
    
    logger.info('processing desc_instance')
    marker = None
    while True:
        logger.info('starting while loop')
        paginator = ssm.get_paginator('describe_instance_information')
        response_iterator = paginator.paginate(
                        Filters=[
                            {
                                'Key': 'tag:nodetype',
                                'Values': ['AWSWorkspace']
                            },
                        ],
                           PaginationConfig={
                                            'PageSize': 20,
                                            'StartingToken': marker})  
        instancearray=[]
        
        userarray=[]
       
        for page in response_iterator:
            instuserarray=[]
            for count in range(len(page['InstanceInformationList'])):
                logger.info ('value of count is %s ', count)
                logger.info(page['InstanceInformationList'][count]['InstanceId'])
                instancearray.append(page['InstanceInformationList'][count]['InstanceId'])
                tagresponse = ssm.list_tags_for_resource(
                    ResourceType='ManagedInstance',
                    ResourceId=page['InstanceInformationList'][count]['InstanceId'])
                taglist=tagresponse['TagList']
                for tag in range(len(taglist)):
                    if taglist[tag]['Key'] == 'username':
                        userarray.append(taglist[tag]['Value'])
                        instuserarray.append(tuple([taglist[tag]['Value'],page['InstanceInformationList'][count]['InstanceId']]))
            logger.info('batching to SQS')    
            response = sqs.send_message(
                                QueueUrl=SqsQueue,
                                MessageBody=(str(instuserarray))
                                )
            logger.info(response)        
            try:
                marker = page['NextToken']
            except KeyError:
                return instuserarray
                break

        
                
                
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
    logger.info('starting function')
    desc_instance()
    
    

    
    
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


