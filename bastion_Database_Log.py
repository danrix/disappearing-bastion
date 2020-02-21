import boto3
import os

def lambda_handler(event, context):
    # Prepare Constants ...................................................... /
    db_table_path = 'database/table'

    # record to database ..................................................... >
    # Get table name 
    table_name = getParameter(db_table_path)

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    try:
        table.put_item(
            Item={
            'StackId': event['detail']['stack_id'],
            'Date': event['time'],
            'owner': event['detail']['source'],
            'user_name': event['detail']['user_name'],
            'user_pass': event['detail']['user_pass']
            }
        )
    except Exception as e:
        print('Failed attempt to log in database: ',e)
        return 500
    else:
        print('Successfully logged stack creation details in database')
        return 400

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
        