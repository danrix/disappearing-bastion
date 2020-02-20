import boto3
import json
import os

def lambda_handler(event, context):
    # Determine if requestor of delete is the owner of the stack ............. /
    # Or a member of the admins group
    is_auth = False
    if (event['detail']['source'] in os.environ['admins_group'].split(',')) or (event['detail']['source'] == event['detail']['stack_owner']):
        is_auth = True

    if not is_auth:
        print('Unauthorized attempt to delete someone else\'s stack by: ',event['detail']['source'])
        return 500

    # Attempt to delete stack ................................................ /
    client = boto3.client('cloudformation')

    try:
        response = client.delete_stack(
            StackName=os.environ['stack_name']
        )
    except Exception as e:
        print('Failed to delete stack: ',e)
        return 500
    else:
        # If processed correctly ............................................. /
        if response['ResponseMetadata']['HTTPStatusCode'] == 200 :
            # Tag breadcrumbs ............................................ /
            event['detail']['breadcrumbs'].append(os.environ['event_detail_type'])
            # Add intance details to detail .............................. /
            event['detail']['instance_state'] = os.environ['event_detail_type']

            # Publish event to EventBridge ................................... /
            try:
                response = publishEvent(event['detail'])
            except Exception as e:
                print('Failed attempt to publish event: ',e)
                return 500
            else:
                return 200

        # something went wrong ............................................... /
        else:
            return 500

def publishEvent(details,detail_type=os.environ['event_detail_type']):
    # Prepare client ......................................................... /
    client = boto3.client('events')
    # Prepare json details ................................................... /
    detail_details = str(json.dumps(details))
    # Prepare event .......................................................... /
    entries = {
        'Source': 'aws:lambda',
        'DetailType': detail_type,
        'Detail': detail_details,
        'EventBusName': os.environ['bus_name']
    }

    # Attempt to publish event ............................................... /
    try:
        response = client.put_events(
            Entries=[
                entries
            ]
        )
    except Exception as e:
        print('Failed publishing event: ',e)
        return 500
    else:
        print('Published event: ',json.dumps(response))
        print('Details published: ',json.dumps(entries))
        return 200
