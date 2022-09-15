import os
from urllib.parse import urljoin

import requests

from . import consts, backend

SLACK_WEBHOOK = os.environ.get(consts.SLACK_WEBHOOK_KEY)


def get_base_url(source_id):
    if "dev" in source_id:
        return os.environ.get(consts.BASEURL_DEV)
    else:
        return os.environ.get(consts.BASEURL_PROD)

def get_requested_feature_classes(analysis_job_id, source_id):
    try:
        resp = backend.api.request('GET', urljoin(get_base_url(source_id), '/api/analysis-job/{}/'.format(analysis_job_id)), timeout=5)
        return resp['target_classes']
    except requests.exceptions.RequestException:
        return None

def get_available_features_classes(source_id):
    group_class_id = 70
    try:
        resp = backend.api.request('GET', urljoin(get_base_url(source_id), '/api/feature-class-group/{}/'.format(group_class_id)), timeout=5)
        return resp['classes']
    except requests.exceptions.RequestException:
        return None

def get_requested_class_statuses(requested_classes,source_id):
    available_classes = get_available_features_classes(source_id)
    # returns a list of requested classes along with a boolean available status value
    return list(map(lambda p_class: {'class_id': p_class, 'status': p_class in available_classes}, requested_classes))



def post_to_slack(blocks):
    res = requests.post(SLACK_WEBHOOK, json={"text": "Feature Classes 👁", "blocks": blocks })
    print(res.content)


def format_str(s, max_length=40):
    if len(s) > max_length:
        return f'...{s[-max_length+3:]}'
    return s.ljust(max_length)


def send_slack_message(pfcs_w_status):
    ids, statuses = [], []
    for i, pfc in enumerate(pfcs_w_status, 1):
        class_id, status = pfc['class_id'], pfc['status']
        status_string = "✅ " if status else "❌ "

        ids.append(str(class_id))
        statuses.append(status_string)

        if i % 20 == 0 or i == len(pfcs_w_status):
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Upcoming requested Classes 👁"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": "*Feature Class Id*"},
                        {"type": "mrkdwn", "text": "*Status*"},
                        {"type": "plain_text", "text": "\n".join(ids)},
                        {"type": "plain_text", "text": "\n".join(statuses)},
                    ],
                }
            ]
            post_to_slack(blocks)
            ids, status = [], []


def lambda_handler(event, context):
    analysis_job_id = event['analysis_job_id']
    source_id = event['source_id']

    # Get feature classes for the specified analysis job.
    requested_feature_classes = get_requested_feature_classes(analysis_job_id, source_id)
    
    # Get 'available' feature classes and create list of prioritized feature_classes that still need more training
    requested_feature_classes_w_status = get_requested_class_statuses(requested_feature_classes, source_id)

    # Report to team via slack
    if(any(pfc['status'] == False for pfc in requested_feature_classes_w_status)):
        send_slack_message(requested_feature_classes_w_status)
