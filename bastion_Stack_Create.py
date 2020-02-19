import boto3
import json
import os

import random
import string

def lambda_handler(event, context):
    # Get Stack base template ................................................ /
    client = boto3.client('s3')
    try:
        response = client.get_object(Bucket=os.environ['bucket_name'], Key=os.environ['bucket_key'])
    except Exception as e:
        print('Failed to get stack template: ',e)
        # Further processing
        pass
    else:
        # Generate credentials ............................................... /
        user_name = createUsername(3)
        user_pass = createPassword(23)

        # Add credentials to Stack template .................................. /
        yaml_base = response['Body'].read().decode('utf-8')
        yaml_final = yaml_base.format(user_name,user_pass)

        # Attempt to create stack ............................................ /
        client = boto3.client('cloudformation')

        try:
            response = client.create_stack(
                StackName=os.environ['stack_name'],
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
            try:
                response = publishEvent(event['detail'],'stack:create:failed')
            except Exception as e:
                print('Failed attempt to publish event: ',e)
                return 500
            else:
                return 200

        else:
            # If processed correctly ......................................... /
            if response['ResponseMetadata']['HTTPStatusCode'] == 200 :
                # Publish event to EventBridge ............................... /
                # stack creation initiated
                event['detail'].update( {'stack_id' : response['StackId']} )
                event['detail'].update( {'user_name' : user_name} )
                event['detail'].update( {'user_pass' : user_pass} )
                try:
                    response = publishEvent(event['detail'],'verify:stack')
                except Exception as e:
                    print('Failed attempt to publish event: ',e)
                    return 500
                else:
                    return 200

            # something went wrong ........................................... /
            else:
                # Publish error event ........................................ /
                pass
                return 500

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
