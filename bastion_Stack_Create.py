import boto3
import json
import os

import random
import string

def lambda_handler(event, context):
    # Prepare Constants ...................................................... /
    bucket_name_path = 'bucket/name'
    bucket_key_path = 'bucket/key'
    detail_type_path = 'lambdas/{}/detail_type'.format(context.function_name)
    failed_detail_type_path = 'lambdas/{}/detail_type/failure'.format(context.function_name)
    stack_name_path = 'stack/name'

    # Get Stack base template ................................................ >
    # Get bucket details
    bucket_name = getParameter(bucket_name_path)
    bucket_key = getParameter(bucket_key_path)

    client = boto3.client('s3')
    try:
        response = client.get_object(Bucket=bucket_name, Key=bucket_key)
    except Exception as e:
        print('Failed to get stack template: ',e)
        # Further processing
        pass
    else:
        # Generate credentials
        user_name = createUsername(3)
        user_pass = createPassword(23)

        # Add credentials to Stack template
        yaml_base = response['Body'].read().decode('utf-8')
        yaml_final = yaml_base.format(user_name,user_pass)

        # Attempt to create stack ............................................ >
        # Get stack name
        stack_name = getParameter(stack_name_path)

        client = boto3.client('cloudformation')

        try:
            response = client.create_stack(
                StackName=stack_name,
                TemplateBody=yaml_final,
                Tags=[
                    {
                        'Key': 'owner',
                        'Value': event['detail']['source']
                    },
                    {
                        'Key': 'cost_center',
                        'Value': 'bastion'
                    }
                ]
                )
        except Exception as e:
            print('Failed to create stack: ',e)

            # Publish event to EventBridge ................................... /
            # stack creation failed
            # Get failure detail type
            detail_type = getParameter(failed_detail_type_path)

        else:
            # If NOT processed correctly ..................................... ?
            if not response['ResponseMetadata']['HTTPStatusCode'] == 200 :
                return 500

            # If processed correctly ......................................... ?
            else:
                # Get detail type
                detail_type = getParameter(detail_type_path)

                # stack creation initiated
                event['detail']['stack_id'] = response['StackId']
                event['detail']['user_name'] = user_name
                event['detail']['user_pass'] = user_pass
        
        ## START: Publish Group ## ........................................... #
        # Publish event to EventBridge   
        try:
            response = publishEvent(event['detail'],detail_type)
        except Exception as e:
            print('Failed attempt to publish event: ',e)
            return 500
        else:
            return 200
        ## END: Publish Group ## ............................................. #

def createUsername(syllables=5, add_number=False):
    rnd = random.SystemRandom()
    s = string.ascii_lowercase
    vowels = 'aeiou'
    consonants = ''.join([x for x in s if x not in vowels])
    result = ''.join([rnd.choice(consonants) + rnd.choice(vowels)
               for x in range(syllables)]).title()
    if add_number:
        result += str(rnd.choice(range(10)))
    return result

def createPassword(length):
    chars = string.ascii_letters + string.digits + '!@#$%^&*()'
    random.seed = (os.urandom(1024))

    return ''.join(random.choice(chars) for i in range(length))

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
        