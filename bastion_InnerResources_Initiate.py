import boto3
import os

def lambda_handler(event, context):
    # Prepare Constants ...................................................... /
    instance_id_path = 'inner_bastion/instanceId'

    # Attempt to start inner bastion instance ............................ /
    # Get instance id 
    instance_id = getParameter(instance_id_path,True)

    client = boto3.client('ec2')
    try:
        response = client.start_instances(
            InstanceIds=[instance_id]
        )
    except Exception as e:
        print('Failed to start inner bastion instance: ',e)
        return 500
    else:
        print('started inner bastion instance',)
        return 200

def getParameter(sub_path,is_encrypted=False):
    # Prepare
    client = boto3.client('ssm')
    full_path = os.environ['parameters_base_path']+sub_path
    
    # Attempt to get parameter
    try:
        response = client.get_parameter(
            Name= full_path,
            WithDecryption=is_encrypted
        )
    except Exception as e:
        print('Failed to get parameter: {0}. Error: {1}'.format(full_path,e))
        return 500
    else:
        return response['Parameter']['Value']
        