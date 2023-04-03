from aws_cdk import (
    aws_eks as eks,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_ssm as ssm,
    CfnJson,
    Fn,
    aws_autoscaling as autoscaling,
    aws_efs as efs,
)
from constructs import Construct
import aws_cdk as cdk

# from aws_cdk.lambda_layer_kubectl import KubectlLayer  #KubectlV24Layer
# import cdk8s
import yaml
from aws_cdk.lambda_layer_kubectl_v24 import KubectlV24Layer
from utils.stack_util import add_tags_to_stack


class EksStack(cdk.Stack):
    """
    EKS Stack
    """

    def __init__(self, scope: Construct, construct_id: str, config, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Apply common tags to stack resources.
        add_tags_to_stack(self, config)

        # Create Resources
        self.__create_cluster()
        self.__cluster_auto_scaling_group()
        self.__cluster_auto_scaler()
        self.__efs_csi_drivers()
        self.__efs_file_system()
        self.__efs_storage_class()
        self.__create_ssm_parameters()

    def __create_cluster(self):
        # EKS Cluster construct
        self.cluster = eks.Cluster(
            self,
            "z2jh",
            version=eks.KubernetesVersion.V1_24,
            kubectl_layer=KubectlV24Layer(self, "kubectl"),
            output_cluster_name=True,
            default_capacity=0,
            prune=True,
        )

    def __cluster_auto_scaling_group(self):
        # Cluster Auto Scaling
        # Cluster Auto Scaling Group of Managed Nodes
        self.cluster.add_auto_scaling_group_capacity(
            "AutoScaling",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.M5, ec2.InstanceSize.LARGE
            ),
            bootstrap_enabled=True,
            min_capacity=2,
            max_capacity=6,
            block_devices=[
                autoscaling.BlockDevice(
                    device_name="/dev/xvda",
                    volume=autoscaling.BlockDeviceVolume.ebs(
                        volume_size=100,
                        volume_type=autoscaling.EbsDeviceVolumeType.GP3,
                        throughput=125,
                        delete_on_termination=True,
                    ),
                ),
            ],
        )

        # Policy
        k8s_asg_policy = iam.PolicyStatement(
            actions=[
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeAutoScalingInstances",
                "autoscaling:DescribeLaunchConfigurations",
                "autoscaling:DescribeTags",
                "autoscaling:SetDesiredCapacity",
                "autoscaling:TerminateInstanceInAutoScalingGroup",
                "ec2:DescribeLaunchTemplateVersions",
            ],
            resources=["*"],
        )
        self.cluster.add_service_account(
            "ca", namespace="kube-system", name="cluster-autoscaler"
        ).add_to_principal_policy(k8s_asg_policy)

    def __yaml_manifest(self, file_locatoin: str, name: str):
        with open(file_locatoin, "r") as f:
            files = f.read().split("---")

            for file in files:
                manifest = yaml.safe_load(file)
                if manifest is not None:
                    self.cluster.add_manifest(
                        manifest["kind"] + name,
                        manifest,
                    )

    def __cluster_auto_scaler(self):
        # Cluster Auto Scaler Manifest
        self.__yaml_manifest("./etc/cluster-autoscaler-autodiscover.yaml", "ca")
        ##############
        # Eviction Policy Needed!!!  #
        ##############

    def __efs_csi_drivers(self):
        # Policy
        oidc_provider_arn = (
            self.cluster.open_id_connect_provider.open_id_connect_provider_arn
        )

        oidc_provider_arn_pieces = Fn.split("oidc-provider/", oidc_provider_arn)

        oidc_provider = Fn.select(1, oidc_provider_arn_pieces)

        string_equals = {
            f"{oidc_provider}:sub": "system:serviceaccount:kube-system:efs-csi-controller-sa"
        }
        oidc_provider_name = CfnJson(self, "OidcCondition", value=string_equals)

        # Extract the resource name
        oidc_provider_resource_name = oidc_provider_name.value

        cap_string_like = {"aws:RequestTag/efs.csi.aws.com/cluster": "true"}
        cap_request_tag_efs = CfnJson(self, "CapCondition", value=cap_string_like)

        dap_string_equals = {"aws:ResourceTag/efs.csi.aws.com/cluster": "true"}
        dap_request_tag_efs = CfnJson(self, "DapCondition", value=dap_string_equals)

        k8s_efs_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "elasticfilesystem:DescribeAccessPoints",
                        "elasticfilesystem:DescribeFileSystems",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    actions=[
                        "elasticfilesystem:CreateAccessPoint",
                    ],
                    resources=["*"],
                    conditions={"StringLike": cap_request_tag_efs},
                ),
                iam.PolicyStatement(
                    actions=[
                        "elasticfilesystem:DeleteAccessPoint",
                    ],
                    resources=["*"],
                    conditions={"StringEquals": dap_request_tag_efs},
                ),
            ],
        )
        k8s_efs_csi_role = iam.Role(
            self,
            "AmazonEKS_EFS_CSI_DriverRole",
            assumed_by=iam.CompositePrincipal(
                iam.FederatedPrincipal(
                    oidc_provider_arn,
                    conditions={"StringEquals": oidc_provider_resource_name},
                    assume_role_action="sts:AssumeRoleWithWebIdentity",
                ),
            ),
            inline_policies={"policy": k8s_efs_policy},
        )
        efs_annontations = {
            "eks.amazonaws.com/role-arn": str(k8s_efs_csi_role.role_arn)
        }
        self.cluster.add_service_account(
            "efs",
            annotations=efs_annontations,
            namespace="kube-system",
            name="efs-csi-controller-sa",
        )
        # EFS CSI Driver
        self.__yaml_manifest("./etc/public-efs-driver.yaml", "efs")

        # EFS Security Groups Settings
        self.cluster_vpc = self.cluster.vpc
        cluster_cidr = self.cluster.vpc.vpc_cidr_block
        self.allow_efs_traffic = ec2.SecurityGroup(
            self,
            "EksAllowInboundEfsTraffic",
            vpc=self.cluster_vpc,
            allow_all_outbound=True,
            description="Allow Inbound EFS Traffic on EKS Cluster",
        )
        self.allow_efs_traffic.add_ingress_rule(
            peer=ec2.Peer.ipv4(cluster_cidr),
            connection=ec2.Port.tcp(2049),
            description="Allow EFS in EKS VPC",
        )

        # Create EFS File System

    def __efs_file_system(self):
        self.efs_file_system = efs.FileSystem(
            self,
            "Z2jhEfsFileSystem",
            vpc=self.cluster_vpc,
            lifecycle_policy=efs.LifecyclePolicy.AFTER_14_DAYS,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            out_of_infrequent_access_policy=efs.OutOfInfrequentAccessPolicy.AFTER_1_ACCESS,
            security_group=self.allow_efs_traffic,
        )

    def __efs_storage_class(self):
        efs_storage_class = {
            "kind": "StorageClass",
            "apiVersion": "storage.k8s.io/v1",
            "metadata": {"name": "efs-sc"},
            "provisioner": "efs.csi.aws.com",
            "parameters": {
                "provisioningMode": "efs-ap",
                "fileSystemId": f"{self.efs_file_system.file_system_id}",
                "directoryPerms": "700",
                "gidRangeStart": "1000",
                "gidRangeEnd": "2000",
            },
        }
        self.cluster.add_manifest(
            "EfsStorageClass",
            efs_storage_class,
        )

    def __create_ssm_parameters(self):
        ssm.StringParameter(
            self,
            "ClusterNameParameter",
            parameter_name="/omnispin/eks/cluster/name",
            string_value=self.cluster.cluster_name,
        )

        ssm.StringParameter(
            self,
            "KubectlRole",
            parameter_name="/omnispin/eks/kubectl/role",
            string_value=str(
                self.cluster.admin_role.role_arn,
            ),
        )

        ssm.StringParameter(
            self,
            "OIDCProvider",
            parameter_name="/omnispin/eks/oidc/arn",
            string_value=str(
                self.cluster.open_id_connect_provider.open_id_connect_provider_arn,
            ),
        )

        ssm.StringParameter(
            self,
            "EKSVpc",
            parameter_name="/omnispin/eks/vpc",
            string_value=str(
                self.cluster.vpc.vpc_id,
            ),
        )

        ssm.StringParameter(
            self,
            "EKSVpcCidr",
            parameter_name="/omnispin/eks/vpc/cidr",
            string_value=str(
                self.cluster.vpc.vpc_cidr_block,
            ),
        )

        ssm.StringParameter(
            self,
            "EfsFileSystemId",
            parameter_name="/omnispin/efs/id",
            string_value=str(
                self.efs_file_system.file_system_id,
            ),
        )

        subnets = self.cluster.vpc.private_subnets

        for i, subnet in enumerate(subnets):
            ssm.StringParameter(
                self,
                f"EKSVpcPrivateRouteTable{i+1}",
                parameter_name=f"/omnispin/eks/vpc/private/routetable{i+1}",
                string_value=str(subnet.route_table.route_table_id),
            )

        ssm.StringParameter(
            self,
            "EKSSecurityGroupId",
            parameter_name="/omnispin/eks/security_group/id",
            string_value=str(
                self.cluster.cluster_security_group_id,
            ),
        )
