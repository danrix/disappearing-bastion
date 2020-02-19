# disappearing-bastion
A bastion host stack in AWS that is spun-up and torn-down automatically, on demand.

The project consists of 8 elements:

- A CloudFormation stack yaml file that generates:
    
    1. A public subnet within an existing VPC

    2. Route tables, routes, and associations between the newly created subnet and an existing IGW

    3. Security Groups:

        - to allow RDP access from the internet to a bastion host on the public subnet
        - to allow RDP access from the public bastion host to a private bastion host

    4. Network ACLs, rules, and associations to restrict traffic to RDP between the internet, the public bastion host, and the private bastion host

    5. And finally, an EC2 instance on the public subnet that is seeded via UserData with a unique, random, username and password for RDP access.

- An AWS SES rule that triggers a Lambda function on receipt of email to a specific address

- An AWS EvenBridge bus that listens to and directs events to various Lambda functions

- A Lex bot that determines intent from email subject lines

- Various Lambda functions, mostly triggered by EventBridge events

- An S3 bucket to hold yaml files

- A DynamoDB table that logs stack operations

- Roles and policies for the different components

Additionally, the projects depends on other AWS resources that are pressumed existing before this stack goes into effect, but that go beyond the scope of this project, so they are not defined as part of this repo:

    - A VPC with a private subnet, and an EC2 instance in it that serves as an "inner bastion".

    - A working SES setup with a verified email address that can receive and send email

    - A set of parameters on Systems Manager > Parameter Store

