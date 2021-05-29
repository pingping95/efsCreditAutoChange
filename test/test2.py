import boto3
import datetime

p_name = 'default'
r_name = 'ap-northeast-2'

session = boto3.session.Session(profile_name=p_name)

efs_cli = session.client(service_name='efs', region_name=r_name)
sns_cli = session.client(service_name='sns', region_name=r_name)
lambda_cli = session.client(service_name='lambda', region_name=r_name)
event_cli = session.client(service_name='events', region_name=r_name)

efs_id = "fs-35ea5855"

def get_efs_throughput_mode(id):
    response = efs_cli.describe_file_systems(
        FileSystemId=efs_id
    ).get('FileSystems')[0]
    mode = response.get('ThroughputMode')
    return mode

efs_mode = get_efs_throughput_mode(id=efs_id)
efs_name = efs_cli.describe_file_systems(
    FileSystemId=efs_id
).get('FileSystems')[0].get('Name')

print(f"efs mode is {efs_mode}")
print(f"efs name is {efs_name}")