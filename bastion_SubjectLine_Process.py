import json
import boto3
import os

import hashlib

def lambda_handler(event, context):
    # Prepare Constants ...................................................... /
    bot_name = getParameter('bot/name')
    bot_alias = getParameter('bot/alias')

    # Send subject line to NLP analysis ...................................... >
    try:
        client = boto3.client('lex-runtime')
        response = client.post_text(
            botName=bot_name,
            botAlias=bot_alias,
            userId= hashlib.md5(event['detail']['source'].encode()).hexdigest(),
            inputText=event['detail']['subject']
        )
    except Exception as e:
        print('Failed attempt to access Lex bot: ', e)
        return 500
    else:
        # If bot matched an intent ........................................... ?
        if response['dialogState'] == 'Fulfilled':

            ## START: Publish Group ## ....................................... #
            # Tag breadcrumbs
            event['detail']['breadcrumbs'].append(response['intentName'])
            # Add intent to detail
            event['detail']['intent'] = response['intentName']

            # Publish event to EventBridge
            try:
                response = publishEvent(event['detail'],response['intentName'])
            except Exception as e:
                print('Failed attempt to publish event: ',e)
                return 500
            else:
                return 200
            ## END: Publish Group ## ......................................... #

        # If intent is unknown ............................................... ?
        else:
            print('Cannot match subject line to intent')
            return 200

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
        