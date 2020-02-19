import json
import boto3
import os

def lambda_handler(event, context):
    
    # Prepare event Entries .................................................. /
    details = {
        'source': event['Records'][0]['ses']['mail']['source'],
        'destination': event['Records'][0]['ses']['mail']['destination'][0],
        'timestamp': event['Records'][0]['ses']['mail']['timestamp'],
        'subject': event['Records'][0]['ses']['mail']['commonHeaders']['subject'],
        'breadcrumbs': [os.environ['event_detail_type']]
    }

    # Publish event to EventBridge ........................................... /
    try:
        response = publishEvent(details)
    except Exception as e:
        print('Failed attempt to publish event: ',e)
        return 500
    else:
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
