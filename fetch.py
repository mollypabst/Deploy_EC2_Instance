import boto3
import yaml
import os
from sys import platform

# open configuration file and store data
with open('fetch.yaml', 'r') as stream:
    try:
        yaml_data = yaml.safe_load(stream) # stores data into dictionary
    except yaml.YAMLError as e:
        print(e)

class EC2():
    def __init__(self):
        self.name = 'FETCH_REWARDS'
        self.vpc_id = None
        self.public_ip = None
        self.allocation_id = None
        self.security_group_id = None
        self.network_interface = None
        self.network_interface_id = None
        self.ec2_instance_id = None
        self.availability_zone = None
        self.instance_type = yaml_data['server']['instance_type']
        self.ami_type = yaml_data['server']['ami_type']
        self.architecture = yaml_data['server']['architecture']
        self.root_device_type = yaml_data['server']['root_device_type']
        self.virtualization_type = yaml_data['server']['virtualization_type']
        self.min_count = yaml_data['server']['min_count']
        self.max_count = yaml_data['server']['max_count']
        self.volumes = yaml_data['server']['volumes']
        self.users = yaml_data['server']['users']
        self.ssm_client = boto3.client('ssm')
        self.iam_resource = boto3.resource('iam')
        # returns dictionary of parameters for latest AMI image based on YAML file data
        self.ami_id_dict = self.ssm_client.get_parameters(
            Names = ['/aws/service/ami-amazon-linux-latest/' + self.ami_type + '-ami-' + self.virtualization_type + '-' + self.architecture + '-' + self.root_device_type]
        )
        # pull just the AMI ID from the dictionary
        self.ami_id = self.ami_id_dict['Parameters'][0]['Value']
        self.ec2_client = boto3.client('ec2') # lower level interface to AWS
        self.ec2_resource = boto3.resource('ec2') # has attributes, identifiers, and actions but doesnt have certain functions like client does
        self.userData = '#!/bin/bash\n' # invoke shell to call all commands after this line

    def create_key_pair(self):
        name = self.name + '_KEY'
        try:
            # create file to store key pair info into .pem file
            filename = name + '.pem'
            with open(filename,'w') as fp:     
                key_pair = self.ec2_client.create_key_pair(KeyName = name)         
                # write key_pair output to file
                fp.write(str(key_pair['KeyMaterial']))
            
            # check OS before using chmod 
            if platform == 'linux' or platform == 'linux2' or platform == 'darwin':
                os.system("chmod 400 " + filename)
 
            return key_pair
        except Exception as e:
            print(e)  
    
    def create_security_group(self):
        # Create security group and add permissions
        security_description = self.name + '_SECURITY_GROUP'
        sec_group = self.ec2_client.create_security_group(VpcId = self.vpc_id, GroupName = 'fetch_security', Description = security_description)
        self.security_group_id = sec_group['GroupId']
        print(self.security_group_id)
        # add inbound rules to security group
        self.ec2_client.authorize_security_group_ingress(
                GroupId= self.security_group_id,
                IpPermissions=[
                    {'IpProtocol': 'tcp', # allow HTTP traffic on port 80 from IPv4 addresses
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
                    {'IpProtocol': 'tcp', # allow SSH traffic on port 22 from IPv4 adddresses
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0'}]} # CidrIp is the IP range it allows so in this case it's any IP
                ]
        )
    
    def create_vpc(self):
        try:
            vpc = self.ec2_client.create_vpc(CidrBlock='10.10.0.0/16') # CidrBlock is range of IPv4 addresses so it will have 256 * 256 addresses in its range
            self.vpc_id = vpc['Vpc']['VpcId'] # vpc is basically a network of your own within AWS

            # attach internet gateway
            gateway = self.ec2_client.create_internet_gateway() # gateway allows communication between the VPC and the internet
            self.igw_id = gateway['InternetGateway']['InternetGatewayId']
            self.ec2_client.attach_internet_gateway(InternetGatewayId = self.igw_id, VpcId = self.vpc_id)

            # get route table and create a route
            route_table = self.ec2_client.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [self.vpc_id]}])
            self.rt_id = route_table['RouteTables'][0]['RouteTableId']
            route = self.ec2_client.create_route( # rule to direct where network traffic from gateway is directed 
                DestinationCidrBlock='0.0.0.0/0',
                GatewayId = self.igw_id,
                RouteTableId=self.rt_id
            )
            # create subnet and store its ID
            subnet_resp = self.ec2_client.create_subnet(VpcId=self.vpc_id, CidrBlock='10.10.1.0/24') # smaller network within VPC so it's more efficient and you can specify rules within it
            self.subnet_id = subnet_resp['Subnet']['SubnetId']
        except Exception as e:
            print(e)


    def create_instance(self):            
        try:
            #create vpc, security group, and key pair
            vpc = self.create_vpc()
            security_group = self.create_security_group()
            key_pair_resp = self.create_key_pair()

            # Allocate Elastic IP address to AWS account
            elastic_ip = self.ec2_client.allocate_address(Domain='vpc') # elastic IP address specific to my AWS account so that I can associate it with network interface 
            self.public_ip = elastic_ip['PublicIp'] # the elastic IP
            self.allocation_id = elastic_ip['AllocationId'] # the ID that AWS assigns to represent the allocation of the elastic IP address for use with instances in the VPC

            # set subnet
            subnet = self.ec2_resource.Subnet(self.subnet_id)

            # create network interface
            interface_description = self.name + '_Interface'
            self.network_interface = subnet.create_network_interface(Description=interface_description,
                                                                Groups=[self.security_group_id])

            # associate elastic IP address 
            self.network_interface_id = self.network_interface.id
            self.ec2_client.associate_address(AllocationId=self.allocation_id,
                                              NetworkInterfaceId=self.network_interface_id) # basically connects the elastic IP address and security group together within the VPC

            # Parse volumes and store in list to use for BlockDeviceMappings when creating instance
            BlockDeviceMappings = [] # defines block devices (volumes) to attach to instance
            for vol in self.volumes:
                block_device = {
                    'DeviceName': vol['device'],
                    'Ebs': # EBS is basically a storage device that is being attached to your instance virtually
                    {
                        'VolumeSize': vol['size_gb'],
                        'DeleteOnTermination': True # deletes volume when instance is terminated
                    }
                }
                BlockDeviceMappings.append(block_device)

                # commands for mounting volume on instance
                self.userData += 'sudo mkfs -t ' + vol['type'] + ' ' + vol['device'] + '\n'
                self.userData += 'sudo mkdir '+ vol['mount'] + '\n'
                self.userData += 'sudo mount -o rw' + vol['device'] + ' ' + vol['mount'] + '\n'

            # create public key based off .pem file and store contents in user_key
            user_public_key = os.popen(f'ssh-keygen -y -f ' + self.name + '_KEY.pem').readlines() # os.popen opens pipe to or from command so in this case it's opening file and reading it
            user_key = user_public_key[0].strip("\n") # there is a return statement at the end of the key that we need to strip otherwise it messes up in the remote machine

            # add users and allow them SSH access
            for user in self.users:
                username = user['login']
                self.userData += 'adduser ' + username + '\n' # create user
                echo_cmd = 'echo ' + '\\\"' + username + ' ALL=(ALL) NOPASSWD:ALL\\\" >> /etc/sudoers.d/cloud_init' # adds username to sudoers file
                self.userData += 'sudo sh -c \"' + echo_cmd + '\"\n' # executes the sudoers command on the machine
                self.userData += 'mkdir /home/' + username + '/.ssh\n' # creates ssh directory for user
                # put public key content in authorized_keys
                cmd = 'echo ' + user_key + ' >> /home/' + username + '/.ssh/authorized_keys'
                self.userData += 'sudo sh -c \"' + cmd + '\"\n'
            
            # key name for instance
            key_name = self.name + '_KEY'

            # create instance
            ec2_instance = self.ec2_resource.create_instances(  
                                                                ImageId=self.ami_id,
                                                                MinCount=self.min_count,
                                                                MaxCount=self.max_count,
                                                                KeyName= key_name,
                                                                InstanceType=self.instance_type,
                                                                BlockDeviceMappings=BlockDeviceMappings,
                                                                UserData = self.userData, 
                                                                NetworkInterfaces=[
                                                                       {'NetworkInterfaceId': self.network_interface_id,
                                                                        'DeviceIndex': 0}],
                                                            )
            print("EC2 Instance Created Successfully\n")
            print("Waiting for instance to start up...\n")
            
            # get instance ID and wait for it to be up and running
            self.ec2_instance_id = ec2_instance[0].id
            instance_resource = self.ec2_resource.Instance(self.ec2_instance_id)
            instance_resource.wait_until_running()

            print("Getting IP address...\n")
            instances_info = self.ec2_client.describe_instances(InstanceIds = [self.ec2_instance_id])
            for reservation in instances_info['Reservations']:
                for instance in reservation['Instances']:
                    self.ip_address = instance.get('PublicIpAddress')
                    print('IP Address found! Please use this address to ssh into your instance: ' + self.ip_address)
                    print('Example: ssh -i FETCH_REWARDS_KEY.pem user1@' + self.ip_address)
                    
        except Exception as e:
            print(e)
            


def main():
    # initialize class
    inst = EC2()
    # create instance
    inst.create_instance()

if __name__ == '__main__':
    main()

