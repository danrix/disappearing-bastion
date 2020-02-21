import json
import boto3
import os

def lambda_handler(event, context):
    # Prepare Constants ...................................................... /
    admins_path = 'admins'

    body_tail = '\r\n\r\n\r\n' \
                '** ATTENTION ** --------------------------------------' \
                '\r\n*\r\n' \
                '*  This is an automated message.' \
                '\r\n' \
                '*  You can reply to this with your further instructions, but the body of your message is ignored.' \
                '\r\n' \
                '*  Only the subject line of your emails is processed.' \
                '\r\n*\r\n' \
                '*  Type your instructions on the subject line, e.g. "help"' \
                '\r\n*\r\n' \
                '** ----------------------------------------------------------' \
                '\r\n'

    # Determine which message to send ........................................ >
    if event['detail-type'] == 'verify:stack':
        body_data = 'Okay. We\'ll set up an RDP access gate and ' \
                    'we\'ll email you when it\'s ready.\r\n' \
                    'The process usually takes about 15 minutes.' + body_tail
    elif event['detail-type'] == 'stack:ready':
        # If the stack does not belong to this requester ..................... ?
        if not event['detail']['stack_owner'] == event['detail']['source'] :
            body_data = 'There is an access gate already running, but it was set up by another user.' \
                '\r\n\r\nWe can only send log-in credentials once, and we have already sent them ' \
                'to this gate\'s owner.' \
                '\r\n\r\nPlease contact them directly to ask for access:' \
                '\r\n\r\n{0}\r\n'.format(event['detail']['stack_owner']) + body_tail
        # If it does ......................................................... ?
        else:
            if 'stack:ready:delayed' in event['detail']['breadcrumbs'] :
                body_data = 'Please remember to send an email to this address ' \
                    'with the subject line: "done" or "finished" or "revoke access"' \
                    'when you finish work.\r\nFor security reasons it\'s important that we shut down the ' \
                    'access gate when you finish using it.'  + body_tail
            else:
                body_data = 'The access gate is ready.' \
                    '\r\n\r\nUse the following credentials to RDP in:' \
                    '\r\n\r\ngate IP: {0}\r\nuser name: {1}\r\npassword: {2}' \
                    '\r\n\r\nIMPORTANT: Please send an email to this address ' \
                    'with the subject line: "done" or "finished" or "revoke access"' \
                    'when you finish work.\r\nIt\'s important, for security reasons, that we shut down the ' \
                    'access gate when you finish using it.'.format(event['detail']['instance_ip'],event['detail']['user_name'],event['detail']['user_pass'])  + body_tail
    elif event['detail-type'] == 'stack:deleted':
        body_data = 'The access gate and all it\'s resources have been terminated.\r\n\r\nThank you.'  + body_tail
    elif event['detail-type'] == 'get_help':
        body_data = 'Send commands to the access gate on the subject line of your emails.' \
                    '\r\n' \
                    'These are the commands currently available:' \
                    '\r\n\r\n' \
                    '- Grant access\r\nVerifies that you are an authorized user and starts preparing the access gate.' \
                    '\r\n' \
                    'You\'ll receive an email when the gate is ready. The process takes 10-15 minutes on average.' \
                    '\r\n\r\n' \
                    '(Also responds to: "let me in", "allow access", "requesting access")' \
                    '\r\n\r\n' \
                    '- Revoke access\r\nDeactivates the access gate after you stop using it.' \
                    '\r\n' \
                    'For security reasons, it\'s very important that you let us know when you finish work by sending this command.' \
                    '\r\n' \
                    'IMPORTANT: This process starts as soon as we receive your email, so make sure that your work is saved and that ' \
                    '\r\n' \
                    'you have logged off before sending it. You will NOT be given a grace period.' \
                    '\r\n\r\n' \
                    '(Also responds to: "I\'m done", "finished")'  + body_tail

    else:
        return 500

    # Send message ........................................................... >
    try:
        # Prepare
        client = boto3.client('ses')

        # Get admins group 
        admins = getParameter(admins_path)

        response = client.send_email(
            Source=event['detail']['destination'],
            Destination={
                'ToAddresses': [event['detail']['source']],
                'CcAddresses': admins.split(',')
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
        print('Failed attempt to send email.\r\n To: {0}\r\n From: {1}\r\n Cc: {2}\r\n Data: {3}\r\n Error message: {4}'.format(event['detail']['source'],event['detail']['destination'],admins,body_data,e))
        return 500
    else:
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
        