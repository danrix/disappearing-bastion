import boto3
import json
import os

def lambda_handler(event, context):
    # Prepare Constants ...................................................... /
    ready_detail_type_path = 'lambdas/{}/detail_type/ready'.format(context.function_name)
    none_detail_type_path = 'lambdas/{}/detail_type/none'.format(context.function_name)
    changing_detail_type_path = 'lambdas/{}/detail_type/changing'.format(context.function_name)
    ami_id_path = 'cloudformation/parameters/amiId'


    # Get details from instance created by Stack ............................. >
    # Get image_id 
    image_id = getParameter(ami_id_path)

    client = boto3.client('ec2')
    # Find all not-terminated instances filtered by the bastion imageId
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
        # If no instances found .............................................. ?
        if not response['Reservations']:
            # Set event DetailType
            detail_type = getParameter(none_detail_type_path)
            # Tag breadcrumbs
            event['detail']['breadcrumbs'].append(detail_type)
            # Add intance details to detail
            event['detail']['instance_state'] = detail_type

        # If instance(s) were found .......................................... ?
        else:
            # Sort list of instances in case there's more than one
            for res in response['Reservations'] :
                instances = sorted(res['Instances'], key = lambda i: i['LaunchTime'])
                # Get details of most recent instance
                for instance in instances :
                    # Set event DetailType
                    if instance['State']['Name'] == 'pending':
                        detail_type = getParameter(changing_detail_type_path)
                    else:
                        detail_type = getParameter(ready_detail_type_path)

                    # Tag breadcrumbs
                    event['detail']['breadcrumbs'].append(detail_type)
                    # Add intance details to detail
                    event['detail']['instance_state'] = detail_type
                    event['detail']['instance_id'] = instance['InstanceId']
                    event['detail']['instance_ip'] = instance['PublicIpAddress']
                    event['detail']['instance_launch_time'] = str(instance['LaunchTime'])

                    # Get stack id, and owner
                    for tag in instance['Tags']:
                        if tag['Key'] == 'owner':
                            event['detail']['stack_owner'] = tag['Value']
                        if tag['Key'] == 'aws:cloudformation:stack-id':
                            event['detail']['stack_id'] = tag['Value']
                    # Process only the most recent instance, ignore others
                    break

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
        