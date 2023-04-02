from aws_cdk import aws_ec2 as ec2
from constructs import Construct
import aws_cdk as cdk
from .cluster_props import ClusterProps
from utils.stack_util import add_tags_to_stack


class TDPConStack(cdk.Stack):
    """
    Setup VPC Peering between Vantage existing VPC and K8s VPC
    1. Get required resource IDs via SSM and its done in `cluster_props.py`
        - VPC
        - CIDR
        - Routing Table IDs
        - Peering Conection Id
    2. Create Peering connections between VPCs
    3. Setup Routes EKS to TD and vice-versa.
    """

    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # config = self.node.try_get_context("env_config")

        add_tags_to_stack(self, config)

        self.cluster_props = ClusterProps(self, "cluster_props")

        self.__peering_connection()
        self.__routes_td()
        self.__routes_eks()

    def __peering_connection(self):
        self.peering_connection = ec2.CfnVPCPeeringConnection(
            self,
            "Z2jhTDVPCPeeringConnection",
            peer_vpc_id=self.cluster_props.td_vpc,
            vpc_id=self.cluster_props.eks_vpc,
        )

    def __routes_td(self):
        routes = [1, 2, 3]
        for route in routes:

            ec2.CfnRoute(
                self,
                f"TdToEks{route}",
                route_table_id=eval(f"self.cluster_props.td_private_routetable{route}"),
                destination_cidr_block=self.cluster_props.eks_vpc_cidr,
                vpc_peering_connection_id=self.peering_connection.attr_id,
            )

    def __routes_eks(self):
        routes = [1, 2, 3]
        for route in routes:

            ec2.CfnRoute(
                self,
                f"EksToTd{route}",
                route_table_id=eval(f"self.cluster_props.eks_private_routetable{route}"),
                destination_cidr_block=self.cluster_props.td_vpc_cidr,
                vpc_peering_connection_id=self.peering_connection.attr_id,
            )
