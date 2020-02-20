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
    else:

        # Attempt to stop inner bastion instance ............................. /
        client = boto3.client('ec2')

        try:
            response = client.stop_instances(
                InstanceIds=[
                    response['Parameter']['Value']
                ]
            )
        except Exception as e:
            print('Failed to stop inner bastion instance: ',e)
        else:
            print('stopped inner bastion instance',)

    # Set back time for rules in EventBridge ................................. /            
    client = boto3.client('events')

    for rule in os.environ['rules_names'].split(','):
        # Remove Target(s) ......
        try:
            response = client.put_rule(
                Name=rule,
                Description='',
                ScheduleExpression='cron({* * * * ? 1999)'
            )
        except Exception as e:
            print('Failed to set-back target(s): ',e)
        else:
            print('Set time back to 1999 for rule(s) in EventBridge: ',os.environ['rules_names'])
            
    return 400

    