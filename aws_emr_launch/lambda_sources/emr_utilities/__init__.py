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
import datetime


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def return_message(code=0, step_ids=None, message='', cluster_id=''):
    return {'Code': code, 'StepIds': step_ids, 'Message': message, 'ClusterId': cluster_id}


class JSONDateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)