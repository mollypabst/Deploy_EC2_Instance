## Deploying an EC2 Instance using Python and boto3
# Requirements
* [Python 3.6+](https://www.python.org/downloads/)
* [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html)
* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
* [PyYAML](https://pyyaml.org/wiki/PyYAMLDocumentation)

If you have pip installed, you can install boto3, AWS CLI, and PyYAML using this command:
```python3
pip install boto3 awscli pyyaml
```

# AWS Requirements
In order to use this script you need an AWS account, a key pair, and a security group. Details on how to obtain these features can be found in the [AWS EC2 Documentation.](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/get-set-up-for-amazon-ec2.html) 
You will also need an IAM User that has programmatic access as well as the 'AmazonEC2FullAccess' and 'AmazonSSMFullAccess' policies attached. If you need to create a new IAM user, please refer to this [link. ](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)If you already have an existing user but need to grant programmatic access follow these steps:

1. Navigate to the "Users" page
2. Find the user you wish to grant programmatic access to, select the user, which will open the details page for that user.
3. Open the "Security Credentials" tab
4. Click "Create Access Key"

The user can then use the access key and secret key to access AWS programmatically. 

In order for the aws command line interface to work, it needs to be configured by calling:

``` python3
aws configure
```
Enter the IAM User access key and secret key when prompted, as well as the default region and default output format if you wish. 

# Notes
* If your AWS account has the max amount of VPC's that you are allowed this will not work due to the fact that a new VPC cannot be created. The error will look like this if that is the case:
 ``` shell
An error occurred (VpcLimitExceeded) when calling the CreateVpc operation: The maximum number of VPCs has been reached.
```
Please delete a VPC or create a new AWS account to solve this issue if applicable.

# Use
Once the instance IP address is printed you can ssh into using this command
``` shell
ssh -i FETCH_REWARDS_KEY.pem username@provided-IPv6-address
``` 
An example ssh command that utilizes the correct IP address can also be found in the terminal.

You have now successfully logged into the instance and can read from and write to the volumes!
To list the available disks, call this command:
``` shell
lsblk
```
