"""
All things network.
"""

import paco.models.applications
import paco.models.iam
from paco.models.base import Parent, Name, Named, Deployable
from paco.models import schemas
from paco.models import vocabulary
from zope.interface import implementer
from zope.schema.fieldproperty import FieldProperty
from paco.models import loader
from paco.models import references

@implementer(schemas.INetworkEnvironments)
class NetworkEnvironments(Named, dict):
    pass


@implementer(schemas.INetworkEnvironment)
class NetworkEnvironment(Named, Deployable, dict):
    """
    Object attrs:
        - environments : dict : Network Environment
        - vpc : obj : instance of VPC model class
        - segments : obj : what are these?

    Container:
        - Dictionary of Environment objects
    """
    availability_zones = FieldProperty(schemas.INetworkEnvironment["availability_zones"])
    vpc = FieldProperty(schemas.INetworkEnvironment["vpc"])

    def environment_pairs(self):
        "Returns a List of Tuples of sorted Environment pairs"
        # used to build UI
        pairs = []
        count = 0
        temp_env = None
        envs = list(self.values())
        for env in envs:
            if count == 0:
                temp_env = env
                count += 1
            else:
                pairs.append( (temp_env, env) )
                count = 0
        if count == 1: # got a left-over
            pairs.append( (temp_env, None))
        return pairs

    @property
    def environments(self):
        return self


@implementer(schemas.IEnvironment)
class Environment(Named, dict):

    @property
    def env_regions(self):
        """Filter out the default and only return EnvironmentRegion instances"""
        results = {}
        for k, v in self.items():
            if k != 'default':
                results[k] = v
        return results


@implementer(schemas.IEnvironmentDefault)
class EnvironmentDefault(Named, dict):

    def __init__(self, name, __parent__):
        super().__init__(name, __parent__)

        # applications
        self.applications = paco.models.applications.ApplicationEngines('applications', self)
        self.applications.title = 'Applications'
        self.__setitem__('applications', self.applications)

        # network
        self.network = Network('network', self)
        self.network.title = 'Network'
        self.__setitem__('network', self.network)

        # secrets_manager
        self.secrets_manager = paco.models.applications.SecretsManager('secrets_manager', self)
        self.secrets_manager.title = 'SecretsManager'
        self.__setitem__('secrets_manager', self.secrets_manager)

        # backup_vaults
        self.backup_vaults = paco.models.backup.BackupVaults('secrets_manager', self)
        self.backup_vaults.title = 'Backup Vaults'
        self.__setitem__('backup_vaults', self.backup_vaults)


@implementer(schemas.IEnvironmentRegion)
class EnvironmentRegion(EnvironmentDefault, Deployable, dict):

    @property
    def title_or_name(self):
        return self.region_full_name

    @property
    def region(self):
        # an EnvironmentRegion *must* always be a valid region name
        return self.__name__

    @property
    def region_full_name(self):
        return vocabulary.aws_regions[self.__name__]['full_name']


@implementer(schemas.INetwork)
class Network(NetworkEnvironment):
    aws_account = FieldProperty(schemas.INetwork["aws_account"])

    def resolve_ref(self, ref):
        if ref.resource_ref == 'aws_account':
            return self.aws_account
        return None

@implementer(schemas.IVPCPeeringRoute)
class VPCPeeringRoute(Parent):
    segment = FieldProperty(schemas.IVPCPeeringRoute["segment"])
    cidr = FieldProperty(schemas.IVPCPeeringRoute["cidr"])

@implementer(schemas.IVPCPeering)
class VPCPeering(Named, Deployable):
    "VPC Peering"
    peer_role_name = FieldProperty(schemas.IVPCPeering["peer_role_name"])
    peer_vpcid = FieldProperty(schemas.IVPCPeering["peer_vpcid"])
    peer_account_id = FieldProperty(schemas.IVPCPeering["peer_account_id"])
    peer_region = FieldProperty(schemas.IVPCPeering["peer_region"])
    network_environment  = FieldProperty(schemas.IVPCPeering["network_environment"])

@implementer(schemas.IVPC)
class VPC(Named, Deployable):
    "VPC"
    cidr = FieldProperty(schemas.IVPC["cidr"])
    enable_dns_hostnames = FieldProperty(schemas.IVPC["enable_dns_hostnames"])
    enable_dns_support = FieldProperty(schemas.IVPC["enable_dns_support"])
    enable_internet_gateway = FieldProperty(schemas.IVPC["enable_internet_gateway"])
    nat_gateway = FieldProperty(schemas.IVPC["nat_gateway"])
    vpn_gateway = FieldProperty(schemas.IVPC["vpn_gateway"])
    private_hosted_zone = FieldProperty(schemas.IVPC["private_hosted_zone"])
    security_groups = FieldProperty(schemas.IVPC["security_groups"])
    segments = FieldProperty(schemas.IVPC["segments"])
    peering = FieldProperty(schemas.IVPC["peering"])

    def resolve_ref(self, ref):
        if ref.last_part == 'vpc':
            return self
        return self.resolve_ref_obj.resolve_ref(ref)

@implementer(schemas.IInternetGateway)
class InternetGateway(Deployable):
    pass

@implementer(schemas.INATGateway)
class NATGateway(Named, Deployable, dict):
    availability_zone = FieldProperty(schemas.INATGateway["availability_zone"])
    segment = FieldProperty(schemas.INATGateway["segment"])
    default_route_segments = FieldProperty(schemas.INATGateway["default_route_segments"])

@implementer(schemas.IVPNGateway)
class VPNGateway(Deployable, dict):
    pass

@implementer(schemas.IPrivateHostedZone)
class PrivateHostedZone(Deployable):
    name = FieldProperty(schemas.IPrivateHostedZone["name"])
    vpc_associations = FieldProperty(schemas.IPrivateHostedZone["vpc_associations"])

    def __init__(self):
        self.vpc_associations = []

    def resolve_ref(self, ref):
        if ref.last_part == 'private_hosted_zone':
            return self
        return self.resolve_ref_obj.resolve_ref(ref)
#@implementer(schemas.ISecurityGroups)
#class SecurityGroups(dict):
#    pass

@implementer(schemas.ISecurityGroup)
class SecurityGroup(Named, Deployable):
    group_name = FieldProperty(schemas.ISecurityGroup["group_name"])
    group_description = FieldProperty(schemas.ISecurityGroup["group_description"])
    ingress = FieldProperty(schemas.ISecurityGroup["ingress"])
    egress = FieldProperty(schemas.ISecurityGroup["egress"])

    def resolve_ref(self, ref):
        return ref.resource.resolve_ref_obj.resolve_ref(ref)


@implementer(schemas.ISecurityGroupRule)
class SecurityGroupRule():
    name = FieldProperty(schemas.ISecurityGroupRule["name"])
    cidr_ip = FieldProperty(schemas.ISecurityGroupRule["cidr_ip"])
    cidr_ip_v6 = FieldProperty(schemas.ISecurityGroupRule["cidr_ip_v6"])
    description = FieldProperty(schemas.ISecurityGroupRule["description"])
    from_port = FieldProperty(schemas.ISecurityGroupRule["from_port"])
    protocol = FieldProperty(schemas.ISecurityGroupRule["protocol"])
    to_port = FieldProperty(schemas.ISecurityGroupRule["to_port"])
    port = FieldProperty(schemas.ISecurityGroupRule["port"])

@implementer(schemas.IIngressRule)
class IngressRule(Parent, SecurityGroupRule):
    source_security_group = FieldProperty(schemas.IIngressRule["source_security_group"])

@implementer(schemas.IEgressRule)
class EgressRule(Parent, SecurityGroupRule):
    destination_security_group = FieldProperty(schemas.IEgressRule["destination_security_group"])

@implementer(schemas.ISegment)
class Segment(Named, Deployable):
    internet_access = FieldProperty(schemas.ISegment["internet_access"])
    az1_cidr = FieldProperty(schemas.ISegment["az1_cidr"])
    az2_cidr = FieldProperty(schemas.ISegment["az2_cidr"])
    az3_cidr = FieldProperty(schemas.ISegment["az3_cidr"])
    az4_cidr = FieldProperty(schemas.ISegment["az4_cidr"])
    az5_cidr = FieldProperty(schemas.ISegment["az5_cidr"])
    az6_cidr = FieldProperty(schemas.ISegment["az6_cidr"])

    def resolve_ref(self, ref):
        if ref.resource_ref == 'az1_cidr':
            return self.az1_cidr
        else:
            stack = self.resolve_ref_obj.resolve_ref(ref)
            if stack == None:
                raise StackException(PacoErrorCode.Unknown)
            else:
                return stack
        return None

