import aws_cdk as cdk
from constructs import Construct
from aws_cdk.pipelines import CodePipelineSource, ShellStep
from aws_cdk import (
    pipelines,
)
from .pipeline_app_stage import (
    ClusterDeployStage,
    Z2jhDeployStage,
    R53EntryStage,
    TDPConStage,
)
from utils.stack_util import add_tags_to_stack
from utils.config_util import add_commit_info_to_config


class CdkZ2jhPipelineStack(cdk.Stack):
    """
    This is a Pipeline Stack for Z2JH
    """

    def __init__(self, scope: Construct, construct_id: str, stage, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Initialize config variable and get context from env_config which we set in app.py
        config = self.node.try_get_context("env_config")

        # Configure Codepipeline source i.e., repo, branch and connection arn
        source_pipeline = CodePipelineSource.connection(
            config["git"]["repo"],
            config["git"]["branch"],
            connection_arn=config["git"]["connection_arn"],
        )

        # Create self-mutated pipeline construct. pipelines.CodePipeline is a self-mutated pipeline
        # Tags are important part of CI/CD process to identify which git commit is responsible for CFT Deploymnet
        pipeline = pipelines.CodePipeline(
            self,
            "Pipeline",
            pipeline_name="CdkZeroToJupyterHub",
            synth=ShellStep(
                "Synth",
                input=source_pipeline,
                install_commands=[
                    "npm install -g aws-cdk",
                    "python -m pip install --upgrade pip",
                    "python -m pip install -r requirements.txt",
                ],
                commands=[f"ls -lah && cdk synth -c stage={stage} -vvv"],
                primary_output_directory="cdk.out",
                env={
                    "GIT_REPO": source_pipeline.source_attribute("FullRepositoryName"),
                    "GIT_BRANCH": source_pipeline.source_attribute("BranchName"),
                    "GIT_COMMIT_ID": source_pipeline.source_attribute("CommitId"),
                    "GIT_COMMIT_MESSAGE": source_pipeline.source_attribute(
                        "CommitMessage"
                    ),
                    "GIT_COMMIT_AUTHOR": source_pipeline.source_attribute("AuthorDate"),
                    "GIT_CONNECTION_ARN": source_pipeline.source_attribute(
                        "ConnectionArn"
                    ),
                },
            ),
        )
        # Append git tags to config so they are applied to subsequent stages
        config = add_commit_info_to_config(config=config)

        add_tags_to_stack(self, config)
        # We could add If Statement here to only include this stage if cluster doesn't exist
        eks_cluster = ClusterDeployStage(
            self,
            "ClusterDeploy",
            env=cdk.Environment(
                account=config["aws"]["account"], region=config["aws"]["region"]
            ),
            config=config,
        )
        pipeline.add_stage(eks_cluster)

        pipeline.add_stage(
            Z2jhDeployStage(
                self,
                "Z2jhDeployStage",
                env=cdk.Environment(
                    account=config["aws"]["account"], region=config["aws"]["region"]
                ),
                config=config,
            )
        )

        pipeline.add_stage(
            R53EntryStage(
                self,
                "R53EntryStage",
                env=cdk.Environment(
                    account=config["aws"]["account"], region=config["aws"]["region"]
                ),
                config=config,
            )
        )

        pipeline.add_stage(
            TDPConStage(
                self,
                "TDPeeringConnectionStage",
                env=cdk.Environment(
                    account=config["aws"]["account"], region=config["aws"]["region"]
                ),
                config=config,
            )
        )
