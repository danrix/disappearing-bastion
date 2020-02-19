import boto3
import os

def lambda_handler(event, context):
    # Get Instance Id of inner bastion ....................................... /
    client = boto3.client('ssm')

    try:
        response = client.get_parameter(
            Name= os.environ['parameter_path'],
            WithDecryption=True
        ) 
    except Exception as e:
        print('Failed to get inner bastion instance Id: ',e)
        return 500
    else:

        # Attempt to start inner bastion instance ............................ /
        client = boto3.client('ec2')

        try:
            response = client.start_instances(
                InstanceIds=[
                    response['Parameter']['Value'],
                ]
            )
        except Exception as e:
            print('Failed to start inner bastion instance: ',e)
            return 500
        else:
            print('started inner bastion instance',)
            return 400