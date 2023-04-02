from aws_cdk import (
    aws_route53 as route53,
    aws_eks as eks,
)
from constructs import Construct
import aws_cdk as cdk
from cdk_pipeline.cluster_props import ClusterProps
from utils.stack_util import add_tags_to_stack


class R53LbRecord(cdk.Stack):
    """
    Create a z2jh.spt-dev.data-lab.io or z2jh.spt.data-lab.io
    It will be an A record and of Alias Type. Region is us-west-2
    Alias to Classic Load Balancer e.g.
    dualstack.a9a62625b0b23443eb498f169df86569-2132870744.us-west-2.elb.amazonaws.com
    1. Get Loadbalancer address via k8s serviceName: proxy-public available in z2jh nameSpace
    2. Pass that lb name to r53 for record creation
    """

    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # config = self.node.try_get_context("env_config")

        add_tags_to_stack(self, config)

        self.cluster_props = ClusterProps(self, "cluster_props")

        self.__z2jh_service_address()
        self.__route53_record()

    def __z2jh_service_address(self):
        self.z2jh_service_address = eks.KubernetesObjectValue(
            self,
            "LoadBalancerAttribute",
            cluster=self.cluster_props.cluster,
            object_type="service",
            object_name=self.cluster_props.service_name,
            object_namespace=self.cluster_props.namesapce,
            json_path=".status.loadBalancer.ingress[0].hostname",
        )

    def __route53_record(self):
        route53.CnameRecord(
            self,
            "CnameZ2jhRecord",
            record_name="z2jh",
            zone=self.cluster_props.zone,
            domain_name=self.z2jh_service_address.value,
        )
