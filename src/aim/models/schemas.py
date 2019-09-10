from zope.interface import Interface, Attribute, invariant, Invalid
from zope.interface.common.mapping import IMapping
from zope.interface.common.sequence import ISequence
from zope import schema
from zope.schema.fieldproperty import FieldProperty
from aim.models import vocabulary
from aim.models.references import TextReference, FileReference
import json
import re
import ipaddress


# Constraints

class InvalidLayerARNList(schema.ValidationError):
    __doc__ = 'Not a valid list of Layer ARNs'

LAYER_ARN = re.compile(r"arn:aws:lambda:(.*):(\d+):layer:(.*):(.*)")
def isListOfLayerARNs(value):
    "Validate a list of Lambda Layer ARNs"
    if len(value) > 5:
        raise InvalidLayerARNList
    for arn in value:
        m = LAYER_ARN.match(arn)
        if not m:
            raise InvalidLayerARNList
        else:
            if m.groups()[0] not in vocabulary.aws_regions:
                raise InvalidLayerARNList
    return True

class InvalidS3KeyPrefix(schema.ValidationError):
    __doc__ = 'Not a valid S3 bucket prefix. Can not start or end with /.'

def isValidS3KeyPrefix(value):
    if value.startswith('/') or value.endswith('/'):
        raise InvalidS3KeyPrefix
    return True

class InvalidSNSSubscriptionProtocol(schema.ValidationError):
    __doc__ = 'Not a valid SNS Subscription protocol.'

def isValidSNSSubscriptionProtocol(value):
    if value not in vocabulary.subscription_protocols:
        raise InvalidSNSSubscriptionProtocol
    return True

class InvalidSNSSubscriptionEndpoint(schema.ValidationError):
    __doc__ = 'Not a valid SNS Endpoint.'

class InvalidJSON(schema.ValidationError):
    __doc__ = "Not a valid JSON document."

def isValidJSONOrNone(value):
    if not value:
        return True
    try:
        json.load(value)
    except json.decoder.JSONDecodeError:
        raise InvalidJSON
    return True

class InvalidApiGatewayAuthorizationType(schema.ValidationError):
    __doc__ = 'Not a valid Api Gateway Method Authorization Type.'

def isValidApiGatewayAuthorizationType(value):
    if value not in ('NONE', 'AWS_IAM', 'CUSTOM', 'COGNITO_USER_POOLS'):
        raise InvalidApiGatewayAuthorizationType
    return True

class InvalidApiGatewayIntegrationType(schema.ValidationError):
    __doc__ = 'Not a valid API Gateway Method Integration Type.'

def isValidApiGatewayIntegrationType(value):
    if value not in ('AWS', 'AWS_PROXY', 'HTTP', 'HTTP_PROXY', 'MOCK'):
        raise InvalidApiGatewayIntegrationType
    return True

class InvalidHttpMethod(schema.ValidationError):
    __doc__ = 'Not a valid HTTP Method.'

def isValidHttpMethod(value):
    if value not in ('ANY', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT'):
        raise InvalidHttpMethod
    return True

class InvalidApiKeySourceType(schema.ValidationError):
    __doc__ = 'Not a valid Api Key Source Type.'

def isValidApiKeySourceType(value):
    if value not in ('HEADER', 'AUTHORIZER'):
        raise InvalidApiKeySourceType
    return True

class InvalidEndpointConfigurationType(schema.ValidationError):
    __doc__ = "Not a valid endpoint configuration type, must be one of: 'EDGE', 'REGIONAL', 'PRIVATE'"

def isValidEndpointConfigurationType(value):
    if value not in ('EDGE', 'REGIONAL', 'PRIVATE'):
        raise
    return True

class InvalidBinaryMediaTypes(schema.ValidationError):
    __doc__ = 'Not a valid binary media types.'

def isValidBinaryMediaTypes(value):
    if len(value) == 0: return True
    d = {}
    # detect duplicates and / chars
    for item in value:
        if item not in d:
            d[item] = None
        else:
            raise InvalidBinaryMediaTypes("Entry {} is provided more than once".format(item))
        if item.find('/') != -1:
            raise InvalidBinaryMediaTypes("Entry {} must not contain a / character.".format(item))

    return True

class InvalidAWSRegion(schema.ValidationError):
    __doc__ = 'Not a valid AWS Region name.'

def isValidAWSRegionName(value):
    # Allow for missing_value
    if value == 'no-region-set': return True
    if value not in vocabulary.aws_regions:
        raise InvalidAWSRegion
    return True

def isValidAWSRegionNameOrNone(value):
    if value == '':
        return True
    if value not in vocabulary.aws_regions:
        raise InvalidAWSRegion
    return True

class InvalidEmailAddress(schema.ValidationError):
    __doc__ = 'Malformed email address'

EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")
def isValidEmail(value):
    if not EMAIL_RE.match(value):
        raise InvalidEmailAddress
    return True

class InvalidHttpUrl(schema.ValidationError):
    __doc__ = 'Malformed HTTP URL'

HTTP_RE = re.compile(r"^http:\/\/(.*)")
def isValidHttpUrl(value):
    if not HTTP_RE.match(value):
        raise InvalidHttpUrl
    return True

class InvalidHttpsUrl(schema.ValidationError):
    __doc__ = 'Malformed HTTPS URL'

HTTPS_RE = re.compile(r"^https:\/\/(.*)")
def isValidHttpsUrl(value):
    if not HTTPS_RE.match(value):
        raise InvalidHttpsUrl
    return True

class InvalidInstanceSizeError(schema.ValidationError):
    __doc__ = 'Not a valid instance size (or update the instance_size_info vocabulary).'

def isValidInstanceSize(value):
    if value not in vocabulary.instance_size_info:
        raise InvalidInstanceSizeError
    return True

class InvalidInstanceAMITypeError(schema.ValidationError):
    __doc__ = 'Not a valid instance AMI type (or update the ami_types vocabulary).'

def isValidInstanceAMIType(value):
    if value not in vocabulary.ami_types:
        raise InvalidInstanceAMITypeError
    return True

class InvalidHealthCheckTypeError(schema.ValidationError):
    __doc__ = 'Not a valid health check type (can only be EC2 or ELB).'

def isValidHealthCheckType(value):
    if value not in ('EC2', 'ELB'):
        raise InvalidHealthCheckTypeError
    return True

class InvalidStringCanOnlyContainDigits(schema.ValidationError):
    __doc__ = 'String must only contain digits.'

def isOnlyDigits(value):
    if re.match('\d+', value):
        return True
    raise InvalidStringCanOnlyContainDigits

class InvalidCloudWatchLogRetention(schema.ValidationError):
    __doc__ = 'String must be valid log retention value: {}'.format(', '.join(vocabulary.cloudwatch_log_retention.keys()))

def isValidCloudWatchLogRetention(value):
    if value == '': return True
    if value not in vocabulary.cloudwatch_log_retention:
        raise InvalidCloudWatchLogRetention
    return True

class InvalidCidrIpv4(schema.ValidationError):
    __doc__ = 'String must be a valid CIDR v4 (e.g. 20.50.120.4/30)'

def isValidCidrIpv4orBlank(value):
    """
    A valid CIDR v4 block or an empty string
    """
    if value == '':
        return True
    try:
        ip, cidr = value.split('/')
    except ValueError:
        raise InvalidCidrIpv4
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise InvalidCidrIpv4
    try:
        cidr = int(cidr)
    except ValueError:
        raise InvalidCidrIpv4
    if cidr < 0 or cidr > 32:
        raise InvalidCidrIpv4
    return True

class InvalidComparisonOperator(schema.ValidationError):
    __doc__ = 'Comparison Operator must be one of: GreaterThanThreshold, GreaterThanOrEqualToThreshold, LessThanThreshold, or LessThanOrEqualToThreshold.'

def isComparisonOperator(value):
    if value not in vocabulary.cloudwatch_comparison_operators:
        raise InvalidComparisonOperator
    return True

class InvalidPeriod(schema.ValidationError):
    __doc__ = 'Period must be one of: 10, 30, 60, 300, 900, 3600, 21600, 90000'

def isValidPeriod(value):
    """
    CloudWatch Period is limited to fixed intervals.
    These are the same intervals offered by the AWS Console.
    If you want to allow another value, need to ensrue the CloudWatchAlarm class
    can represent a human-readable value of it.
    """
    if value not in (10, 30, 60, 300, 900, 3600, 21600, 90000):
        raise InvalidPeriod
    return True

class InvalidAlarmSeverity(schema.ValidationError):
    __doc__ = 'Severity must be one of: low, critical'

def isValidAlarmSeverity(value):
    if value not in ('low','critical'):
        raise InvalidAlarmSeverity
    return True

def isValidAlarmSeverityFilter(value):
    "Filters can be None or ''"
    if not value: return True
    return isValidAlarmSeverity(value)

class InvalidAlarmClassification(schema.ValidationError):
    __doc__ = 'Classification must be one of: health, performance, security'

def isValidAlarmClassification(value):
    if value not in vocabulary.alarm_classifications:
        raise InvalidAlarmClassification
    return True

def isValidAlarmClassificationFilter(value):
    "Filters can be None or ''"
    if not value: return True
    return isValidAlarmClassification(value)

class InvalidASGMetricName(schema.ValidationError):
    __doc__ = 'ASG Metric name is not valid'

def isValidASGMetricNames(value):
    for string in value:
        if string not in vocabulary.asg_metrics:
            raise InvalidASGMetricName
    return True

class InvalidCWAgentTimezone(schema.ValidationError):
    __doc__ = 'Timezone choices for CW Agent'

def isValidCWAgentTimezone(value):
    if value not in ('Local','UTC'):
        raise InvalidCWAgentTimezone
    return True

class InvalidCFViewerProtocolPolicy(schema.ValidationError):
    __doc__ = 'Viewer Protocol Policy must be one of: allow-all | https-only | redirect-to-https'

def isValidCFViewerProtocolPolicy(value):
    if value not in ('allow-all','https-only','redirect-to-https'):
        raise InvalidCFViewerProtocolPolicy
    return True

class InvalidCloudFrontCookiesForward(schema.ValidationError):
    __doc__ = 'Cookies Forward must be one of: all | none | whitelist'

def isValidCloudFrontCookiesForward(value):
    if value not in ('all', 'none', 'whitelist'):
        raise InvalidCloudFrontCookiesForward
    return True

class InvalidCFSSLSupportedMethod(schema.ValidationError):
    __doc__ = 'SSL Supported Methods must be one of: sni-only | vip'

def isValidCFSSLSupportedMethod(value):
    if value not in ('sni-only', 'vip'):
        raise InvalidCFSSLSupportedMethod
    return True

class InvalidCFMinimumProtocolVersion(schema.ValidationError):
    __doc__ = 'Mimimum SSL Protocol Version must be one of: SSLv3 | TLSv1 | TLSv1.1_2016 | TLSv1.2_2018 | TLSv1_2016'

def isValidCFMinimumProtocolVersion(value):
    if value not in ('SSLv3', 'TLSv1', 'TLSv1.1_2016', 'TLSv1.2_2018', 'TLSv1_2016'):
        raise InvalidCFMinimumProtocolVersion
    return True

class InvalidCFPriceClass(schema.ValidationError):
    __doc__ = 'Price Class must be one of: 100 | 200 | All'

def isValidCFPriceClass(value):
    if value not in ('100', '200', 'All'):
        raise InvalidCFPriceClass
    return True

class InvalidCFProtocolPolicy(schema.ValidationError):
    __doc__ = 'Protocol Policy must be one of: http-only | https-only | match-viewer'

def isValidCFProtocolPolicy(value):
    if value not in ('http-only', 'https-only', 'match-viewer'):
        raise InvalidCFPProtocolPolicy
    return True

class InvalidCFSSLProtocol(schema.ValidationError):
    __doc__ = 'SSL Protocols must be one of: SSLv3 | TLSv1 | TLSv1.1 | TLSv1.2'

def isValidCFSSLProtocol(value):
    for protocol in value:
        if protocol not in ('SSLv3', 'TLSv1', 'TLSv1.1', 'TLSv1.2'):
            raise InvalidCFSSLProtocol
    return True

# ElastiCache
class InvalidAZMode(schema.ValidationError):
    __doc__ = 'AZMode must be one of: cross-az | single-az'

def isValidAZMode(value):
    if value not in ('cross-az', 'single-az'):
        raise InvalidAZMode
    return True

class InvalidRedisCacheParameterGroupFamily(schema.ValidationError):
    __doc__ = 'cache_parameter_group_family must be one of: redis2.6 | redis2.8 | redis3.2 | redis4.0 | redis5.0'

def isRedisCacheParameterGroupFamilyValid(value):
    if value not in ('redis2.6', 'redis2.8', 'redis3.2', 'redis4.0', 'redis5.0'):
        raise InvalidRedisCacheParameterGroupFamily
    return True


# IAM
class InvalidAIMCodeCommitPermissionPolicy(schema.ValidationError):
    __doc__ = 'permission must be one of: ReadWrite | ReadOnly'

def isAIMCodeCommitPermissionPolicyValid(value):
    if value not in ('ReadWrite', 'ReadOnly'):
        raise InvalidAIMCodeCommitPermissionPolicy
    return True

# CodeBuild
class InvalidCodeBuildComputeType(schema.ValidationError):
    __doc__ = 'codebuild_compute_type must be one of: BUILD_GENERAL1_SMALL | BUILD_GENERAL1_MEDIUM | BUILD_GENERAL1_LARGE'

def isValidCodeBuildComputeType(value):
    if value not in ('BUILD_GENERAL1_SMALL', 'BUILD_GENERAL1_MEDIUM', 'BUILD_GENERAL1_LARGE'):
        raise InvalidCodeBuildComputeType
    return True

# ----------------------------------------------------------------------------
# Here be Schemas!
#
class IDNSEnablable(Interface):
    """Provides a parent with an inheritable DNS enabled field"""
    dns_enabled = schema.Bool(
        title = 'Boolean indicating whether DNS record sets will be created.',
        default = True
    )

class CommaList(schema.List):
    """Comma separated list of valeus"""

    def constraint(self, value):
        """
        Validate something
        """
        return True
        # ToDo: how to get the AIM HOME and change to that directory from here?
        #path = pathlib.Path(value)
        #return path.exists()

class INamed(Interface):
    """
    A locatable resource
    """
    __parent__ = Attribute("Object reference to the parent in the object hierarchy")

    name = schema.TextLine(
        title="Name",
        default=""
    )
    title = schema.TextLine(
        title="Title",
        default="",
        required=False
    )

class IDeployable(Interface):
    enabled = schema.Bool(
        title="Enabled",
        description = "Could be deployed to AWS",
        default=False
    )

class IName(Interface):
    """
    A resource which has a name but is not locatable
    """
    name = schema.TextLine(
        title="Name",
        default=""
    )


class ITextReference(Interface):
    """A field containing a reference an aim model object or attribute"""
    pass
# work around a circular import
from zope.interface import classImplements
classImplements(TextReference, ITextReference)

class INameValuePair(Interface):
    name = schema.TextLine(
        title = "Name"
    )
    value = schema.TextLine(
        title = "Value"
    )

class IAdminIAMUser(IDeployable):
    """An AWS Account Administerator IAM User"""
    username = schema.TextLine(
        title = "IAM Username",
        default = ""
    )

class IAccounts(IMapping):
    "Collection of Accounts"
    pass

class IAccount(INamed):
    "Cloud account information"
    account_type = schema.TextLine(
        title = "Account Type",
        description = "Supported types: 'AWS'",
        default = "AWS"
    )
    account_id = schema.TextLine(
        title = "Account ID",
        description = "Can only contain digits.",
        required = True,
        constraint = isOnlyDigits
    )
    admin_delegate_role_name = schema.TextLine(
        title = "Administrator delegate IAM Role name for the account",
        description = "",
        default = ""
    )
    is_master = schema.Bool(
        title = "Boolean indicating if this a Master account",
        default = False
    )
    region = schema.TextLine(
        title = "Region to install AWS Account specific resources",
        default = "no-region-set",
        missing_value = "no-region-set",
        required = True,
        description = 'Must be a valid AWS Region name',
        constraint = isValidAWSRegionName
    )
    root_email = schema.TextLine(
        title = "The email address for the root user of this account",
        required = True,
        description = 'Must be a valid email address.',
        constraint = isValidEmail
    )
    organization_account_ids = schema.List(
        title = "A list of account ids to add to the Master account's AWS Organization",
        value_type = schema.TextLine(),
        required = False,
        default = [],
        description = 'Each string in the list must contain only digits.'
    )
    admin_iam_users = schema.Dict(
        title="Admin IAM Users",
        value_type = schema.Object(IAdminIAMUser),
        required = False
    )

class ISecurityGroupRule(IName):
    cidr_ip = schema.TextLine(
        title = "CIDR IP",
        default = "",
        description = "A valid CIDR v4 block or an empty string",
        constraint = isValidCidrIpv4orBlank
    )
    cidr_ip_v6 = schema.TextLine(
        title = "CIDR IP v6",
        description = "A valid CIDR v6 block or an empty string",
        default = ""
    )
    description = schema.TextLine(
        title = "Description",
        default = "",
        description = "Max 255 characters. Allowed characters are a-z, A-Z, 0-9, spaces, and ._-:/()#,@[]+=;{}!$*."
    )
    from_port = schema.Int(
        title = "From port",
        description = "A value of -1 indicates all ICMP/ICMPv6 types. If you specify all ICMP/ICMPv6 types, you must specify all codes.",
        default = -1,
        required = False
    )
    protocol = schema.TextLine(
        title = "IP Protocol",
        description = "The IP protocol name (tcp, udp, icmp, icmpv6) or number."
    )
    to_port = schema.Int(
        title = "To port",
        description = "A value of -1 indicates all ICMP/ICMPv6 types. If you specify all ICMP/ICMPv6 types, you must specify all codes.",
        default = -1,
        required = False
    )
    port = schema.Int(
        title = "Port",
        description = "A value of -1 indicates all ICMP/ICMPv6 types. If you specify all ICMP/ICMPv6 types, you must specify all codes.",
        default = -1,
        required = False
    )
    source_security_group = TextReference(
        title = "Source Security Group Reference",
        required = False,
        description = "An AIM Reference to a SecurityGroup",
        str_ok = True
    )

    @invariant
    def to_from_or_port(obj):
        if obj.port != -1 and (obj.to_port != -1 or obj.from_port != -1):
            raise Invalid("Both 'port' and 'to_port/from_port' must not have values.")
        elif obj.to_port == -1 and obj.from_port != -1:
            raise Invalid("The 'from_port' field must not be blank when 'to_port' has a value.")
        elif obj.from_port == -1 and obj.to_port != -1:
            raise Invalid("The 'to_port' field must not be blank when 'from_port' has a value.")

class IIngressRule(ISecurityGroupRule):
    "Security group ingress"

class IEgressRule(ISecurityGroupRule):
    "Security group egress"

class ISecurityGroup(INamed, IDeployable):
    """
    AWS Resource: Security Group
    """
    group_name = schema.TextLine(
        title = "Group name",
        default = "",
        description = "Up to 255 characters in length. Cannot start with sg-."
    )
    group_description = schema.TextLine(
        title = "Group description",
        default = "",
        description = "Up to 255 characters in length"
    )
    ingress = schema.List(
        title = "Ingress",
        value_type=schema.Object(schema=IIngressRule),
        default = [],
        description = "Every list item must be an IngressRule"
    )
    egress = schema.List(
        title = "Egress",
        value_type=schema.Object(schema=IEgressRule),
        default = [],
        description = "Every list item must be an EgressRule"
    )


class IApplicationEngines(INamed, IMapping):
    "A collection of Application Engines"
    pass

class IResource(INamed, IDeployable, IDNSEnablable):
    """
    AWS Resource to support an Application
    """
    type = schema.TextLine(
        title = "Type of Resources",
        description = "A valid AWS Resource type: ASG, LBApplication, etc."
    )
    resource_name = schema.TextLine(
        title = "AWS Resource Name",
        description = "",
        default = ""
    )
    resource_fullname = schema.TextLine(
        title = "AWS Resource Fullname",
        description = "",
        default = ""
    )
    order = schema.Int(
        title = "The order in which the resource will be deployed",
        description = "",
        min = 0,
        default = 0,
        required = False
    )
    change_protected = schema.Bool(
        title = "Boolean indicating whether this resource can be modified or not.",
        default = False
    )

class IServices(INamed, IMapping):
    """
    Services
    """
    pass


class IServiceAccountRegion(Interface):
    "An account and region for a service"
    account = TextReference(
        title = "Account Reference",
        required = False
    )
    region = schema.TextLine(
        title = "AWS Region",
        description = "Must be a valid AWS Region name",
        default = "no-region-set",
        missing_value = "no-region-set",
        required = True,
        constraint = isValidAWSRegionName
    )

class IServiceEnvironment(IServiceAccountRegion, INamed):
    "A service composed of one or more applications"
    applications = schema.Object(
        title = "Applications",
        schema = IApplicationEngines,
    )

class IGlobalResources(INamed, IMapping):
    "A collection of global Resources"

class IResources(INamed, IMapping):
    "A collection of Application Resources"
    pass

class IResourceGroup(INamed, IDeployable, IMapping, IDNSEnablable):
    "A collection of Application Resources"
    title = schema.TextLine(
        title="Title",
        default = ""
    )
    type = schema.TextLine(
        title="Type"
    )
    order = schema.Int(
        title = "The order in which the group will be deployed",
        description = "",
        min = 1,  # 0 is loading ad NoneType
        required = True
    )
    resources = schema.Object(IResources)
    dns_enabled = schema.Bool(
        title = ""
    )


class IResourceGroups(INamed, IMapping):
    "A collection of Application Resource Groups"
    pass

# Alarm and notification schemas

class IAlarmNotifications(IMapping):
    """
    Alarm Notifications
    """

class IAlarmNotification(Interface):
    """
    Alarm Notification
    """
    groups = schema.List(
        title = "List of groups",
        value_type=schema.TextLine(
            title="Group"
        ),
        required = True
    )
    classification = schema.TextLine(
        title = "Classification filter",
        description = "Must be one of: 'performance', 'security', 'health' or ''.",
        constraint = isValidAlarmClassificationFilter,
        default = ''
    )
    severity = schema.TextLine(
        title = "Severity filter",
        constraint = isValidAlarmSeverityFilter,
        description = "Must be one of: 'low', 'critical'"
    )

class INotifiable(Interface):
    """
    A notifiable object
    """
    notifications = schema.Object(
        title = "Alarm Notifications",
        schema = IAlarmNotifications,
    )

class IAlarmSet(INamed, IMapping, INotifiable):
    """
    A collection of Alarms
    """
    resource_type = schema.TextLine(
        title = "Resource type",
        description = "Must be a valid AWS resource type"
    )


class IAlarmSets(INamed, IMapping):
    """
    A collection of AlarmSets
    """

class IDimension(Interface):
    """
    A dimension of a metric
    """
    name = schema.TextLine(
        title = "Dimension name"
    )
    value = schema.TextLine(
        title = "Value to look-up dimension"
    )

class IAlarm(INamed, IDeployable, IName, INotifiable):
    """
    An Alarm
    """
    classification = schema.TextLine(
        title = "Classification",
        description = "Must be one of: 'performance', 'security' or 'health'",
        constraint = isValidAlarmClassification,
        required = True,
        default = 'unset',
        missing_value = 'unset'
    )
    description = schema.TextLine(
        title = "Description",
    )
    notification_groups = schema.List(
        readonly = True,
        title = "List of notificationn groups the alarm is subscribed to.",
        value_type=schema.TextLine(title="Notification group name")
    )
    runbook_url = schema.TextLine(
        title = "Runbook URL",
    )
    severity = schema.TextLine(
        title = "Severity",
        default = "low",
        constraint = isValidAlarmSeverity,
        description = "Must be one of: 'low', 'critical'"
    )

class ICloudWatchAlarm(IAlarm):
    """
    A CloudWatch Alarm
    """
    alarm_actions = schema.List(
        title = "Alarm Actions",
        readonly = True,
        value_type = schema.TextLine(
            title = "Alarm Action"
        )
    )
    alarm_description = schema.Text(
        title = "Alarm Description",
        readonly = True,
        description = "Valid JSON document with AIM fields."
    )
    actions_enabled = schema.Bool(
        title = "Actions Enabled",
        readonly = True,
    )
    comparison_operator = schema.TextLine(
        title = "Comparison operator",
        constraint = isComparisonOperator,
        description = "Must be one of: 'GreaterThanThreshold','GreaterThanOrEqualToThreshold', 'LessThanThreshold', 'LessThanOrEqualToThreshold'"
    )
    dimensions = schema.List(
        title = "Dimensions",
        value_type = schema.Object(schema=IDimension),
        default = []
    )
    evaluate_low_sample_count_percentile = schema.TextLine(
        title = "Evaluate low sample count percentile"
    )
    evaluation_periods = schema.Int(
        title = "Evaluation periods"
    )
    extended_statistic = schema.TextLine(
        title = "Extended statistic"
    )
    metric_name = schema.TextLine(
        title = "Metric name",
        required = True
    )
    namespace = schema.TextLine(
        title = "Namespace"
    )
    period = schema.Int(
        title = "Period in seconds",
        constraint = isValidPeriod,
        description = "Must be one of: 10, 30, 60, 300, 900, 3600, 21600, 90000"
    )
    statistic = schema.TextLine(
        title = "Statistic"
    )
    threshold = schema.Float(
        title = "Threshold"
    )
    treat_missing_data = schema.TextLine(
        title = "Treat missing data"
    )

class INotificationGroups(IServiceAccountRegion):
    "Container for Notification Groups"

# Logging schemas

class ICloudWatchLogRetention(Interface):
    expire_events_after_days = schema.TextLine(
        title = "Expire Events After. Retention period of logs in this group",
        description = "",
        default = "",
        constraint = isValidCloudWatchLogRetention
    )

class ICloudWatchLogSources(INamed, IMapping):
    """
    A collection of Log Sources
    """

class ICloudWatchLogSource(INamed, ICloudWatchLogRetention):
    """
    Log source for a CloudWatch agent
    """
    encoding = schema.TextLine(
        title = "Encoding",
        default = "utf-8"
    )
    log_stream_name = schema.TextLine(
        title = "Log stream name",
        description = "CloudWatch Log Stream name",
        default = ""
    )
    multi_line_start_pattern = schema.Text(
        title = "Multi-line start pattern",
        default = ""
    )
    path = schema.TextLine(
        title = "Path",
        default = "",
        required = True,
        description = "Must be a valid filesystem path expression. Wildcard * is allowed."
    )
    timestamp_format = schema.TextLine(
        title = "Timestamp format",
        default = "",
    )
    timezone = schema.TextLine(
        title = "Timezone",
        default = "Local",
        constraint = isValidCWAgentTimezone,
        description = "Must be one of: 'Local', 'UTC'"
    )

class IMetricTransformation(Interface):
    """
    Metric Transformation
    """
    default_value = schema.Float(
        title = "The value to emit when a filter pattern does not match a log event.",
        required = False,
    )
    metric_name = schema.TextLine(
        title = "The name of the CloudWatch Metric.",
        required = True,
    )
    metric_namespace = schema.TextLine(
        title = "The namespace of the CloudWatch metric.",
        required = True,
        max_length = 255,
    )
    metric_value = schema.TextLine(
        title = "The value that is published to the CloudWatch metric.",
        required = True,
    )

class IMetricFilters(INamed, IMapping):
    """
    Metric Filters
    """

class IMetricFilter(INamed):
    """
    Metric filter
    """
    filter_pattern = schema.Text(
        title = "Filter pattern",
        default = ""
    )
    metric_transformations = schema.List(
        title = "Metric transformations",
        value_type=schema.Object(
            title="Metric Transformation",
            schema=IMetricTransformation
        ),
        default = []
    )

class ICloudWatchLogGroups(INamed, IMapping):
    """
    A collection of Log Group objects
    """

class ICloudWatchLogGroup(INamed, ICloudWatchLogRetention):
    """
    A CloudWatchLogGroup is responsible for retention, access control and metric filters
    """
    metric_filters = schema.Object(
        title = "Metric Filters",
        schema = IMetricFilters
    )
    sources = schema.Object(
        title = "A CloudWatchLogSources container",
        schema = ICloudWatchLogSources
    )
    log_group_name = schema.TextLine(
        title = "Log group name. Can override the LogGroup name used from the name field.",
        description = "",
        default = ""
    )

class ICloudWatchLogSets(INamed, IMapping):
    """
    A collection of information about logs to collect.
    A mapping of ILogSet objects.
    """

class ICloudWatchLogSet(INamed, ICloudWatchLogRetention, IMapping):
    """
    A set of Log Group objects
    """
    log_groups = schema.Object(
        title = "A CloudWatchLogGroups container",
        schema = ICloudWatchLogGroups
    )

class ICloudWatchLogging(INamed, ICloudWatchLogRetention):
    """
    CloudWatch Logging configuration
    """
    log_sets = schema.Object(
        title = "A CloudWatchLogSets container",
        schema = ICloudWatchLogSets
    )

# Metric and monitoring schemas

class IMetric(Interface):
    """
    A set of metrics to collect and an optional collection interval:

    - name: disk
      measurements:
        - free
      collection_interval: 900
    """
    name = schema.TextLine(
        title = "Metric(s) group name"
    )
    measurements = schema.List(
        title = "Measurements",
        value_type=schema.TextLine(title="Metric measurement name")
    )
    collection_interval = schema.Int(
        title = "Collection interval",
        description = "",
        min = 1,
        required=False
    )

class IMonitorConfig(IDeployable, INamed, INotifiable):
    """
    A set of metrics and a default collection interval
    """
    collection_interval = schema.Int(
        title = "Collection interval",
        min = 1,
        default=60
    )
    metrics = schema.List(
        title = "Metrics",
        value_type=schema.Object(IMetric),
        default = []
    )
    asg_metrics = schema.List(
        title = "ASG Metrics",
        value_type=schema.TextLine(),
        default= [],
        constraint = isValidASGMetricNames,
        description = "Must be one of: 'GroupMinSize', 'GroupMaxSize', 'GroupDesiredCapacity', 'GroupInServiceInstances', 'GroupPendingInstances', 'GroupStandbyInstances', 'GroupTerminatingInstances', 'GroupTotalInstances'"
    )
    alarm_sets = schema.Object(
        title="Sets of Alarm Sets",
        schema=IAlarmSets,
    )
    log_sets = schema.Object(
        title="Sets of Log Sets",
        schema=ICloudWatchLogSets,
    )


class IMonitorable(Interface):
    """
    A monitorable resource
    """
    monitoring = schema.Object(
        schema = IMonitorConfig,
        required = False
    )

class IS3BucketPolicy(Interface):
    """
    S3 Bucket Policy
    """
    # ToDo: Validate actions using awacs
    action = schema.List(
        title="List of Actions",
        value_type=schema.TextLine(
            title="Action"
        ),
        required = True
    )
    aws = schema.List(
        title = "List of AWS Principles.",
        description = "Either this field or the principal field must be set.",
        value_type = schema.TextLine(
            title = "AWS Principle"
        ),
        default = [],
        required = False
    )
    condition = schema.Dict(
        title = "Condition",
        description = 'Each Key is the Condition name and the Value must be a dictionary of request filters. e.g. { "StringEquals" : { "aws:username" : "johndoe" }}',
        default = {},
        required = False,
        # ToDo: Use awacs to add a constraint to check for valid conditions
    )
    # ToDo: validate principal using awacs
    # ToDo: validate that only one principal type is supplied, as that is all that is currently supported by aim.cftemplates.s3.py
    principal = schema.Dict(
        title = "Prinicpals",
        description = "Either this field or the aws field must be set. Key should be one of: AWS, Federated, Service or CanonicalUser. Value can be either a String or a List.",
        default = {},
        required = False
    )
    effect = schema.TextLine(
        title="Effect",
        default="Deny",
        required = True,
        description = "Must be one of: 'Allow', 'Deny'"
    )
    resource_suffix = schema.List(
        title="List of AWS Resources Suffixes",
        value_type=schema.TextLine(
            title="Resources Suffix"
        ),
        required = True
    )
    @invariant
    def aws_or_principal(obj):
        if obj.aws == [] and obj.principal == {}:
            raise Invalid("Either the aws or the principal field must not be blank.")
        if obj.aws != [] and obj.principal != {}:
            raise Invalid("Can not set bot the aws and the principal fields.")


class IS3LambdaConfiguration(Interface):
    # ToDo: add constraint
    event = schema.TextLine(
        title = "S3 bucket event for which to invoke the AWS Lambda function",
        description = "Must be a supported event type: https://docs.aws.amazon.com/AmazonS3/latest/dev/NotificationHowTo.html",
    )
    # ToDo: constraint to validate the ref is to a Lambda type (tricky?)
    function = TextReference(
        title = "Reference to a Lambda"
    )

class IS3NotificationConfiguration(Interface):
    lambdas = schema.List(
        title = "Lambda configurations",
        value_type = schema.Object(IS3LambdaConfiguration),
        default = []
    )

class IS3Bucket(IResource, IDeployable):
    """
    S3 Bucket : A template describing an S3 Bbucket
    """
    bucket_name = schema.TextLine(
        title = "Bucket Name",
        description = "A short unique name to assign the bucket.",
        default = "bucket",
        required = True
    )
    account = TextReference(
        title = "Account Reference"
    )
    deletion_policy = schema.TextLine(
        title = "Bucket Deletion Policy",
        default = "delete",
        required = False
    )
    notifications = schema.Object(
        title = "Notification configuration",
        schema = IS3NotificationConfiguration,
    )
    policy = schema.List(
        title="List of S3 Bucket Policies",
        description="",
        value_type=schema.Object(IS3BucketPolicy),
        default=[]
    )
    region = schema.TextLine(
        title = "Bucket region",
        default = None,
        required = False
    )
    cloudfront_origin = schema.Bool(
        title = "Creates and listens for a CloudFront Access Origin Identity",
        required = False,
        default = False
    )
    external_resource = schema.Bool(
        title='Boolean indicating whether the S3 Bucket already exists or not',
        default = False
    )
    versioning = schema.Bool(
        title = "Enable Versioning on the bucket.",
        default = False
    )

class IS3Resource(INamed):
    """
    EC2 Resource Configuration
    """
    buckets = schema.Dict(
        title = "Group of EC2 Key Pairs",
        value_type = schema.Object(IS3Bucket),
        default = {}
    )

class IApplicationEngine(INamed, IDeployable, INotifiable, IDNSEnablable):
    """
    Application Engine : A template describing an application
    """
    groups = schema.Object(IResourceGroups)


class IApplication(IApplicationEngine, IMapping):
    """
    Application : An Application Engine configuration to run in a specific Environment
    """

#class IDeployment(IResource):
#    """
#    An application deployment
#    """

class ICodePipeBuildDeploy(IResource):
    """
    Code Pipeline: Build and Deploy
    """
    deployment_environment = schema.TextLine(
        title = "Deployment Environment",
        description = "",
        default = ""
    )
    deployment_branch_name = schema.TextLine(
        title = "Deployment Branch Name",
        description = "",
        default = ""
    )
    manual_approval_enabled = schema.Bool(
        title = "Manual approval enabled",
        description = "",
        default = False
    )
    manual_approval_notification_email = schema.TextLine(
        title = "Manual approval notification email",
        description = "",
        default = ""
    )
    codecommit_repository = TextReference(
        title = 'CodeCommit Respository'
    )
    asg = TextReference(
        title = "ASG Reference"
    )
    auto_rollback_enabled = schema.Bool(
        title = "Automatic rollback enabled",
        description = "",
        default = True
    )
    deploy_config_type = schema.TextLine(
        title = "Deploy Config Type",
        description = "",
        default = "HOST_COUNT"
    )
    deploy_style_option = schema.TextLine(
        title = "Deploy Style Option",
        description = "",
        default = "WITH_TRAFFIC_CONTROL"
    )
    deploy_config_value = schema.Int(
        title = "Deploy Config Value",
        description = "",
        default = 0
    )
    deploy_instance_role = TextReference(
        title = "Deploy Instance Role Reference"
    )
    elb_name = schema.TextLine(
        title = "ELB Name",
        description = "",
        default = ""
    )
    alb_target_group = TextReference(
        title = "ALB Target Group Reference"
    )
    tools_account = TextReference(
        title = "Tools Account Reference"
    )
    data_account = TextReference(
        title = "Data Account Reference"
    )
    cross_account_support = schema.Bool(
        title = "Cross Account Support",
        description = "",
        default = False
    )
    artifacts_bucket = TextReference(
        title = "Artifacts S3 Bucket Reference",
        description=""
    )
    codebuild_image = schema.TextLine(
        title = 'CodeBuild Docker Image'
    )
    codebuild_compute_type = schema.TextLine(
        title = 'CodeBuild Compute Type',
        constraint = isValidCodeBuildComputeType
    )
    timeout_mins = schema.Int(
        title = 'Timeout in Minutes',
        min = 5,
        max = 480,
        default = 60
    )

class IEC2KeyPair(INamed):
    """
    EC2 SSH Key Pair
    """
    region = schema.TextLine(
        title = "AWS Region",
        description = "Must be a valid AWS Region name",
        default = "no-region-set",
        missing_value = "no-region-set",
        required = True,
        constraint = isValidAWSRegionName
        )
    account = TextReference(
        title = 'AWS Account Reference'
    )

class IEC2Resource(INamed):
    """
    EC2 Resource Configuration
    """
    keypairs = schema.Dict(
        title = "Group of EC2 Key Pairs",
        value_type = schema.Object(IEC2KeyPair)
    )


class IService(IResource):
    """
    Specialized type of Resource
    """

class IEC2(IResource):
    """
    EC2 Instance
    """
    associate_public_ip_address = schema.Bool(
        title="Associate Public IP Address",
        description="",
        default=False
    )
    instance_iam_profile = Attribute("Instance IAM Profile")
    instance_ami = schema.TextLine(
        title="Instance AMI",
        description="",
    )
    instance_key_pair = TextReference(
        title = "Instance key pair reference",
        description=""
    )
    instance_type = schema.TextLine(
        title = "Instance type",
        description="",
    )
    segment = schema.TextLine(
        title="Segment",
        description="",
    )
    security_groups = schema.List(
        title="Security groups",
        description="",
        value_type=TextReference(
            title="AIM Reference"
        )
    )
    root_volume_size_gb = schema.Int(
        title="Root volume size GB",
        description="",
        default=8,
        min=8
    )
    disable_api_termination = schema.Bool(
        title="Disable API Termination",
        description="",
        default=False
    )
    private_ip_address = schema.TextLine(
        title="Private IP Address",
        description=""
    )
    user_data_script = schema.Text(
        title="User data script",
        description="",
        default=""
    )


class INetworkEnvironments(INamed, IMapping):
    """
    A collection of NetworkEnvironments
    """
    pass

class IProject(INamed, IMapping):
    "Project : the root node in the config for an AIM Project"
    aim_project_version = schema.TextLine(
        title = "AIM Project version",
        default = ""
    )

class IInternetGateway(IDeployable):
    """
    AWS Resource: IGW
    """

class INATGateway(INamed, IDeployable, IMapping):
    """
    AWS Resource: NAT Gateway
    """
    availability_zone = schema.Int(
        title="Availability Zone",
        description = "",
    )
    segment = TextReference(
        title="Segment",
        description = ""
    )
    default_route_segments = schema.List(
        title = "Default Route Segments",
        description = "",
        default = [],
        value_type = TextReference(
            title = "Segment"
        )
    )

class IVPNGateway(IDeployable, IMapping):
    """
    AWS Resource: VPN Gateway
    """

class IPrivateHostedZone(IDeployable):
    """
    AWS Resource: Private Hosted Zone
    """
    name = schema.TextLine(
        title = "Hosted zone name"
    )

class ISegment(INamed, IDeployable):
    """
    AWS Resource: Segment
    """
    internet_access = schema.Bool(
        title = "Internet Access",
        default = False
    )
    az1_cidr = schema.TextLine(
        title = "Availability Zone 1 CIDR",
        default = ""
    )
    az2_cidr = schema.TextLine(
        title = "Availability Zone 2 CIDR",
        default = ""
    )
    az3_cidr = schema.TextLine(
        title = "Availability Zone 3 CIDR",
        default = ""
    )
    az4_cidr = schema.TextLine(
        title = "Availability Zone 4 CIDR",
        default = ""
    )
    az5_cidr = schema.TextLine(
        title = "Availability Zone 5 CIDR",
        default = ""
    )
    az6_cidr = schema.TextLine(
        title = "Availability Zone 6 CIDR",
        default = ""
    )

class IVPCPeeringRoute(Interface):
    """
    VPC Peering Route
    """
    segment = TextReference(
        title = "Segment reference"
    )
    cidr = schema.TextLine(
        title = "CIDR IP",
        default = "",
        description = "A valid CIDR v4 block or an empty string",
        constraint = isValidCidrIpv4orBlank
    )

class IVPCPeering(INamed, IDeployable):
    """
    VPC Peering
    """
    # peer_* is used when peering with an external VPC
    peer_role_name = schema.TextLine(
        title = 'Remote peer role name',
        required = False
    )
    peer_vpcid = schema.TextLine(
        title = 'Remote peer VPC Id',
        required = False
    )
    peer_account_id = schema.TextLine(
        title = 'Remote peer AWS account Id',
        required = False
    )
    peer_region = schema.TextLine(
        title = 'Remote peer AWS region',
        required = False
    )
    # network_environment is used when peering with a network environment
    # local to the project.
    network_environment = TextReference(
        title = 'Network Environment Reference',
        required = False
    )
    # Routes forward traffic to the peering connection
    routing = schema.List(
        title = "Peering routes",
        value_type = schema.Object(IVPCPeeringRoute),
        required = True
    )


class IVPC(INamed, IDeployable):
    """
    AWS Resource: VPC
    """
    cidr = schema.TextLine(
        title = "CIDR",
        description = "",
        default = ""
    )
    enable_dns_hostnames = schema.Bool(
        title = "Enable DNS Hostnames",
        description = "",
        default = False
    )
    enable_dns_support = schema.Bool(
        title="Enable DNS Support",
        description = "",
        default = False
    )
    enable_internet_gateway = schema.Bool(
        title = "Internet Gateway",
        description = "",
        default = False
    )
    nat_gateway = schema.Dict(
        title = "NAT Gateway",
        description = "",
        value_type = schema.Object(INATGateway),
        required = True,
        default = {}

    )
    vpn_gateway = schema.Dict(
        title = "VPN Gateway",
        description = "",
        value_type = schema.Object(IVPNGateway),
        required = True,
        default = {}
    )
    private_hosted_zone = schema.Object(
        title = "Private hosted zone",
        description = "",
        schema = IPrivateHostedZone,
        required = False
    )
    security_groups = schema.Dict(
        # This is a dict of dicts ...
        title = "Security groups",
        default = {},
        description = "Two level deep dictionary: first key is Application name, second key is Resource name."
    )
    segments = schema.Dict(
        title="Segments",
        value_type = schema.Object(ISegment),
        required = False
    )
    peering = schema.Dict(
        title = 'VPC Peering',
        value_type = schema.Object(IVPCPeering),
        required = False
    )

class INetworkEnvironment(INamed, IDeployable, IMapping):
    """
    Network Environment : A template for a Network Environment
    """
    availability_zones = schema.Int(
        title="Availability Zones",
        description = "",
        default=0
    )
    vpc = schema.Object(
        title = "VPC",
        description = "",
        schema=IVPC,
        required=False
    )

class ICredentials(INamed):
    aws_access_key_id = schema.TextLine(
        title = "AWS Access Key ID",
        description = "",
        default = ""
        )
    aws_secret_access_key = schema.TextLine(
        title = "AWS Secret Access Key",
        description = "",
        default = ""
        )
    aws_default_region = schema.TextLine(
        title = "AWS Default Region",
        description = "Must be a valid AWS Region name",
        default = "no-region-set",
        missing_value = "no-region-set",
        required = True,
        constraint = isValidAWSRegionName
        )
    master_account_id = schema.TextLine(
        title = "Master AWS Account ID",
        description = "",
        default = ""
        )
    master_admin_iam_username = schema.TextLine(
        title = "Master Account Admin IAM Username",
        description = "",
        default = ""
        )
    admin_iam_role_name = schema.TextLine(
        title = "Administrator IAM Role Name"
        )
    mfa_session_expiry_secs = schema.Int(
        title = 'The number of seconds before an MFA token expires.',
        default = 60 * 60,   # 1 hour
        min = 60 * 15,       # 15 minutes
        max = (60 * 60) * 12 # 12 hours
    )
    assume_role_session_expiry_secs = schema.Int(
        title = 'The number of seconds before an assumed role token expires.',
        default = 60 * 15,   # 15 minuts
        min = 60 * 15,       # 15 minutes
        max = 60 * 60        # 1 hour
    )

class INetwork(INetworkEnvironment):
    aws_account = TextReference(
        title = 'AWS Account Reference'
    )

class IAWSCertificateManager(IResource):
    domain_name = schema.TextLine(
        title = "Domain Name",
        description = "",
        default = ""
    )
    subject_alternative_names = schema.List(
        title = "Subject alternative names",
        description = "",
        value_type=schema.TextLine(
            title="alternative name"
        ),
        default = []
    )
    external_resource = schema.Bool(
        title = "Marks this resource as external to avoid creating and validating it.",
        default = False,
        required = False
    )

class IPortProtocol(Interface):
    """Port and Protocol"""
    port = schema.Int(
        title = "Port"
    )
    protocol = schema.Choice(
        title="Protocol",
        vocabulary=vocabulary.target_group_protocol
    )

class ITargetGroup(IPortProtocol, IResource):
    """Target Group"""
    health_check_interval = schema.Int(
        title = "Health check interval"
    )
    health_check_timeout = schema.Int(
        title = "Health check timeout"
    )
    healthy_threshold = schema.Int(
        title = "Healthy threshold"
    )
    unhealthy_threshold = schema.Int(
        title = "Unhealthy threshold"
    )
    health_check_http_code = schema.TextLine(
        title = "Health check HTTP codes"
    )
    health_check_path = schema.TextLine(
        title = "Health check path",
        default = "/"
    )
    connection_drain_timeout = schema.Int(
        title = "Connection drain timeout"
    )

class IListenerRule(IDeployable):
    rule_type = schema.TextLine(
        title = "Type of Rule"
    )
    priority = schema.Int(
        title="Forward condition priority",
        required=False,
        default=1
    )
    host = schema.TextLine(
        title = "Host header value"
    )
    # Redirect Rule Variables
    redirect_host = schema.TextLine(
        title="The host to redirect to",
        required=False
    )
    # Forward Rule Variables
    target_group = schema.TextLine(
        title="Target group name",
        required=False
    )

class IListener(IPortProtocol):
    redirect = schema.Object(
        title = "Redirect",
        schema=IPortProtocol,
        required=False
    )
    ssl_certificates = schema.List(
        title = "List of SSL certificate References",
        value_type = TextReference(
            title = "SSL Certificate Reference"
        ),
        required=False,
        default = []
    )
    target_group = schema.TextLine(
        title = "Target group",
        default = "",
        required=False
    )
    rules = schema.Dict(
        title = "Container of listener rules",
        value_type = schema.Object(IListenerRule),
        required=False,
        default=None
    )

class IDNS(Interface):
    hosted_zone = TextReference(
        title = "Hosted Zone Id Reference",
        required = False
    )
    domain_name = TextReference(
        title = "Domain name",
        required = False,
        str_ok = True
     )
    ssl_certificate = TextReference(
        title = "SSL certificate Reference",
        required = False
    )

class ILBApplication(IResource, IMonitorable, IMapping):
    """Application Load Balancer"""
    target_groups = schema.Dict(
        title = "Target Groups",
        value_type=schema.Object(ITargetGroup)
    )
    listeners = schema.Dict(
        title = "Listeners",
        value_type=schema.Object(IListener)
    )
    dns = schema.List(
        title = "List of DNS for the ALB",
        value_type = schema.Object(IDNS),
        default = []
    )

    scheme = schema.Choice(
        title = "Scheme",
        vocabulary=vocabulary.lb_scheme
    )
    security_groups = schema.List(
        title = "Security Groups",
        value_type=TextReference(
            title="AIM Reference"
        )
    )
    segment = schema.TextLine(
        title = "Id of the segment stack"
    )
    idle_timeout_secs = schema.Int(
        title = 'Idle timeout in seconds',
        description = 'The idle timeout value, in seconds.',
        default = 60
    )


class IIAMs(INamed, IMapping):
    "Container for IAM Groups"

class IStatement(Interface):
    effect = schema.TextLine(
        title = "Effect",
        description = "Must be one of: 'Allow', 'Deny'",
        # ToDo: check constraint
        # constraint = vocabulary.iam_policy_effect
    )
    action = schema.List(
        title = "Action(s)",
        value_type=schema.TextLine(),
        default = []
    )
    resource =schema.List(
        title = "Resrource(s)",
        value_type=schema.TextLine(),
        default = []
    )

class IPolicy(Interface):
    name = schema.TextLine(
        title = "Policy name",
        default = ""
    )
    statement = schema.List(
        title = "Statements",
        value_type=schema.Object(
            title="Statement",
            schema=IStatement
        )
    )

class IAssumeRolePolicy(Interface):
    effect = schema.TextLine(
        title = "Effect",
        # ToDo: check constraint
        # constraint = vocabulary.iam_policy_effect
    )
    aws = schema.List(
        title = "List of AWS Principles",
        value_type=schema.TextLine(
            title="AWS Principle",
            default = "",
            required = False
        ),
        default = [],
        required = False
    )
    service = schema.List(
        title = "Service",
        value_type=schema.TextLine(
            title="Service",
            default = "",
            required = False
        ),
        default = [],
        required = False
    )
    # ToDo: what are 'aws' keys for? implement ...

class IRole(IDeployable):
    assume_role_policy = schema.Object(
        title = "Assume role policy",
        schema=IAssumeRolePolicy,
        required = False
    )
    instance_profile = schema.Bool(
        title = "Instance profile",
        default = False,
        required = False
    )
    path = schema.TextLine(
        title = "Path",
        default = "/",
        required = False
    )
    role_name = schema.TextLine(
        title = "Role name",
        default = "",
        required = False
    )
    policies = schema.List(
        title = "Policies",
        value_type=schema.Object(
            schema=IPolicy
        ),
        default = [],
        required = False
    )
    managed_policy_arns = schema.List(
        title = "Managed policy ARNs",
        value_type=schema.TextLine(
            title = "Managed policy ARN"
        ),
        default = [],
        required = False
    )
    max_session_duration = schema.Int(
        title = "Maximum session duration",
        description = "The maximum session duration (in seconds)",
        min = 3600,
        max = 43200,
        default = 3600,
        required = False
    )
    permissions_boundary = schema.TextLine(
        title = "Permissions boundary ARN",
        description = "Must be valid ARN",
        default = "",
        required = False
    )

#class IManagedPolicies(IMapping):
#    """
#    Container of IAM Managed Policices
#    """

class IManagedPolicy(INamed, IDeployable, IMapping):
    """
    IAM Managed Policy
    """

    roles = schema.List(
        title = "List of Role Names",
        value_type=schema.TextLine(
            title="Role Name"
        ),
        default = []
    )
    users = schema.List(
        title = "List of IAM Users",
        value_type=schema.TextLine(
            title = "IAM User name"
        ),
        default = []
    )
    statement = schema.List(
        title = "Statements",
        value_type=schema.Object(
            title="Statement",
            schema=IStatement
        )
    )
    path = schema.TextLine(
        title = "Path",
        default = "/",
        required = False
    )


class IIAM(INamed, IMapping):
    roles = schema.Dict(
        title = "Roles",
        value_type=schema.Object(
            title="Role",
            schema=IRole
        )
    )

    policies = schema.Dict(
        title = "Policies",
        value_type=schema.Object(
            title="ManagedPolicy",
            schema=IManagedPolicy
        )
    )

class IASG(IResource, IMonitorable):
    """
    Auto-scaling group
    """
    desired_capacity = schema.Int(
        title="Desired capacity",
        description="",
        default=1
    )
    min_instances = schema.Int(
        title="Minimum instances",
        description="",
        default=1
    )
    max_instances = schema.Int(
        title="Maximum instances",
        description="",
        default=2
    )
    update_policy_max_batch_size = schema.Int(
        title="Update policy maximum batch size",
        description="",
        default=1
    )
    update_policy_min_instances_in_service = schema.Int(
        title="Update policy minimum instances in service",
        description="",
        default=1
    )
    associate_public_ip_address = schema.Bool(
        title="Associate Public IP Address",
        description="",
        default=False
    )
    cooldown_secs = schema.Int(
        title="Cooldown seconds",
        description="",
        default=300
    )
    ebs_optimized = schema.Bool(
        title="EBS Optimized",
        description="",
        default=False
    )
    health_check_type = schema.TextLine(
        title="Health check type",
        description="Must be one of: 'EC2', 'ELB'",
        default='EC2',
        constraint = isValidHealthCheckType
    )
    health_check_grace_period_secs = schema.Int(
        title="Health check grace period in seconds",
        description="",
        default=300
    )
    instance_iam_role = schema.Object(IRole)
    instance_ami = TextReference(
        title="Instance AMI",
        description="",
        str_ok=True
    )
    instance_ami_type = schema.TextLine(
        title = "The AMI Operating System family",
        description = "Must be one of amazon, centos, suse, debian, ubuntu, microsoft or redhat.",
        constraint = isValidInstanceAMIType,
        default = "amazon"
    )
    instance_key_pair = TextReference(
        title = "Instance key pair reference",
        description=""
    )
    instance_type = schema.TextLine(
        title = "Instance type",
        description="",
        constraint = isValidInstanceSize
    )
    segment = schema.TextLine(
        title="Segment",
        description="",
    )
    termination_policies = schema.List(
        title="Terminiation policies",
        description="",
        value_type=schema.TextLine(
            title="Termination policy",
            description=""
        )
    )
    security_groups = schema.List(
        title="Security groups",
        description="",
        value_type=TextReference(
            title="AIM Reference"
        )
    )
    target_groups = schema.List(
        title="Target groups",
        description="",
        value_type=TextReference(
            title="AIM Reference"
        ),
        default = []
    )
    load_balancers = schema.List(
        title="Target groups",
        description="",
        value_type=TextReference(
            title="AIM Reference"
        ),
        default = []
    )
    termination_policies = schema.List(
        title="Termination policies",
        description="",
        value_type=schema.TextLine(
            title="Termination policy"
        )
    )
    user_data_script = schema.Text(
        title="User data script",
        description="",
        default=""
    )
    instance_monitoring =schema.Bool(
        title="Instance monitoring",
        description="",
        default=False
    )
    scaling_policy_cpu_average = schema.Int(
        title="Average CPU Scaling Polciy",
        # Default is 0 == disabled
        default=0,
        min=0,
        max=100
    )

class IEnvironmentDefault(INamed, IMapping):
    """
    Default values for an Environments configuration
    """

class IEnvironmentRegion(IEnvironmentDefault, IDeployable):
    """
    An actual deployed Environment in a specific region.
    May contains overrides of the IEnvironmentDefault where needed.
    """

class IEnvironment(INamed, IMapping):
    """
    Environment: Logical group of deployments
    """
    #default = schema.Object(IEnvironmentDefault)


class ILambdaVariable(Interface):
    """
    Lambda Environment Variable
    """
    key = schema.TextLine(
        title = 'Variable Name',
        required = True
    )
    value = TextReference(
        title = 'Variable Value',
        required = True,
        str_ok=True
    )

class ILambdaEnvironment(IMapping):
    """
    Lambda Environment
    """
    variables = schema.List(
        title = "Lambda Function Variables",
        value_type = schema.Object(ILambdaVariable),
        default = []
    )

class ILambdaFunctionCode(Interface):
    """The deployment package for a Lambda function."""

    @invariant
    def is_either_s3_or_zipfile(obj):
        "Validate that either zipfile or s3 bucket is set."
        if not obj.zipfile and not (obj.s3_bucket and obj.s3_key):
            raise Invalid("Either zipfile or s3_bucket and s3_key must be set. Or zipfile fle is an empty file.")
        if obj.zipfile and obj.s3_bucket:
            raise Invalid("Can not set both zipfile and s3_bucket")
        if obj.zipfile and len(obj.zipfile) > 4096:
            raise Invalid("Too bad, so sad. Limit of inline code of 4096 characters exceeded. File is {} chars long.".format(len(obj.zipfile)))

    zipfile = FileReference(
        title = "The function as an external file.",
        description = "Maximum of 4096 characters.",
        required = False
    )
    s3_bucket = TextReference(
        title = "An Amazon S3 bucket in the same AWS Region as your function",
        required = False
    )
    s3_key = schema.TextLine(
        title = "The Amazon S3 key of the deployment package.",
        required = False
    )

class ILambda(IResource, IMonitorable):
    """
    Lambda Function resource
    """
    code = schema.Object(
        title = "The function deployment package.",
        schema = ILambdaFunctionCode,
        required = True
    )
    description = schema.TextLine(
        title = "A description of the function.",
        required = True
    )
    environment = schema.Object(
        title = "Lambda Function Environment",
        schema = ILambdaEnvironment,
        default = None
    )
    iam_role = schema.Object(
        title = "The functions execution IAM role",
        required = True,
        schema = IRole
    )
    layers = schema.List(
        title = "Layers",
        value_type = schema.TextLine(),
        default = [],
        description = "Up to 5 Layer ARNs",
        constraint = isListOfLayerARNs
    )
    handler = schema.TextLine(
        title = "Function Handler",
        required = True
    )
    memory_size = schema.Int(
        title = "Function memory size (MB)",
        min = 128,
        max = 3008,
        default = 128
    )
    reserved_concurrent_executions = schema.Int(
        title = "Reserved Concurrent Executions",
        default = 0
    )
    runtime = schema.TextLine(
        title = "Runtime environment",
        required = True,
        # dotnetcore1.0 | dotnetcore2.1 | go1.x | java8 | nodejs10.x | nodejs8.10 | provided | python2.7 | python3.6 | python3.7 | ruby2.5
        default = 'python3.7'
    )
    # The amount of time that Lambda allows a function to run before stopping it. The default is 3 seconds. The maximum allowed value is 900 seconds.
    timeout = schema.Int(
        title = "Max function execution time in seconds.",
        description = "Must be between 0 and 900 seconds.",
        min = 0,
        max = 900,
    )
    sdb_cache = schema.Bool(
        title = "SDB Cache Domain",
        required=False,
        default=False
    )
    sns_topics = schema.List(
        title = "List of SNS Topic AIM Referenes",
        value_type =  TextReference(
            title = "SNS Topic AIM Reference",
            str_ok=True
        ),
        default = []
    )

# API Gateway

class IApiGatewayMethodMethodResponseModel(Interface):
    content_type = schema.TextLine(
        title = "Content Type"
    )
    model_name = schema.TextLine(
        title = "Model name",
        default = ""
    )

class IApiGatewayMethodMethodResponse(Interface):
    status_code = schema.TextLine(
        title = "HTTP Status code",
        description = "",
        required = True
    )
    response_models = schema.List(
        title = "The resources used for the response's content type.",
        description = """Specify response models as key-value pairs (string-to-string maps),
with a content type as the key and a Model AIM name as the value.""",
        value_type = schema.Object(title="Response Model", schema = IApiGatewayMethodMethodResponseModel),
        default = [],
    )

class IApiGatewayMethodIntegrationResponse(Interface):
    content_handling = schema.TextLine(
        title = "Specifies how to handle request payload content type conversions.",
        description = """Valid values are:

CONVERT_TO_BINARY: Converts a request payload from a base64-encoded string to a binary blob.

CONVERT_TO_TEXT: Converts a request payload from a binary blob to a base64-encoded string.

If this property isn't defined, the request payload is passed through from the method request
to the integration request without modification.
""",
        required = False
    )
    response_parameters = schema.Dict(
        title = "Response Parameters",
        default = {}
    )
    response_templates = schema.Dict(
        title = "Response Templates",
        default = {}
    )
    selection_pattern = schema.TextLine(
        title = "A regular expression that specifies which error strings or status codes from the backend map to the integration response.",
        required = False
    )
    status_code = schema.TextLine(
        title = "The status code that API Gateway uses to map the integration response to a MethodResponse status code.",
        description  = "Must match a status code in the method_respones for this API Gateway REST API.",
        required = True,
    )

class IApiGatewayMethodIntegration(Interface):
    integration_responses = schema.List(
        title = "Integration Responses",
        value_type = schema.Object(IApiGatewayMethodIntegrationResponse),
        default = []
    )
    request_parameters = schema.Dict(
        title = "The request parameters that API Gateway sends with the backend request.",
        description = """
        Specify request parameters as key-value pairs (string-to-string mappings), with a
destination as the key and a source as the value. Specify the destination by using the
following pattern `integration.request.location.name`, where `location` is query string, path,
or header, and `name` is a valid, unique parameter name.

The source must be an existing method request parameter or a static value. You must
enclose static values in single quotation marks and pre-encode these values based on
their destination in the request.
        """,
        default = {}
    )
    integration_http_method = schema.TextLine(
        title = "Integration HTTP Method",
        description = "Must be one of ANY, DELETE, GET, HEAD, OPTIONS, PATCH, POST or PUT.",
        default = "POST",
        constraint = isValidHttpMethod,
    )
    integration_type = schema.TextLine(
        title = "Integration Type",
        description = "Must be one of AWS, AWS_PROXY, HTTP, HTTP_PROXY or MOCK.",
        constraint = isValidApiGatewayIntegrationType,
        default = "AWS",
        required = True
    )
    integration_lambda = TextReference(
        title = "Integration Lambda"
    )
    uri = schema.TextLine(
        title = "Integration URI",
        required = False
    )


class IApiGatewayMethod(IResource):
    "API Gateway Method"
    authorization_type = schema.TextLine(
        title = "Authorization Type",
        description = "Must be one of NONE, AWS_IAM, CUSTOM or COGNITO_USER_POOLS",
        constraint = isValidApiGatewayAuthorizationType,
        required = True
    )
    http_method = schema.TextLine(
        title = "HTTP Method",
        description = "Must be one of ANY, DELETE, GET, HEAD, OPTIONS, PATCH, POST or PUT.",
        constraint = isValidHttpMethod
    )
    resource_id = schema.TextLine(
        title = "Resource Id"
    )
    integration = schema.Object(
        title = "Integration",
        schema = IApiGatewayMethodIntegration,
    )
    method_responses = schema.List(
        title = "Method Responses",
        description = "List of ApiGatewayMethod MethodResponses",
        value_type = schema.Object(IApiGatewayMethodMethodResponse),
        default = []
    )
    request_parameters = schema.Dict(
        title = "Request Parameters",
        description = """Specify request parameters as key-value pairs (string-to-Boolean mapping),
        with a source as the key and a Boolean as the value. The Boolean specifies whether
        a parameter is required. A source must match the format method.request.location.name,
        where the location is query string, path, or header, and name is a valid, unique parameter name.""",
        default = {}
    )

class IApiGatewayModel(IResource):
    content_type = schema.TextLine(
        title = "Content Type"
    )
    description = schema.Text(
        title = "Description"
    )
    schema = schema.Dict(
        title = "Schema",
        description = 'JSON format. Will use null({}) if left empty.',
        default = {},
    )

class IApiGatewayResource(IResource):
    parent_id = schema.TextLine(
        title = "Id of the parent resource. Default is 'RootResourceId' for a resource without a parent.",
        default = "RootResourceId",
    )
    path_part = schema.TextLine(
        title = "Path Part",
        required = True
    )
    rest_api_id = schema.TextLine(
        title = "Name of the API Gateway REST API this resource belongs to.",
        readonly = True
    )

class IApiGatewayStage(IResource):
    "API Gateway Stage"
    deployment_id = schema.TextLine(
        title = "Deployment ID"
    )
    description = schema.Text(
        title = "Description"
    )
    stage_name = schema.TextLine(
        title = "Stage name"
    )

class IApiGatewayModels(INamed, IMapping):
    "Container for API Gateway Model objects"

class IApiGatewayMethods(INamed, IMapping):
    "Container for API Gateway Method objects"

class IApiGatewayResources(INamed, IMapping):
    "Container for API Gateway Resource objects"

class IApiGatewayStages(INamed, IMapping):
    "Container for API Gateway Stage objects"

class IApiGatewayRestApi(IResource):
    "An Api Gateway Rest API resource"
    @invariant
    def is_valid_body_location(obj):
        "Validate that only one of body or body_file_location or body_s3_location is set or all are empty."
        count = 0
        if obj._body: count += 1
        if obj.body_file_location: count += 1
        if obj.body_s3_location: count += 1
        if count > 1:
            raise Invalid("Only one of body, body_file_location or body_s3_location can be set.")

    api_key_source_type = schema.TextLine(
        title = "API Key Source Type",
        description = "Must be one of 'HEADER' to read the API key from the X-API-Key header of a request or 'AUTHORIZER' to read the API key from the UsageIdentifierKey from a Lambda authorizer.",
        constraint = isValidApiKeySourceType
    )
    binary_media_types = schema.List(
        title = "Binary Media Types. The list of binary media types that are supported by the RestApi resource, such as image/png or application/octet-stream. By default, RestApi supports only UTF-8-encoded text payloads.",
        description = "Duplicates are not allowed. Slashes must be escaped with ~1. For example, image/png would be image~1png in the BinaryMediaTypes list.",
        constraint = isValidBinaryMediaTypes,
        value_type = schema.TextLine(
            title = "Binary Media Type"
        ),
        default = []
    )
    body = schema.Text(
        title = "Body. An OpenAPI specification that defines a set of RESTful APIs in JSON or YAML format. For YAML templates, you can also provide the specification in YAML format.",
        description = "Must be valid JSON."
    )
    body_file_location = FileReference(
        title = "Path to a file containing the Body.",
        description = "Must be valid path to a valid JSON document."
    )
    body_s3_location = schema.TextLine(
        title = "The Amazon Simple Storage Service (Amazon S3) location that points to an OpenAPI file, which defines a set of RESTful APIs in JSON or YAML format.",
        description = "Valid S3Location string to a valid JSON or YAML document."
    )
    clone_from = schema.TextLine(
        title = "CloneFrom. The ID of the RestApi resource that you want to clone."
    )
    description = schema.Text(
        title = "Description of the RestApi resource."
    )
    endpoint_configuration = schema.List(
        title = "Endpoint configuration. A list of the endpoint types of the API. Use this field when creating an API. When importing an existing API, specify the endpoint configuration types using the `parameters` field.",
        description = "List of strings, each must be one of 'EDGE', 'REGIONAL', 'PRIVATE'",
        value_type = schema.TextLine(
            title = "Endpoint Type",
            constraint = isValidEndpointConfigurationType
        ),
        default = []
    )
    fail_on_warnings = schema.Bool(
        title = "Indicates whether to roll back the resource if a warning occurs while API Gateway is creating the RestApi resource.",
        default = False
    )
    methods = schema.Object(
        schema = IApiGatewayMethods
    )
    minimum_compression_size = schema.Int(
        title = "An integer that is used to enable compression on an API. When compression is enabled, compression or decompression is not applied on the payload if the payload size is smaller than this value. Setting it to zero allows compression for any payload size.",
        description = "A non-negative integer between 0 and 10485760 (10M) bytes, inclusive.",
        default = None,
        required = False,
        min = 0,
        max = 10485760
    )
    models = schema.Object(
        schema = IApiGatewayModels
    )
    parameters = schema.Dict(
        title = "Parameters. Custom header parameters for the request.",
        description = "Dictionary of key/value pairs that are strings.",
        value_type = schema.TextLine(title = "Value"),
        default = {}
    )
    policy = schema.Text(
        title = """A policy document that contains the permissions for the RestApi resource, in JSON format. To set the ARN for the policy, use the !Join intrinsic function with "" as delimiter and values of "execute-api:/" and "*".""",
        description = "Valid JSON document",
        constraint = isValidJSONOrNone
    )
    resources = schema.Object(
        schema = IApiGatewayResources
    )
    stages = schema.Object(
        schema = IApiGatewayStages
    )

# Route53

class IRoute53HostedZone(IDeployable):
    """
    Route53 Hosted Zone
    """
    domain_name = schema.TextLine(
        title = "Domain Name",
        required = True
    )
    account = TextReference(
        title = "AWS Account Reference",
        required = True
    )

class IRoute53Resource(Interface):
    """
    Route53 Service Configuration
    """
    hosted_zones = schema.Dict(
        title = "Hosted Zones",
        value_type = schema.Object(IRoute53HostedZone),
        default = None
    )

class ICodeCommitUser(Interface):
    """
    CodeCommit User
    """
    username = schema.TextLine(
        title = "CodeCommit Username"
    )
    public_ssh_key = schema.TextLine(
        title = "CodeCommit User Public SSH Key",
        default = None,
        required = False
    )

class ICodeCommitRepository(INamed, IDeployable, IMapping):
    """
    CodeCommit Repository Configuration
    """
    repository_name = schema.TextLine(
        title = "Repository Name"
    )
    account = TextReference(
        title = "AWS Account Reference",
        required = True
    )
    region = schema.TextLine(
        title = "AWS Region"
    )
    description = schema.TextLine(
        title = "Repository Description"
    )
    users = schema.Dict(
        title = "CodeCommit Users",
        value_type = schema.Object(ICodeCommitUser),
        default = None
    )

class ICodeCommit(Interface):
    """
    CodeCommit Service Configuration
    """
    repository_groups = schema.Dict(
        title = "Group of Repositories",
        value_type = schema.Object(ICodeCommitRepository)
    )

class ISNSTopicSubscription(Interface):

    @invariant
    def is_valid_endpoint_for_protocol(obj):
        "Validate enpoint"
        # ToDo: this relies on other validation functions, maybe catch an re-raise
        # with more helpful error message context.
        # also check the other protocols ...
        if obj.protocol == 'http':
            isValidHttpUrl(obj.endpoint)
        elif obj.protocol == 'https':
            isValidHttpsUrl(obj.endpoint)
        elif obj.protocol in ['email','email-json']:
            isValidEmail(obj.endpoint)

    protocol = schema.TextLine(
        title = "Notification protocol",
        default = "email",
        description = "Must be a valid SNS Topic subscription protocol: 'http', 'https', 'email', 'email-json', 'sms', 'sqs', 'application', 'lambda'.",
        constraint = isValidSNSSubscriptionProtocol
    )
    endpoint = TextReference(
        title = "SNS Topic Endpoint",
        str_ok = True
    )

class ISNSTopic(IResource):
    """
    SNS Topic Resource Configuration
    """
    display_name = schema.TextLine(
        title = "Display name for SMS Messages"
    )
    subscriptions = schema.List(
        title = "List of SNS Topic Subscriptions",
        value_type = schema.Object(ISNSTopicSubscription),
        default = []
    )

class ICloudTrail(IResource):
    """
    CloudTrail resource
    """
    accounts = schema.List(
        title = "Accounts to enable this CloudTrail in. Leave blank to assume all accounts.",
        description = "A list of references to AIM Accounts.",
        value_type = TextReference(
            title = "Account Reference",
        ),
        default = []
    )
    cloudwatchlogs_log_group = TextReference(
        title = "A CloudWatch Logs LogGroup to deliver this trail to.",
        required = False
    )
    enable_kms_encryption = schema.Bool(
        title = "Enable KMS Key encryption",
        default = False
    )
    enable_log_file_validation = schema.Bool(
        title = "Enable log file validation",
        default = True
    )
    include_global_service_events = schema.Bool(
        title = "Include global service events",
        default = True
    )
    is_multi_region_trail = schema.Bool(
        title = "Is multi-region trail?",
        default = True
    )
    region = schema.TextLine(
        title = "Region to create the CloudTrail",
        default = "",
        description = 'Must be a valid AWS Region name or empty string',
        constraint = isValidAWSRegionNameOrNone
    )
    s3_key_prefix = schema.TextLine(
        title = "S3 Key Prefix specifies the Amazon S3 key prefix that comes after the name of the bucket.",
        description = "Do not include a leading or trailing / in your prefix. They are provided already.",
        default = "",
        max_length = 200,
        constraint = isValidS3KeyPrefix
    )

class ICloudTrails(INamed, IMapping):
    """
    Container for CloudTrail objects
    """

class ICloudTrailResource(INamed):
    """
    Global CloudTrail configuration
    """
    trails = schema.Object(
        title = "CloudTrails",
        schema = ICloudTrails,
        default = None
    )

class ICloudFrontCookies(Interface):
    forward = schema.TextLine(
        title = "Cookies Forward Action",
        constraint = isValidCloudFrontCookiesForward,
        default = 'all'
    )
    white_listed_names = schema.List(
        title = "White Listed Names",
        value_type = schema.TextLine(),
        default = [],
        required = False
    )

class ICloudFrontForwardedValues(Interface):
    query_string = schema.Bool(
        title = "Forward Query Strings",
        default = True
    )
    cookies = schema.Object(
        title = "Forward Cookies",
        schema = ICloudFrontCookies
    )
    headers = schema.List(
        title = "Forward Headers",
        value_type = schema.TextLine(),
        default = ['*']
    )

class ICloudFrontDefaultCacheBehaviour(Interface):
    allowed_methods = schema.List(
        title = "List of Allowed HTTP Methods",
        value_type = schema.TextLine(),
        default = [ 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT' ]
    )
    default_ttl = schema.Int(
        title = "Default TTTL",
        # Disable TTL bydefault, just pass through
        default = 0
    )
    target_origin = TextReference(
        title = "Target Origin"
    )
    viewer_protocol_policy = schema.TextLine(
        title = "Viewer Protocol Policy",
        constraint = isValidCFViewerProtocolPolicy,
        default = 'redirect-to-https'
    )
    forwarded_values = schema.Object(
        title = "Forwarded Values",
        schema = ICloudFrontForwardedValues
    )

class ICloudFrontViewerCertificate(IDeployable):
    certificate = TextReference(
        title = "Certificate Reference",
        required = False,
    )
    ssl_supported_method = schema.TextLine(
        title = "SSL Supported Method",
        constraint = isValidCFSSLSupportedMethod,
        required = False,
        default = 'sni-only'
    )
    minimum_protocol_version = schema.TextLine(
        title = "Minimum SSL Protocol Version",
        constraint = isValidCFMinimumProtocolVersion,
        required = False,
        default = 'TLSv1.1_2016'
    )

class ICloudFrontCustomErrorResponse(Interface):
    error_caching_min_ttl = schema.Int(
        title = "Error Caching Min TTL"
    )
    error_code = schema.Int(
        title = "HTTP Error Code"
    )
    response_code = schema.Int(
        title = "HTTP Response Code"
    )
    response_page_path = schema.TextLine(
        title = "Response Page Path"
    )

class ICloudFrontCustomOriginConfig(Interface):
    http_port = schema.Int(
        title = "HTTP Port",
        required = False
    )
    https_port = schema.Int(
        title = "HTTPS Port"
    )
    protocol_policy = schema.TextLine(
        title = "Protocol Policy",
        constraint = isValidCFProtocolPolicy
    )
    ssl_protocols = schema.List(
        title = "List of SSL Protocols",
        value_type = schema.TextLine(),
        constraint = isValidCFSSLProtocol
    )
    read_timeout = schema.Int(
        title = "Read timeout",
        min = 4,
        max = 60,
        default = 30
    )
    keepalive_timeout = schema.Int(
        title = "HTTP Keepalive Timeout",
        min = 1,
        max = 60,
        default = 5
    )

class ICloudFrontOrigin(INamed):
    """
    CloudFront Origin Configuration
    """
    s3_bucket = TextReference(
        title = "Origin S3 Bucket Reference",
        required = False
    )
    domain_name = TextReference(
        title = "Origin Resource Reference",
        str_ok = True,
        required = False
    )
    custom_origin_config = schema.Object(
        title = "Custom Origin Configuration",
        schema = ICloudFrontCustomOriginConfig,
        required = False
    )

class ICloudFrontFactory(INamed):
    """
    CloudFront Factory
    """
    domain_aliases = schema.List(
        title = "List of DNS for the Distribution",
        value_type = schema.Object(IDNS),
        default = []
    )

    viewer_certificate = schema.Object(
        title = "Viewer Certificate",
        schema = ICloudFrontViewerCertificate
    )

class ICloudFront(IResource, IDeployable):
    """
    CloudFront CDN Configuration
    """
    domain_aliases = schema.List(
        title = "List of DNS for the Distribution",
        value_type = schema.Object(IDNS),
        default = []
    )
    default_root_object = schema.TextLine(
        title = "The default path to load from the origin.",
        default = 'index.html'
    )
    default_cache_behavior = schema.Object(
        title = "Default Cache Behavior",
        schema = ICloudFrontDefaultCacheBehaviour
    )
    viewer_certificate = schema.Object(
        title = "Viewer Certificate",
        schema = ICloudFrontViewerCertificate
    )
    price_class = schema.TextLine(
        title = "Price Class",
        constraint = isValidCFPriceClass,
        default = 'All'
    )
    custom_error_responses = schema.List(
        title = "List of Custom Error Responses",
        value_type = schema.Object(ICloudFrontCustomErrorResponse),
        default = []
    )
    origins = schema.Dict(
        title = "Map of Origins",
        value_type = schema.Object(ICloudFrontOrigin)
    )
    webacl_id = schema.TextLine(
        title = "WAF WebACLId"
    )
    factory = schema.Dict(
        title = "CloudFront Factory",
        value_type = schema.Object(ICloudFrontFactory),
        default = None
    )

class IRDSOptionConfiguration(Interface):
    """
    AWS::RDS::OptionGroup OptionConfiguration
    """
    option_name = schema.TextLine(
        title = 'Option Name'
    )
    option_settings = schema.List(
        title = 'List of option name value pairs.',
        value_type = schema.Object(INameValuePair),
        default = [],
        required = False,
    )
    option_version = schema.TextLine(
        title = 'Option Version',
        required = False,
    )
    port = schema.TextLine(
        title = 'Port',
        required = False,
    )
    # - DBSecurityGroupMemberships
    #   A list of DBSecurityGroupMembership name strings used for this option.
    # - VpcSecurityGroupMemberships
    #   A list of VpcSecurityGroupMembership name strings used for this option.




class IRDS(Interface):
    """
    RDS Common Interface
    """
    engine = schema.TextLine(
        title = "RDS Engine"
    )
    engine_version = schema.TextLine(
        title = "RDS Engine Version"
    )
    db_instance_type = schema.TextLine(
        title = "RDS Instance Type"
    )
    port = schema.Int(
        title = "DB Port"
    )
    segment = TextReference(
        title="Segment"
    )
    storage_type = schema.TextLine(
        title = "DB Storage Type"
    )
    storage_size_gb = schema.Int(
        title = "DB Storage Size in Gigabytes"
    )
    storage_encrypted = schema.Bool(
        title = "Enable Storage Encryption"
    )
    kms_key_id = TextReference(
        title = "Enable Storage Encryption",
        required = False
    )
    allow_major_version_upgrade = schema.Bool(
        title = "Allow major version upgrades"
    )
    allow_minor_version_upgrade = schema.Bool(
        title = "Allow minor version upgrades"
    )
    publically_accessible = schema.Bool(
        title = "Assign a Public IP address"
    )
    master_username = schema.TextLine(
        title = "Master Username"
    )
    master_user_password = schema.TextLine(
        title = "Master User Password"
    )
    backup_preferred_window = schema.TextLine(
        title = "Backup Preferred Window"
    )
    backup_retention_period = schema.Int(
        title = "Backup Retention Period in days"
    )
    maintenance_preferred_window = schema.TextLine(
        title = "Maintenance Preferred Window"
    )
    security_groups = schema.List(
        title = "List of Security Groups",
        value_type = TextReference()
    )
    primary_domain_name = TextReference(
        title = "Primary Domain Name",
        str_ok = True
    )
    primary_hosted_zone = TextReference(
        title = "Primary Hosted Zone"
    )
    db_snapshot_identifier = schema.TextLine(
        title = 'DB Snapshot Identifier to restore from'
    )
    option_configurations = schema.List(
        title = "Option Configurations",
        value_type=schema.Object(IRDSOptionConfiguration),
        required = False,
        default = []
    )

class IRDSMysql(IResource, IRDS):
    """
    RDS Mysql
    """
    multi_az = schema.Bool(
        title = "MultiAZ Support",
        default = False
    )

class IRDSAurora(IResource, IRDS):
    """
    RDS Aurora
    """
    secondary_domain_name = TextReference(
        title = "Secondary Domain Name",
        str_ok = True
    )
    secondary_hosted_zone = TextReference(
        title = "Secondary Hosted Zone"
    )

class IElastiCache(Interface):
    """
    Base ElastiCache Interface
    """
    engine = schema.TextLine(
        title = "ElastiCache Engine",
        required = False
    )
    engine_version = schema.TextLine(
        title = "ElastiCache Engine Version",
        required = False
    )
    automatic_failover_enabled = schema.Bool(
        title = "Specifies whether a read-only replica is automatically promoted to read/write primary if the existing primary fails"
    )
    number_of_read_replicas = schema.Int(
        title = "Number of read replicas"
    )
    port = schema.Int(
        title = 'Port'
    )
    at_rest_encryption = schema.Bool(
        title = "Enable encryption at rest"
    )
    auto_minor_version_upgrade = schema.Bool(
        title = "Enable automatic minor version upgrades"
    )
    az_mode = schema.TextLine(
        title = "AZ mode",
        constraint = isValidAZMode
    )
    cache_node_type  = schema.TextLine(
        title = "Cache Node Instance type",
        description=""
    )
    maintenance_preferred_window = schema.TextLine(
        title = 'Preferred maintenance window'
    )
    security_groups = schema.List(
        title = "List of Security Groups",
        value_type = TextReference()
    )
    segment = TextReference(
        title="Segment"
    )

class IElastiCacheRedis(IResource, IElastiCache):
    """
    Redis ElastiCache Interface
    """
    cache_parameter_group_family = schema.TextLine(
        title = 'Cache Parameter Group Family',
        constraint = isRedisCacheParameterGroupFamilyValid,
        required = False
    )
    #snapshot_retention_limit_days: 1
    #snapshot_window: 05:00-09:00

class IIAMUserProgrammaticAccess(IDeployable):
    """
    IAM User Programmatic Access Configuration
    """
    access_key_1_version = schema.Int(
        title = 'Access key version id',
        default = 0,
        required = False
    )
    access_key_2_version = schema.Int(
        title = 'Access key version id',
        default = 0,
        required = False
    )

class IIAMUserPermission(INamed, IDeployable):
    """
    IAM User Permission
    """
    type = schema.TextLine(
        title = "Type of IAM User Access",
        description = "A valid AIM IAM user access type: Administrator, CodeCommit, etc."
    )

class IIAMUserPermissionAdministrator(IIAMUserPermission):
    """
    Administrator IAM User Permission
    """
    accounts = CommaList(
        title = 'Comma separated list of AIM AWS account names this user has access to'
    )
    read_only = schema.Bool(
        title = 'Enabled ReadOnly access',
        default = False,
        required = False
    )


class IIAMUserPermissionCodeCommitRepository(Interface):
    """
    CodeCommit Repository IAM User Permission Definition
    """
    codecommit = TextReference(
        title = 'CodeCommit Repository Reference',
        required = False
    )
    permission = schema.TextLine(
        title = 'AIM Permission policy',
        constraint = isAIMCodeCommitPermissionPolicyValid,
        required = False
    )
    console_access_enabled = schema.Bool(
        title = 'Console Access Boolean',
        required = False
    )
    public_ssh_key = schema.TextLine(
        title = "CodeCommit User Public SSH Key",
        default = None,
        required = False
    )

class IIAMUserPermissionCodeCommit(IIAMUserPermissionCodeCommitRepository):
    """
    CodeCommit IAM User Permission
    """
    repositories = schema.List(
        title = 'List of repository permissions',
        value_type = schema.Object(IIAMUserPermissionCodeCommitRepository)
    )

class IIAMUserPermissions(INamed, IMapping):
    """
    Group of IAM User Permissions
    """
    pass

class IIAMUser(INamed):
    """
    IAM User
    """
    account = TextReference(
        title = "AIM account reference to install this user",
        required = True
    )
    username = schema.TextLine(
        title = 'IAM Username'
    )
    description = schema.TextLine(
        title = 'IAM User Description'
    )
    console_access_enabled = schema.Bool(
        title = 'Console Access Boolean'
    )
    programmatic_access = schema.Object(
        title = 'Programmatic Access',
        schema = IIAMUserProgrammaticAccess
    )
    permissions = schema.Object(
        title = 'AIM IAM User Permissions',
        schema = IIAMUserPermissions
    )
    account_whitelist = CommaList(
        title = 'Comma separated list of AIM AWS account names this user has access to'
    )

class IIAMResource(INamed):
    """
    IAM AWS Resource
    """
    users = schema.Dict(
        title = 'IAM Users',
        value_type = schema.Object(IIAMUser)
    )

class IDeploymentPipelineConfiguration(INamed):
    """
    Deployment Pipeline General Configuration
    """
    artifacts_bucket = TextReference(
        title = "Artifacts S3 Bucket Reference",
        description=""
    )
    account = TextReference(
        title = "The account where Pipeline tools will be provisioned."
    )

class IDeploymentPipelineStageAction(INamed, IDeployable, IMapping):
    """
    Deployment Pipeline Source Stage
    """
    type = schema.TextLine(
        title = 'The type of DeploymentPipeline Source Stage'
    )
    run_order = schema.Int(
        title = 'The order in which to run this stage',
        min = 1,
        max = 999,
        default = 1,
    )

class IDeploymentPipelineSourceCodeCommit(IDeploymentPipelineStageAction):
    """
    CodeCommit DeploymentPipeline Source Stage
    """
    codecommit_repository = TextReference(
        title = 'CodeCommit Respository'
    )

    deployment_branch_name = schema.TextLine(
        title = "Deployment Branch Name",
        description = "",
        default = ""
    )

class IDeploymentPipelineBuildCodeBuild(IDeploymentPipelineStageAction):
    """
    CodeBuild DeploymentPipeline Build Stage
    """
    deployment_environment = schema.TextLine(
        title = "Deployment Environment",
        description = "",
        default = ""
    )
    codebuild_image = schema.TextLine(
        title = 'CodeBuild Docker Image'
    )
    codebuild_compute_type = schema.TextLine(
        title = 'CodeBuild Compute Type',
        constraint = isValidCodeBuildComputeType
    )
    timeout_mins = schema.Int(
        title = 'Timeout in Minutes',
        min = 5,
        max = 480,
        default = 60
    )

class IDeploymentPipelineDeployS3(IDeploymentPipelineStageAction):
    """
    Amazon S3 Deployment Provider
    """
    # BucketName: Required
    bucket = TextReference(
        title = "S3 Bucket Reference"
    )
    # Extract: Required: Required if Extract = false
    extract = schema.Bool(
        title = "Boolean indicating whether the deployment artifact will be unarchived.",
        default = True
    )
    # ObjectKey: Required if Extract = false
    object_key = schema.TextLine(
        title = "S3 object key to store the deployment artifact as.",
        required = False
    )
    # KMSEncryptionKeyARN: Optional
    # This is used internally for now.
    #kms_encryption_key_arn = schema.TextLine(
    #    title = "The KMS Key Arn used for artifact encryption.",
    #    required = False
    #)
    # : CannedACL: Optional
    # https://docs.aws.amazon.com/AmazonS3/latest/dev/acl-overview.html#canned-acl
    # canned_acl =

    # CacheControl: Optional
    # cache_control = schema.TextLine()
    # The CacheControl parameter controls caching behavior for requests/responses for objects
    # in the bucket. For a list of valid values, see the Cache-Control header field for HTTP
    # operations. To enter multiple values in CacheControl, use a comma between each value.
    #
    # You can add a space after each comma (optional), as shown in this example for the CLI:
    #
    # "CacheControl": "public, max-age=0, no-transform"

class IDeploymentPipelineDeployManualApproval(IDeploymentPipelineStageAction):
    """
    ManualApproval DeploymentPipeline Deploy Stage
    """
    manual_approval_notification_email = schema.TextLine(
        title = "Manual approval notification email",
        description = "",
        default = ""
    )

class ICodeDeployMinimumHealthyHosts(INamed):
    """
    CodeDeploy Minimum Healthy Hosts
    """
    type = schema.TextLine(
        title = "Deploy Config Type",
        default = "HOST_COUNT"
    )
    value = schema.Int(
        title = "Deploy Config Value",
        default = 0
    )


class IDeploymentPipelineDeployCodeDeploy(IDeploymentPipelineStageAction):
    """
    CodeDeploy DeploymentPipeline Deploy Stage
    """
    auto_scaling_group = TextReference(
        title = "ASG Reference"
    )
    auto_rollback_enabled = schema.Bool(
        title = "Automatic rollback enabled",
        description = "",
        default = True
    )
    minimum_healthy_hosts = schema.Object(
        title = "The minimum number of healthy instances that should be available at any time during the deployment.",
        schema = ICodeDeployMinimumHealthyHosts,
        required = False
    )
    deploy_style_option = schema.TextLine(
        title = "Deploy Style Option",
        description = "",
        default = "WITH_TRAFFIC_CONTROL"
    )
    deploy_instance_role = TextReference(
        title = "Deploy Instance Role Reference"
    )
    elb_name = schema.TextLine(
        title = "ELB Name",
        description = "",
        default = ""
    )
    alb_target_group = TextReference(
        title = "ALB Target Group Reference"
    )

class IDeploymentPipelineSourceStage(INamed, IMapping):
    """
    A map of DeploymentPipeline source stage actions
    """
    pass

class IDeploymentPipelineBuildStage(INamed, IMapping):
    """
    A map of DeploymentPipeline build stage actions
    """
    pass

class IDeploymentPipelineDeployStage(INamed, IMapping):
    """
    A map of DeploymentPipeline deploy stage actions
    """
    pass

class IDeploymentPipeline(IResource):
    """
    Code Pipeline: Build and Deploy
    """
    configuration = schema.Object(
        title = 'Deployment Pipeline General Configuration',
        schema = IDeploymentPipelineConfiguration
    )
    source = schema.Object(
        title = 'Deployment Pipeline Source Stage',
        schema = IDeploymentPipelineSourceStage
    )
    build = schema.Object(
        title = 'Deployment Pipeline Build Stage',
        schema = IDeploymentPipelineBuildStage
    )
    deploy = schema.Object(
        title = 'Deployment Pipeline Deploy Stage',
        schema =IDeploymentPipelineDeployStage
    )