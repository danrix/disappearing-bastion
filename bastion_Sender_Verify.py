import json
import boto3
import os

def lambda_handler(event, context):
    # Get list of allowed senders ............................................ /
    client = boto3.client('ssm')

    try:
        response = client.get_parameter(
            Name= os.environ['parameter_path'],
            WithDecryption=True
        ) 
    except Exception as e:
        print('Failed to get list of allowed senders',e)
        return 500
    else:
        allowed_senders = response['Parameter']['Value'].split(',')

    # Check if sender is in allowed senders list ............................. /
    if event['detail']['source'] in allowed_senders:

        # Tag breadcrumbs .................................................... /
        event['detail']['breadcrumbs'].append(os.environ['event_detail_type'])

        # Publish event to EventBridge ....................................... /
        try:
            response = publishEvent(event['detail'])
        except Exception as e:
            print('Failed attempt to publish event: ',e)
            return 500
        else:
            return 200

    # If sender is not allowed. Print attempt to logs, then die .............. /
    else:
        print('Unauthorized email attempt: ',json.dumps(event['detail']))
        return 200

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
