import json
import os
import boto3
from ldap3 import Server, Connection, Tls, NTLM, ALL
from ldap3.extend.microsoft.addMembersToGroups import ad_add_members_to_groups as addUsersInGroups

#secrets = boto3.client('secretsmanager')
#ds = boto3.client('ds')

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
       print ('failed adding tag') 


def lambda_handler(event, context):
    grouparray=[]
    region= os.environ['stackregion']
    ldapserv= os.environ['ldapserv']
    basedn=os.environ['basedn']
    ldapdomain= os.environ['domain']
    ldapname=os.environ['user']
    ldapuser= ldapdomain +'\\'+ldapname
    ssmclient= boto3.client('ssm', region)
    sec = boto3.client(service_name='secretsmanager',region_name='us-east-1')
    print(event)
    miid = event["queryStringParameters"]['miid']
    username = event["queryStringParameters"]['username']
    print ('user is', username)

    get_secret_val = sec.get_secret_value(
            SecretId='adpasswd'
        )

    serchstring ="(&(objectclass=user)(sAMAccountName=" + username + "))"
    server = Server(ldapserv, get_info=ALL)
    conn = Connection(server, user=ldapuser, password=get_secret_val['SecretString'], authentication=NTLM, auto_bind=True)
    conn.search(basedn,serchstring, attributes=['memberOf'])
    response = json.loads(conn.response_to_json())
    print(response)
    w=[]
    for i in range(len(response['entries'][0]['attributes']['memberOf'])):
        a=response['entries'][0]['attributes']['memberOf'][i].split(",")[0]
        w=a.split('=')
        print(w[1])
        outval=addtagfunc(ssmclient,miid,w[1],'yes')
        grouparray.append(w[1])
    print(grouparray)
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


