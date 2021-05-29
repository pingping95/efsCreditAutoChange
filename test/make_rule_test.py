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

# 1. Put Rule
rule = event_cli.put_rule(
    Name=rule_name,
    ScheduleExpression=expression,
    State="ENABLED"
)

# 2. Put Targets
putted_tg = event_cli.put_targets(
    Rule=rule_name,
    Targets=[   
        {
            "Id": rule_name,
            "Arn": lambda_fnc_arn,
        }
    ]
)

# 3. Add Permission
added_perm = lambda_cli.add_permission(
    FunctionName=lambda_fnc_name,
    StatementId="LambdaInvokeRule",
    Action="lambda:InvokeFunction",
    Principal="events.amazonaws.com",
    SourceArn=rule.get('RuleArn')
)

print(rule)

print(putted_tg)

print(added_perm)