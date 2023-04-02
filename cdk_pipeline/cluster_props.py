from aws_cdk import (
    aws_eks as eks,
    aws_ssm as ssm,
    aws_route53 as route53,
)
from constructs import Construct


class ClusterProps(Construct):
    """
    Cluster Variables
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        config = self.node.try_get_context("env_config")
        # EKS: Cluster
        self.cluster_name = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/cluster/name"
        )

        self.kubectl_role = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/kubectl/role"
        )

        self.oidc_arn = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/oidc/arn"
        )

        self.eks_vpc = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/vpc"
        )

        self.eks_vpc_cidr = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/vpc/cidr"
        )

        self.eks_private_routetable1 = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/vpc/private/routetable1"
        )

        self.eks_private_routetable2 = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/vpc/private/routetable2"
        )

        self.eks_private_routetable3 = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/vpc/private/routetable3"
        )

        self.eks_security_group_id = ssm.StringParameter.value_for_string_parameter(
            self, "/omnispin/eks/security_group/id"
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

        # ROUT 53: hosted_zone_id and zone_name Based on Account. Need to create a map for this
        hosted_zone_id = config["r53"]["zone_id"]
        zone_name = config["r53"]["zone_name"]
        self.zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "HostedZone", hosted_zone_id=hosted_zone_id, zone_name=zone_name
        )
        self.service_name = "proxy-public"
        self.namesapce = "z2jh"

        # TD: Vantage properties
        self.td_vpc = ssm.StringParameter.value_for_string_parameter(
            self, "/spt/core/vpc"
        )

        self.td_vpc_cidr = ssm.StringParameter.value_for_string_parameter(
            self, "/spt/core/vpcCidrBlock"
        )

        self.td_private_subnet1 = ssm.StringParameter.value_for_string_parameter(
            self, "/spt/core/privateSubnet1"
        )

        self.td_private_subnet2 = ssm.StringParameter.value_for_string_parameter(
            self, "/spt/core/privateSubnet2"
        )

        self.td_private_subnet3 = ssm.StringParameter.value_for_string_parameter(
            self, "/spt/core/privateSubnet3"
        )

        self.td_private_routetable1 = ssm.StringParameter.value_for_string_parameter(
            self, "/spt/core/privateRouteTable1"
        )

        self.td_private_routetable2 = ssm.StringParameter.value_for_string_parameter(
            self, "/spt/core/privateRouteTable2"
        )

        self.td_private_routetable3 = ssm.StringParameter.value_for_string_parameter(
            self, "/spt/core/privateRouteTable3"
        )
