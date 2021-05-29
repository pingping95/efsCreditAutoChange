import boto3
import datetime

p_name = 'default'
r_name = 'ap-northeast-2'

session = boto3.session.Session(profile_name=p_name)

efs_cli = session.client(service_name='efs', region_name=r_name)
sns_cli = session.client(service_name='sns', region_name=r_name)
lambda_cli = session.client(service_name='lambda', region_name=r_name)
event_cli = session.client(service_name='events', region_name=r_name)

efs_id = "fs-fa20929a"

efs_mode = "bursting"
efs_mibps = 30


before_efs_mode = efs_mode

efs_updater = efs_cli.update_file_system(
    FileSystemId=efs_id,
    ThroughputMode="provisioned",
    ProvisionedThroughputInMibps=efs_mibps)

print(efs_updater)