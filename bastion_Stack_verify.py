import boto3
import json
import os

def lambda_handler(event, context):
    # Get the imageId from parameter store ................................... /
    client = boto3.client('ssm')

    try:
        response = client.get_parameter(
            Name= os.environ['amiid_parameter_path'],
            WithDecryption=False
        ) 
    except Exception as e:
        print('Failed to get image Id',e)
        return 500
    else:
        image_id = response['Parameter']['Value']
        # Get details from instance created by Stack ......................... /
        client = boto3.client('ec2')

        # Find all not-terminated instances filtered by the bastion imageId .. /
        try:
            response = client.describe_instances(
                Filters=[
                    {
                        'Name': 'image-id',
                        'Values': [ image_id ]
                    },
                    {
                        'Name': 'instance-state-name',
                        'Values': [
                            'pending',
                            'running'
                        ]
                    }
                ]
            )
        except Exception as e:
            print('Failed to get list of appropriate instances: ',e)
            return 500
        else:
            # If no instances found .......................................... /
            if not response['Reservations']:
                # Set event DetailType ....................................... /
                detail_type = os.environ['none_detail_type']
                # Tag breadcrumbs ............................................ /
                event['detail']['breadcrumbs'].append(detail_type)
                # Add intance details to detail .............................. /
                event['detail']['instance_state'] = detail_type

            # Determine the state of the instance ............................ /
            else:
                # Sort list of instances in case there's more than one ....... /
                for res in response['Reservations'] :
                    instances = sorted(res['Instances'], key = lambda i: i['LaunchTime'])
                    # Get details of most recent instance ...
                    for instance in instances :
                        # Set event DetailType
                        if instance['State']['Name'] == 'pending':
                            detail_type = 'stack:changing'
                        else:
                            detail_type = 'stack:ready'

                        # Tag breadcrumbs .................................... /
                        event['detail']['breadcrumbs'].append(detail_type)
                        # Add intance details to detail ...................... /
                        event['detail']['instance_state'] = detail_type
                        event['detail']['instance_id'] = instance['InstanceId']
                        event['detail']['instance_ip'] = instance['PublicIpAddress']
                        event['detail']['instance_launch_time'] = str(instance['LaunchTime'])

                        # Get stack id, and owner ............................ /
                        for tag in instance['Tags']:
                            if tag['Key'] == 'owner':
                                event['detail']['stack_owner'] = tag['Value']
                            if tag['Key'] == 'aws:cloudformation:stack-id':
                                event['detail']['stack_id'] = tag['Value']
                        # Process only the most recent instance, ignore others
                        break

            # Publish event to EventBridge ................................... /
            try:
                response = publishEvent(event['detail'],detail_type)
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
