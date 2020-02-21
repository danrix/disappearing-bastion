import json
import boto3
import os

def lambda_handler(event, context):
    # Prepare Constants ...................................................... /
    detail_type_path = 'lambdas/{}/detail_type'.format(context.function_name)
    
    ## START: Publish Group ## ............................................... #
    # Get detail type 
    detail_type = getParameter(detail_type_path)

    # Prepare event Entries
    details = {
        'source': event['Records'][0]['ses']['mail']['source'],
        'destination': event['Records'][0]['ses']['mail']['destination'][0],
        'timestamp': event['Records'][0]['ses']['mail']['timestamp'],
        'subject': event['Records'][0]['ses']['mail']['commonHeaders']['subject'],
        'breadcrumbs': [detail_type]
    }

    # Publish event to EventBridge
    try:
        response = publishEvent(details,detail_type)
    except Exception as e:
        print('Failed attempt to publish event: ',e)
        return 500
    else:
        return 200
    ## END: Publish Group ## ................................................. #

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
        