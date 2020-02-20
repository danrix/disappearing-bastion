import boto3
import json
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
        # Set cron back in time to avoid running
        try:
            response = client.put_rule(
                Name=rule,
                Description='',
                ScheduleExpression='cron(* * * * ? 1999)'
            )
        except Exception as e:
            print('Failed to set-back target(s): ',e)
        else:
            print('Set time back to 1999 for rule in EventBridge: ',rule)

            # Get list of targets per rule
            try:
                response = client.list_targets_by_rule(
                    Rule=rule,
                )
            except Exception as e:
                print('Failed to get list of targets for rule',e)
            else:
                # Clear the input for every target in every rule
                for target in response['Targets'] :
                    try:
                        response = client.put_targets(
                            Rule=rule,
                            Targets=[
                                {
                                    'Id': target['Id'],
                                    'Arn': target['Arn'],
                                    'Input': json.dumps('{}')
                                },
                            ]
                        )
                    except Exception as e:
                        print('Failed attempt to update target\'s input on rule ',e)
                    else:
                        print('Updated event and target successfully: ',target['Arn'])

    return 200

    