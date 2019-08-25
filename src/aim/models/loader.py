"""
The loader is responsible for reading an AIM Project and creating a tree of Python
model objects.
"""

import aim.models.services
import itertools, os, copy
import logging
import pkg_resources
import ruamel.yaml
import zope.schema
import zope.schema.interfaces
from aim.models.logging import CloudWatchLogSources, CloudWatchLogSource, MetricFilters, MetricFilter, \
    CloudWatchLogGroups, CloudWatchLogGroup, CloudWatchLogSets, CloudWatchLogSet, CloudWatchLogging, \
    MetricTransformation
from aim.models.exceptions import InvalidAimProjectFile, UnusedAimProjectField
from aim.models.metrics import MonitorConfig, Metric, ec2core, CloudWatchAlarm, AlarmSet, \
    AlarmSets, AlarmNotifications, AlarmNotification, NotificationGroups, Dimension
from aim.models.networks import NetworkEnvironment, Environment, EnvironmentDefault, \
    EnvironmentRegion, Segment, Network, VPC, VPCPeering, VPCPeeringRoute, NATGateway, VPNGateway, \
    PrivateHostedZone, SecurityGroup, IngressRule, EgressRule
from aim.models.project import Project, Credentials
from aim.models.applications import Application, ResourceGroup, RDS, CodePipeBuildDeploy, ASG, \
    Resource, Resources,LBApplication, TargetGroup, Listener, DNS, PortProtocol, EC2, S3Bucket, \
    S3BucketPolicy, AWSCertificateManager, ListenerRule, Lambda, LambdaEnvironment, \
    LambdaFunctionCode, LambdaVariable, SNSTopic, SNSTopicSubscription, \
    CloudFront, CloudFrontFactory, CloudFrontCustomErrorResponse, CloudFrontOrigin, CloudFrontCustomOriginConfig, \
    CloudFrontDefaultCacheBehaviour, CloudFrontForwardedValues, CloudFrontCookies, CloudFrontViewerCertificate, \
    RDSMysql, ElastiCacheRedis
from aim.models.resources import EC2Resource, EC2KeyPair, S3Resource, Route53Resource, Route53HostedZone, \
    CodeCommit, CodeCommitRepository, CodeCommitUser, CloudTrailResource, CloudTrails, CloudTrail, \
    ApiGatewayRestApi, IAMResource, IAMUser, IAMUserPermission, IAMUserPermissions, IAMUserProgrammaticAccess, \
    IAMUserPermissionCodeCommitRepository, IAMUserPermissionCodeCommit, IAMUserPermissionAdministrator
from aim.models.iam import IAMs, IAM, ManagedPolicy, Role, Policy, AssumeRolePolicy, Statement
from aim.models.base import get_all_fields, most_specialized_interfaces
from aim.models.accounts import Account, AdminIAMUser
from aim.models.references import Reference, TextReference, FileReference
from aim.models.vocabulary import aws_regions
from aim.models.references import resolve_ref
from aim.models import schemas
from pathlib import Path
from ruamel.yaml.compat import StringIO
from zope.schema.interfaces import ConstraintNotSatisfied, ValidationError


def get_logger():
    log = logging.getLogger("aim.models")
    log.setLevel(logging.DEBUG)
    return log


class YAML(ruamel.yaml.YAML):
    def dump(self, data, stream=None, **kw):
        dumps = False
        if stream is None:
            dumps = True
            stream = StringIO()
        ruamel.yaml.YAML.dump(self, data, stream, **kw)
        if dumps:
            return stream.getvalue()

logger = get_logger()

IAM_USER_PERMISSIONS_CLASS_MAP = {
    'CodeCommit': IAMUserPermissionCodeCommit,
    'Administrator': IAMUserPermissionAdministrator
}

RESOURCES_CLASS_MAP = {
    'ApiGatewayRestApi': ApiGatewayRestApi,
    'ASG': ASG,
    'CodePipeBuildDeploy': CodePipeBuildDeploy,
    'ACM': AWSCertificateManager,
    'RDS': RDS,
    'LBApplication': LBApplication,
    'EC2': EC2,
    'Lambda': Lambda,
    'ManagedPolicy': ManagedPolicy,
    'S3Bucket': S3Bucket,
    'SNSTopic': SNSTopic,
    'CloudFront': CloudFront,
    'RDSMysql': RDSMysql,
    'ElastiCacheRedis': ElastiCacheRedis,
}

SUB_TYPES_CLASS_MAP = {
    RDSMysql: {
        'security_groups': ('str_list', TextReference)
    },
    ElastiCacheRedis: {
        'security_groups': ('str_list', TextReference)
    },
    CloudFront: {
        'default_cache_behavior': ('unnamed_dict', CloudFrontDefaultCacheBehaviour),
        'domain_aliases': ('obj_list', DNS),
        'custom_error_responses': ('obj_list', CloudFrontCustomErrorResponse),
        'origins': ('named_dict', CloudFrontOrigin),
        'viewer_certificate': ('unnamed_dict', CloudFrontViewerCertificate),
        'factory': ('named_dict', CloudFrontFactory)
    },
    CloudFrontDefaultCacheBehaviour: {
        'allowed_methods': ('str_list', zope.schema.TextLine),
        'forwarded_values': ('unnamed_dict', CloudFrontForwardedValues)
    },
    CloudFrontForwardedValues: {
        'cookies': ('unnamed_dict', CloudFrontCookies),
    },
    CloudFrontCookies: {
        'white_listed_names': ('str_list', zope.schema.TextLine)
    },
    CloudFrontOrigin: {
        'custom_origin_config': ('unnamed_dict', CloudFrontCustomOriginConfig)
    },
    CloudFrontCustomOriginConfig: {
        'ssl_protocols': ('str_list', zope.schema.TextLine)
    },
    CloudFrontFactory: {
        'domain_aliases': ('obj_list', DNS),
        'viewer_certificate': ('unnamed_dict', CloudFrontViewerCertificate),
    },
    SNSTopic: {
        'subscription': ('obj_list', SNSTopicSubscription),
    },
    # Resource sub-objects
    CloudWatchAlarm: {
        'dimensions': ('obj_list', Dimension)
    },
    LBApplication: {
        'target_groups': ('named_dict', TargetGroup),
        'security_groups': ('str_list', TextReference),
        'listeners': ('named_dict', Listener),
        'dns': ('obj_list', DNS),
        'monitoring': ('unnamed_dict', MonitorConfig)
    },
    ASG: {
        'security_groups': ('str_list', TextReference),
        'target_groups': ('str_list', TextReference),
        'monitoring': ('unnamed_dict', MonitorConfig),
        'instance_iam_role': ('unnamed_dict', Role)
    },
    Listener: {
        'redirect': ('unnamed_dict', PortProtocol),
        'rules': ('named_dict', ListenerRule)
    },
    EC2: {
        'security_groups': ('str_list', TextReference)
    },
    CodePipeBuildDeploy: {
        'artifacts_bucket': ('named_dict', S3Bucket),
    },
    S3Bucket: {
        'policy': ('obj_list', S3BucketPolicy)
    },
    CloudTrailResource: {
        'trails': ('container', (CloudTrails, CloudTrail)),
    },

    # monitoring and logging
    MonitorConfig: {
        'metrics': ('obj_list', Metric),
        'alarm_sets': ('alarm_sets', AlarmSets),
        'log_sets': ('log_sets', CloudWatchLogSets),
        'notifications': ('notifications', AlarmNotifications)
    },
    CloudWatchLogging: {
        'log_sets': ('container', (CloudWatchLogSets, CloudWatchLogSet)),
    },
    CloudWatchLogGroup: {
        'metric_filters': ('container', (MetricFilters, MetricFilter)),
        'sources': ('container', (CloudWatchLogSources, CloudWatchLogSource)),
    },
    MetricFilter: {
        'metric_transformations': ('obj_list', MetricTransformation)
    },
    CloudWatchLogSet: {
        'log_groups': ('container', (CloudWatchLogGroups, CloudWatchLogGroup)),
    },

    # Networking
    NetworkEnvironment: {
        'vpc': ('unnamed_dict', VPC)
    },
    Network: {
        'vpc': ('unnamed_dict', VPC)
    },
    VPC: {
        'nat_gateway': ('named_dict', NATGateway),
        'vpn_gateway': ('named_dict', VPNGateway),
        'private_hosted_zone': ('unnamed_dict', PrivateHostedZone),
        'segments': ('named_dict', Segment),
        'security_groups': ('named_twolevel_dict', SecurityGroup),
        'peering': ('named_dict', VPCPeering)
    },
    VPCPeering: {
        'routing': ('obj_list', VPCPeeringRoute)
    },
    SecurityGroup: {
        'ingress': ('obj_list', IngressRule),
        'egress' : ('obj_list', EgressRule)
    },

    # Application
    Application: {
        'notifications': ('notifications', AlarmNotifications)
    },

    # IAM
    IAM: {
        'roles': ('named_dict', Role)
        #'policies': ('named_dict', ManagedPolicies)
    },
    Role: {
        'policies': ('obj_list', Policy),
        'assume_role_policy': ('unnamed_dict', AssumeRolePolicy)
    },
    Policy: {
        'statement': ('obj_list', Statement)
    },
    Statement: {
        'action': ('str_list', zope.schema.TextLine),
        'resource': ('str_list', zope.schema.TextLine)
    },
    Lambda: {
        'environment': ('unnamed_dict', LambdaEnvironment),
        'code': ('unnamed_dict', LambdaFunctionCode),
        'iam_role': ('unnamed_dict', Role),
        'monitoring': ('unnamed_dict', MonitorConfig)
    },
    LambdaEnvironment: {
        'variables': ('obj_list', LambdaVariable)
    },
    ManagedPolicy: {
        'roles': ('str_list', zope.schema.TextLine),
        'statement': ('obj_list', Statement)
    },
    # Accounts
    Account: {
        'admin_iam_users': ('named_dict', AdminIAMUser)
    },
    Route53Resource: {
        'hosted_zones': ('named_dict', Route53HostedZone)
    },
    SNSTopic: {
        'subscriptions': ('obj_list', SNSTopicSubscription)
    },
    CodeCommitRepository: {
        'users': ('named_dict', CodeCommitUser)
    },
    IAMResource: {
        'users': ('named_dict', IAMUser)
    },
    IAMUser: {
        'programmatic_access': ('unnamed_dict', IAMUserProgrammaticAccess),
        'permissions': ('iam_user_permissions', IAMUserPermissions)
    },
    IAMUserPermissionCodeCommit: {
        'repositories': ('obj_list', IAMUserPermissionCodeCommitRepository)
    }
}


def load_string_from_path(path, base_path=None):
    if not base_path.endswith(os.sep):
        base_path += os.sep
    if base_path:
        path = base_path + path
    path = Path(path)
    if path.is_file():
        fh = path.open()
        return fh.read()
    else:
        # ToDo: better error help
        raise InvalidAimProjectFile("For FileReference field, File does not exist at filesystem path {}".format(path))

def merge(base, override):
    """
    Merge two dictionaries of arbitray depth
    """
    if isinstance(base, dict) and isinstance(override, dict):
        new_dict = dict(base)
        new_dict.update(
            {k: merge(base.get(k, None), override[k]) for k in override}
        )
        return new_dict

    if isinstance(base, list) and isinstance(override, list):
        return [merge(x, y) for x, y in itertools.zip_longest(base, override)]

    return copy.deepcopy(base) if override is None else copy.deepcopy(override)

def annotate_base_config(obj, override_config, base_config):
    """
    Adds attributes prefixed with __base__<name> with values from the
    base configuration for every attribute that has been overriden.
    """
    for name in override_config.keys():
        value = getattr(base_config, name, None)
        if value:
            setattr(obj, '__base__' + name, value)

def gen_yaml_filename(folder, filename):
    for ext in ['.yaml', '.yml']:
        yaml_file = os.path.join(folder, filename+ext)
        if os.path.isfile(yaml_file):
            return yaml_file
    return yaml_file


def get_all_nodes(root):
    "Return a list of all nodes in aim.model"
    nodes = []
    stack = [root]
    while stack:
        cur_node = stack[0]
        stack = stack[1:]
        nodes.append(cur_node)
        if type({}) == type(cur_node) or zope.interface.common.mapping.IMapping.providedBy(cur_node):
            for child in cur_node.values():
                stack.insert(0, child)
        # check for obj or dict attributes
        for field_name, field in get_all_fields(cur_node).items():
            # drill down into objects for non-locatable nodes
            if zope.schema.interfaces.IObject.providedBy(field):
                obj = getattr(cur_node, field_name, None)
                if obj:
                    stack.insert(0, obj)
            elif zope.schema.interfaces.IDict.providedBy(field):
                # dicts are model nodes, don't return them - only their values
                obj = getattr(cur_node, field_name, None)
                if obj:
                    for child in obj.values():
                        stack.insert(0, child)
            elif zope.schema.interfaces.IList.providedBy(field):
                # skip computed fields
                if field.readonly: continue
                # don't drill down into lists of strings - only lists of model objects
                for obj in getattr(cur_node, field_name, None):
                    if type(obj) != type(''):
                        stack.insert(0, obj)
    return nodes

def add_metric(obj, metric):
    """Add metrics to a resource"""
    if not obj.monitoring:
        obj.monitoring = MonitorConfig('monitoring', obj)
    obj.monitoring.metrics.insert(0, metric)


def apply_attributes_from_config(obj, config, config_folder=None, lookup_config=None, read_file_path=''):
    """
    Iterates through the field an object's schema has
    and applies the values from configuration.

    Also handles loading of sub-types ...
    """
    # throw an error if there are fields which do not match the schema
    fields = get_all_fields(obj)
    if not zope.interface.common.mapping.IMapping.providedBy(obj):
        for key in config.keys():
            if key not in fields:
                raise UnusedAimProjectField("""Error in file at {}
Unneeded field '{}' in config for object type '{}'
""".format(read_file_path, key, obj.__class__.__name__))

    # all most-specialized interfaces implemented by obj
    for interface in most_specialized_interfaces(obj):
        fields = zope.schema.getFields(interface)
        for name, field in fields.items():
            # Locatable Objects get their name from their key in the config, for example:
            #   environments:
            #     demo:
            # creates an Environment with the name 'demo'.
            # These objects implement the INamed interface.
            # Do not try to find their 'name' attr from the config.
            if name != 'name' or not schemas.INamed.providedBy(obj):
                # FileReferences load the string from file - the original path value is lost ¯\_(ツ)_/¯
                if type(field) == type(FileReference()):
                    if read_file_path:
                        # set it to the containing directory of the file
                        path = Path(read_file_path)
                        base_path = os.sep.join(path.parts[:-1])[1:]
                    else:
                        base_path = None
                    value = load_string_from_path(
                        config.get(name, None),
                        base_path=base_path,
                    )
                # CommaList: Parse comma separated list into python list()
                elif type(field) == type(schemas.CommaList()):

                    value = []
                    for list_value in config[name].split(','):
                        value.append(list_value.strip())
                else:
                    value = config.get(name, None)
                if value != None:
                    # YAML loads "1" as an Int, cast to a Float where expected by the schema
                    if zope.schema.interfaces.IFloat.providedBy(field):
                        value = float(value)
                    # YAML loads 'field: 404' as an Int where the field could be Text or TextLine
                    # You can force a string with "field: '404'" but this removes the need to do that.
                    if isinstance(field, (zope.schema.TextLine, zope.schema.Text)) and type(value) != str:
                        value = str(value)
                    # is the value a reference?
                    ref_field = TextReference()
                    try:
                        ref_field._validate(value)
                        # some fields are meant to be reference only
                        if schemas.ITextReference.providedBy(field):
                            setattr(obj, name, value)
                        else:
                            # reference - set a special _ref_ attribute for later look-up
                            setattr(obj, '_ref_' + name, copy.deepcopy(value))

                    except (ValidationError, ConstraintNotSatisfied):
                        # not a reference - set the attribute on the object

                        # ToDo: resources could be loaded here?
                        # resources are loaded later based on type
                        if schemas.IApplication.providedBy(obj) and name == 'groups':
                            continue
                        if schemas.IResourceGroup.providedBy(obj) and name == 'resources':
                            continue
                        try:
                            if type(obj) in SUB_TYPES_CLASS_MAP:
                                if name in SUB_TYPES_CLASS_MAP[type(obj)]:
                                    value = sub_types_loader(
                                        obj,
                                        name,
                                        value,
                                        config_folder,
                                        lookup_config,
                                        read_file_path
                                    )
                                    setattr(obj, name, value)
                                else:
                                    setattr(obj, name, copy.deepcopy(value))
                            else:
                                setattr(obj, name, copy.deepcopy(value))
                        except ValidationError as exc:
                            try:
                                field_context_name = exc.field.context.name
                            except AttributeError:
                                field_context_name = 'Not applicable'
                            raise InvalidAimProjectFile(
                                """Error in file at {}
Invalid config for field '{}' for object type '{}'.
Value supplied: {}
Field Context name: {}
Reason: {}
Schema error: {}""".format(read_file_path, name, obj.__class__.__name__, value, field_context_name, exc.__doc__, exc)
                            )

def sub_types_loader(obj, name, value, config_folder=None, lookup_config=None, read_file_path=''):
    """
    Load sub types
    """
    sub_type, sub_class = SUB_TYPES_CLASS_MAP[type(obj)][name]

    if sub_type == 'named_dict':
        sub_dict = {}
        for sub_key, sub_value in value.items():
            if schemas.INamed.implementedBy(sub_class):
                sub_obj = sub_class(sub_key, obj)
            else:
                sub_obj = sub_class()
            apply_attributes_from_config(sub_obj, sub_value, config_folder, lookup_config, read_file_path)
            sub_dict[sub_key] = sub_obj
        return sub_dict

    elif sub_type == 'obj':
        sub_obj = sub_class(name, obj)
        apply_attributes_from_config(sub_obj, value, config_folder)
        return sub_obj

    elif sub_type == 'container':
        container_class = sub_class[0]
        object_class = sub_class[1]
        container = container_class(name, obj)
        for sub_key, sub_value in value.items():
            sub_obj = object_class(sub_key, container)
            apply_attributes_from_config(sub_obj, sub_value, config_folder, lookup_config, read_file_path)
            container[sub_key] = sub_obj
        return container

    elif sub_type == 'twolevel_container':
        container_class = sub_class[0]
        first_object_class = sub_class[1]
        second_object_class = sub_class[2]
        container = container_class(name, obj)
        for first_key, first_value in value.items():
            # special case for AlarmSet.notifications
            if first_key == 'notifications' and schemas.IAlarmSet.implementedBy(first_object_class):
                notifications = instantiate_notifications(value['notifications'], read_file_path)
                container.notifications = notifications
            else:
                first_obj = first_object_class(first_key, container)
                container[first_key] = first_obj
            for second_key, second_value in first_value.items():
                # special case for Alarm.notifications
                if second_key == 'notifications' and schemas.IAlarm.implementedBy(second_object_class):
                    notifications = instantiate_notifications(value[first_key]['notifications'], read_file_path)
                    container[first_key].notifications = notifications
                else:
                    second_obj = second_object_class(second_key, container[first_key])
                    apply_attributes_from_config(second_obj, second_value, config_folder, lookup_config, read_file_path)
                    container[first_key][second_key] = second_obj
        return container

    elif sub_type == 'named_twolevel_dict':
        sub_dict = {}
        for first_key, first_value in value.items():
            sub_dict[first_key]  = {}
            for sub_key, sub_value in first_value.items():
                sub_obj = sub_class()
                apply_attributes_from_config(sub_obj, sub_value, config_folder, lookup_config, read_file_path)
                sub_dict[first_key][sub_key] = sub_obj
        return sub_dict

    elif sub_type == 'unnamed_dict':
        if schemas.INamed.implementedBy(sub_class):
            sub_obj = sub_class(name, obj)
        else:
            sub_obj = sub_class()
        apply_attributes_from_config(sub_obj, value, config_folder, lookup_config, read_file_path)
        return sub_obj

    elif sub_type == 'obj_list':
        sub_list = []
        for sub_value in value:
            if schemas.INamed.implementedBy(sub_class):
                sub_obj = sub_class(name, obj)
            else:
                sub_obj = sub_class()
            apply_attributes_from_config(sub_obj, sub_value, config_folder, lookup_config, read_file_path)
            sub_list.append(sub_obj)
        return sub_list

    elif sub_type == 'str_list':
        sub_list = []
        for sub_value in value:
            sub_obj = sub_class().fromUnicode(sub_value)
            sub_list.append(sub_obj)
        return sub_list

    elif sub_type == 'log_sets':
        # Special loading for CloudWatch Log Sets
        default_config = lookup_config['logging']['cw_logging']
        merged_config = merge(default_config['log_sets'], value)
        log_sets = CloudWatchLogSets('log_sets', obj)
        for log_set_name in merged_config.keys():
            log_set = CloudWatchLogSet(log_set_name, log_sets)
            apply_attributes_from_config(log_set, merged_config[log_set_name], config_folder)
            log_sets[log_set_name] = log_set
        return log_sets

    elif sub_type == 'alarm_sets':
        # Special loading for AlarmSets
        alarm_sets = AlarmSets('alarm_sets', obj)
        for alarm_set_name in value.keys():
            # look-up AlarmsSet by Resource type and name
            resource_type = obj.__parent__.type
            alarm_set = AlarmSet(alarm_set_name, alarm_sets)
            alarm_set.resource_type = resource_type
            for alarm_name, alarm_config in lookup_config['alarms'][resource_type][alarm_set_name].items():
                alarm = CloudWatchAlarm(alarm_name, alarm_set)
                apply_attributes_from_config(alarm, alarm_config, config_folder, read_file_path=read_file_path)
                alarm_set[alarm_name] = alarm
            alarm_sets[alarm_set_name] = alarm_set

            # check for and apply overrides
            if value[alarm_set_name] is not None:
                for alarm_name in value[alarm_set_name].keys():
                    for setting_name, setting_value in value[alarm_set_name][alarm_name].items():
                        # 'notifications' is a reserved name for AlarmSet and Alarm objects
                        # load notifications for an AlarmSet
                        if alarm_name == 'notifications':
                            alarm_sets[alarm_set_name].notifications = instantiate_notifications(
                                value[alarm_set_name]['notifications'],
                                read_file_path
                            )
                        # load notifications for an Alarm
                        elif setting_name == 'notifications':
                            alarm_sets[alarm_set_name][alarm_name].notifications = instantiate_notifications(
                                value[alarm_set_name][alarm_name]['notifications'],
                                read_file_path
                            )
                        else:
                            if setting_name == 'dimensions':
                                setting_value = [
                                    Dimension(item['name'], item['value'])
                                    for item in setting_value
                                ]
                            setattr(alarm_sets[alarm_set_name][alarm_name], setting_name, setting_value)

        return alarm_sets

    elif sub_type == 'notifications':
        # Special loading for AlarmNotifications
        return instantiate_notifications(value, read_file_path)
    elif sub_type == 'iam_user_permissions':
        return instantiate_iam_user_permissions(value, obj, read_file_path)


def load_resources(res_groups, groups_config, config_folder=None, monitor_config=None, read_file_path=''):
    """
    Loads resources for an Application
    """
    for grp_key, grp_config in groups_config.items():
        resource_group = ResourceGroup(grp_key, res_groups)
        apply_attributes_from_config(resource_group, grp_config, config_folder, read_file_path=read_file_path)
        res_groups[grp_key] = resource_group
        for res_key, res_config in grp_config['resources'].items():
            try:
                klass = RESOURCES_CLASS_MAP[res_config['type']]
            except KeyError:
                if 'type' not in res_config:
                    raise InvalidAimProjectFile("Error in file at {}\nNo type for resource '{}'.\n\nConfiguration section:\n{}".format(
                        read_file_path, res_key, res_config)
                    )
                raise InvalidAimProjectFile(
                    """Error in file at {}
    No mapping for type '{}' for resource named '{}'

    Configuration section:
    {}
    """.format(read_file_path, res_config['type'], res_key, res_config)
                )
            obj = klass(res_key, res_groups[grp_key].resources)
            apply_attributes_from_config(obj, res_config, config_folder, lookup_config=monitor_config, read_file_path=read_file_path)
            # invariants need to be validated if they are not explicitly part of a schema.Object() field
            for interface in most_specialized_interfaces(obj):
                interface.validateInvariants(obj)
            res_groups[grp_key].resources[res_key] = obj

def instantiate_notifications(value, read_file_path):
    notifications = AlarmNotifications()
    for notification_name in value.keys():
        notification = AlarmNotification()
        apply_attributes_from_config(notification, value[notification_name], read_file_path=read_file_path)
        notifications[notification_name] = notification
    return notifications

def instantiate_iam_user_permissions(value, parent, read_file_path):
    permissions = IAMUserPermissions('permissions', parent)
    for permission_name in value.keys():
        permission_config = value[permission_name]
        permission_obj = IAM_USER_PERMISSIONS_CLASS_MAP[permission_config['type']](permission_name, permissions)
        #breakpoint()
        apply_attributes_from_config(permission_obj, permission_config, read_file_path=read_file_path)
        permissions[permission_name] = permission_obj
    return permissions

class ModelLoader():
    """
    Loads YAML config files into aim.model instances
    """

    def __init__(self, config_folder, config_processor=None):
        self.config_folder = config_folder
        self.config_subdirs = {
            "MonitorConfig": self.instantiate_monitor_config,
            "Accounts": self.instantiate_accounts,
            "NetworkEnvironments": self.instantiate_network_environments,
            "Resources": self.instantiate_resources,
        }
        self.yaml = YAML(typ="safe", pure=True)
        self.yaml.default_flow_sytle = False
        self.config_processor = config_processor
        self.project = None

    def read_yaml(self, sub_dir='', fname=''):
        """Read a YAML file"""
        # default is to load root project.yaml
        if sub_dir == '':
            path = self.config_folder + os.sep + fname
        else:
            path = self.config_folder + os.sep + sub_dir + os.sep + fname
        logger.debug("Loading YAML: %s" % (path))

        # Credential files must be secured. This seems hacky, is there a better way?
        if fname == '.credentials.yaml':
            cred_stat = os.stat(path)
            oct_perm = oct(cred_stat.st_mode)
            if oct_perm != '0o100400':
                raise PermissionError('Credentials file permissions are too relaxed. Run: chmod 0400 %s' % (path))

        # Validate Configuration
        if self.config_processor != None:
            self.config_processor(sub_dir, fname)

        # everytime a file is read, update read_file_path to assist with debugging messages
        self.read_file_path = path

        # read the YAML!
        with open(path, 'r') as stream:
            config = self.yaml.load(stream)
        return config

    def load_all(self):
        'Basically does a LOAD "*",8,1'
        aim_project_version = self.read_aim_project_version()
        self.check_aim_project_version(aim_project_version)
        self.instantiate_project('project', self.read_yaml('', 'project.yaml'))
        self.project.aim_project_version = '{}.{}'.format(aim_project_version[0], aim_project_version[1])

        if os.path.isfile(self.config_folder + os.sep + '.credentials.yaml'):
            self.instantiate_project('.credentials', self.read_yaml('', '.credentials.yaml'))
        for subdir, instantiate_method in self.config_subdirs.items():
            for fname in os.listdir(self.config_folder + os.sep + subdir):
                if fname.endswith('.yml') or fname.endswith('.yaml'):
                    if fname.endswith('.yml'):
                        name = fname[:-4]
                    elif fname.endswith('.yaml'):
                        name = fname[:-5]
                    config = self.read_yaml(subdir, fname)
                    instantiate_method(name, config)
        self.instantiate_services()
        self.check_notification_config()
        # ToDo: references only need to be loaded for things like web UIs, implementation not complete
        #self.load_references()
        self.load_outputs()
        self.load_core_monitoring()

    def read_aim_project_version(self):
        "Reads <project>/aim-project-version.txt and returns a tuple (major,medium) version"
        version_file = self.config_folder + os.sep + 'aim-project-version.txt'
        if not os.path.isfile(version_file):
            raise InvalidAimProjectFile(
                'You need a <project>/aim-project-version.txt file that declares your AIM Project file foramt version.'
            )
        with open(version_file) as f:
            version = f.read()
        version = version.strip().replace(' ', '')
        major, medium = version.split('.')
        major = int(major)
        medium = int(medium)
        return (major, medium)

    def check_aim_project_version(self, version):
        aim_models_version = pkg_resources.get_distribution('aim.models').version
        aim_major, aim_medium = aim_models_version.split('.')[0:2]
        if version[0] != int(aim_major) or version[1] != int(aim_medium):
            raise InvalidAimProjectFile(
                "Version mismatch: project declares AIM Project version {}.{} but aim.models is at version {}".format(
                    version[0], version[1], aim_models_version
                ))

    def load_references(self):
        """
        Resolves all references
        A reference is a string that refers to another value in the model. The original
        reference string is stored as '_ref_<attribute>' while the resolved reference is
        stored in the attribute.
        """
        # walk the model
        for model in get_all_nodes(self.project):
            for name, field in get_all_fields(model).items():
                # check for lists of refs
                #if zope.schema.interfaces.IList.providedBy(field):

                # check for refs as normal attrs
                if hasattr(model, '_ref_' + name):
                    value = resolve_ref(getattr(model, '_ref_' + name), self.project)
                    setattr(model, name, value)

    def load_core_monitoring(self):
        "Loads monitoring metrics that are built into resources"
        for model in get_all_nodes(self.project):
            # ToDo: only doing metrics for ASG right now
            if schemas.IASG.providedBy(model):
                add_metric(model, ec2core)

    def load_outputs(self):
        "Loads resource ids from CFN Outputs"

        base_output_path = 'Outputs' + os.sep
        monitor_config_output_path = base_output_path + 'MonitorConfig'
        if os.path.isfile(self.config_folder + os.sep + monitor_config_output_path + os.sep + 'NotificationGroups.yaml'):
            notif_groups_config = self.read_yaml(monitor_config_output_path, 'NotificationGroups.yaml')
            if 'groups' in notif_groups_config:
                notif_groups = self.project['notificationgroups']
                for group_name in notif_groups_config['groups'].keys():
                    notif_groups[group_name].resource_name = notif_groups_config['groups'][group_name]['__name__']

        ne_outputs_path = base_output_path + 'NetworkEnvironments'
        if os.path.isdir(self.config_folder + os.sep + ne_outputs_path):
            for rfile in os.listdir(self.config_folder + os.sep + ne_outputs_path):
                # parse filename
                info = rfile.split('.')[0]
                ne_name = info.split('-')[0]
                env_name = info.split('-')[1]
                region = info[len(ne_name) + len(env_name) + 2:]

                env_reg = self.project['netenv'][ne_name][env_name][region]
                reg_config = self.read_yaml(ne_outputs_path, rfile)

                if 'applications' in reg_config:
                    for app_name in reg_config['applications'].keys():
                        groups_config = reg_config['applications'][app_name]['groups']
                        for grp_name in groups_config:
                            for res_name in groups_config[grp_name]['resources']:
                                # Standard AWS Resources in an Application's Resource Group
                                resource_config = groups_config[grp_name]['resources'][res_name]
                                resource = env_reg.applications[app_name].groups[grp_name].resources[res_name]

                                if 'fullname' in resource_config:
                                    resource.resource_fullname = resource_config['fullname']['__name__']
                                if 'name' in resource_config:
                                    # ALB have a name attribute with an embedded __name__
                                    resource.resource_name = resource_config['name']['__name__']
                                    # TargetGroups are nested in the ALB Output
                                    if 'target_groups' in resource_config:
                                        for tg_name, tg_config in resource_config['target_groups'].items():
                                            tg_resource = resource.target_groups[tg_name]
                                            tg_resource.resource_name = tg_config['name']['__name__']
                                            tg_resource.resource_fullname = tg_config['arn']['__name__'].split(':')[-1:][0]
                                elif '__name__' in resource_config:
                                    resource.resource_name = resource_config['__name__']

                                # CloudWatch Alarms
                                if 'monitoring' in resource_config:
                                    if 'alarm_sets' in resource_config['monitoring']:
                                        for alarm_set_name in resource_config['monitoring']['alarm_sets']:
                                            for alarm_name in resource_config['monitoring']['alarm_sets'][alarm_set_name]:
                                                alarm = resource.monitoring.alarm_sets[alarm_set_name][alarm_name]
                                                alarm.resource_name = resource_config['monitoring']['alarm_sets'][alarm_set_name][alarm_name]['__name__']

    def load_iam_group(self, res_groups, app_config, local_config={}):
        """
        Loads resources for IAM
        """

        if 'groups' not in app_config:
            app_config['groups'] = {}

        # layer env config over base app config
        if  len(local_config.keys()) > 0:
            merged_config = merge(app_config['groups'], local_config)
        # if no customizations, use only base config
        else:
            merged_config = app_config

        for grp_key, grp_config in merged_config['groups'].items():
            obj = ResourceGroup(grp_key, res_groups)
            apply_attributes_from_config(obj, grp_config, self.config_folder, read_file_path=self.read_file_path)
            res_groups[grp_key] = obj
            for res_key, res_config in grp_config['resources'].items():
                try:
                    klass = RESOURCES_CLASS_MAP[res_config['type']]
                except KeyError:
                    if 'type' not in res_config:
                        raise InvalidAimProjectFile("No type for resource {}".format(res_key))
                    raise InvalidAimProjectFile(
                        "No mapping for type {} for {}".format(res_config['type'], res_key)
                    )
                obj = klass(res_key, res_groups)
                apply_attributes_from_config(obj, res_config, self.config_folder, read_file_path=self.read_file_path)
                res_groups[grp_key].resources[res_key] = obj

    def create_apply_and_save(self, name, parent, klass, config):
        """
        Helper to create a new model instance
        apply config to it
        and save in the object hierarchy
        """
        obj = klass(name, parent)
        apply_attributes_from_config(obj, config, self.config_folder, read_file_path=self.read_file_path)
        parent[name] = obj
        return obj

    def insert_env_ref_aim_sub(self, str_value, env_id, region):
        """
        aim.sub substition
        """
        # Isolate string between quotes: aim.sub ''
        sub_idx = str_value.find('aim.sub')
        if sub_idx == -1:
            return str_value
        end_idx = str_value.find('\n', sub_idx)
        if end_idx == -1:
            end_idx = len(str_value)
        str_idx = str_value.find("'", sub_idx, end_idx)
        if str_idx == -1:
            raise StackException(AimErrorCode.Unknown)
        str_idx += 1
        end_str_idx = str_value.find("'", str_idx, end_idx)
        if end_str_idx == -1:
            raise StackException(AimErrorCode.Unknown)

        # Isolate any ${} replacements
        first_pass = True
        while True:
            dollar_idx = str_value.find("${", str_idx, end_str_idx)
            if dollar_idx == -1:
                if first_pass == True:
                    raise StackException(AimErrorCode.Unknown)
                else:
                    break
            rep_1_idx = dollar_idx
            rep_2_idx = str_value.find("}", rep_1_idx, end_str_idx)+1
            netenv_ref_idx = str_value.find(
                "aim.ref netenv.", rep_1_idx, rep_2_idx)
            if netenv_ref_idx != -1:
                #sub_ref_idx = netenv_ref_idx + len("aim.ref netenv.")
                sub_ref_idx = netenv_ref_idx
                sub_ref_end_idx = sub_ref_idx+(rep_2_idx-sub_ref_idx-1)
                sub_ref = str_value[sub_ref_idx:sub_ref_end_idx]

                new_ref = self.insert_env_ref_str(sub_ref, env_id, region)
                sub_var = str_value[sub_ref_idx:sub_ref_end_idx]
                str_value = str_value.replace(sub_var, new_ref, 1)
            else:
                break
            first_pass = False

        return str_value

    def insert_env_ref_str(self, str_value, env_id, region):
        netenv_ref_idx = str_value.find("aim.ref netenv.")
        if netenv_ref_idx == -1:
            return str_value

        if str_value.startswith("aim.sub "):
            return self.insert_env_ref_aim_sub(str_value, env_id, region)

        netenv_ref_raw = str_value
        sub_ref_len = len(netenv_ref_raw)

        netenv_ref = netenv_ref_raw[0:sub_ref_len]
        ref = Reference(netenv_ref)
        if ref.type == 'netenv' and ref.parts[2] == env_id and ref.parts[3] == region:
            return str_value
        ref.parts.insert(2, env_id)
        ref.parts.insert(3, region)
        new_ref_parts = '.'.join(ref.parts)
        new_ref = ' '.join(['aim.ref', new_ref_parts])

        return new_ref

    def normalize_environment_refs(self, env_config, env_name, env_region):
        """
        Resolves all references
        A reference is a string that refers to another value in the model. The original
        reference string is stored as '_ref_<attribute>' while the resolved reference is
        stored in the attribute.
        Inserts the Environment and Region into any aim.ref netenv.references.
        """
        # walk the model
        model_list = get_all_nodes(env_config)
        for model in model_list:
            #continue
            all_fields = get_all_fields(model).items()
            for name, field in all_fields:
                if hasattr(model, name) == False:
                    continue
                if isinstance(field, (str, zope.schema.TextLine, zope.schema.Text)):
                    ref_name = '_ref_' + name
                    if hasattr(model, '_ref_' + name):
                        attr_name = ref_name
                    else:
                        attr_name = name
                    value = getattr(model, attr_name)
                    if value != None and value.find('aim.ref netenv.') != -1:
                        value = self.insert_env_ref_str(value, env_name, env_region)
                        setattr(model, attr_name, value)
                elif zope.schema.interfaces.IList.providedBy(field) and field.readonly == False:
                    new_list = []
                    attr_name = name
                    modified = False
                    for item in getattr(model, name):
                        if isinstance(item, (str, zope.schema.TextLine, zope.schema.Text)):
                            value = self.insert_env_ref_str(item, env_name, env_region)
                            modified = True
                        else:
                            value = item
                        new_list.append(value)
                    if modified == True:
                        setattr(model, attr_name, new_list)

    def instantiate_project(self, name, config):
        if name == 'project':
            self.project = Project(config['name'], None)
            self.project['home'] = self.config_folder
            apply_attributes_from_config(self.project, config, self.config_folder, read_file_path=self.read_file_path)
        elif name == '.credentials':
            apply_attributes_from_config(self.project['credentials'], config, self.config_folder, read_file_path=self.read_file_path)

    def instantiate_services(self):
        """
        Load Services
        These are loaded from an entry point named 'aim.services'.
        The entry point name will match a filename at:
          <AIMProject>/Services/<EntryPointName>(.yml|.yaml)
        """
        service_plugins = aim.models.services.list_service_plugins()
        services_dir = self.config_folder + os.sep + 'Services' + os.sep
        for plugin_name, plugin_module in service_plugins.items():
            if os.path.isfile(services_dir + plugin_name + '.yml'):
                fname = plugin_name + '.yml'
            elif os.path.isfile(services_dir + plugin_name + '.yaml'):
                fname = plugin_name + '.yaml'
            else:
                continue
            config = self.read_yaml('Services', fname)
            service = plugin_module.instantiate_model(
                config,
                self.project,
                self.monitor_config,
                read_file_path=services_dir + fname
            )
            self.project[plugin_name.lower()] = service
            if hasattr(plugin_module, 'load_outputs'):
                plugin_module.load_outputs(self)
        return

    def check_notification_config(self):
        """Detect misconfigured alarm notification situations.
        This happens after both MonitorConfig and NetworkEnvironments have loaded.
        """
        if 'notificationgroups' in self.project:
            for app in self.project.get_all_applications():
                if app.is_enabled():
                    for alarm_info in app.list_alarm_info():
                        alarm = alarm_info['alarm']
                        # warn on alarms with no subscriptions
                        if len(alarm.notification_groups) == 0:
                            print("Alarm {} for app {} does not have any notifications.".format(
                                alarm.name,
                                app.name
                            ))
                        # alarms with groups that do not exist
                        for groupname in alarm.notification_groups:
                            if groupname not in self.project['notificationgroups']:
                                raise InvalidAimProjectFile(
                                    "Alarm {} for app {} notifies to group '{}' which does belong in Notification service group names.".format(
                                        alarm.name,
                                        app.name,
                                        groupname
                                    )
                                )

    def instantiate_monitor_config(self, name, config):
        """
        Loads Logging and AlarmSets config
        These do not get directly loaded into the model, their config is simply stored
        in Loader and applied to the model when named in alarm_sets and log_sets configuration
        in a NetworkEnvironment.
        """
        if not hasattr(self, 'monitor_config'):
            self.monitor_config = {}
        if name.lower() == 'alarmsets':
            self.monitor_config['alarms'] = config
        elif name.lower() == 'logging':
            if 'cw_logging' in config:
                # load the CloudWatch logging into the model, currently this is
                # just done to validate the YAML
                cw_logging = CloudWatchLogging('cw_logging', self.project)
                apply_attributes_from_config(cw_logging, config['cw_logging'])
                self.project['cw_logging'] = cw_logging
            self.monitor_config['logging'] = config
        elif name.lower() == 'notificationgroups':
            groups = NotificationGroups('notificationgroups', self.project)
            self.project['notificationgroups'] = groups
            if 'groups' in config:
                # top-level 'groups:' gets absorbed into a top-level NotificationGroups mapping
                # fiddle with the data to make apply_attrs happy ...
                groups_config = copy.deepcopy(config['groups'])
                del config['groups']
                apply_attributes_from_config(groups, config, read_file_path=self.read_file_path)
                # load SNS Topics
                for topicname, topic_config in groups_config.items():
                    topic = SNSTopic(topicname, groups)
                    apply_attributes_from_config(topic, topic_config)
                    groups[topicname] = topic
            else:
                raise InvalidAimProjectFile("MonitorConfig/NotificationGroups.yaml does not have a top-level `groups:`.")
            self.monitor_config['notificationgroups'] = config

    def instantiate_cloudwatch_log_groups(self, config):
        cw_log_groups = CWLogGroups()
        self.project['cloudwatch_log_groups'] = cw_log_groups
        if 'log_groups' in config:
            apply_attributes_from_config(cw_log_groups, config['log_groups'])

    def instantiate_accounts(self, name, config, read_file_path=''):
        accounts = self.project['accounts']
        self.create_apply_and_save(
            name,
            self.project['accounts'],
            Account,
            config
        )

    def instantiate_cloudtrail(self, config):
        obj = CloudTrailResource('cloudtrail', self.project)
        if config != None:
            apply_attributes_from_config(obj, config, self.config_folder)
        return obj

    def instantiate_route53(self, config):
        obj = Route53Resource(config)
        if config != None:
            apply_attributes_from_config(obj, config, self.config_folder)
        return obj

    def instantiate_codecommit(self, config):
        if config == None:
            return
        codecommit_obj = CodeCommit()
        codecommit_obj.repository_groups = {}
        for group_id in config.keys():
            group_config = config[group_id]
            codecommit_obj.repository_groups[group_id] = {}
            for repo_id in group_config.keys():
                repo_config = group_config[repo_id]
                repo_obj = CodeCommitRepository(repo_config['repository_name'], codecommit_obj)
                apply_attributes_from_config(repo_obj, repo_config, self.config_folder)
                codecommit_obj.repository_groups[group_id][repo_id] = repo_obj
        codecommit_obj.gen_repo_by_account()

        return codecommit_obj

    def instantiate_ec2(self, config):
        if config == None or 'keypairs' not in config.keys():
            return
        ec2_obj = EC2Resource()
        ec2_obj.keypairs = {}
        for keypair_id in config['keypairs'].keys():
            keypair_config = config['keypairs'][keypair_id]
            keypair_obj = EC2KeyPair(keypair_config['name'], ec2_obj)
            apply_attributes_from_config(keypair_obj, keypair_config, self.config_folder)
            ec2_obj.keypairs[keypair_id] = keypair_obj
        return ec2_obj

    def instantiate_s3(self, config):
        if config == None or 'buckets' not in config.keys():
            return
        s3_obj = S3Resource()
        s3_obj.buckets = {}
        for bucket_id in config['buckets'].keys():
            bucket_config = config['buckets'][bucket_id]
            bucket_obj = S3Bucket(bucket_id, s3_obj)
            apply_attributes_from_config(bucket_obj, bucket_config, self.config_folder)
            s3_obj.buckets[bucket_id] = bucket_obj
        return s3_obj

    def instantiate_iam(self, config):
        iam_obj = IAMResource()
        #for user_name in config['users']:
        #    user_config = config['users'][user_name]
        #    user_obj = IAMUser(user_name, iam_obj)
        #    for access_name in user_config['permissions']:
        #        perm_obj =

        apply_attributes_from_config(iam_obj, config)
        return iam_obj

    def instantiate_resources(self, name, config):
        if name == "Route53":
            self.project['route53'] = self.instantiate_route53(config)
        elif name == "CodeCommit":
            self.project['codecommit'] = self.instantiate_codecommit(config)
        elif name == "EC2":
            self.project['ec2'] = self.instantiate_ec2(config)
        elif name == "S3":
            self.project['s3'] = self.instantiate_s3(config)
        elif name == 'CloudTrail':
            self.project['cloudtrail'] = self.instantiate_cloudtrail(config)
        elif name == 'IAM':
            self.project['iam'] = self.instantiate_iam(config)

    def instantiate_env_region_config(
        self,
        config_name, # iam, applications
        item_klass,
        env_region_config,
        env_region,
        global_config
    ):
        """Load applications and IAM into an EnvironmentRegion

        Applications merge the global ApplicationEngine configuration
        with the EnvironmentDefault configuration with the final
        EnvironmentRegion configuration.
        """
        if config_name in env_region_config:
            global_item_config = global_config[config_name]
            for item_name, item_config in env_region_config[config_name].items():
                item = item_klass(item_name, getattr(env_region, config_name))
                if env_region.name == 'default':
                    # merge global with default
                    item_config = merge(global_config[config_name][item_name], env_region_config[config_name][item_name])
                    annotate_base_config(item, item_config, global_item_config[item_name])
                else:
                    # merge global with default, then merge that with local config
                    env_default = global_config['environments'][env_region.__parent__.name]['default']
                    if config_name in env_default:
                        default_region_config = env_default[config_name][item_name]
                        default_config = merge(global_item_config[item_name], default_region_config)
                        item_config = merge(default_config, item_config)
                        annotate_base_config(item, item_config, default_config)
                    # no default config, merge local with global
                    else:
                        item_config = merge(global_item_config[item_name], item_config)
                        annotate_base_config(item, item_config, global_item_config[item_name])

                env_region[config_name][item_name] = item # save
                apply_attributes_from_config(item, item_config, self.config_folder, read_file_path=self.read_file_path)

                if config_name == 'applications':
                    # Load resources for an application
                    if 'groups' not in item_config:
                        item_config['groups'] = {}
                    load_resources(
                        item.groups,
                        item_config['groups'],
                        self.config_folder,
                        self.monitor_config,
                        self.read_file_path
                    )
                elif config_name == 'iam':
                    self.load_iam_group(item.groups, item_config)

    def instantiate_network_environments(self, name, config):
        "Instantiates objects for everything in a NetworkEnvironments/some-workload.yaml file"
         # Network Environment
        if config['network'] == None:
            return
        net_env = self.create_apply_and_save(
            name, self.project['netenv'], NetworkEnvironment, config['network']
        )

        # Environments
        if 'environments' in config:
            for env_name, env_config in config['environments'].items():
                env = self.create_apply_and_save(
                    env_name,
                    net_env,
                    Environment,
                    env_config
                )
                # Load the EnvironmentRegion(s) and EnvironmentDefault
                for env_reg_name, env_reg_config in config['environments'][env_name].items():
                    # skip attributes
                    if env_reg_name == 'title': continue
                    # key must be a valid aws region name
                    if env_reg_name != 'default' and env_reg_name not in aws_regions:
                        raise InvalidAimProjectFile(
                            "Environment region name is not valid: {} in {}".format(env_reg_name, env_name)
                        )
                    if env_reg_name is not 'default':
                        env_region_config = merge(env_config['default'], env_reg_config)
                    else:
                        env_region_config = env_config['default']

                    if env_reg_name == 'default':
                        env_region = self.create_apply_and_save(
                            env_reg_name,
                            env,
                            EnvironmentDefault,
                            env_region_config
                        )
                    else:
                        env_region = self.create_apply_and_save(
                            env_reg_name,
                            env,
                            EnvironmentRegion,
                            env_region_config
                        )

                    # Network
                    network = env_region.network
                    # merge default only with base netenv
                    if env_reg_name == 'default':
                        if not 'network' in env_reg_config:
                            raise InvalidAimProjectFile(
                                "Default Environment {} must have base network config".format(env_region.__parent__.name)
                            )
                        net_config = merge(config['network'], env_reg_config['network'])
                    # merge EnvDefault and base network, then merge that with any EnvReg config
                    else:
                        default = config['environments'][env_region.__parent__.name]['default']
                        if not 'network' in default:
                            raise InvalidAimProjectFile(
                                "Default Environment {} must have base network config".format(env_region.__parent__.name)
                            )
                        net_config = merge(
                            config['network'],
                            default['network']
                        )
                        if 'network' in env_reg_config:
                            net_config = merge(net_config, env_reg_config['network'])
                    apply_attributes_from_config(network, net_config, self.config_folder, read_file_path=self.read_file_path)

                    # Applications
                    self.instantiate_env_region_config(
                        'applications',
                        Application,
                        env_region_config,
                        env_region,
                        config
                    )
                    if env_reg_name != 'default':
                        # Insert the environment and region into any Refs
                        self.normalize_environment_refs(env_region, env_name, env_reg_name)
