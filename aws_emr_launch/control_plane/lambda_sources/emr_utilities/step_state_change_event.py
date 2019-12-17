# Copyright 2019 Amazon.com, Inc. and its affiliates. All Rights Reserved.
#
# Licensed under the Amazon Software License (the 'License').
# You may not use this file except in compliance with the License.
# A copy of the License is located at
#
#   http://aws.amazon.com/asl/
#
# or in the 'license' file accompanying this file. This file is distributed
# on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied. See the License for the specific language governing
# permissions and limitations under the License.

import json
import boto3
import logging
import traceback

from botocore.exceptions import ClientError

ssm = boto3.client('ssm')
sfn = boto3.client('stepfunctions')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

PARAMETER_STORE_PREFIX = '/emr_launch/control_plane/task_tokens/emr_utilities/{}/{}'


def cluster_state_change_key(cluster_id):
    return PARAMETER_STORE_PREFIX.format('cluster_state', cluster_id)


def step_state_change_key(step_id):
    return PARAMETER_STORE_PREFIX.format('step_state', step_id)


def handler(event, context):

    LOGGER.info('Lambda metadata: {} (type = {})'.format(json.dumps(event), type(event)))
    step_id = event['detail']['stepId']
    state = event['detail']['state']
    message = json.loads(event['detail']['message'])

    parameter_name = step_state_change_key(step_id)
    LOGGER.info('Getting TaskToken from Parameter Store: {}'.format(parameter_name))
    try:
        task_token = ssm.get_parameter(Name=parameter_name)['Parameter']['Value']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            task_token = None
        else:
            raise e

    try:
        if task_token is None:
            LOGGER.info('No {} Parameter found'.format(parameter_name))
            return

        if state == 'COMPLETED':
            success = True
            message = {
                'StepId': step_id,
                'StepState': state,
                'Message': message
            }
        elif state in ['CANCELLED', 'FAILED', 'INTERRUPTED']:
            success = False
            message = {
                'StepId': step_id,
                'StepState': state,
                'Message': message
            }
        else:
            LOGGER.info('Sending Task Heartbeat, TaskToken: {}, StepState: {}'.format(task_token, state))
            sfn.send_task_heartbeat(taskToken=task_token)
            return

        LOGGER.info('Removing TaskToken Parameter: {}'.format(parameter_name))
        ssm.delete_parameter(Name=parameter_name)

        if success:
            LOGGER.info('Sending Task Success, TaskToken: {}, Output: {}'.format(task_token, message))
            sfn.send_task_success(taskToken=task_token, output=json.dumps(message))
        else:
            LOGGER.info('Sending Task Failure, TaskToken: {}, Output: {}'.format(task_token, message))
            sfn.send_task_failure(taskToken=task_token, error='ClusterFailedError', cause=json.dumps(message))

    except Exception as e:
        trc = traceback.format_exc()
        s = 'Failed handling state change {}: {}\n\n{}'.format(str(event), str(e), trc)
        LOGGER.error(s)
        if task_token:
            sfn.send_task_failure(taskToken=task_token, error=str(e), cause=s)
        raise e