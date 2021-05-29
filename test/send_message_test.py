import boto3
import datetime

p_name = 'default'
r_name = 'ap-northeast-2'

session = boto3.session.Session(profile_name=p_name)

efs_cli = session.client(service_name='efs', region_name=r_name)
sns_cli = session.client(service_name='sns', region_name=r_name)
lambda_cli = session.client(service_name='lambda', region_name=r_name)
event_cli = session.client(service_name='events', region_name=r_name)

efs_id = "fs-f474d695"

cron_date = datetime.datetime.today() + datetime.timedelta(days=1, minutes=10)
expression = '"cron(' + str(cron_date.minute) + ' ' + str(cron_date.hour) + ' ' + str(cron_date.day) + ' * ? *' + ')'


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
        if arn:
            response = sns_cli.publish(
                Subject=subject,
                TopicArn=arn,
                Message=message
            )
            if not response_check(response):
                raise Exception
            print('[Successed Send Email to Admin]')
        else:
            print('[Failed Send Email to Admin]\nThis lambda does not have a topicArn tag.')
        return True
    except Exception:
        print('[Failed Send Email to Admin]')
        return False

before_mode = "bursting"
after_mode = "provisioned"

efs_name = "TEST_EFS"
sns_message = "EFS Credit이 성공적으로 변경되었습니다. \n대상 : " + efs_id + "\n변경 사항: " + before_mode + " -> " + after_mode + "\n변경 시점: 2021-05-26"
sns_arn = "arn:aws:sns:ap-northeast-2:001243379513:EFS_Credit_Low"
                
send_message_to_admin(
    subject="[EFS Automation Alarm Success] " + efs_name,
    message=sns_message,
    arn=sns_arn
)