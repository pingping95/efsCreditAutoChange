import boto3
import datetime
from time import sleep

"""
Lambda IAM Policy :

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "sns:publish",
                "lambda:AddPermission",
                "lambda:RemovePermission",
                "lambda:TagResource",
                "lambda:ListTags",
                "elasticfilesystem:UpdateFileSystem",
                "elasticfilesystem:DescribeFileSystems",
                "events:DeleteRule",
                "events:PutTargets",
                "events:DescribeRule",
                "events:EnableRule",
                "events:RemoveTargets",
                "events:ListTargetsByRule",
                "events:DisableRule",
                "events:PutRule",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:CreateLogGroup"
            ],
            "Resource": "*"
        }
    ]
}
"""


def lambda_handler(event, context):
    # Set Variables
    r_name = 'ap-northeast-2'
    lambda_fnc_arn = context.invoked_function_arn
    lambda_fnc_name = context.function_name
    rule_name = "temp_rule"
    print(f"function arn, name : {lambda_fnc_arn}, {lambda_fnc_name}")

    efs_cli = boto3.client(service_name='efs', region_name=r_name)
    sns_cli = boto3.client(service_name='sns', region_name=r_name)
    lambda_cli = boto3.client(service_name='lambda', region_name=r_name)
    event_cli = boto3.client(service_name='events', region_name=r_name)

    def get_lambda_tag(lambda_client, resource_arn):
        response = lambda_client.list_tags(
            Resource=resource_arn
        )
        return response.get('Tags')

    def response_check(res):
        try:
            is_succeeded = True
            status_code = res['ResponseMetadata']['HTTPStatusCode']
            if status_code != 200:
                is_succeeded = False
        except Exception:
            is_succeeded = False
        return is_succeeded

    def send_message_to_admin(subject, message, arn):
        try:
            print(subject)
            print(message)
            print(arn)
            if arn:
                response = sns_cli.publish(
                    Subject=subject,
                    TopicArn=arn,
                    Message=message 
                )
                if not response_check(response):
                    raise Exception
                print('[Successes Send Email to Admin]')
            else:
                print('[Failed Send Email to Admin]\nThis lambda does not have a topicArn tag.')
            return True
        except Exception:
            print('[Failed Send Email to Admin]')
            return False

    def get_efs_throughput_mode(id):
        response = efs_cli.describe_file_systems(
            FileSystemId=id
        ).get('FileSystems')[0]
        mode = response.get('ThroughputMode')
        return mode

    def get_lambda_event_source(event):
        # SNS
        try:
            if event.get('Records')[0].get('EventSource') == 'aws:sns':
                return 'sns'
        except Exception:
            pass
        # Event Bridge
        try:
            if event['source'] == 'aws.events':
                return 'scheduled_event'
        except Exception:
            pass

    # Get provisioned_mibps & sns_arn
    lambda_tags = get_lambda_tag(lambda_cli, lambda_fnc_arn)
    efs_mibps = int(lambda_tags.get('mibps'))
    sns_arn = lambda_tags.get('sns_arn')
    efs_id = lambda_tags.get('efs_id')
    print(efs_id)
    
    print(event)

    # Check who triggered lambda.
    event_src = get_lambda_event_source(event)
    print(f"event source : {event_src}")

    # Check EFS Throughput Mode and get name
    efs_mode = get_efs_throughput_mode(id=efs_id)
    efs_name = efs_cli.describe_file_systems(
        FileSystemId=efs_id
    ).get('FileSystems')[0].get('Name')

    # Source == SNS
    if event_src == "sns":
        # Bursting -> Provisioned
        if efs_mode == "bursting":
            # Update EFS Mode to Provisioned
            efs_cli.update_file_system(
                FileSystemId=efs_id,
                ThroughputMode="provisioned",
                ProvisionedThroughputInMibps=efs_mibps)

            sleep(3)
            after_efs_mode = get_efs_throughput_mode(
                id=efs_id
            )

            if efs_mode != after_efs_mode:
                # Succeeded mode update, Send Success Message to Admin
                success_sns_message = 'Successfully updated ' + efs_name + "\n변경 대상: " + efs_name +\
                            " (" + efs_id + ") " + "\n변경 사항 : " + efs_mode + " => " + after_efs_mode
                send_message_to_admin(
                    subject="[EFS Automation Success] " + efs_name,
                    message=success_sns_message,
                    arn=sns_arn
                    )

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
                print(rule)
                
                # 2. Put Targets
                putted_target = event_cli.put_targets(
                    Rule=rule_name,
                    Targets=[
                        {
                            "Id": rule_name,
                            "Arn": lambda_fnc_arn,
                        }
                    ]
                )
                print(putted_target)

                # 3. Add Permission
                addad_perm = lambda_cli.add_permission(
                    FunctionName=lambda_fnc_name,
                    StatementId="LambdaInvokeRule",
                    Action="lambda:InvokeFunction",
                    Principal="events.amazonaws.com",
                    SourceArn=rule.get('RuleArn')
                )
                print(addad_perm)
                
            else:
                # Failed File System mode update, Send Fail Message to Admin
                failure_sns_message = 'Failed update of ' + efs_name
                send_message_to_admin(
                    subject="[EFS Automation Failure] " + efs_name,
                    message=failure_sns_message,
                    arn=sns_arn
                )

        # If Provisioned
        else:
            print("EFS is already provisioned mode.")

    # Source == Event Bridge
    if event_src == "scheduled_event":
        # Provisioned -> Bursting
        if efs_mode == "provisioned":
            # Update EFS Mode to Bursting

            efs_updater = efs_cli.update_file_system(
                FileSystemId=efs_id,
                ThroughputMode="bursting")
            
            sleep(3)
            after_efs_mode = efs_updater.get('ThroughputMode')

            if efs_mode != after_efs_mode:
                # Succeeded mode update, Send Success Message to Admin
                sns_message = 'Successfully updated ' + efs_name + "\n변경 대상: " + efs_name + " (" + efs_id + ") " + \
                    "\n변경 사항 : " + efs_mode + " => " + \
                    after_efs_mode
                send_message_to_admin(
                    subject="EFS Automation Alarm Success " + efs_name,
                    message=sns_message,
                    arn=sns_arn
                )

                # Delete Event Bridge rule because event rule successfully changed EFS Mode to bursting
                # 1. Remove Target
                removed_rule = event_cli.remove_targets(
                    Rule=rule_name,
                    Ids=[
                        rule_name
                    ]
                )
                print(removed_rule)

                # 2. Delete Rule
                deleted_rule = event_cli.delete_rule(
                    Name=rule_name
                )
                print(deleted_rule)

                # 3. Remove Permission
                removed_perm = lambda_cli.remove_permission(
                    FunctionName=lambda_fnc_arn,
                    StatementId="LambdaInvokeRule"
                )
                print(removed_perm)

            else:
                # Failed File System mode update, Send Fail Message to Admin
                sns_message = 'Failed update of ' + efs_name
                send_message_to_admin(
                    subject="[EFS Automation Failure] " + efs_name,
                    message=sns_message,
                    arn=sns_arn
                )
        else:
            print("EFS is already bursting mode.")
