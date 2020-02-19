import boto3
import os

def lambda_handler(event, context):
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
            return 200

        # something went wrong ............................................... /
        else:
            return 500
