import json
import boto3
import os

import hashlib

def lambda_handler(event, context):
    # Send subject line to NLP analysis ...................................... /
    try:
        client = boto3.client('lex-runtime')
        response = client.post_text(
            botName=os.environ['bot_name'],
            botAlias=os.environ['bot_alias'],
            userId= hashlib.md5(event['detail']['source'].encode()).hexdigest(),
            inputText=event['detail']['subject']
        )
    except Exception as e:
        print('Failed attempt to access Lex bot: ', e)
        return 500
    else:
        # If bot matched an intent ........................................... /
        if response['dialogState'] == 'Fulfilled':

            # Tag breadcrumbs ................................................ /
            event['detail']['breadcrumbs'].append(response['intentName'])
            # Add intent to detail ........................................... /
            event['detail'].update( {'intent': response['intentName']} )

            # Publish event to EventBridge ................................... /
            try:
                response = publishEvent(event['detail'],response['intentName'])
            except Exception as e:
                print('Failed attempt to publish event: ',e)
                return 500
            else:
                return 200

        # If intent is unknown, exit ......................................... /
        else:
            print('Cannot match subject line to intent')
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
