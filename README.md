# disappearing-bastion
A bastion host stack in AWS that is spun-up and torn-down automatically, on demand.

The project consists of XX elements:

- A CloudFormation stack yaml file that generates:
    
    1. A public subnet within an existing VPC

    2. Route tables, routes, and associations between the newly created subnet and an existing IGW

    3. Security Groups:

        - to allow RDP access from the internet to a bastion host on the public subnet
        - to allow RDP access from the public bastion host to a private bastion host

    4. Network ACLs, rules, and associations to restrict traffic to RDP between the internet, the public bastion host, and the private bastion host

    5. And finally, an EC2 instance on the public subnet that is seeded via UserData with a unique, random, username and password for RDP access.

