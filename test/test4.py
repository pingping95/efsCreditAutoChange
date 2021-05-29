# Author : Taehun Kim
# E-Mail : taehun.kim@bespinglobal.com
# Date Created : 2021-05-
# Python Version : 3.9

import boto3
import datetime


# Set Variables
r_name = 'ap-northeast-2'
efs_id = "fs-f474d695"
rule_name = "update_efs_throughput_mode_rule"


efs_cli = boto3.client(service_name='efs', region_name=r_name)
sns_cli = boto3.client(service_name='sns', region_name=r_name)
lambda_cli = boto3.client(service_name='lambda', region_name=r_name)
event_cli = boto3.client(service_name='events', region_name=r_name)


response = lambda_cli.list_event_source_mappings()


print(response)