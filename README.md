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
In order to use this script you need an AWS account. You will also need an IAM User that has programmatic access as well as the 'AmazonEC2FullAccess' , 'AmazonSSMFullAccess', and 'EC2InstanceConnect' policies attached. If you need to create a new IAM user, please refer to this [link. ](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)If you already have an existing user but need to grant programmatic access follow these steps:

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

If you need to attach policies, refer to these steps 
1. Go to the IAM Dashboard
2. Click users on the left-hand side and click your username
3. Click "Add permissions" and select "Attach existing policies directly"
4. Search for 'AmazonEC2FullAccess', 'AmazonSSMFullAccess', and 'EC2InstanceConnect' and select the checkbox next to them
5. Click 'Next: review' and select 'Add permissions'

If your IAM user has permissions to do so, you can attach these policies via the command line

``` shell
aws iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess --user-name <AWS IAM user name>
```
``` shell
aws iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/AmazonSSMFullAccess --user-name <AWS IAM user name>
```
```shell
aws iam attach-user-policy --policy-arn arn:aws:iam::aws:policy/EC2InstanceConnect --user-name <AWS IAM user name>
```
* If you get an AccessDenied error, you will have to attach the policies through the IAM Dashboard.

# Notes
* If your AWS account has the max amount of VPC's that you are allowed this will not work due to the fact that a new VPC cannot be created. The error will look like this if that is the case:
 ``` shell
An error occurred (VpcLimitExceeded) when calling the CreateVpc operation: The maximum number of VPCs has been reached.
```
Please delete a VPC or create a new AWS account to solve this issue if applicable.

# Use
To start, clone the repository to get the script and YAML configuration or download the files directly from [the repository.](https://github.com/mollypabst/Deploy_EC2_Instance.git)
``` shell
git clone https://github.com/mollypabst/Deploy_EC2_Instance.git

cd Deploy_EC2_Instance
```
Once you have the files, run the script and it will perform various tasks to create an EC2 instance, attach volumes, and add SSH users based on the YAML configuration. Feel free to change the YAML configuration, the script will handle new changes. The great thing about the script is that you do not have to paste the user's SSH key into the config file, the script automatically creates a key and puts it into the authorized_keys file of the user for convenience. 

Once the instance IP address is printed you can SSH into your new instance using this command
``` shell
ssh -i FETCH_REWARDS_KEY.pem username@provided-IPv6-address
``` 
An example ssh command that utilizes the correct IP address can also be found in the terminal.

You have now successfully logged into the instance and can read from and write to the volumes!
To list the available disks, call this command:
``` shell
lsblk
```
