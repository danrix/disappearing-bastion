import boto3
import json
import os

from datetime import datetime

def lambda_handler(event, context):
    # Prepare a time X minutes in the future ................................. /
    now_obj = datetime.now()
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

    # Attempt to update appropriate event in bridge with new time ............ /
    client = boto3.client('events')

    try:
        response = client.put_rule(
            Name=os.environ['rule_name'],
            Description=event_description,
            ScheduleExpression=cron_expression
        )
    except Exception as e:
        print('Failed attempt to update timer event: ',e)
    else:
        # Prepare payload for target ......................................... /
        new_event = {}
        new_event['source'] = 'aws:lambda'
        new_event['detail-type'] = 'verify:stack'
        new_event['detail'] = event['detail']
        new_event['detail']['breadcrumbs'].append('verify:stack:delayed')
        # Update the event's target payload .................................. /
        try:
            response = client.put_targets(
                Rule=os.environ['rule_name'],
                Targets=[
                    {
                        'Id': 'rule_target_',
                        'Arn': os.environ['target_arn'],
                        'Input': json.dumps(new_event)
                    },
                ]
            )
        except Exception as e:
            raise e
        else:
            print('Updated event and target successfully: ',response)
            return 400