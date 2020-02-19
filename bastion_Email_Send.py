import json
import boto3
import os

def lambda_handler(event, context):
    # Prepare to send email .................................................. /
    client = boto3.client('ses')

    # Determine which response to send ....................................... /
    if event['detail-type'] == 'verify:stack':
        body_data = 'Okay. We\'ll set up an RDP access gate and ' \
                    'we\'ll email you when it\'s ready.\r\n' \
                    'The process usually takes about 15 minutes.'
    elif event['detail-type'] == 'stack:ready':
        # If the stack does not belong to this requester ..................... ?
        if not event['detail']['stack_owner'] == event['detail']['source'] :
            body_data = 'There is an access gate already running, but it was set up by another user.' \
                '\r\n\r\nWe can only send log-in credentials once, and we have already sent them ' \
                'to this gate\'s owner.' \
                '\r\n\r\nPlease contact them directly to ask for access:' \
                '\r\n\r\n{0}\r\n'.format(event['detail']['stack_owner'])
        # If it does ......................................................... ?
        else:
            body_data = 'The access gate is ready.' \
                '\r\n\r\nUse the following credentials to RDP in:' \
                '\r\n\r\ngate IP: {0}\r\nuser name: {1}\r\npassword: {2}' \
                '\r\n\r\nIMPORTANT: Please send an email to this address ' \
                'with the subject line: "done" or "finished" or "revoke access"' \
                'when you finish work.\r\nIt\'s important so we can shut it down' \
                ' for security reasons.'.format(event['detail']['instance_ip'],event['detail']['user_name'],event['detail']['user_pass'])
    else:
        return 500

    # Send message ........................................................... /
    try:
        response = client.send_email(
            Source=event['detail']['destination'],
            Destination={
                'ToAddresses': [
                    event['detail']['source'],
                ],
                'CcAddresses': [
                    os.environ['admins_group'],
                ]
            },
            Message={
                'Subject': {
                    'Data': 'RE: {}'.format(event['detail']['subject']),
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body_data,
                        'Charset': 'UTF-8'
                    }
                }
            },
            Tags=[
                {
                    'Name': 'cost_center',
                    'Value': 'bastion'
                },
            ],
        )
    except Exception as e:
        print('Failed attempt to send email: ',e)
        return 500
    else:
        return 200
