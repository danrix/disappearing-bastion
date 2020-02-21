import boto3
import json
import os

def lambda_handler(event, context):
    # Prepare Constants ...................................................... /
    instance_id_path = 'inner_bastion/instanceId'
    rules_names_path = 'rules/names'

    # Attempt to stop inner bastion instance ................................. >

    # Get instance id 
    instance_id = getParameter(instance_id_path,True)

    client = boto3.client('ec2')
    try:
        response = client.stop_instances(
            InstanceIds=[instance_id]
        )
    except Exception as e:
        print('Failed to stop inner bastion instance: ',e)
    else:
        print('stopped inner bastion instance',)

    # Set back time for rules in EventBridge ................................. >
    # Get rules names 
    rules_names = getParameter(rules_names_path)

    client = boto3.client('events')

    for rule in rules_names.split(','):
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
            