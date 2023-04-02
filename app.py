#!/usr/bin/env python3
import sys

import aws_cdk as cdk

from cdk_pipeline.pipeline_stack import CdkZ2jhPipelineStack

from utils import config_util

app = cdk.App()

# Ensure environment(stage) is passed in context to pick correct values from context
stage = app.node.try_get_context("stage")
if stage is None or stage == "unknown":
    sys.exit(
        "You need to set the target stage." " USAGE: cdk <command> -c stage=dev <stack>"
    )

# Load stage config and set cdk environment
config = config_util.load_config(stage)

# this will allow using get_context where we don't specifically want to pass parameters
app.node.set_context("env_config", config)

# Setting up AWS Account and Region from yaml config
env = cdk.Environment(
    account=config["aws"]["account"],
    region=config["aws"]["region"],
)

# Passing stage to build CFT specific to an environment
CdkZ2jhPipelineStack(
    app,
    "CdkZ2jhPipelineStack",
    stage=stage,
    env=env,
)

app.synth()
