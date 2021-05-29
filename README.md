# EFS Credit Auto Change Python Script

## 개요

- EFS는 EC2 등과 동일하게 Credit이란 개념이 있으며, 해당 Credit 모드를 다 쓰게 되면 성능이 저하될 수 있다.
- 그 중, Credit 소모량을 결정하는 2가지 모드가 있는데, Bursting Mode와 Provisioned Mode가 있다.
- Credit을 모두 소모하게 되면 Provisioned Mode로 변경되어야 하며, Credit이 꽉 차게 되면 Bursting Mode가 되어야 한다.

## Script에서 고려해야 할 사항

1. Throughput Mode는 변경할 경우 24시간 동안 변경할 수 없다.
    => 1일 10분 후에 Lambda를 Trigger해야 함
2. 모든 변경 사항은 관리자(Admin)에게 Email로 보고되어야 한다.
    1) EFS Credit Low
    2) EFS Mode Changed {} into {} (Provisioned or Bursting)

## 사용 Stack

- CloudWatch Metric, CloudWatch Alarm, CloudWatch Rules
- EFS Throughput Mode
- Lambda
- Python (3.x)
- SNS

## 순서

1. CloudWatch Metric으로 모니터링하다가 Credit이 모두 소진되면, CloudWatch 경보 발생
    : 경보가 울릴 경우 SNS로 각 관리자들에게 Email 발송
3. SNS가 발송될 시, Lambda를 Trigger한다.
    : Lambda에서 Bursting Mode -> Provisioned Mode로 변경
4. Lambda가 실행
    => CloudWatch 현 시간 기준으로 1일 10분 후에 Lambda를 Trigger하는 Event Bridge를 생성
    => 내부 Script로 각 Admin에게 SNS Topic Publish함
5. Event Bridge는 Crontab을 실행시키며, Crontab에 의해 Lambda가 Trigger된다.
6. Lambda가 실행
    : Provisioned Mode -> Bursting Mode로 변경
    : SNS가 발송된다.
    : Event Bridge로 Trigger된 Lambda일 경우 기존의 Event Bridge를 삭제하는 Logic 생성