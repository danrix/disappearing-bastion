import boto3
import json
import os

from datetime import datetime

def lambda_handler(event, context):
    # Preparation ............................................................ /
    now_obj = datetime.now()

    # If VERIFY:STACK is the event that triggered this ....................... ?
    if event['detail-type'] == 'verify:stack':

        mins_lapse = os.environ['mins_lapse']

        # Prevent errors if too close to end of hour
        if (now_obj.minute + int(mins_lapse)) >= 60:
            mins = (now_obj.minute + int(mins_lapse)) - 60
            hours = now_obj.hour + 1
        else:
            mins = now_obj.minute + int(mins_lapse)
            hours = now_obj.hour

        # Prepare cron statement for event:  cron(min, hour, month-day, month, week-day, year)
        cron_expression = 'cron({0} {1} {2} {3} ? {4})'.format(mins,hours,now_obj.day,now_obj.month,now_obj.year)
        # Prepare description for event
        event_description = 'Wait until: {0}:{1} UTC'.format(str(hours).zfill(2),str(mins).zfill(2))

        # Prepare rule name
        rule_name = os.environ['rule_name_verify']

        # Prepare rule target
        target_arn = os.environ['verify_target_arn']
        target_id = os.environ['verify_target_id']

    # If STACK:READY is the event that triggered this ........................ ?
    elif event['detail-type'] == 'stack:ready':
        # If the STACK:READY:DELAY timer has already been set, exit
        if 'stack:ready:delay' in event['detail']['breadcrumbs'] :
            return 400

        loop_lapse = os.environ['loop_lapse']

        # Prevent errors if too close to end of hour
        if (now_obj.minute + int(loop_lapse)) >= 60:
            mins = (now_obj.minute + int(loop_lapse)) - 60
        else:
            mins = now_obj.minute + int(loop_lapse)

        # Prepare cron statement for event:  cron(min, hour, month-day, month, week-day, year)
        cron_expression = 'cron({} * * * ? *)'.format(mins)
        # Prepare description for event
        event_description = 'Run every hour on the {0} minute'.format(str(mins).zfill(2))

        # Prepare rule name
        rule_name = os.environ['rule_name_ready']

        # Prepare rule target
        target_arn = os.environ['ready_target_arn']
        target_id = os.environ['ready_target_id']

    # If unanticipated: exit ................................................. ?
    else:
        return 500

    # Attempt to update appropriate event in bridge with new time ............ /
    client = boto3.client('events')

    try:
        response = client.put_rule(
            Name=rule_name,
            Description=event_description,
            ScheduleExpression=cron_expression
        )
    except Exception as e:
        print('Failed attempt to update timer event: ',e)
        print('cron exp: ',cron_expression)
    else:
        # Prepare payload for target ......................................... /
        new_event = {}
        new_event['source'] = 'aws:lambda'
        new_event['detail-type'] = event['detail-type']
        new_event['detail'] = event['detail']
        new_event['detail']['breadcrumbs'].append('{}:delayed'.format(event['detail-type']))
        # Update the event's target payload .................................. /
        try:
            response = client.put_targets(
                Rule=rule_name,
                Targets=[
                    {
                        'Id': target_id,
                        'Arn': target_arn,
                        # 'RoleArn': target_role,
                        'Input': json.dumps(new_event)
                    },
                ]
            )
        except Exception as e:
            print('Failed attempt to put target(s) on rule: ',e)
            print(new_event)
        else:
            print('Updated event and target successfully: ',response)
            return 400