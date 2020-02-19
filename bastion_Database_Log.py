import boto3
import os

def lambda_handler(event, context):
    # record to database ..................................................... /
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['db_table'])

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