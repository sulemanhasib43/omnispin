import json
import yaml
from aws_cdk import aws_eks as eks, aws_ssm as ssm
from constructs import Construct
import aws_cdk as cdk
from utils.stack_util import add_tags_to_stack


class Z2jhDeployStack(cdk.Stack):
    """
    Pipeline Stack
    """

    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # config = self.node.try_get_context("env_config")

        add_tags_to_stack(self, config)

        self.__cluster_init()
        self.__install_z2jh_with_helm()

    def __cluster_init(self):
        # Cluster
        self.cluster_name = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/cluster/name"
        )

        self.kubectl_role = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/kubectl/role"
        )

        self.oidc_arn = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/oidc/arn"
        )

        self.provider = eks.OpenIdConnectProvider.from_open_id_connect_provider_arn(
            self, "oidc_provider", self.oidc_arn
        )

        self.cluster = eks.Cluster.from_cluster_attributes(
            self,
            "z2jh",
            cluster_name=self.cluster_name,
            kubectl_role_arn=self.kubectl_role,
            open_id_connect_provider=self.provider,
        )

    def __install_z2jh_with_helm(self):
        with open("./etc/jhConfig.yaml", "r") as file:
            configuration = yaml.safe_load(file)

        with open("./etc/jhConfig.json", "w") as json_file:
            json.dump(configuration, json_file)

        jupyter_config = json.load(open("./etc/jhConfig.json"))
        # Add and Apply Helm Chart
        self.cluster.add_helm_chart(
            "JupyterHub",
            chart="jupyterhub",
            repository="https://jupyterhub.github.io/helm-chart/",
            namespace="z2jh",
            version="2.0.0",
            values=jupyter_config,
            wait=True,
        )
