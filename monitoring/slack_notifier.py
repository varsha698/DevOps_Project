import json
import urllib.request
import urllib.parse
import os

def handler(event, context):
    """Lambda function to send CloudWatch alarms to Slack"""
    
    webhook_url = os.environ['SLACK_WEBHOOK_URL']
    
    # Parse SNS message
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    
    # Extract alarm information
    alarm_name = sns_message.get('AlarmName', 'Unknown Alarm')
    new_state = sns_message.get('NewStateValue', 'UNKNOWN')
    reason = sns_message.get('NewStateReason', 'No reason provided')
    timestamp = sns_message.get('StateChangeTime', '')
    
    # Determine color based on state
    color = "danger" if new_state == "ALARM" else "good" if new_state == "OK" else "warning"
    emoji = "🔴" if new_state == "ALARM" else "✅" if new_state == "OK" else "⚠️"
    
    # Create Slack message
    slack_message = {
        "text": f"{emoji} CloudWatch Alarm: {alarm_name}",
        "attachments": [
            {
                "color": color,
                "fields": [
                    {
                        "title": "Alarm Name",
                        "value": alarm_name,
                        "short": True
                    },
                    {
                        "title": "State",
                        "value": new_state,
                        "short": True
                    },
                    {
                        "title": "Reason",
                        "value": reason,
                        "short": False
                    },
                    {
                        "title": "Time",
                        "value": timestamp,
                        "short": True
                    }
                ]
            }
        ]
    }
    
    # Send to Slack
    data = json.dumps(slack_message).encode('utf-8')
    req = urllib.request.Request(webhook_url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        response = urllib.request.urlopen(req)
        return {
            'statusCode': 200,
            'body': json.dumps('Message sent to Slack')
        }
    except Exception as e:
        print(f"Error sending to Slack: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

