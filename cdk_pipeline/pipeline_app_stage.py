import aws_cdk as cdk
from constructs import Construct
from cdk_pipeline.eks_cluster_deploy import EksStack
from cdk_pipeline.z2jh_deploy import Z2jhDeployStack
from cdk_pipeline.r53_lb_record import R53LbRecord
from cdk_pipeline.td_peering_connection import TDPConStack


class ClusterDeployStage(cdk.Stage):
    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        EksStack(self, "EksStack", config)


class Z2jhDeployStage(cdk.Stage):
    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        Z2jhDeployStack(self, "Z2jhDeployStack", config)


class R53EntryStage(cdk.Stage):
    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        R53LbRecord(self, "R53EntryStack", config)


class TDPConStage(cdk.Stage):
    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        TDPConStack(self, "TDPConStack", config)
