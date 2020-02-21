import boto3
import json
import os

def lambda_handler(event, context):
    # Prepare Constants ...................................................... /
    detail_type_path = 'lambdas/{}/detail_type'.format(context.function_name)
    stack_name_path = 'stack/name'
    admins_group_path = 'admins'

    # Get Stack details ...................................................... >
    # Get stack name
    stack_name = getParameter(stack_name_path)

    client = boto3.client('cloudformation')
    try:
        response = client.describe_stacks(
            StackName=stack_name
        )
    except Exception as e:
        print('Failed to get stack details: ',e)
    else:
        # Prepare to delete stack ............................................ /
        is_auth = False
        # Get stack name
        admins_group = getParameter(admins_group_path)

        # If requestor IS a member of the admins group ....................... ?
        if event['detail']['source'] in admins_group.split(','):
            is_auth = True

        # If the requestor OWNS the stack .................................... ?
        for stack in response['Stacks']:
            for tag in stack['Tags']:
                if tag['Key'] == 'owner':
                    if tag['Value'] == event['detail']['source']:
                        is_auth = True
    
    # If NO authorization found .............................................. ?
    if not is_auth:
        print('Unauthorized attempt to delete someone else\'s stack by: ',event['detail']['source'])
        return 500

    # Attempt to delete stack ................................................ /
    client = boto3.client('cloudformation')

    try:
        response = client.delete_stack(
            StackName=stack_name
        )
    except Exception as e:
        print('Failed to delete stack: ',e)
        return 500
    else:
        # If processed correctly ............................................. ?
        if response['ResponseMetadata']['HTTPStatusCode'] == 200 :
            
            ## START: Publish Group ## ....................................... #
            # Get detail type 
            detail_type = getParameter(detail_type_path)
            # Tag breadcrumbs
            event['detail']['breadcrumbs'].append(detail_type)
            # Add intance details to detail
            event['detail']['instance_state'] = detail_type

            # Publish event to EventBridge
            try:
                response = publishEvent(event['detail'],detail_type)
            except Exception as e:
                print('Failed attempt to publish event: ',e)
                return 500
            else:
                return 200
            ## END: Publish Group ## ......................................... #

        # If something went wrong deleting stack ............................. ?
        else:
            return 500

def publishEvent(details,detail_type):
    # Prepare
    bus_name_path = 'bus_name'
    client = boto3.client('events')
    detail_details = str(json.dumps(details))

    entries = {
        'Source': 'aws:lambda',
        'DetailType': detail_type,
        'Detail': detail_details,
        'EventBusName': getParameter(bus_name_path)
    }

    # Attempt to publish event
    try:
        response = client.put_events(
            Entries=[entries]
        )
    except Exception as e:
        print('Failed publishing event: ',e)
        return 500
    else:
        print('Published event: ',json.dumps(response))
        print('Details published: ',json.dumps(entries))
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
        