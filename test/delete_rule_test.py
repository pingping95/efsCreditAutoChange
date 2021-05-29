import boto3
import datetime

p_name = 'default'
r_name = 'ap-northeast-2'

session = boto3.session.Session(profile_name=p_name)

efs_cli = session.client(service_name='efs', region_name=r_name)
sns_cli = session.client(service_name='sns', region_name=r_name)
lambda_cli = session.client(service_name='lambda', region_name=r_name)
event_cli = session.client(service_name='events', region_name=r_name)

efs_id = "fs-fd20929d"

rule_name = "test_rule"
lambda_fnc_arn = "arn:aws:lambda:ap-northeast-2:001243379513:function:find_source_event"
lambda_fnc_name = "find_source_event"

# Create Event Bridge rule to change to bursting mode after 24 hours and 10 minutes.
cron_date = datetime.datetime.today() + datetime.timedelta(days=1, minutes=10)
expression = 'cron(' + str(cron_date.minute) + ' ' + str(cron_date.hour) + ' ' + str(
    cron_date.day) + ' * ? *' + ')'

# Delete Event Bridge rule because event rule successfully changed EFS Mode to bursting
# 1. Remove Target
removed_rule = event_cli.remove_targets(
    Rule=rule_name,
    Ids=[
        rule_name,
    ],
    Force=True
)

# 2. Delete Rule
deleted_rule = event_cli.delete_rule(
    Name=rule_name
)

# 3. Delete Trigger from lambda


#
# # 3. Remove Permission
removed_perm = lambda_cli.remove_permission(
    FunctionName=lambda_fnc_arn,
    StatementId="LambdaInvokeRule"
)

print(removed_rule)
print("=========================")
print(deleted_rule)
print("=========================")
print(removed_perm)