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

from typing import List

from aws_cdk import (
    aws_ssm as ssm,
    core
)

from .lambdas.emr_utilities import EMRUtilities
from .events.emr_events import EMREvents


class ControlPlaneStack(core.Stack):
    def __init__(self, app: core.App, name: str, **kwargs):
        super().__init__(app, name, **kwargs)

        self._emr_utilities = EMRUtilities(self, 'EMRUtilities')

        self._string_parameters = []
        for f in self._emr_utilities.shared_functions:
            self._string_parameters.append(
                ssm.StringParameter(
                    self,
                    '{}_SSMParameter'.format(f.node.id),
                    parameter_name='/emr_launch/control_plane/lambda_arns/emr_utilities/{}'.format(f.function_name),
                    string_value=f.function_arn
                ))

        self._emr_events = EMREvents(
            self,
            'EMREvents',
            cluster_state_change_event=self._emr_utilities.cluster_state_change_event
        )

    @property
    def emr_utilities(self) -> EMRUtilities:
        return self._emr_utilities

    @property
    def string_parameters(self) -> List[ssm.StringParameter]:
        return self._string_parameters

    @property
    def emr_events(self) -> EMREvents:
        return self._emr_events

