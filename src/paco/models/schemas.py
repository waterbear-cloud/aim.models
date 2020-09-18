from zope.interface import Interface, Attribute, invariant, Invalid, classImplements, taggedValue
from zope.interface.common.mapping import IMapping
from zope.interface.common.sequence import ISequence
from zope import schema
from zope.schema.fieldproperty import FieldProperty
from paco.models import vocabulary
from paco.models import gen_vocabulary
from paco.models.references import PacoReference, FileReference, StringFileReference, YAMLFileReference
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

class InvalidStringConditionOperator(schema.ValidationError):
    __doc__ = 'String Condition operator must be one of: StringEquals, StringNotEquals, StringEqualsIgnoreCase, StringNotEqualsIgnoreCase, StringLike, StringNotLike.',

def isValidStringConditionOperator(value):
    if value.lower() not in ('stringequals', 'stringnotequals', 'stringequalsignorecase', 'stringnotequalsignorecase', 'stringlike', 'stringnotlike'):
        raise InvalidStringConditionOperator
    return True

class InvalidBackupNotification(schema.ValidationError):
    __doc__ = 'Backup Vault notification event must be one of: BACKUP_JOB_STARTED, BACKUP_JOB_COMPLETED, RESTORE_JOB_STARTED, RESTORE_JOB_COMPLETED, RECOVERY_POINT_MODIFIED.'

def isValidBackupNotification(value):
    for item in value:
        if item not in ('BACKUP_JOB_STARTED', 'BACKUP_JOB_COMPLETED', 'RESTORE_JOB_STARTED', 'RESTORE_JOB_COMPLETED', 'RECOVERY_POINT_MODIFIED'):
            raise InvalidBackupNotification
    return True

class InvalidEnhancedMonitoringInterval(schema.ValidationError):
    __doc__ = 'Enhanced Monitoring Interval must be one of 0, 1, 5, 10, 15, 30, 60'

def isValidEnhancedMonitoringInterval(value):
    if value not in [None, 0, 1, 5, 10, 15, 30, 60]:
        raise InvalidEnhancedMonitoringInterval
    return True

class InvalidCodeDeployComputePlatform(schema.ValidationError):
    __doc__ = 'compute_platform must be one of ECS, Lambda or Server.'

def isValidCodeDeployComputePlatform(value):
    if value not in ('ECS', 'Lambda', 'Server'):
        raise InvalidCodeDeployComputePlatform
    return True

class InvalidDeploymentGroupBundleType(schema.ValidationError):
    __doc__ = 'Bundle Type must be one of JSON, tar, tgz, YAML or zip.'

def isValidDeploymentGroupBundleType(value):
    if value not in ('JSON', 'tar', 'tgz', 'YAML', 'zip'):
        raise InvalidDeploymentGroupBundleType
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
        json.loads(value)
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
        raise InvalidEndpointConfigurationType
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

class InvalidS3BucketHash(schema.ValidationError):
    __doc__ = 'S3 Bucket suffix must be lower-case alphanumberic characters and no longer than 12 characters.'

def isValidS3BucketHash(value):
    "Must be lowercase alphanumeric and no more than 12 characters"
    if len(value) > 12:
        raise InvalidS3BucketHash
    if re.match('^[0-9a-z]+$', value):
        return True
    raise InvalidS3BucketHash

def isValidAWSRegionList(value):
    for region in value:
        isValidAWSRegionName(region)
    return True

def isValidAWSRegionOrAllList(value):
    if value == ['ALL']: return True
    for region in value:
        isValidAWSRegionName(region)
    return True

class InvalidAWSHealthCheckRegion(schema.ValidationError):
    __doc__ = "AWS Health Check regions are: 'sa-east-1', 'us-west-1', 'us-west-2', 'ap-northeast-1', 'ap-southeast-1', 'eu-west-1', 'us-east-1', 'ap-southeast-2'"

def isValidHealthCheckAWSRegionList(value):
    # must be at least 3 but 0 is Okay too
    if len(value) == 1 or len(value) == 2:
        raise InvalidAWSHealthCheckRegion("If health_check_regions is specified, it must contain at least 3 regions.")
    regions = ('sa-east-1', 'us-west-1', 'us-west-2', 'ap-northeast-1', 'ap-southeast-1', 'eu-west-1', 'us-east-1', 'ap-southeast-2')
    for region in value:
        if region not in regions:
            raise InvalidAWSHealthCheckRegion("Region {} is not a valid Route53 health check region.".format(region))
    return True


valid_legacy_flags = (
        'cftemplate_aws_name_2019_09_17',
        'route53_controller_type_2019_09_18',
        'codecommit_controller_type_2019_09_18',
        'lambda_controller_type_2019_09_18',
        'cloudwatch_controller_type_2019_09_18',
        'cftemplate_iam_user_delegates_2019_10_02',
        'route53_hosted_zone_2019_10_12',
        'iam_user_default_password_2019_10_12',
        'netenv_loggroup_name_2019_10_13',
        'route53_record_set_2019_10_16',
        'target_group_name_2019_10_29',
        'aim_name_2019_11_28'
    )
class InvalidLegacyFlag(schema.ValidationError):
    __doc__ = 'Not a valid legacy flag. Must be one of: '
    first = True
    for flag in valid_legacy_flags:
        if first == False:
            __doc__ += ' | '
        __doc__ += flag
        first = False

def isValidLegacyFlag(value):
    if value not in valid_legacy_flags:
        raise InvalidLegacyFlag
    return True

def isValidLegacyFlagList(value):
    for flag in value:
        isValidLegacyFlag(flag)
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

class InvalidRoute53HealthCheckTypeError(schema.ValidationError):
    __doc__ = 'Route53 health check type must be one of HTTP, HTTPS or TCP.'

def isValidRoute53HealthCheckType(value):
    if value not in ('HTTP', 'HTTPS', 'TCP'):
        raise InvalidRoute53HealthCheckTypeError
    return True

class InvalidRoute53RecordSetTypeError(schema.ValidationError):
    __doc__ = 'Route53 RecordSet "type" be one of: A | MX | CNAME | Alias | SRV | TXT | NS | SOA'

def isValidRoute53RecordSetType(value):
    if value not in ('A', 'MX', 'CNAME', 'Alias', 'SRV', 'TXT', 'NS', 'SOA'):
        raise InvalidRoute53RecordSetTypeError
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

class InvalidMissingDataValue(schema.ValidationError):
    __doc__ = 'treat_missing_data must be one of: breaching, notBreaching, ignore or missing'

def isMissingDataValue(value):
    if value not in ('breaching', 'notBreaching', 'ignore', 'missing'):
        raise InvalidMissingDataValue
    return True

class InvalidAlarmStatistic(schema.ValidationError):
    __doc__ = 'statistic must be one of: Average, Maximum, Minimum, SampleCount or Sum.'

def isValidAlarmStatisticValue(value):
    if value not in ('Average', 'Maximum', 'Minimum', 'SampleCount', 'Sum'):
        raise InvalidAlarmStatistic
    return True

class InvalidExtendedStatisticValue(schema.ValidationError):
    __doc__ = '`extended_statistic` must match pattern p(\d{1,2}(\.\d{0,2})?|100). Examlpes: p95, p0.0, p98.59, p100'

def isValidExtendedStatisticValue(value):
    if re.match('^p\d{1,2}((\.\d{0,2})?|100)$', value):
        return True
    else:
        raise InvalidExtendedStatisticValue

class InvalidEvaluateLowSampleCountPercentileValue(schema.ValidationError):
    __doc__ = 'evaluate_low_sample_count_percentile must be one of: evaluate or ignore.'

def isValidEvaluateLowSampleCountPercentileValue(value):
    if value not in ('evaluate', 'ignore'):
        raise InvalidEvaluateLowSampleCountPercentileValue
    return True

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
        raise InvalidCFProtocolPolicy
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
class InvalidPacoCodeCommitPermissionPolicy(schema.ValidationError):
    __doc__ = 'permission must be one of: ReadWrite | ReadOnly'

def isPacoCodeCommitPermissionPolicyValid(value):
    if value not in ('ReadWrite', 'ReadOnly'):
        raise InvalidPacoCodeCommitPermissionPolicy
    return True

# CodeBuild
class InvalidCodeBuildComputeType(schema.ValidationError):
    __doc__ = 'codebuild_compute_type must be one of: BUILD_GENERAL1_SMALL | BUILD_GENERAL1_MEDIUM | BUILD_GENERAL1_LARGE'

def isValidCodeBuildComputeType(value):
    if value not in ('BUILD_GENERAL1_SMALL', 'BUILD_GENERAL1_MEDIUM', 'BUILD_GENERAL1_LARGE'):
        raise InvalidCodeBuildComputeType
    return True

# ASG Scaling Policy Type
class InvalidASGScalignPolicyType(schema.ValidationError):
    __doc__ = 'policy_type must be one of: SimpleScaling | StepScaling | TargetTrackingScaling'

def IsValidASGScalignPolicyType(value):
    if value not in ('SimpleScaling', 'StepScaling', 'TargetTrackingScaling'):
        raise InvalidASGScalignPolicyType
    return True

# ASG Scaling Policy Adjustment Type
class InvalidASGScalingPolicyAdjustmentType(schema.ValidationError):
    __doc__ = 'policy_type must be one of: ChangeInCapacity | ExactCapacity | PercentChangeInCapacity'

def IsValidASGScalingPolicyAdjustmentType(value):
    if value not in ('ChangeInCapacity', 'ExactCapacity', 'PercentChangeInCapacity'):
        raise InvalidASGScalingPolicyAdjustmentType
    return True

# ASG Scaling Policy Adjustment Type
class InvalidASGLifecycleTransition(schema.ValidationError):
    __doc__ = 'lifecycle_transition must be one of: autoscaling:EC2_INSTANCE_LAUNCHING | autoscaling:EC2_INSTANCE_TERMINATING'

def IsValidASGLifecycleTransition(value):
    if value not in ('autoscaling:EC2_INSTANCE_LAUNCHING', 'autoscaling:EC2_INSTANCE_TERMINATING'):
        raise InvalidASGLifecycleTransition
    return True

# ASG Scaling Policy Adjustment Type
class InvalidASGLifecycleDefaultResult(schema.ValidationError):
    __doc__ = 'default_result must be one of: CONTINUE | ABANDON'

def IsValidASGLifecycleDefaultResult(value):
    if value not in ('CONTINUE', 'ABANDON'):
        raise InvalidASGLifecycleTransition
    return True

# ASG AvailabilityZones
class InvalidASGAvailabilityZone(schema.ValidationError):
    __doc__ = 'availability_zone must be one of: all | 1 | 2 | 3 | 4 | ...'

def IsValidASGAvailabilityZone(value):
    if value == 'all':
        return True
    if value.isnumeric() == False:
        raise InvalidASGAvailabilityZone
    if int(value) < 0 or int(value) > 10:
        raise InvalidASGAvailabilityZone
    return True


# Lambda Environment variables
class InvalidLambdaEnvironmentVariable(schema.ValidationError):
    __doc__ = 'Can not be a reserved Environment Variable name and must be alphanumeric or _ character only.'

RESERVED_ENVIRONMENT_VARIABLES = [
    'AWS_ACCESS_KEY',
    'AWS_ACCESS_KEY_ID',
    'AWS_DEFAULT_REGION',
    'AWS_EXECUTION_ENV',
    'AWS_LAMBDA_FUNCTION_MEMORY_SIZE',
    'AWS_LAMBDA_FUNCTION_NAME',
    'AWS_LAMBDA_FUNCTION_VERSION',
    'AWS_LAMBDA_LOG_GROUP_NAME',
    'AWS_LAMBDA_LOG_STREAM_NAME',
    'AWS_REGION',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_SECRET_KEY',
    'AWS_SECURITY_TOKEN',
    'AWS_SESSION_TOKEN',
    'LAMBDA_RUNTIME_DIR',
    'LAMBDA_TASK_ROOT',
    'TZ'
]
ENVIRONMENT_VARIABLES_NAME_PATTERN = r'[a-zA-Z][a-zA-Z0-9_]+'

def isValidLambdaVariableName(value):
    # this can be uninitialized
    if value == '':
        return True
    if value in RESERVED_ENVIRONMENT_VARIABLES:
        raise InvalidLambdaEnvironmentVariable("Reserved name: {}".format(value))
    elif not re.match(ENVIRONMENT_VARIABLES_NAME_PATTERN, value):
        raise InvalidLambdaEnvironmentVariable("Invalid characters in name: %s" % value)
    return True

class InvalidBranchEnvMappings(schema.ValidationError):
    __doc__ = 'Branch to environment mappings must be in the form <branch-name>:<environment-name>.'

def isValidBranchEnvMappings(value):
    for mapping in value:
        if len(mapping.split(':')) != 2:
            raise InvalidBranchEnvMappings("Could not map from branch to env for '{}'.".format(mapping))
    return True

# EBS Volume Type
class InvalidEBSVolumeType(schema.ValidationError):
    __doc__ = 'volume_type must be one of: gp2 | io1 | sc1 | st1 | standard'

def isValidEBSVolumeType(value):
    if value not in ('gp2', 'io1', 'sc1', 'st1', 'standard'):
        raise InvalidEBSVolumeType
    return True

# NAT Gateway
class InvalidNATGatewayType(schema.ValidationError):
    __doc__ = 'NATGateay type must be one of: Managed | EC2'

def IsValidNATGatewayType(value):
    if value not in ['Managed', 'EC2']:
        raise InvalidNATGatewayType
    return True

# ----------------------------------------------------------------------------
# Here be Schemas!
#
class IDNSEnablable(Interface):
    """Provides a parent with an inheritable DNS enabled field"""
    dns_enabled = schema.Bool(
        title='Boolean indicating whether DNS record sets will be created.',
        default=True,
        required=False,
    )

class CommaList(schema.List):
    """Comma separated list of valeus"""

    def constraint(self, value):
        """
        Validate something
        """
        return True
        # ToDo: how to get the PACO_HOME and change to that directory from here?
        #path = pathlib.Path(value)
        #return path.exists()

class IParent(Interface):
    """
An object in the Paco project model tree with a reference to a parent object.
    """
    __parent__ = Attribute("Object reference to the parent in the object hierarchy")

class ITitle(Interface):
    """
A title is a human-readable name. It can be as long as you want, and can change without
breaking any configuration.
    """
    title=schema.TextLine(
        title="Title",
        default="",
        required=False,
    )

class INamed(IParent, ITitle):
    """
A name given to a cloud resource. Names identify resources and changing them
can break configuration.
"""
    name = schema.TextLine(
        title="Name",
        default="",
        required=False,
    )

# IEnablable is the same as IDeployable except it defaults to True
class IEnablable(Interface):
    """
Indicate if this configuration should be enabled.
    """
    enabled = schema.Bool(
        title="Enabled",
        description="",
        default=True,
        required=False,
    )

class IDeployable(Interface):
    """
Indicates if this configuration tree should be enabled or not.
    """
    enabled = schema.Bool(
        title="Enabled",
        description="Could be deployed to AWS",
        default=False,
        required=False,
    )

class IName(Interface):
    """
A name that can be changed or duplicated with other similar cloud resources without breaking anything.
    """
    name = schema.TextLine(
        title="Name",
        default="",
        required=False,
    )

class IFunction(Interface):
    """
A callable function that returns a value.
    """

class IFileReference(Interface):
    pass

class IStringFileReference(IFileReference):
    pass

class IYAMLFileReference(IFileReference):
    pass

class IPacoReference(Interface):
    """A field containing a reference an paco model object or attribute"""
    pass

class ILocalPath(Interface):
    """Path to a directory or file on the local filesystem"""

class LocalPath(schema.TextLine):
    pass

# work around circular imports for references
classImplements(LocalPath, ILocalPath)
classImplements(PacoReference, IPacoReference)
classImplements(FileReference, IFileReference)
classImplements(StringFileReference, IStringFileReference)
classImplements(YAMLFileReference, IYAMLFileReference)


class INameValuePair(IParent):
    """A Name/Value pair to use for RDS Option Group configuration"""
    name = schema.TextLine(
        title="Name",
        required=True,
    )
    value = PacoReference(
        title="Value",
        required=True,
        str_ok=True,
        schema_constraint='Interface'
    )

class IAdminIAMUser(IDeployable):
    """An AWS Account Administerator IAM User"""
    username = schema.TextLine(
        title="IAM Username",
        default="",
        required=False,
    )

class IAccounts(IMapping):
    "Collection of Accounts"
    pass

class IAccount(INamed, IDeployable):
    """
Cloud accounts.

The specially named `master.yaml` file is for the AWS Master account. It is the only account
which can have the field `organization_account_ids` which is used to define and create the
child accounts.

.. code-block:: yaml
    :caption: Example accounts/master.yaml account file

    name: Master
    title: Master AWS Account
    is_master: true
    account_type: AWS
    account_id: '123456789012'
    region: us-west-2
    organization_account_ids:
      - prod
      - tools
      - dev
    root_email: master@example.com

.. code-block:: yaml
    :caption: Example accounts/dev.yaml account file

    name: Development
    title: Development AWS Account
    account_type: AWS
    account_id: '123456789012'
    region: us-west-2
    root_email: dev@example.com

"""
    account_type = schema.TextLine(
        title="Account Type",
        description="Supported types: 'AWS'",
        default="AWS",
        required=False,
    )
    account_id = schema.TextLine(
        title="Account ID",
        description="Can only contain digits.",
        required=False,
        constraint = isOnlyDigits
    )
    admin_delegate_role_name = schema.TextLine(
        title="Administrator delegate IAM Role name for the account",
        description="",
        default="Paco-Organization-Account-Delegate-Role",
        required=False,
    )
    is_master = schema.Bool(
        title="Boolean indicating if this a Master account",
        default=False,
        required=False,
    )
    region = schema.TextLine(
        title="Region to install AWS Account specific resources",
        default="no-region-set",
        missing_value = "no-region-set",
        required=True,
        description='Must be a valid AWS Region name',
        constraint = isValidAWSRegionName
    )
    root_email = schema.TextLine(
        title="The email address for the root user of this account",
        required=True,
        description='Must be a valid email address.',
        constraint = isValidEmail
    )
    organization_account_ids = schema.List(
        title="A list of account ids to add to the Master account's AWS Organization",
        value_type=schema.TextLine(),
        required=False,
        description='Each string in the list must contain only digits.'
    )
    admin_iam_users = schema.Dict(
        title="Admin IAM Users",
        value_type=schema.Object(IAdminIAMUser),
        required=False,
    )

class ISecurityGroupRule(IName):
    cidr_ip = schema.TextLine(
        title="CIDR IP",
        default="",
        description="A valid CIDR v4 block or an empty string",
        constraint = isValidCidrIpv4orBlank,
        required=False,
    )
    cidr_ip_v6 = schema.TextLine(
        title="CIDR IP v6",
        description="A valid CIDR v6 block or an empty string",
        default="",
        required=False,
    )
    description=schema.TextLine(
        title="Description",
        default="",
        description="Max 255 characters. Allowed characters are a-z, A-Z, 0-9, spaces, and ._-:/()#,@[]+=;{}!$*.",
        required=False,
    )
    from_port = schema.Int(
        title="From port",
        description="A value of -1 indicates all ICMP/ICMPv6 types. If you specify all ICMP/ICMPv6 types, you must specify all codes.",
        default=-1,
        required=False
    )
    protocol = schema.TextLine(
        title="IP Protocol",
        description="The IP protocol name (tcp, udp, icmp, icmpv6) or number.",
        required=False,
    )
    to_port = schema.Int(
        title="To port",
        description="A value of -1 indicates all ICMP/ICMPv6 types. If you specify all ICMP/ICMPv6 types, you must specify all codes.",
        default=-1,
        required=False
    )
    port = schema.Int(
        title="Port",
        description="A value of -1 indicates all ICMP/ICMPv6 types. If you specify all ICMP/ICMPv6 types, you must specify all codes.",
        default=-1,
        required=False
    )

    @invariant
    def to_from_or_port(obj):
        if obj.port != -1 and (obj.to_port != -1 or obj.from_port != -1):
            raise Invalid("Both 'port' and 'to_port/from_port' must not have values.")
        elif obj.to_port == -1 and obj.from_port != -1:
            raise Invalid("The 'from_port' field must not be blank when 'to_port' has a value.")
        elif obj.from_port == -1 and obj.to_port != -1:
            raise Invalid("The 'to_port' field must not be blank when 'from_port' has a value.")

class IIngressRule(IParent, ISecurityGroupRule):
    "Security group ingress"
    source_security_group = PacoReference(
        title="Source Security Group Reference",
        required=False,
        description="A Paco Reference to a SecurityGroup",
        str_ok=True,
        schema_constraint='ISecurityGroup'
    )

class IEgressRule(IParent, ISecurityGroupRule):
    "Security group egress"
    destination_security_group = PacoReference(
        title="Destination Security Group Reference",
        required=False,
        description="A Paco reference to a SecurityGroup",
        str_ok=True,
        schema_constraint='ISecurityGroup'
    )

class ISecurityGroup(INamed, IDeployable):
    """
AWS Resource: Security Group
    """
    group_name = schema.TextLine(
        title="Group name",
        default="",
        description="Up to 255 characters in length. Cannot start with sg-.",
        required=False,
    )
    group_description=schema.TextLine(
        title="Group description",
        default="",
        description="Up to 255 characters in length",
        required=False,
    )
    ingress = schema.List(
        title="Ingress",
        value_type=schema.Object(schema=IIngressRule),
        description="Every list item must be an IngressRule",
        required=False,
    )
    egress = schema.List(
        title="Egress",
        value_type=schema.Object(schema=IEgressRule),
        description="Every list item must be an EgressRule",
        required=False,
    )

class IApplicationEngines(INamed, IMapping):
    "A container for Application Engines"
    taggedValue('contains', 'IApplicationEngine')

class IType(Interface):
    type = schema.TextLine(
        title="Type of Resources",
        description="A valid AWS Resource type: ASG, LBApplication, etc.",
        required=False,
    )

class IResource(IType, INamed, IDeployable, IDNSEnablable):
    """Configuration for a cloud resource.
Resources may represent a single physical resource in the cloud,
or several closely related resources.
    """
    order = schema.Int(
        title="The order in which the resource will be deployed",
        description="",
        min=0,
        default=0,
        required=False,
    )
    change_protected = schema.Bool(
        title="Boolean indicating whether this resource can be modified or not.",
        default=False,
        required=False,
    )

class IApplicationResource(IResource):
    """A resource which supports a specific application."""


class IServices(INamed, IMapping):
    """
Services
    """
    taggedValue('contains', 'IService')


class IAccountRef(Interface):
    "An account and region for a service"
    account = PacoReference(
        title="Account Reference",
        required=False,
        schema_constraint=IAccount
    )

class IServiceEnvironment(IAccountRef, INamed):
    "A service composed of one or more applications"
    applications = schema.Object(
        title="Applications",
        schema = IApplicationEngines,
        required=False,
    )
    region = schema.TextLine(
        title="Region",
        required=False,
        constraint = isValidAWSRegionName,
    )

class IGlobalResources(INamed, IMapping):
    "A container for global Resources"
    taggedValue('contains', 'mixed')

class IAccountRegions(IParent):
    """An Account and one or more Regions"""
    account = PacoReference(
        title="AWS Account",
        required=True,
        schema_constraint='IAccount'
    )
    regions = schema.List(
        title="Regions",
        required=True,
    )

class IResources(INamed, IMapping):
    "A container of Resources to support an `Application`_."
    taggedValue('contains', 'mixed')

class IResourceGroup(INamed, IDeployable, IDNSEnablable):
    "A group of `Resources`_ to support an `Application`_."
    title=schema.TextLine(
        title="Title",
        default="",
        required=False,
    )
    type = schema.TextLine(
        title="Type"
    )
    order = schema.Int(
        title="The order in which the group will be deployed",
        description="",
        min=0,
        required=True
    )
    resources = schema.Object(IResources)
    dns_enabled = schema.Bool(
        title="",
        required=False,
    )


class IResourceGroups(INamed, IMapping):
    "A container of Application `ResourceGroup`_ objects."
    taggedValue('contains', 'IResourceGroup')


# Alarm and notification schemas

class IAlarmNotifications(INamed, IMapping):
    """
Container for `AlarmNotification`_ objects.
    """
    taggedValue('contains', 'IAlarmNotification')

class IAlarmNotification(INamed):
    """
Alarm Notification
    """
    groups = schema.List(
        title="List of groups",
        value_type=schema.TextLine(
            title="Group"
        ),
        required=True
    )
    classification = schema.TextLine(
        title="Classification filter",
        description="Must be one of: 'performance', 'security', 'health' or ''.",
        constraint = isValidAlarmClassificationFilter,
        default='',
        required=False,
    )
    severity = schema.TextLine(
        title="Severity filter",
        constraint = isValidAlarmSeverityFilter,
        description="Must be one of: 'low', 'critical'",
        required=False,
    )

class INotifiable(Interface):
    """
A notifiable object
    """
    notifications = schema.Object(
        title="Alarm Notifications",
        schema = IAlarmNotifications,
        required=False,
    )

class IAlarmSet(INamed, IMapping, INotifiable):
    """
A container of Alarm objects.
    """
    taggedValue('contains', 'mixed')
    resource_type = schema.TextLine(
        title="Resource type",
        description="Must be a valid AWS resource type",
        required=False,
    )


class IAlarmSets(INamed, IMapping):
    """
Alarm Sets are defined in the file ``monitor/alarmsets.yaml``.

AlarmSets are named to match a Paco Resource type, then a unique AlarmSet name.


.. code-block:: yaml
    :caption: Structure of an alarmets.yaml file

    # AutoScalingGroup alarms
    ASG:
        launch-health:
            GroupPendingInstances-Low:
                # alarm config here ...
            GroupPendingInstances-Critical:
                # alarm config here ...

    # Application LoadBalancer alarms
    LBApplication:
        instance-health:
            HealthyHostCount-Critical:
                # alarm config here ...
        response-latency:
            TargetResponseTimeP95-Low:
                # alarm config here ...
            HTTPCode_Target_4XX_Count-Low:
                # alarm config here ...


The base `Alarm`_ schema contains fields to add additional metadata to alarms. For CloudWatchAlarms, this
metadata set in the AlarmDescription field as JSON:

Alarms can have different contexts, which increases the number of metadata that is populated in the AlarmDescription field:

 * Global context. Only has base context. e.g. a CloudTrail log alarm.

 * NetworkEnvironmnet context. Base and NetworkEnvironment context. e.g. a VPC flow log alarm.

 * Application context alarm. Base, NetworkEnvironment and Application contexts. e,g, an external HTTP health check alarm

 * Resource context alarm. Base, NetworkEnvironment, Application and Resource contexts. e.g. an AutoScalingGroup CPU alarm

.. code-block:: yaml

    Base context for all alarms
    ----------------------------

    "project_name": Project name
    "project_title": Project title
    "account_name": Account name
    "alarm_name": Alarm name
    "classification": Classification
    "severity": Severity
    "topic_arns": SNS Topic ARN subscriptions
    "description": Description (only if supplied)
    "runbook_url": Runbook URL (only if supplied)

    NetworkEnvironment context alarms
    ---------------------------------

    "netenv_name": NetworkEnvironment name
    "netenv_title": NetworkEnvironment title
    "env_name": Environment name
    "env_title": Environment title
    "envreg_name": EnvironmentRegion name
    "envreg_title": EnvironmentRegion title

    Application context alarms
    --------------------------

    "app_name": Application name
    "app_title": Application title

     Resource context alarms
     -----------------------

    "resource_group_name": Resource Group name
    "resource_group_title": Resource Group title
    "resource_name": Resource name
    "resource_title": Resource title

Alarms can be set in the ``monitoring:`` field for `Application`_ and `Resource`_ objects. The name of
each `AlarmSet` should be listed in the ``alarm_sets:`` field. It is possible to override the individual fields of
an Alarm in a netenv file.

.. code-block:: yaml
    :caption: Examples of adding AlarmSets to Environmnets

    environments:
      prod:
        title: "Production"
        default:
          enabled: true
          applications:
            app:
              monitoring:
                enabled: true
                alarm_sets:
                  special-app-alarms:
              groups:
                site:
                  resources:
                    alb:
                      monitoring:
                        enabled: true
                        alarm_sets:
                          core:
                          performance:
                            # Override the SlowTargetResponseTime Alarm threshold field
                            SlowTargetResponseTime:
                              threshold: 2.0

Stylistically, ``monitoring`` and ``alarm_sets`` can be specified in the base ``applications:`` section in a netenv file,
and set to ``enabled: false``. Then only the production environment can override the enabled field to true. This makes it
easy to enable a dev or test environment if you want to test alarms before using in a production environment.

Alternatively, you may wish to only specify the monitoring in the ``environments:`` section of your netenv file only
for production, and keep the base ``applications:`` configuration shorter.


Alarm notifications tell alarms which SNS Topics to notify. Alarm notifications are set with the ``notifications:`` field
at the `Application`_, `Resource`_, `AlarmSet`_ and `Alarm`_ level.

.. code-block:: yaml
    :caption: Examples of Alarm notifications

    applications:
      app:
        enabled: true
        # Application level notifications
        notifications:
          ops_team:
            groups:
            - cloud_ops
        groups:
          site:
            resources:
              web:
                monitoring:
                  # Resource level notifications
                  notifications:
                    web_team:
                      groups:
                      - web
                  alarm_sets:
                    instance-health-cwagent:
                      notifications:
                        # AlarmSet notifications
                        alarmsetnotif:
                          groups:
                          - misterteam
                      SwapPercent-Low:
                        # Alarm level notifications
                        notifications:
                          singlealarm:
                            groups:
                            - oneguygetsthis

Notifications can be filtered for specific ``severity`` and ``classification`` levels. This allows you to direct
critical severity to one group and low severity to another, or to send only performance classification alarms to one
group and security classification alarms to another.

.. code-block:: yaml
    :caption: Examples of severity and classification filters

    notifications:
      severe_security:
        groups:
        - security_group
        severity: 'critical'
        classification: 'security'

Note that although you can configure multiple SNS Topics to subscribe to a single alarm, CloudWatch has a maximum
limit of five SNS Topics that a given alarm may be subscribed to.

It is also possible to write a Paco add-on that overrides the default CloudWatch notifications and instead notifies
a single SNS Topic. This is intended to allow you to write an add-on that directs all alarms through a single Lambda
(regardless or account or region) which is then responsible for delivering or taking action on alarms.

Currently Global and NetworkEnvironment alarms are only supported through Paco add-ons.


.. code-block:: yaml
    :caption: Example alarmsets.yaml for Application, ALB, ASG, RDSMySQL and LogAlarms

    App:
      special-app-alarms:
        CustomMetric:
          description: "Custom metric has been triggered."
          classification: health
          severity: low
          metric_name: "custom_metric"
          period: 86400 # 1 day
          evaluation_periods: 1
          threshold: 1
          comparison_operator: LessThanThreshold
          statistic: Average
          treat_missing_data: breaching
          namespace: 'CustomMetric'

    LBApplication:
      core:
        HealthyHostCount-Critical:
          classification: health
          severity: critical
          description: "Alert if fewer than X number of backend hosts are passing health checks"
          metric_name: "HealthyHostCount"
          dimensions:
            - name: LoadBalancer
              value: paco.ref netenv.wa.applications.ap.groups.site.resources.alb.fullname
            - name: TargetGroup
              value: paco.ref netenv.wa.applications.ap.groups.site.resources.alb.target_groups.ap.fullname
          period: 60
          evaluation_periods: 5
          statistic: Minimum
          threshold: 1
          comparison_operator: LessThanThreshold
          treat_missing_data: breaching
      performance:
        SlowTargetResponseTime:
          severity: low
          classification: performance
          description: "Average HTTP response time is unusually slow"
          metric_name: "TargetResponseTime"
          period: 60
          evaluation_periods: 5
          statistic: Average
          threshold: 1.5
          comparison_operator: GreaterThanOrEqualToThreshold
          treat_missing_data: missing
          dimensions:
            - name: LoadBalancer
              value: paco.ref netenv.wa.applications.ap.groups.site.resources.alb.fullname
            - name: TargetGroup
              value: paco.ref netenv.wa.applications.ap.groups.site.resources.alb.target_groups.ap.fullname
        HTTPCode4XXCount:
          classification: performance
          severity: low
          description: "Large number of 4xx HTTP error codes"
          metric_name: "HTTPCode_Target_4XX_Count"
          period: 60
          evaluation_periods: 5
          statistic: Sum
          threshold: 100
          comparison_operator: GreaterThanOrEqualToThreshold
          treat_missing_data: notBreaching
        HTTPCode5XXCount:
          classification: performance
          severity: low
          description: "Large number of 5xx HTTP error codes"
          metric_name: "HTTPCode_Target_5XX_Count"
          period: 60
          evaluation_periods: 5
          statistic: Sum
          threshold: 100
          comparison_operator: GreaterThanOrEqualToThreshold
          treat_missing_data: notBreaching

    ASG:
      core:
        StatusCheck:
          classification: health
          severity: critical
          metric_name: "StatusCheckFailed"
          namespace: AWS/EC2
          period: 60
          evaluation_periods: 5
          statistic: Maximum
          threshold: 0
          comparison_operator: GreaterThanThreshold
          treat_missing_data: breaching
        CPUTotal:
          classification: performance
          severity: critical
          metric_name: "CPUUtilization"
          namespace: AWS/EC2
          period: 60
          evaluation_periods: 30
          threshold: 90
          statistic: Average
          treat_missing_data: breaching
          comparison_operator: GreaterThanThreshold
      cwagent:
        SwapPercentLow:
          classification: performance
          severity: low
          metric_name: "swap_used_percent"
          namespace: "CWAgent"
          period: 60
          evaluation_periods: 5
          statistic: Maximum
          threshold: 80
          comparison_operator: GreaterThanThreshold
          treat_missing_data: breaching
        DiskSpaceLow:
          classification: health
          severity: low
          metric_name: "disk_used_percent"
          namespace: "CWAgent"
          period: 300
          evaluation_periods: 1
          statistic: Minimum
          threshold: 60
          comparison_operator: GreaterThanThreshold
          treat_missing_data: breaching
        DiskSpaceCritical:
          classification: health
          severity: low
          metric_name: "disk_used_percent"
          namespace: "CWAgent"
          period: 300
          evaluation_periods: 1
          statistic: Minimum
          threshold: 80
          comparison_operator: GreaterThanThreshold
          treat_missing_data: breaching

      # CloudWatch Log Alarms
      log-alarms:
        CfnInitError:
          type: LogAlarm
          description: "CloudFormation Init Errors"
          classification: health
          severity: critical
          log_set_name: 'cloud'
          log_group_name: 'cfn_init'
          metric_name: "CfnInitErrorMetric"
          period: 300
          evaluation_periods: 1
          threshold: 1.0
          treat_missing_data: notBreaching
          comparison_operator: GreaterThanOrEqualToThreshold
          statistic: Sum
        CodeDeployError:
          type: LogAlarm
          description: "CodeDeploy Errors"
          classification: health
          severity: critical
          log_set_name: 'cloud'
          log_group_name: 'codedeploy'
          metric_name: "CodeDeployErrorMetric"
          period: 300
          evaluation_periods: 1
          threshold: 1.0
          treat_missing_data: notBreaching
          comparison_operator: GreaterThanOrEqualToThreshold
          statistic: Sum
        WsgiError:
          type: LogAlarm
          description: "HTTP WSGI Errors"
          classification: health
          severity: critical
          log_set_name: 'ap'
          log_group_name: 'httpd_error'
          metric_name: "WsgiErrorMetric"
          period: 300
          evaluation_periods: 1
          threshold: 1.0
          treat_missing_data: notBreaching
          comparison_operator: GreaterThanOrEqualToThreshold
          statistic: Sum
        HighHTTPTraffic:
          type: LogAlarm
          description: "High number of http access logs"
          classification: performance
          severity: low
          log_set_name: 'ap'
          log_group_name: 'httpd_access'
          metric_name: "HttpdLogCountMetric"
          period: 300
          evaluation_periods: 1
          threshold: 1000
          treat_missing_data: ignore
          comparison_operator: GreaterThanOrEqualToThreshold
          statistic: Sum

    RDSMysql:
      basic-database:
        CPUTotal-Low:
          classification: performance
          severity: low
          metric_name: "CPUUtilization"
          namespace: AWS/RDS
          period: 300
          evaluation_periods: 6
          threshold: 90
          comparison_operator: GreaterThanOrEqualToThreshold
          statistic: Average
          treat_missing_data: breaching

        FreeableMemoryAlarm:
          classification: performance
          severity: low
          metric_name: "FreeableMemory"
          namespace: AWS/RDS
          period: 300
          evaluation_periods: 1
          threshold: 100000000
          comparison_operator: LessThanOrEqualToThreshold
          statistic: Minimum
          treat_missing_data: breaching

        FreeStorageSpaceAlarm:
          classification: performance
          severity: low
          metric_name: "FreeStorageSpace"
          namespace: AWS/RDS
          period: 300
          evaluation_periods: 1
          threshold: 5000000000
          comparison_operator: LessThanOrEqualToThreshold
          statistic: Minimum
          treat_missing_data: breaching


    """
    taggedValue('contains', 'IAlarmSet')


class IDimension(IParent):
    """
A dimension of a metric
    """
    name = schema.TextLine(
        title="Dimension name",
        required=False,
    )
    value = PacoReference(
        title="String or a Paco Reference to resource output.",
        required=False,
        str_ok=True,
        schema_constraint='Interface'
    )

class IAlarm(INamed, IDeployable, IName, INotifiable):
    """
A Paco Alarm.

This is a base schema which defines metadata useful to categorize an alarm.
    """
    classification = schema.TextLine(
        title="Classification",
        description="Must be one of: 'performance', 'security' or 'health'",
        constraint = isValidAlarmClassification,
        required=True,
        default='unset',
        missing_value = 'unset',
    )
    description=schema.TextLine(
        title="Description",
        required=False,
    )
    notification_groups = schema.List(
        readonly = True,
        title="List of notification groups the alarm is subscribed to.",
        value_type=schema.TextLine(title="Notification group name"),
        required=False,
    )
    runbook_url = schema.TextLine(
        title="Runbook URL",
        required=False,
    )
    severity = schema.TextLine(
        title="Severity",
        default="low",
        constraint = isValidAlarmSeverity,
        description="Must be one of: 'low', 'critical'",
        required=False,
    )

class ICloudWatchAlarm(IType, IAlarm):
    """
A CloudWatch Alarm
    """
    @invariant
    def evaluate_low_sample_statistic(obj):
        if getattr(obj, 'evaluate_low_sample_count_percentile', None):
            if getattr(obj, 'statistic', None):
                raise Invalid('Field `evaluate_low_sample_count_percentile` can not be used with the `statistic` field, only with the `extended_statistic` field.')
            if not getattr(obj, 'extended_statistic', None):
                raise Invalid('Field `evaluate_low_sample_count_percentile` requires field `extended_statistic` to be a valid percentile value.')

    @invariant
    def check_statistic(obj):
        "Must be one of ExtendedStatistic, Metrics or Statistic"
        # ToDo: implement Metrics
        if not getattr(obj, 'statistic', None) and not getattr(obj, 'extended_statistic', None):
            raise Invalid('Must include one of `statistic` or `extended_statistic`.')

    alarm_actions = schema.List(
        title="Alarm Actions",
        readonly = True,
        value_type=schema.TextLine(
            title="Alarm Action",
            required=False,
        ),
        required=False,
    )
    alarm_description=schema.Text(
        title="Alarm Description",
        readonly = True,
        description="Valid JSON document with Paco fields.",
        required=False,
    )
    actions_enabled = schema.Bool(
        title="Actions Enabled",
        readonly = True,
        required=False,
    )
    comparison_operator = schema.TextLine(
        title="Comparison operator",
        constraint = isComparisonOperator,
        description="Must be one of: 'GreaterThanThreshold','GreaterThanOrEqualToThreshold', 'LessThanThreshold', 'LessThanOrEqualToThreshold'",
        required=False,
    )
    dimensions = schema.List(
        title="Dimensions",
        value_type=schema.Object(schema=IDimension),
        required=False,
    )
    enable_ok_actions = schema.Bool(
        title="Enable Actions when alarm transitions to the OK state.",
        default=False,
        required=False,
    )
    enable_insufficient_data_actions = schema.Bool(
        title="Enable Actions when alarm transitions to the INSUFFICIENT_DATA state.",
        default=False,
        required=False,
    )
    evaluate_low_sample_count_percentile = schema.TextLine(
        title="Evaluate low sample count percentile",
        description="Must be one of `evaluate` or `ignore`.",
        required=False,
        constraint = isValidEvaluateLowSampleCountPercentileValue,
    )
    evaluation_periods = schema.Int(
        title="Evaluation periods",
        min=1,
        required=False,
    )
    extended_statistic = schema.TextLine(
        title="Extended statistic",
        description="A value between p0.0 and p100.",
        required=False,
        constraint = isValidExtendedStatisticValue,
    )
    # ToDo: implement Metrics - also update invariant
    # metrics = schema.List()
    metric_name = schema.TextLine(
        title="Metric name",
        required=True,
    )
    namespace = schema.TextLine(
        title="Namespace",
        required=False,
    )
    period = schema.Int(
        title="Period in seconds",
        required=False,
        min=1,
    )
    statistic = schema.TextLine(
        title="Statistic",
        required=False,
        description="Must be one of `Maximum`, `SampleCount`, `Sum`, `Minimum`, `Average`.",
        constraint = isValidAlarmStatisticValue,
    )
    threshold = schema.Float(
        title="Threshold",
        required=False,
    )
    treat_missing_data = schema.TextLine(
        title="Treat missing data",
        description="Must be one of `breaching`, `notBreaching`, `ignore` or `missing`.",
        required=False,
        constraint = isMissingDataValue,
    )

class ICloudWatchLogAlarm(ICloudWatchAlarm):
    log_set_name = schema.TextLine(
        title="Log Set Name",
        required=True
    )
    log_group_name = schema.TextLine(
        title="Log Group Name",
        required=True
    )

# New-style sns.yaml support

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
        title="Notification protocol",
        default="email",
        description="Must be a valid SNS Topic subscription protocol: 'http', 'https', 'email', 'email-json', 'sms', 'sqs', 'application', 'lambda'.",
        constraint = isValidSNSSubscriptionProtocol,
        required=False,
    )
    endpoint = PacoReference(
        title="SNS Topic ARN or Paco Reference",
        str_ok=True,
        required=False,
        schema_constraint='ISNSTopic'
    )
    filter_policy = schema.TextLine(
        title="Filter Policy",
        description="Must be valid JSON",
        constraint=isValidJSONOrNone,
        required=False,
    )

class ISNSTopic(IEnablable, IResource):
    """
Simple Notification Service (SNS) Topic resource.

.. sidebar:: Prescribed Automation

    ``cross_account_access``: Creates an SNS Topic Policy which will grant all of the AWS Accounts in this
    Paco Project access to the ``sns.Publish`` permission for this SNS Topic.

.. code-block:: yaml
    :caption: Example SNSTopic resource YAML

    type: SNSTopic
    order: 1
    enabled: true
    display_name: "Waterbear Cloud AWS"
    cross_account_access: true
    subscriptions:
      - endpoint: http://example.com/yes
        protocol: http
      - endpoint: https://example.com/orno
        protocol: https
      - endpoint: bob@example.com
        protocol: email
      - endpoint: bob@example.com
        protocol: email-json
        filter_policy: '{"State": [ { "anything-but": "COMPLETED" } ] }'
      - endpoint: '555-555-5555'
        protocol: sms
      - endpoint: arn:aws:sqs:us-east-2:444455556666:queue1
        protocol: sqs
      - endpoint: arn:aws:sqs:us-east-2:444455556666:queue1
        protocol: application
      - endpoint: arn:aws:lambda:us-east-1:123456789012:function:my-function
        protocol: lambda

"""
    display_name = schema.TextLine(
        title="Display name for SMS Messages",
        required=False,
    )
    locations = schema.List(
        title="Locations",
        description="Only applies to a global SNS Topic",
        value_type=schema.Object(IAccountRegions),
        default=[],
        required=False,
    )
    subscriptions = schema.List(
        title="List of SNS Topic Subscriptions",
        value_type=schema.Object(ISNSTopicSubscription),
        required=False,
    )
    cross_account_access = schema.Bool(
        title="Cross-account access from all other accounts in this project.",
        description="",
        required=False,
        default=False,
    )

class ITopics(INamed, IMapping):
    """
Container for `SNSTopic`_ objects.
    """
    taggedValue('contains', 'ISNSTopic')

class ISNS(INamed, IMapping):
    """
AWS Simple Notification Systems (SNS)
    """
    default_locations = schema.List(
        title="Locations",
        value_type=schema.Object(IAccountRegions),
        default=[],
        required=False,
    )
    topics = schema.Object(
        title="SNS Topics",
        schema=ITopics,
        required=False,
    )

# Legacy snstopics.yaml support

class ISNSTopics(IAccountRef):
    "Container for SNS Topics"
    regions = schema.List(
        title="Regions to provision the Notification Groups in. Special list of ['ALL'] will select all of the project's active regions.",
        required=False,
        default=['ALL'],
        constraint=isValidAWSRegionOrAllList
    )

class IDashboardVariables(INamed, IMapping):
    """
Variables to make available to the dashboard JSON for interpolation.
    """
    taggedValue('contains', 'mixed')

class ICloudWatchDashboard(IResource):
    dashboard_file = StringFileReference(
        title="File path to a JSON templated dashboard.",
        required=True,
        constraint=isValidJSONOrNone
    )
    variables = schema.Dict(
        title="Dashboard Variables",
        default={},
        required=False
    )

# Logging schemas

class ICloudWatchLogRetention(Interface):
    expire_events_after_days = schema.TextLine(
        title="Expire Events After. Retention period of logs in this group",
        description="",
        default="",
        constraint = isValidCloudWatchLogRetention,
        required=False,
    )

class ICloudWatchLogSources(INamed, IMapping):
    """
A container of `CloudWatchLogSource`_ objects.
    """
    taggedValue('contains', 'ICloudWatchLogSource')

class ICloudWatchLogSource(INamed, ICloudWatchLogRetention):
    """
Log source for a CloudWatch agent.
    """
    encoding = schema.TextLine(
        title="Encoding",
        default="utf-8",
        required=False,
    )
    log_stream_name = schema.TextLine(
        title="Log stream name",
        description="CloudWatch Log Stream name",
        required=True,
        min_length=1
    )
    multi_line_start_pattern = schema.Text(
        title="Multi-line start pattern",
        default="",
        required=False,
    )
    path = schema.TextLine(
        title="Path",
        default="",
        required=True,
        description="Must be a valid filesystem path expression. Wildcard * is allowed."
    )
    timestamp_format = schema.TextLine(
        title="Timestamp format",
        default="",
        required=False,
    )
    timezone = schema.TextLine(
        title="Timezone",
        default="Local",
        constraint = isValidCWAgentTimezone,
        description="Must be one of: 'Local', 'UTC'",
        required=False,
    )

class IMetricTransformation(Interface):
    """
Metric Transformation
    """
    default_value = schema.Float(
        title="The value to emit when a filter pattern does not match a log event.",
        required=False,
    )
    metric_name = schema.TextLine(
        title="The name of the CloudWatch Metric.",
        required=True,
    )
    metric_namespace = schema.TextLine(
        title="The namespace of the CloudWatch metric. If not set, the namespace used will be 'AIM/{log-group-name}'.",
        required=False,
        max_length = 255,
    )
    metric_value = schema.TextLine(
        title="The value that is published to the CloudWatch metric.",
        required=True,
    )

class IMetricFilters(INamed, IMapping):
    """
Container for `Metric`Filter` objects.
    """
    taggedValue('contains', 'IMetricFilter')

class IMetricFilter(INamed):
    """
    Metric filter
    """
    filter_pattern = schema.Text(
        title="Filter pattern",
        default="",
        required=False,
    )
    metric_transformations = schema.List(
        title="Metric transformations",
        value_type=schema.Object(
            title="Metric Transformation",
            schema=IMetricTransformation
        ),
        required=False,
    )

class ICloudWatchLogGroups(INamed, IMapping):
    """
Container for `CloudWatchLogGroup`_ objects.
    """
    taggedValue('contains', 'ICloudWatchLogGroup')


class ICloudWatchLogGroup(INamed, ICloudWatchLogRetention):
    """
A CloudWatchLogGroup is responsible for retention, access control and metric filters
    """
    metric_filters = schema.Object(
        title="Metric Filters",
        schema = IMetricFilters,
        required=False,
    )
    sources = schema.Object(
        title="A CloudWatchLogSources container",
        schema = ICloudWatchLogSources,
        required=False,
    )
    log_group_name = schema.TextLine(
        title="Log group name. Can override the LogGroup name used from the name field.",
        description="",
        default="",
        required=False,
    )

class ICloudWatchLogSets(INamed, IMapping):
    """
Container for `CloudWatchLogSet`_ objects.
    """
    taggedValue('contains', 'ICloudWatchLogSet')

class ICloudWatchLogSet(INamed, ICloudWatchLogRetention):
    """
A set of Log Group objects
    """
    log_groups = schema.Object(
        title="A CloudWatchLogGroups container",
        schema = ICloudWatchLogGroups,
        required=False,
    )

class ICloudWatchLogging(INamed, ICloudWatchLogRetention):
    """
CloudWatch Logging configuration
    """
    log_sets = schema.Object(
        title="A CloudWatchLogSets container",
        schema = ICloudWatchLogSets,
        required=False,
    )

# Events

class IEventTarget(INamed):
    target = PacoReference(
        title="Paco Reference to an AWS Resource to invoke",
        schema_constraint='Interface',
        required=True,
    )
    input_json = schema.TextLine(
        title="Valid JSON passed as input to the target.",
        required=False,
        constraint=isValidJSONOrNone,
    )

class IEventsRule(IResource):
    """
Events Rule resources match incoming or scheduled events and route them to target using Amazon EventBridge.

.. sidebar:: Prescribed Automation

    ``targets``: If the ``target`` is a Lambda, an IAM Role will be created that is granted permission to invoke it by this EventRule.

.. code-block:: yaml
    :caption: Lambda function resource YAML

    type: EventsRule
    enabled: true
    order: 10
    description: Invoke a Lambda every other minute
    schedule_expression: "cron(*/2 * * * ? *)"
    targets:
        - target: paco.ref netenv.mynet.applications.myapp.groups.mygroup.resources.mylambda

    """
    # ToDo: add event_pattern field and invariant to make schedule_expression conditional
    # ToDo: constraint regex that validates schedule_expression
    description=schema.Text(
        title="Description",
        required=False,
        default='',
        max_length=512,
    )
    schedule_expression = schema.TextLine(
        title="Schedule Expression",
        required=True
    )
    enabled_state = schema.Bool(
        title="Enabled State",
        required=False,
        default=True
    )
    # ToDo: constrain List to not be empty
    targets = schema.List(
        title="The AWS Resources that are invoked when the Rule is triggered.",
        description="",
        required=True,
        value_type=schema.Object(IEventTarget),
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
        title="Metric(s) group name",
        required=False,
    )
    measurements = schema.List(
        title="Measurements",
        value_type=schema.TextLine(title="Metric measurement name"),
        required=False,
    )
    collection_interval = schema.Int(
        title="Collection interval",
        description="",
        min=1,
        required=False,
    )
    resources = schema.List(
        title="List of resources for this metric",
        value_type=schema.TextLine(title="Metric resource"),
        required=False
    )
    drop_device = schema.Bool(
        title="Drops the device name from disk metrics",
        default=True,
        required=False
    )


class IHealthChecks(INamed, IMapping):
    "Container for `Route53HealthCheck`_ objects."
    taggedValue('contains', 'IRoute53HealthCheck')

class IMonitorConfig(IDeployable, INamed, INotifiable):
    """
A set of metrics and a default collection interval
    """
    asg_metrics = schema.List(
        title="ASG Metrics",
        value_type=schema.TextLine(),
        constraint=isValidASGMetricNames,
        description="Must be one of: 'GroupMinSize', 'GroupMaxSize', 'GroupDesiredCapacity', 'GroupInServiceInstances', 'GroupPendingInstances', 'GroupStandbyInstances', 'GroupTerminatingInstances', 'GroupTotalInstances'",
        required=False,
    )
    alarm_sets = schema.Object(
        title="Sets of Alarm Sets",
        schema=IAlarmSets,
        required=False,
    )
    collection_interval = schema.Int(
        title="Collection interval",
        min=1,
        default=60,
        required=False,
    )
    health_checks = schema.Object(
        title="Set of Health Checks",
        schema=IHealthChecks,
        required=False,
    )
    log_sets = schema.Object(
        title="Sets of Log Sets",
        schema=ICloudWatchLogSets,
        required=False,
    )
    metrics = schema.List(
        title="Metrics",
        value_type=schema.Object(IMetric),
        required=False,
    )

class IMonitorable(Interface):
    """
A monitorable resource
    """
    monitoring = schema.Object(
        schema = IMonitorConfig,
        required=False,
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
        required=True,
    )
    aws = schema.List(
        title="List of AWS Principals.",
        description="Either this field or the principal field must be set.",
        value_type=schema.TextLine(
            title="AWS Principal"
        ),
        required=False,
    )
    condition = schema.Dict(
        title="Condition",
        description='Each Key is the Condition name and the Value must be a dictionary of request filters. e.g. { "StringEquals" : { "aws:username" : "johndoe" }}',
        default={},
        required=False,
        # ToDo: Use awacs to add a constraint to check for valid conditions
    )
    # ToDo: validate principal using awacs
    # ToDo: validate that only one principal type is supplied, as that is all that is currently supported by paco.cftemplates.s3.py
    principal = schema.Dict(
        title="Prinicpals",
        description="Either this field or the aws field must be set. Key should be one of: AWS, Federated, Service or CanonicalUser. Value can be either a String or a List.",
        default={},
        required=False,
    )
    effect = schema.Choice(
        title="Effect",
        description="Must be one of 'Allow' or 'Deny'",
        required=True,
        vocabulary=vocabulary.iam_policy_effect,
    )
    resource_suffix = schema.List(
        title="List of AWS Resources Suffixes",
        value_type=schema.TextLine(
            title="Resources Suffix"
        ),
        required=True,
    )
    sid = schema.TextLine(
        title="Statement Id",
        required=False,
    )
    @invariant
    def aws_or_principal(obj):
        if obj.aws == [] and obj.principal == {}:
            raise Invalid("Either the aws or the principal field must not be blank.")
        if obj.aws != [] and obj.principal != {}:
            raise Invalid("Can not set bot the aws and the principal fields.")


class IS3LambdaConfiguration(IParent):
    # ToDo: add constraint
    event = schema.TextLine(
        title="S3 bucket event for which to invoke the AWS Lambda function",
        description="Must be a supported event type: https://docs.aws.amazon.com/AmazonS3/latest/dev/NotificationHowTo.html",
        required=False,
    )
    function = PacoReference(
        title="Lambda function to notify",
        required=False,
        schema_constraint='ILambda',
    )

class IS3NotificationConfiguration(IParent):
    lambdas = schema.List(
        title="Lambda configurations",
        value_type=schema.Object(IS3LambdaConfiguration),
        required=False,
    )

class IS3StaticWebsiteHostingRedirectRequests(IParent):
    target = PacoReference(
        title="Target S3 Bucket or domain.",
        str_ok=True,
        required=True,
        schema_constraint='IS3Bucket'
    )
    protocol = schema.TextLine(
        title="Protocol",
        required=True
    )

class IS3StaticWebsiteHosting(IParent, IDeployable):
    redirect_requests = schema.Object(
        title="Redirect requests configuration.",
        schema=IS3StaticWebsiteHostingRedirectRequests,
        required=False
    )

class IS3Bucket(IResource, IDeployable):
    """S3Bucket is an object storage resource in the Amazon S3 service.

S3Buckets may be declared either in the global ``resource/s3.yaml`` file or in a network environment in
as an application resource.

S3Buckets in an application context will use the same ``account`` and ``region`` as the application, although
it is still possible to override this to use other accouns and regions if desired.

.. sidebar:: Prescribed Automation

    ``deletion_policy``: The ``deletion_policy:`` field supports a ``delete`` or ``keep`` values. The ``delete``
    choice will delete all objects from the S3 Bucket if a Paco delete command is applied. Otherwise AWS will not
    allow you to delete an S3 Bucket that is not empty until all objects are deleted.

    ``resource_suffix``: The ``policy`` field allows you to declare S3 Bucket policies. These policies need to be
    restricted to the S3 Bucket resource itself. The ``resource_suffix`` will be prefixed with the S3 Bucket ARN
    and you only need to declare keys within the bucket.

.. code-block:: yaml
    :caption: example S3Bucket resource

    type: S3Bucket
    title: My S3 Bucket
    enabled: true
    order: 10
    account: paco.ref accounts.data
    region: us-west-2
    deletion_policy: "delete"
    notifications:
        lambdas:
         - paco.ref netenv.mynet.applications.app.groups.serverless.resources.mylambda
    cloudfront_origin: false
    external_resource: false
    versioning: false
    policy:
      - principal:
          Service: iotanalytics.amazonaws.com
        effect: 'Allow'
        action:
          - s3:Get*
          - s3:ListBucket
          - s3:ListBucketMultipartUploads
          - s3:ListMultipartUploadParts
        resource_suffix:
          - '/*'
          - ''
      - aws:
          - paco.sub '${paco.ref netenv.mynet.applications.app.groups.site.resources.demo.instance_iam_role.arn}'
        effect: 'Allow'
        action:
          - 's3:Get*'
          - 's3:List*'
        resource_suffix:
          - '/*'
          - ''

"""
    bucket_name = schema.TextLine(
        title="Bucket Name",
        description="A short unique name to assign the bucket.",
        default="bucket",
        required=True,
    )
    account = PacoReference(
        title="Account that S3 Bucket belongs to.",
        required=False,
        schema_constraint='IAccount',
    )
    deletion_policy = schema.TextLine(
        title="Bucket Deletion Policy",
        default="delete",
        required=False,
    )
    notifications = schema.Object(
        title="Notification configuration",
        schema = IS3NotificationConfiguration,
        required=False,
    )
    policy = schema.List(
        title="List of S3 Bucket Policies",
        description="",
        value_type=schema.Object(IS3BucketPolicy),
        required=False,
    )
    region = schema.TextLine(
        title="Bucket region",
        default=None,
        required=False
    )
    cloudfront_origin = schema.Bool(
        title="Creates and listens for a CloudFront Access Origin Identity",
        required=False,
        default=False,
    )
    external_resource = schema.Bool(
        title='Boolean indicating whether the S3 Bucket already exists or not',
        default=False,
        required=False,
    )
    versioning = schema.Bool(
        title="Enable Versioning on the bucket.",
        default=False,
        required=False,
    )
    static_website_hosting = schema.Object(
        title="Static website hosting configuration.",
        required=False,
        schema = IS3StaticWebsiteHosting
    )

class IApplicationS3Bucket(IApplicationResource, IS3Bucket):
    """An S3 Bucket specific to an application."""

class IS3Buckets(INamed, IMapping):
    """Container for `S3Bucket`_ objects.
"""
    taggedValue('contains', 'IS3Bucket')

class IS3Resource(INamed):
    """S3 Bucket"""
    buckets = schema.Object(
        title="Dictionary of S3Bucket objects",
        schema=IS3Buckets,
        required=True,
    )

class IApplicationEngine(INamed, IDeployable, INotifiable, IMonitorable, IDNSEnablable):
    """
Application Engine : A template describing an application
    """
    order = schema.Int(
        title="The order in which the application will be processed",
        description="",
        min=0,
        default=0,
        required=False
    )
    groups = schema.Object(IResourceGroups)


class IApplication(IApplicationEngine):
    """
An Application is groups of cloud resources to support a workload.
    """

class IEC2KeyPair(INamed):
    """
EC2 SSH Key Pair
    """
    keypair_name = schema.TextLine(
        title="The name of the EC2 KeyPair",
        description="",
        required=True
    )
    region = schema.TextLine(
        title="AWS Region",
        description="Must be a valid AWS Region name",
        default="no-region-set",
        missing_value="no-region-set",
        required=True,
        constraint=isValidAWSRegionName,
    )
    account = PacoReference(
        title='AWS Account the key pair belongs to',
        required=False,
        schema_constraint='IAccount'
    )

class IEC2KeyPairs(INamed, IMapping):
    """
Container for `EC2KeyPair`_ objects.
    """
    taggedValue('contains', 'IEC2KeyPair')

class IEC2User(INamed):
    full_name = schema.TextLine(
        title="Full Name",
        required=False,
    )
    email = schema.TextLine(
        title="Email",
        required=False,
        constraint=isValidEmail,
    )
    public_ssh_key = schema.TextLine(
        title="Public SSH Key",
        required=True,
    )

class IEC2Users(INamed, IMapping):
    """
Container for `EC2User`_ objects.
    """
    taggedValue('contains', 'IEC2User')

class IEC2Group(INamed):
    members = schema.List(
        title="List of Users",
        default=[],
        required=True,
    )

class IEC2Groups(INamed, IMapping):
    """
Container for `EC2Group`_ objects.
    """
    taggedValue('contains', 'IEC2Group')


class IEC2Resource(INamed):
    """
EC2 Resource Configuration
    """
    keypairs = schema.Object(
        title="Group of EC2 Key Pairs",
        schema=IEC2KeyPairs,
        required=False,
    )
    users = schema.Object(
        title="SSH Users",
        schema=IEC2Users,
        required=False
    )
    groups = schema.Object(
        title="SSH Users",
        schema=IEC2Groups,
        required=False
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
        default=False,
        required=False,
    )
    instance_iam_profile = Attribute("Instance IAM Profile")
    instance_ami = schema.TextLine(
        title="Instance AMI",
        description="",
        required=False,
    )
    instance_key_pair = PacoReference(
        title="key pair for connections to instance",
        description="",
        required=False,
        schema_constraint=IEC2KeyPair
    )
    instance_type = schema.TextLine(
        title="Instance type",
        description="",
        required=False,
    )
    segment = schema.TextLine(
        title="Segment",
        description="",
        required=False,
    )
    security_groups = schema.List(
        title="Security groups",
        description="",
        value_type=PacoReference(
            title="Paco reference",
            schema_constraint='ISecurityGroup',
        ),
        required=False,
    )
    root_volume_size_gb = schema.Int(
        title="Root volume size GB",
        description="",
        default=8,
        min=8,
        required=False,
    )
    disable_api_termination = schema.Bool(
        title="Disable API Termination",
        description="",
        default=False,
        required=False,
    )
    private_ip_address = schema.TextLine(
        title="Private IP Address",
        description="",
        required=False,
    )
    user_data_script = schema.Text(
        title="User data script",
        description="",
        default="",
        required=False,
    )


class INetworkEnvironments(INamed, IMapping):
    """Container for `NetworkEnvironment`_ objects."""
    taggedValue('contains', 'INetworkEnvironment')

class IVersionControl(INamed):
    "Version control configuration for Paco"
    enforce_branch_environments = schema.Bool(
        title="Enforce vcs branches to provision environments",
        default=False,
        required=False,
    )
    environment_branch_prefix = schema.TextLine(
        title="Environment branch prefix",
        default="ENV-",
        required=False,
    )
    git_branch_environment_mappings = schema.List(
        title="Git branch to environment mappings",
        description="Must be in the format <environment-name>:<branch-name>. The branch name " + \
        "will not be prefixed with the normal environment branch prefix.",
        default=[],
        value_type=schema.TextLine(),
        required=False,
        constraint=isValidBranchEnvMappings,
    )
    global_environment_name = schema.TextLine(
        title="Name of the environment that controls global resources.",
        default="prod",
        required=False,
    )

class IPacoWorkBucket(INamed):
    bucket_name = schema.TextLine(
        title="Bucket Name",
        description="A short unique name to assign the bucket",
        default="paco-work",
        required=False,
    )
    enabled = schema.Bool(
        title="Enable sharing the .paco-work directory by syncing to an S3 Bucket.",
        required=False,
        default=False,
    )
    account = PacoReference(
        title="Account Reference",
        required=True,
        schema_constraint=IAccount
    )
    region = schema.TextLine(
        title="AWS Region",
        required=False,
        constraint=isValidAWSRegionNameOrNone,
    )

class ISharedState(INamed):
    paco_work_bucket = schema.Object(
        title="Paco work bucket",
        description="",
        schema=IPacoWorkBucket,
        required=False
    )

class IProject(INamed, IMapping):
    "Project : the root node in the config for a Paco Project"
    taggedValue('contains', 'mixed')
    paco_project_version = schema.TextLine(
        title="Paco project version",
        default="",
        required=False,
    )
    active_regions = schema.List(
        title="Regions that resources can be provisioned in",
        value_type=schema.TextLine(),
        constraint=isValidAWSRegionList,
        required=False,
    )
    legacy_flags = schema.List(
        title='List of Legacy Flags',
        value_type=schema.TextLine(),
        constraint=isValidLegacyFlagList,
        required=False,
    )
    version_control = schema.Object(
        title="Version Control integration",
        description="",
        schema=IVersionControl,
        required=False,
    )
    shared_state = schema.Object(
        title="Shared State",
        description="",
        schema=ISharedState,
        required=False
    )
    s3bucket_hash = schema.TextLine(
        title="S3 Bucket hash suffix",
        description="",
        required=False,
        constraint=isValidS3BucketHash,
    )


# duplicate function as in paco.models.locations to avoid circular imports
def get_parent_by_interface(context, interface=IProject):
    """
    Walk up the tree until an object provides the requested Interface
    """
    max = 999
    while context is not None:
        if interface.providedBy(context):
            return context
        if IProject.providedBy(context):
            return None
        else:
            context = context.__parent__
        max -= 1
        if max < 1:
            raise TypeError("Maximum location depth exceeded. Model is borked!")

class IRoute53RecordSet(Interface):
    """
Route53 Record Set
    """
    record_name = schema.TextLine(
        title='Record Set Full Name',
        required=True
    )
    type = schema.TextLine(
        title='Record Set Type',
        required=True,
        constraint = isValidRoute53RecordSetType
    )
    resource_records = schema.List(
        title='Record Set Values',
        required=True,
        value_type=schema.TextLine(title='Resource Record')
    )
    ttl = schema.Int(
        title='Record TTL',
        required=False,
        default=300
    )

    @invariant
    def is_valid_values_check(obj):
        if obj.type in ['CNAME', 'SOA']:
            if len(obj.resource_records) > 1:
                raise Invalid("If 'type' is {}, you may only specify one 'value'.".format(obj.type))

class IRoute53HostedZoneExternalResource(INamed, IDeployable):
    """
Existing Hosted Zone configuration
    """
    hosted_zone_id = schema.TextLine(
        title='ID of an existing Hosted Zone',
        required=True
    )
    nameservers = schema.List(
        title='List of the Hosted Zones Nameservers',
        value_type=schema.TextLine(title='Nameservers'),
        required=True
    )

class IHostedZone(Interface):
    "Base interface for IRoute53HostedZone and IPrivateHostedZone"

class IRoute53HostedZone(IHostedZone, INamed, IDeployable):
    """
Route53 Hosted Zone
    """
    domain_name = schema.TextLine(
        title="Domain Name",
        required=True
    )
    account = PacoReference(
        title="Account this Hosted Zone belongs to",
        required=True,
        schema_constraint='IAccount'
    )
    record_sets = schema.List(
        title='List of Record Sets',
        value_type=schema.Object(IRoute53RecordSet),
        required=True
    )
    parent_zone = schema.TextLine(
        title='Parent Hozed Zone name',
        required=False
    )
    external_resource = schema.Object(
        title='External HostedZone Id Configuration',
        schema = IRoute53HostedZoneExternalResource,
        required=False
    )
    private_hosted_zone = schema.Bool(
        title='Make this hosted zone private.',
        required=False,
        default=False
    )
    vpc_associations = PacoReference(
        title="The VPC the private hosted zone will be provisioned in.",
        required=False,
        schema_constraint='IVPC'
    )

class IInternetGateway(IDeployable):
    """
AWS Resource: IGW
    """

class INATGateway(INamed, IDeployable):
    """NAT Gateway"""
    type = schema.TextLine(
        title='NAT Gateway type',
        default='Managed',
        required=False,
        constraint=IsValidNATGatewayType
    )
    availability_zone = schema.TextLine(
        title='Availability Zones to launch instances in.',
        description="Can be 'all' or number of AZ: 1, 2, 3, 4 ...",
        default='all',
        required=False,
        constraint=IsValidASGAvailabilityZone
    )
    segment = PacoReference(
        title="Segment",
        description="",
        required=False,
        schema_constraint='ISegment'
    )
    default_route_segments = schema.List(
        title="Default Route Segments",
        description="",
        value_type=PacoReference(
            title="Segment",
            schema_constraint="ISegment"
        ),
        required=False,
    )
    security_groups = schema.List(
        title="Security Groups",
        value_type=PacoReference(
            title="Paco reference",
            schema_constraint='ISecurityGroup'
        ),
        required=False,
    )
    ec2_key_pair = PacoReference(
        title="EC2 key pair",
        description="",
        required=False,
        schema_constraint=IEC2KeyPair
    )
    ec2_instance_type = schema.TextLine(
        title="EC2 Instance Type",
        required=False,
        default='t2.nano'
    )

class IVPNGateway(INamed, IDeployable):
    """VPN Gateway"""

class IPrivateHostedZone(IHostedZone, IParent, IDeployable):
    """Private Hosted Zone"""
    name = schema.TextLine(
        title="Hosted zone name",
        required=False,
    )
    vpc_associations = schema.List(
        title="List of VPC Ids",
        required=False,
        value_type=schema.TextLine(
            title="VPC ID"
        ),
        default=None
    )

class ISegment(INamed, IDeployable):
    """
Segment
    """
    internet_access = schema.Bool(
        title="Internet Access",
        default=False,
        required=False,
    )
    az1_cidr = schema.TextLine(
        title="Availability Zone 1 CIDR",
        default="",
        required=False,
    )
    az2_cidr = schema.TextLine(
        title="Availability Zone 2 CIDR",
        default="",
        required=False,
    )
    az3_cidr = schema.TextLine(
        title="Availability Zone 3 CIDR",
        default="",
        required=False,
    )
    az4_cidr = schema.TextLine(
        title="Availability Zone 4 CIDR",
        default="",
        required=False,
    )
    az5_cidr = schema.TextLine(
        title="Availability Zone 5 CIDR",
        default="",
        required=False,
    )
    az6_cidr = schema.TextLine(
        title="Availability Zone 6 CIDR",
        default="",
        required=False,
    )

class IVPCPeeringRoute(IParent):
    """
VPC Peering Route
    """
    segment = PacoReference(
        title="Segment",
        required=False,
        schema_constraint='ISegment'
    )
    cidr = schema.TextLine(
        title="CIDR IP",
        default="",
        description="A valid CIDR v4 block or an empty string",
        constraint = isValidCidrIpv4orBlank,
        required=False,
    )

class IVPCPeering(INamed, IDeployable):
    """
VPC Peering
    """
    # peer_* is used when peering with an external VPC
    peer_role_name = schema.TextLine(
        title='Remote peer role name',
        required=False
    )
    peer_vpcid = schema.TextLine(
        title='Remote peer VPC Id',
        required=False
    )
    peer_account_id = schema.TextLine(
        title='Remote peer AWS account Id',
        required=False
    )
    peer_region = schema.TextLine(
        title='Remote peer AWS region',
        required=False
    )
    # network_environment is used when peering with a network environment
    # local to the project.
    network_environment = PacoReference(
        title='Network Environment Reference',
        required=False,
        schema_constraint='INetworkEnvironment'
    )
    # Routes forward traffic to the peering connection
    routing = schema.List(
        title="Peering routes",
        value_type=schema.Object(IVPCPeeringRoute),
        required=True
    )

class INATGateways(INamed, IMapping):
    """Container for `NATGateway`_ objects."""
    taggedValue('contains', 'INATGateway')

class IVPNGateways(INamed, IMapping):
    """Container for `VPNGateway`_ objects."""
    taggedValue('contains', 'IVPNGateway')

class ISecurityGroups(INamed, IMapping):
    """Container for `SecurityGroup`_ objects."""
    taggedValue('contains', 'ISecurityGroup')

class ISecurityGroupSets(INamed, IMapping):
    """Container for `SecurityGroups`_ objects."""
    taggedValue('contains', 'ISecurityGroups')

class ISegments(INamed, IMapping):
    """Container for `Segment`_ objects."""
    taggedValue('contains', 'ISegment')

class IVPCPeerings(INamed, IMapping):
    """Container for `VPCPeering`_ objects."""
    taggedValue('contains', 'IVPCPeering')

class IVPC(INamed, IDeployable):
    """VPC"""
    cidr = schema.TextLine(
        title="CIDR",
        description="",
        default="",
        required=False,
    )
    enable_dns_hostnames = schema.Bool(
        title="Enable DNS Hostnames",
        description="",
        default=False,
        required=False,
    )
    enable_dns_support = schema.Bool(
        title="Enable DNS Support",
        description="",
        default=False,
        required=False,
    )
    enable_internet_gateway = schema.Bool(
        title="Internet Gateway",
        description="",
        default=False,
        required=False,
    )
    nat_gateway = schema.Object(
        title="NAT Gateways",
        description="",
        schema=INATGateways,
        required=True,
    )
    vpn_gateway = schema.Object(
        title="VPN Gateways",
        description="",
        schema=IVPNGateways,
        required=True,
    )
    private_hosted_zone = schema.Object(
        title="Private hosted zone",
        description="",
        schema=IPrivateHostedZone,
        required=False,
    )
    security_groups = schema.Object(
        title="Security Group Sets",
        description="Security Groups Sets are containers for SecurityGroups containers.",
        schema=ISecurityGroupSets,
        required=True,
    )
    segments = schema.Object(
        title="Segments",
        description="",
        schema=ISegments,
        required=True,
    )
    peering = schema.Object(
        title="VPC Peering",
        description="",
        schema=IVPCPeerings,
        required=True,
    )

class INetworkEnvironment(INamed, IDeployable, IMapping):
    """NetworkEnvironment"""
    # technically contains IEnvironment but there are set by the loader
    # for the docs we do not want to indicate that environments are configured from within
    # the network: key.
    taggedValue('contains', 'mixed')

class ICredentials(INamed):
    aws_access_key_id = schema.TextLine(
        title="AWS Access Key ID",
        description="",
        default="",
        required=False,
    )
    aws_secret_access_key = schema.TextLine(
        title="AWS Secret Access Key",
        description="",
        default="",
        required=False,
    )
    aws_default_region = schema.TextLine(
        title="AWS Default Region",
        description="Must be a valid AWS Region name",
        default="no-region-set",
        missing_value = "no-region-set",
        required=True,
        constraint = isValidAWSRegionName
    )
    master_account_id = schema.TextLine(
        title="Master AWS Account ID",
        description="",
        default="",
        required=False,
    )
    master_admin_iam_username = schema.TextLine(
        title="Master Account Admin IAM Username",
        description="",
        default="",
        required=False,
    )
    admin_iam_role_name = schema.TextLine(
        title="Administrator IAM Role Name",
        required=False,
    )
    mfa_session_expiry_secs = schema.Int(
        title='The number of seconds before an MFA token expires.',
        default=60 * 60,    # 1 hour: 3600 seconds
        min=60 * 15,        # 15 minutes: 900 seconds
        max=(60 * 60) * 12, # 12 hours: 43200 seconds
        required=False,
    )
    assume_role_session_expiry_secs = schema.Int(
        title='The number of seconds before an assumed role token expires.',
        default=60 * 15,   # 15 minutes: 900 seconds
        min=60 * 15,       # 15 minutes: 900 seconds
        max=60 * 60,       # 1 hour: 3600 seconds
        required=False,
    )

class INetwork(INamed, IDeployable, IMapping):
    # contains Environment objects but do not indicate this
    # in the docs, they are configured under `environments:`.
    taggedValue('contains', 'mixed')
    aws_account = PacoReference(
        title='Account this Network belongs to',
        required=False,
        schema_constraint='IAccount',
    )
    availability_zones = schema.Int(
        title="Availability Zones",
        description="",
        default=0,
        required=False,
    )
    vpc = schema.Object(
        title="VPC",
        description="",
        schema=IVPC,
        required=False,
    )


# Secrets Manager schemas

class IGenerateSecretString(IParent, IDeployable):
    exclude_characters = schema.Text(
        title="A string that includes characters that should not be included in the generated password.",
        required=False,
        max_length=4096
    )
    exclude_lowercase = schema.Bool(
        title="The generated password should not include lowercase letters.",
        default=False,
        required=False
    )
    exclude_numbers = schema.Bool(
        title="The generated password should exclude digits.",
        default=False,
        required=False
    )
    exclude_punctuation = schema.Bool(
        title="The generated password should not include punctuation characters.",
        default=False,
        required=False
    )
    exclude_uppercase = schema.Bool(
        title="The generated password should not include uppercase letters.",
        default=False,
        required=False
    )
    generate_string_key = schema.TextLine(
        title="The JSON key name that's used to add the generated password to the JSON structure.",
        required=False,
        max_length=10240
    )
    include_space = schema.Bool(
        title="The generated password can include the space character.",
        required=False
    )
    password_length = schema.Int(
        title="The desired length of the generated password.",
        default=32,
        required=False
    )
    require_each_included_type = schema.Bool(
        title="The generated password must include at least one of every allowed character type.",
        default=True,
        required=False
    )
    secret_string_template = schema.Text(
        title="A properly structured JSON string that the generated password can be added to.",
        required=False,
        max_length=10240
    )


class ISecretsManagerSecret(INamed, IDeployable):
    """Secret for the Secrets Manager."""
    account = PacoReference(
        title="Account to provision the Secret in",
        required=False,
        schema_constraint='IAccount'
    )
    generate_secret_string = schema.Object(
        title="Generate SecretString object",
        required=False,
        schema=IGenerateSecretString,
        default=None
    )

class ISecretsManagerGroup(INamed, IMapping):
    """Container for `SecretsManagerSecret`_ objects."""
    taggedValue('contains', 'ISecretsManagerSecret')

class ISecretsManagerApplication(INamed, IMapping):
    """Container for `SecretsManagerGroup`_ objects."""
    taggedValue('contains', 'ISecretsManagerGroup')

class ISecretsManager(INamed, IMapping):
    """Secrets Manager contains `SecretManagerApplication` objects."""
    taggedValue('contains', 'ISecretsManagerApplication')

# Environment, Account and Region containers

class IAccountContainer(INamed, IMapping):
    """Container for `RegionContainer`_ objects."""
    taggedValue('contains', 'IRegionContainer')

class IRegionContainer(INamed, IMapping):
    "Container for objects which do not belong to a specific Environment."
    taggedValue('contains', 'mixed')
    alarm_sets = schema.Object(
        title="Alarm Sets",
        schema=IAlarmSets,
        required=False
    )

class IEnvironmentDefault(IRegionContainer):
    """
Default values for an Environment's configuration
    """
    # EnvironmentDefault inherits from RegionContainer so
    # technically it can contain non-environment objects directly,
    # but it should never do so.
    taggedValue('contains', 'mixed')
    applications = schema.Object(
        title="Application container",
        required=True,
        schema = IApplicationEngines,
    )
    network = schema.Object(
        title="Network",
        required=False,
        schema = INetwork,
    )
    secrets_manager = schema.Object(
        title="Secrets Manager",
        required=False,
        schema = ISecretsManager
    )

class IEnvironmentRegion(IEnvironmentDefault, IDeployable):
    """
An actual provisioned Environment in a specific region.
May contains overrides of the IEnvironmentDefault where needed.
    """
    taggedValue('contains', 'mixed')

class IEnvironment(INamed, IMapping):
    """
Environment
    """
    # contains 'default' EnvironmentDefault and 'us-west-2' EnvironmentRegion objects
    taggedValue('contains', 'mixed')


# SSM

class ISSMDocuments(INamed, IMapping):
    "A container of EnvironmentRegion `SSMDocument`_ objects."
    taggedValue('contains', 'ISSMDocument')

class ISSMDocument(IResource):
    locations = schema.List(
        title="Locations",
        value_type=schema.Object(IAccountRegions),
        default=[],
        required=True,
    )
    content = schema.Text(
        title="JSON or YAML formatted SSM document",
        required=True,
    )
    document_type = schema.Choice(
        title="Document Type",
        required=True,
        vocabulary=vocabulary.ssm_document_types,
    )

class ISSMResource(INamed):
    ssm_documents = schema.Object(
        title="SSM Documents",
        schema=ISSMDocuments,
        required=True,
    )

# Networking

class IAWSCertificateManager(IResource):
    domain_name = schema.TextLine(
        title="Domain Name",
        description="",
        default="",
        required=False,
    )
    subject_alternative_names = schema.List(
        title="Subject alternative names",
        description="",
        value_type=schema.TextLine(
            title="alternative name"
        ),
        required=False,
    )
    external_resource = schema.Bool(
        title="Marks this resource as external to avoid creating and validating it.",
        default=False,
        required=False,
    )
    private_ca = schema.TextLine(
        title="Private Certificate Authority ARN",
        description="",
        default=None,
        required=False,
    )

class IPortProtocol(Interface):
    """Port and Protocol"""
    port = schema.Int(
        title="Port",
        required=False,
    )
    protocol = schema.Choice(
        title="Protocol",
        vocabulary=vocabulary.target_group_protocol,
        required=False,
    )

class ITargetGroups(INamed, IMapping):
    """
Container for `TargetGroup`_ objects.
    """
    taggedValue('contains', 'ITargetGroup')

class ITargetGroup(IPortProtocol, IResource):
    """Target Group"""
    health_check_interval = schema.Int(
        title="Health check interval",
        required=False,
    )
    health_check_timeout = schema.Int(
        title="Health check timeout",
        required=False,
    )
    healthy_threshold = schema.Int(
        title="Healthy threshold",
        required=False,
    )
    unhealthy_threshold = schema.Int(
        title="Unhealthy threshold",
        required=False,
    )
    health_check_http_code = schema.TextLine(
        title="Health check HTTP codes",
        required=False,
    )
    health_check_path = schema.TextLine(
        title="Health check path",
        default="/",
        required=False,
    )
    connection_drain_timeout = schema.Int(
        title="Connection drain timeout",
        required=False,
    )

class IListenerRule(IDeployable):
    rule_type = schema.TextLine(
        title="Type of Rule",
        required=False,
    )
    priority = schema.Int(
        title="Forward condition priority",
        required=False,
        default=1
    )
    host = schema.TextLine(
        title="Host header value",
        required=False,
    )
    path_pattern = schema.List(
        title="List of paths to match",
        value_type=schema.TextLine(),
        required=False
    )
    # Redirect Rule Variables
    redirect_host = schema.TextLine(
        title="The host to redirect to",
        required=False,
    )
    # Forward Rule Variables
    target_group = schema.TextLine(
        title="Target group name",
        required=False,
    )

class IListeners(INamed, IMapping):
    """
Container for `Listener`_ objects.
    """
    taggedValue('contains', 'IListener')

class IListener(IParent, IPortProtocol):
    @invariant
    def redirect_or_target_group(obj):
        "Must set one of redirect or target_group but not both"
        if obj.redirect == None and obj.target_group == '':
            raise Invalid("Either a redirect or a target_group must be set for a listener.")
        if obj.redirect != None and obj.target_group != '':
            raise Invalid("Can not set both a redirect and a target_group for a listener.")

    redirect = schema.Object(
        title="Redirect",
        schema=IPortProtocol,
        required=False,
    )
    ssl_certificates = schema.List(
        title="List of SSL certificate References",
        value_type=PacoReference(
            title="SSL Certificate Reference",
            schema_constraint='IAWSCertificateManager'
        ),
        required=False,
    )
    ssl_policy = schema.Choice(
        title="SSL Policy",
        default="",
        vocabulary=vocabulary.lb_ssl_policy,
        required=False,
    )
    target_group = schema.TextLine(
        title="Target group",
        default="",
        required=False
    )
    rules = schema.Dict(
        title="Container of listener rules",
        value_type=schema.Object(IListenerRule),
        required=False,
        default=None
    )

class IDNS(IParent):
    hosted_zone = PacoReference(
        title="Hosted Zone Id",
        required=False,
        str_ok=True,
        schema_constraint='IHostedZone'
    )
    domain_name = PacoReference(
        title="Domain name",
        required=False,
        str_ok=True,
        schema_constraint='IRoute53HostedZone'
     )
    ssl_certificate = PacoReference(
        title="SSL certificate Reference",
        required=False,
        schema_constraint='IAWSCertificateManager'
    )
    ttl = schema.Int(
        title="TTL",
        default=300,
        required=False
    )

class ILBApplication(IResource, IMonitorable):
    """
The ``LBApplication`` resource type creates an Application Load Balancer. Use load balancers to route traffic from
the internet to your web servers.

Load balancers have ``listeners`` which will accept requrests on specified ports and protocols. If a listener
uses the HTTPS protocol, it can have a Paco reference to an SSL Certificate. A listener can then either
redirect the traffic to another port/protcol or send it one of it's named ``target_groups``.

Each target group will specify it's health check configuration. To specify which resources will belong
to a target group, use the ``target_groups`` field on an ASG resource.

.. sidebar:: Prescribed Automation

    ``dns``: Creates Route 53 Record Sets that will resolve DNS records to the domain name of the load balancer.

    ``enable_access_logs``: Set to True to turn on access logs for the load balancer, and will automatically create
    an S3 Bucket with permissions for AWS to write to that bucket.

    ``access_logs_bucket``: Name an existing S3 Bucket (in the same region) instead of automatically creating a new one.
    Remember that if you supply your own S3 Bucket, you are responsible for ensuring that the bucket policy for
    it grants AWS the `s3:PutObject` permission.

.. code-block:: yaml
    :caption: Example LBApplication load balancer resource YAML

    type: LBApplication
    enabled: true
    enable_access_logs: true
    target_groups:
        api:
            health_check_interval: 30
            health_check_timeout: 10
            healthy_threshold: 2
            unhealthy_threshold: 2
            port: 3000
            protocol: HTTP
            health_check_http_code: 200
            health_check_path: /
            connection_drain_timeout: 30
    listeners:
        http:
            port: 80
            protocol: HTTP
            redirect:
                port: 443
                protocol: HTTPS
        https:
            port: 443
            protocol: HTTPS
            ssl_certificates:
                - paco.ref netenv.app.applications.app.groups.certs.resources.root
            target_group: api
    dns:
        - hosted_zone: paco.ref resource.route53.mynetenv
          domain_name: api.example.com
    scheme: internet-facing
    security_groups:
        - paco.ref netenv.app.network.vpc.security_groups.app.alb
    segment: public

"""
    target_groups = schema.Object(
        title="Target Groups",
        schema=ITargetGroups,
        required=False,
    )
    listeners = schema.Object(
        title="Listeners",
        schema=IListeners,
        required=False,
    )
    dns = schema.List(
        title="List of DNS for the ALB",
        value_type=schema.Object(IDNS),
        required=False,
    )
    scheme = schema.Choice(
        title="Scheme",
        vocabulary=vocabulary.lb_scheme,
        required=False,
    )
    security_groups = schema.List(
        title="Security Groups",
        value_type=PacoReference(
            title="Paco reference",
            schema_constraint='ISecurityGroup',
        ),
        required=False,
    )
    segment = schema.TextLine(
        title="Id of the segment stack",
        required=False,
    )
    idle_timeout_secs = schema.Int(
        title='Idle timeout in seconds',
        description='The idle timeout value, in seconds.',
        default=60,
        required=False,
    )
    enable_access_logs = schema.Bool(
        title="Write access logs to an S3 Bucket",
        required=False
    )
    access_logs_bucket=PacoReference(
        title="Bucket to store access logs in",
        required=False,
        schema_constraint='IS3Bucket'
    )
    access_logs_prefix = schema.TextLine(
        title="Access Logs S3 Bucket prefix",
        required=False
    )

class IPrincipal(INamed):
    aws = schema.List(
        title="List of AWS Principals",
        value_type=schema.TextLine(
            title="AWS Principal",
            default="",
            required=False
        ),
        required=False
    )
    service = schema.List(
        title="List of AWS Service Principals",
        value_type=schema.TextLine(
            title="AWS Service Principal",
            default="",
            required=False
        ),
        required=False
    )

class IStatement(INamed):
    action = schema.List(
        title="Action(s)",
        value_type=schema.TextLine(),
        required=False,
    )
    condition = schema.Dict(
        title="Condition",
        description='Each Key is the Condition name and the Value must be a dictionary of request filters. e.g. { "StringEquals" : { "aws:username" : "johndoe" }}',
        default={},
        required=False,
        # ToDo: Use awacs to add a constraint to check for valid conditions
    )
    effect = schema.Choice(
        title="Effect",
        description="Must be one of 'Allow' or 'Deny'",
        required=False,
        vocabulary=vocabulary.iam_policy_effect,
    )
    resource = schema.List(
        title="Resrource(s)",
        value_type=schema.TextLine(),
        required=False,
    )
    principal = schema.Object(
        title="Principal",
        schema=IPrincipal,
        required=False
    )


class IPolicy(IParent):
    name = schema.TextLine(
        title="Policy name",
        default="",
        required=False,
    )
    statement = schema.List(
        title="Statements",
        value_type=schema.Object(
            title="Statement",
            schema=IStatement
        ),
        required=False,
    )

class IAssumeRolePolicy(IParent):
    effect = schema.Choice(
        title="Effect",
        description="Must be one of 'Allow' or 'Deny'",
        required=False,
        vocabulary=vocabulary.iam_policy_effect,
    )
    aws = schema.List(
        title="List of AWS Principals",
        value_type=schema.TextLine(
            title="AWS Principal",
            default="",
            required=False
        ),
        required=False
    )
    service = schema.List(
        title="Service",
        value_type=schema.TextLine(
            title="Service",
            default="",
            required=False
        ),
        required=False
    )
    # ToDo: what are 'aws' keys for? implement ...

class IRole(INamed, IDeployable):
    assume_role_policy = schema.Object(
        title="Assume role policy",
        schema=IAssumeRolePolicy,
        required=False
    )
    instance_profile = schema.Bool(
        title="Instance profile",
        default=False,
        required=False
    )
    path = schema.TextLine(
        title="Path",
        default="/",
        required=False
    )
    role_name = schema.TextLine(
        title="Role name",
        default="",
        required=False
    )
    global_role_name = schema.Bool(
        title="Role name is globally unique and will not be hashed",
        required=False,
        default=False,
    )
    policies = schema.List(
        title="Policies",
        value_type=schema.Object(
            schema=IPolicy
        ),
        required=False
    )
    managed_policy_arns = schema.List(
        title="Managed policy ARNs",
        value_type=schema.TextLine(
            title="Managed policy ARN"
        ),
        required=False
    )
    max_session_duration = schema.Int(
        title="Maximum session duration",
        description="The maximum session duration (in seconds)",
        min=3600,
        max=43200,
        default=3600,
        required=False
    )
    permissions_boundary = schema.TextLine(
        title="Permissions boundary ARN",
        description="Must be valid ARN",
        default="",
        required=False
    )

class IManagedPolicy(INamed, IDeployable):
    """
IAM Managed Policy
    """
    policy_name = schema.TextLine(
        title="Policy Name used in AWS. This will be prefixed with an 8 character hash.",
        required=True,
    )
    roles = schema.List(
        title="List of Role Names",
        value_type=schema.TextLine(
            title="Role Name"
        ),
        required=False,
    )
    users = schema.List(
        title="List of IAM Users",
        value_type=schema.TextLine(
            title="IAM User name"
        ),
        required=False,
    )
    statement = schema.List(
        title="Statements",
        value_type=schema.Object(
            title="Statement",
            schema=IStatement
        ),
        required=False,
    )
    path = schema.TextLine(
        title="Path",
        default="/",
        required=False,
    )


class IIAM(INamed):
    roles = schema.Dict(
        title="Roles",
        value_type=schema.Object(
            title="Role",
            schema=IRole
        ),
        required=False,
    )
    policies = schema.Dict(
        title="Policies",
        value_type=schema.Object(
            title="ManagedPolicy",
            schema=IManagedPolicy
        ),
        required=False,
    )

class IEFSMount(IDeployable):
    """
EFS Mount Folder and Target Configuration
    """
    folder = schema.TextLine(
        title='Folder to mount the EFS target',
        required=True
    )
    target = PacoReference(
        title='EFS Target Resource Reference',
        required=True,
        str_ok=True,
        schema_constraint='IEFS'
    )

class ISimpleCloudWatchAlarm(IParent):
    """
A Simple CloudWatch Alarm
    """
    alarm_description=schema.Text(
        title="Alarm Description",
        description="Valid JSON document with Paco fields.",
        required=False,
    )
    actions_enabled = schema.Bool(
        title="Actions Enabled",
        required=False,
    )
    comparison_operator = schema.TextLine(
        title="Comparison operator",
        constraint = isComparisonOperator,
        description="Must be one of: 'GreaterThanThreshold','GreaterThanOrEqualToThreshold', 'LessThanThreshold', 'LessThanOrEqualToThreshold'",
        required=False,
    )
    evaluation_periods = schema.Int(
        title="Evaluation periods",
        required=False,
    )
    metric_name = schema.TextLine(
        title="Metric name",
        required=True,
    )
    namespace = schema.TextLine(
        title="Namespace",
        required=False,
    )
    period = schema.Int(
        title="Period in seconds",
        required=False,
    )
    statistic = schema.TextLine(
        title="Statistic",
        required=False,
    )
    threshold = schema.Float(
        title="Threshold",
        required=False,
    )
    dimensions = schema.List(
        title='Dimensions',
        value_type=schema.Object(IDimension),
        required=False,
    )

# CloudFormation Init schemas

class ICloudFormationConfigSets(INamed, IMapping):
    taggedValue('contains', 'mixed')
    @invariant
    def configurations_lists(obj):
        """
        ConfigSets:

        ascending:
            - "config1"
            - "config2"
        descending:
            - "config2"
            - "config1"
        """
        for key, value in obj.items():
            if type(key) != type(str()):
                raise Invalid('ConfigSet name must be a string')
            if len(key) < 1:
                raise Invalid('ConfigSet name must be at least 1 char')
            configurations = obj.__parent__.configurations
            if configurations == None:
                # if configurations haven't loaded yet, they can't be validated
                return
            for item in value:
                if item not in configurations:
                    raise Invalid('ConfigSet name does not match any configurations')

class ICloudFormationConfigurations(INamed, IMapping):
    taggedValue('contains', 'ICloudFormationConfiguration')

class ICloudFormationInitVersionedPackageSet(IMapping):
    taggedValue('contains', 'mixed')
    @invariant
    def packages_with_optional_versions(obj):
        """
        Packages lists should look like this:

        yum:
            httpd: ["0.10.2"]
            php: ["5.1", "5.2"]
            wordpress: []
        """
        for key, value in obj.items():
            if type(key) != type(str()):
                raise Invalid('Package name must be a string')
            if len(key) < 1:
                raise Invalid('Package name must be at least 1 char')
            if type(value) != type(list()):
                raise Invalid('Package version must be a list')
            for item in value:
                if type(item) != type(str()):
                    raise Invalid('Package version must be a string')
                if len(item) < 1:
                    raise Invalid('Package version must be at least 1 char')

class ICloudFormationInitPathOrUrlPackageSet(IMapping):
    taggedValue('contains', 'mixed')
    @invariant
    def packages_with_path_or_url(obj):
        """
        Packages should look like this:

        rpm:
            epel: "http://download.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm"

        """
        for key, value in obj.items():
            if type(key) != type(str()):
                raise Invalid('Package name must be a string')
            if len(key) < 1:
                raise Invalid('Package name must be at least 1 char')
            if type(value) != type(str()):
                raise Invalid('Package path/URL must be a string')
            if len(value) < 1:
                raise Invalid('Package path/URL must be at least 1 char')

class ICloudFormationInitPackages(INamed):
    apt = schema.Object(
        title="Apt packages",
        schema=ICloudFormationInitVersionedPackageSet,
        required=False
    )
    msi = schema.Object(
        title="MSI packages",
        schema=ICloudFormationInitPathOrUrlPackageSet,
        required=False
    )
    python = schema.Object(
        title="Apt packages",
        schema=ICloudFormationInitVersionedPackageSet,
        required=False
    )
    rpm = schema.Object(
        title="RPM packages",
        schema=ICloudFormationInitPathOrUrlPackageSet,
        required=False
    )
    rubygems = schema.Object(
        title="Rubygems packages",
        schema=ICloudFormationInitVersionedPackageSet,
        required=False
    )
    yum = schema.Object(
        title="Yum packages",
        schema=ICloudFormationInitVersionedPackageSet,
        required=False
    )

class ICloudFormationInitGroup(Interface):
    gid = schema.TextLine(
        title="Gid",
        required=False,
    )

class ICloudFormationInitGroups(Interface):
    """
Container for CloudFormationInit Groups
    """

class ICloudFormationInitUser(Interface):
    groups = schema.List(
        title="Groups",
        required=False,
        value_type=schema.TextLine(
            title="Group"
        ),
        default=[]
    )
    uid = schema.Int(
        title="Uid",
        required=False,
        min=100,
        max=65535
    )
    home_dir = schema.TextLine(
        title="Home dir",
        required=True
    )

class ICloudFormationInitUsers(Interface):
    """
Container for CloudFormationInit Users
    """

class ICloudFormationInitSources(INamed, IMapping):
    taggedValue('contains', 'mixed')

class InvalidCfnInitEncoding(schema.ValidationError):
    __doc__ = 'File encoding must be one of plain or base64.'

def isValidCfnInitEncoding(value):
    if value not in ('plain', 'base64'):
        raise InvalidCfnInitEncoding

def isValidS3KeyPrefix(value):
    if value.startswith('/') or value.endswith('/'):
        raise InvalidS3KeyPrefix
    return True

class InvalidStorageKeyPrefix(schema.ValidationError):
    __doc__ = "Not a valid key prefix. Must match regular expression pattern ^[a-zA-Z0-9!_.*'()/{}:-]*/$"

KEYPREFIX_RE = re.compile(r"^[a-zA-Z0-9!_.*'()/{}:-]*/$")
def isValidStorageKeyPrefix(value):
    if value == '': return True
    if not KEYPREFIX_RE.match(value):
        raise InvalidStorageKeyPrefix
    return True

class ICloudFormationInitFiles(INamed, IMapping):
    taggedValue('contains', 'mixed')

class ICloudFormationInitFile(INamed):
    @invariant
    def content_or_source(obj):
        if obj.content != None and obj.content_file != None and obj.content_cfn_file != None:
            raise Invalid("Can not specify more than one of content, content_cfn_file and content_file for cfn-init file configuration.")
        elif obj.content != None and obj.source != None:
            raise Invalid("Can not specify both content and source for cfn-init file configuration.")
        elif obj.content_file != None and obj.source != None:
            raise Invalid("Can not specify both content_file and source for cfn-init file configuration.")

    @invariant
    def encoding_for_source(obj):
        if obj.encoding != None and obj.content == None:
            raise Invalid("For cfn-init file configuration, encoding requires the content to be set.")

    content = schema.Object(
        title="""Either a string or a properly formatted YAML object.""",
        required=False,
        schema=Interface
    )
    content_file = StringFileReference(
        title="""File path to a string.""",
        required=False
    )
    content_cfn_file = YAMLFileReference(
        title="File path to a properly formatted CloudFormation Functions YAML object.",
        required=False
    )
    source = schema.TextLine(
        title="A URL to load the file from.",
        required=False
    )
    encoding = schema.TextLine(
        title="The encoding format.",
        required=False,
        constraint=isValidCfnInitEncoding
    )
    group = schema.TextLine(
        title="The name of the owning group for this file. Not supported for Windows systems.",
        required=False
    )
    owner = schema.TextLine(
        title="The name of the owning user for this file. Not supported for Windows systems.",
        required=False
    )
    mode = schema.TextLine(
        title="""A six-digit octal value representing the mode for this file.""",
        min_length=6,
        max_length=6,
        required=False
    )
    authentication = schema.TextLine(
        title="""The name of an authentication method to use.""",
        required=False
    )
    context = schema.TextLine(
        title="""Specifies a context for files that are to be processed as Mustache templates.""",
        required=False
    )

class ICloudFormationInitCommands(INamed, IMapping):
    taggedValue('contains', 'mixed')

class ICloudFormationInitCommand(Interface):
    command = schema.Text(
        title="Command",
        required=True,
        min_length=1
    )
    env = schema.Dict(
        title="Environment Variables. This property overwrites, rather than appends, the existing environment.",
        required=False,
        default={}
    )
    cwd = schema.TextLine(
        title="Cwd. The working directory",
        required=False,
        min_length=1
    )
    test = schema.TextLine(
        title="A test command that determines whether cfn-init runs commands that are specified in the command key. If the test passes, cfn-init runs the commands.",
        required=False,
        min_length=1
    )
    ignore_errors = schema.Bool(
        title="Ingore errors - determines whether cfn-init continues to run if the command in contained in the command key fails (returns a non-zero value). Set to true if you want cfn-init to continue running even if the command fails.",
        required=False,
        default=False
    )

class ICloudFormationInitService(Interface):
    # ToDo: Invariant to check commands list
    ensure_running = schema.Bool(
        title="Ensure that the service is running or stopped after cfn-init finishes.",
        required=False
    )
    enabled = schema.Bool(
        title="Ensure that the service will be started or not started upon boot.",
        required=False
    )
    files = schema.List(
        title="A list of files. If cfn-init changes one directly via the files block, this service will be restarted",
        required=False,
        value_type=schema.TextLine(
            title="File"
        ),
    )
    sources = schema.List(
        title="A list of directories. If cfn-init expands an archive into one of these directories, this service will be restarted.",
        required=False,
        value_type=schema.TextLine(
            title="Sources"
        ),
    )
    packages = schema.Dict(
        title="A map of package manager to list of package names. If cfn-init installs or updates one of these packages, this service will be restarted.",
        required=False,
        default={}
    )
    commands = schema.List(
        title="A list of command names. If cfn-init runs the specified command, this service will be restarted.",
        required=False,
        value_type=schema.TextLine(
            title="Commands"
        ),
    )

class ICloudFormationInitServiceCollection(INamed, IMapping):
    taggedValue('contains', 'mixed')

class ICloudFormationInitServices(INamed):
    sysvinit = schema.Object(
        title="SysVInit Services for Linux OS",
        schema=ICloudFormationInitServiceCollection,
        required=False
    )
    windows = schema.Object(
        title="Windows Services for Windows OS",
        schema=ICloudFormationInitServiceCollection,
        required=False
    )

class ICloudFormationConfiguration(INamed):
    @invariant
    def check_user_group_duplicates(obj):
        for username in obj.users.keys():
            if username in obj.groups:
                raise Invalid("Both user and group with the name {} can not be set. When a user is created it automatically creates a group with the same name. Explicitly creating the group will cause the user add operation to fail.".format(username))

    packages = schema.Object(
        title="Packages",
        schema=ICloudFormationInitPackages,
        required=False
    )
    groups = schema.Object(
        title="Groups",
        schema=ICloudFormationInitGroups,
        required=False
    )
    users = schema.Object(
        title="Users",
        schema=ICloudFormationInitUsers,
        required=False
    )
    sources = schema.Object(
        title="Sources",
        schema=ICloudFormationInitSources,
        required=False
    )
    files = schema.Object(
        title="Files",
        schema=ICloudFormationInitFiles,
        required=False
    )
    commands = schema.Object(
        title="Commands",
        schema=ICloudFormationInitCommands,
        required=False
    )
    services = schema.Object(
        title="Services",
        schema=ICloudFormationInitServices,
        required=False
    )

class ICloudFormationParameters(INamed, IMapping):
    taggedValue('contains', 'mixed')

class ICloudFormationInit(INamed):
    """
`CloudFormation Init`_ is a method to configure an EC2 instance after it is launched.
CloudFormation Init is a much more complete and robust method to install configuration files and
pakcages than using a UserData script.

It stores information about packages, files, commands and more in CloudFormation metadata. It is accompanied
by a ``cfn-init`` script which will run on the instance to fetch this configuration metadata and apply
it. The whole system is often referred to simply as cfn-init after this script.

The ``cfn_init`` field of for an ASG contains all of the cfn-init configuration. After an instance
is launched, it needs to run a local cfn-init script to pull the configuration from the CloudFromation
stack and apply it. After cfn-init has applied configuration, you will run cfn-signal to tell CloudFormation
the configuration was successfully applied. Use the ``launch_options`` field for an ASG to let Paco take care of all this
for you.

.. sidebar:: Prescribed Automation

    ``launch_options``: The ``cfn_init_config_sets:`` field is a list of cfn-init configurations to
    apply at launch. This list will be applied in order. On Amazon Linux the cfn-init script is pre-installed
    in /opt/aws/bin. If you enable a cfn-init launch option, Paco will install cfn-init in /opt/paco/bin for you.

Refer to the `CloudFormation Init`_ docs for a complete description of all the configuration options
available.

.. code-block:: yaml
    :caption: cfn_init with launch_options

    launch_options:
        cfn_init_config_sets:
        - "Install"
    cfn_init:
      parameters:
        BasicKey: static-string
        DatabasePasswordarn: paco.ref netenv.mynet.secrets_manager.app.site.database.arn
      config_sets:
        Install:
          - "Install"
      configurations:
        Install:
          packages:
            rpm:
              epel: "http://download.fedoraproject.org/pub/epel/5/i386/epel-release-5-4.noarch.rpm"
            yum:
              jq: []
              python3: []
          files:
            "/tmp/get_rds_dsn.sh":
              content_cfn_file: ./webapp/get_rds_dsn.sh
              mode: '000700'
              owner: root
              group: root
            "/etc/httpd/conf.d/saas_wsgi.conf":
              content_file: ./webapp/saas_wsgi.conf
              mode: '000600'
              owner: root
              group: root
            "/etc/httpd/conf.d/wsgi.conf":
              content: "LoadModule wsgi_module modules/mod_wsgi.so"
              mode: '000600'
              owner: root
              group: root
            "/tmp/install_codedeploy.sh":
              source: https://aws-codedeploy-us-west-2.s3.us-west-2.amazonaws.com/latest/install
              mode: '000700'
              owner: root
              group: root
          commands:
            10_install_codedeploy:
              command: "/tmp/install_codedeploy.sh auto > /var/log/cfn-init-codedeploy.log 2>&1"
          services:
            sysvinit:
              codedeploy-agent:
                enabled: true
                ensure_running: true

The ``parameters`` field is a set of Parameters that will be passed to the CloudFormation stack. This
can be static strings or ``paco.ref`` that are looked up from already provisioned cloud resources.

CloudFormation Init can be organized into Configsets. With raw cfn-init using Configsets is optional,
but is required with Paco.

In a Configset, the ``files`` field has four fields for specifying the file contents.

 * ``content_file:`` A path to a file on the local filesystem. A convenient practice is to make a
   sub-directory in the ``netenv`` directory for keeping cfn-init files.

 * ``content_cfn_file:`` A path to a file on the local filesystem. This file will have FnSub and FnJoin
   CloudFormation applied to it.

 * ``content:`` For small files, the content can be in-lined directly in this field.

 * ``source:`` Fetches the file from a URL.

If you are using ``content_cfn_file`` to interpolate Parameters, the file might look like:

.. code-block:: bash

    !Sub |
        #!/bin/bash

        echo "Database ARN is " ${DatabasePasswordarn}
        echo "AWS Region is " ${AWS::Region}

If you want to include a raw ``${SomeValue}`` string in your file, use the ! character to escape it like this:
``${!SomeValue}``. cfn-init also supports interpolation with Mustache templates, but Paco support for this is
not yet implemented.

.. _CloudFormation Init: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-init.html

    """
    config_sets = schema.Object(
        title="CloudFormation Init configSets",
        schema=ICloudFormationConfigSets,
        required=True
    )
    configurations = schema.Object(
        title="CloudFormation Init configurations",
        schema=ICloudFormationConfigurations,
        required=True
    )
    parameters = schema.Dict(
        title="Parameters",
        default={},
        required=False
    )

# AutoScalingGroup schemas

class IASGLifecycleHooks(INamed, IMapping):
    """
Container for `ASGLifecycleHook` objects.
    """
    taggedValue('contains', 'IASGLifecycleHook')

class IASGLifecycleHook(INamed, IDeployable):
    """
ASG Lifecycle Hook
    """
    lifecycle_transition = schema.TextLine(
        title='ASG Lifecycle Transition',
        constraint = IsValidASGLifecycleTransition,
        required=True
    )
    notification_target_arn = schema.TextLine(
        title='Lifecycle Notification Target Arn',
        required=True
    )
    role_arn = schema.TextLine(
        title='Licecycel Publish Role ARN',
        required=True
    )
    default_result = schema.TextLine(
        title='Default Result',
        required=False,
        constraint = IsValidASGLifecycleDefaultResult
    )

class IASGScalingPolicies(INamed, IMapping):
    """
Container for `ASGScalingPolicy`_ objects.
    """
    taggedValue('contains', 'IASGScalingPolicy')

class IASGScalingPolicy(INamed, IDeployable):
    """
Auto Scaling Group Scaling Policy
    """
    policy_type = schema.TextLine(
        title='Policy Type',
        default='SimpleScaling',
        # SimpleScaling, StepScaling, and TargetTrackingScaling
        constraint=IsValidASGScalignPolicyType,
    )
    adjustment_type = schema.TextLine(
        title='Adjustment Type',
        default='ChangeInCapacity',
        # ChangeInCapacity, ExactCapacity, and PercentChangeInCapacity
        constraint=IsValidASGScalingPolicyAdjustmentType,
    )
    scaling_adjustment = schema.Int(
        title='Scaling Adjustment'
    )
    cooldown = schema.Int(
        title='Scaling Cooldown in Seconds',
        default=300,
        min=0,
        required=False
    )
    alarms = schema.List(
        title='Alarms',
        value_type=schema.Object(ISimpleCloudWatchAlarm),
    )

    @invariant
    def required_simple_scaling_properties(obj):
        if obj.policy_type == 'SimpleScaling':
            if obj.scaling_adjustment == None:
                raise Invalid("'scaling_adjustment' must be specified when policy_type is 'SimpleScaling'")
        if obj.policy_type != 'SimpleScaling':
            if obj.scaling_adjustment != None:
                raise Invalid("'policy_type' must be 'SimpleScaling' when 'scaling_adjustment' is used.")
            if obj.cooldown != None:
                raise Invalid("'cooldown' may only be used when policy_type is 'SimpleScaling'")

class IEIP(IResource):
    """
Elastic IP (EIP) resource.

.. sidebar:: Prescribed Automation

    ``dns``: Adds a DNS CNAME to resolve to this EIP's IP address to the Route 53 HostedZone.

.. code-block:: yaml
    :caption: Example EIP resource YAML

    type: EIP
    order: 5
    enabled: true
    dns:
      - domain_name: example.com
        hosted_zone: paco.ref resource.route53.examplecom
        ttl: 60

"""
    dns = schema.List(
        title="List of DNS for the EIP",
        value_type=schema.Object(IDNS),
        required=False
    )

class IEBSVolumeMount(IParent, IDeployable):
    """
EBS Volume Mount Configuration
    """
    folder = schema.TextLine(
        title='Folder to mount the EBS Volume',
        required=True
    )
    volume = PacoReference(
        title='EBS Volume Resource Reference',
        required=True,
        str_ok=True,
        schema_constraint='IEBS'
    )
    device = schema.TextLine(
        title='Device to mount the EBS Volume with.',
        required=True
    )
    filesystem = schema.TextLine(
        title='Filesystem to mount the EBS Volume with.',
        required=True
    )

class IEBS(IResource):
    """
Elastic Block Store (EBS) Volume.

It is required to specify the ``availability_zone`` the EBS Volume will be created in.
If the volume is going to be used by an ASG, it should launch an instance in the same
``availability_zone`` (and region).

.. code-block:: yaml
    :caption: Example EBS resource YAML

    type: EBS
    order: 5
    enabled: true
    size_gib: 4
    volume_type: gp2
    availability_zone: 1

    """

    size_gib = schema.Int(
        title="Volume Size in GiB",
        description="",
        default=10,
        required=False
    )
    snapshot_id = schema.TextLine(
        title="Snapshot ID",
        description="",
        required=False
    )
    availability_zone = schema.Int(
        # Can be: 1 | 2 | 3 | 4 | ...
        title='Availability Zone to create Volume in.',
        required=True
    )
    volume_type = schema.TextLine(
        title="Volume Type",
        description="Must be one of: gp2 | io1 | sc1 | st1 | standard",
        default='gp2',
        constraint = isValidEBSVolumeType,
        required=False
    )

class IEC2LaunchOptions(INamed):
    """
EC2 Launch Options
    """
    update_packages = schema.Bool(
        title='Update Distribution Packages',
        required=False,
        default=False
    )
    cfn_init_config_sets = schema.List(
        title="List of cfn-init config sets",
        value_type=schema.TextLine(
            title="",
            required=False
        ),
        required=False,
        default=[]
    )
    ssm_agent = schema.Bool(
        title='Install SSM Agent',
        required=False,
        default=True
    )
    ssm_expire_events_after_days = schema.TextLine(
        title="Retention period of SSM logs",
        description="",
        default="30",
        constraint = isValidCloudWatchLogRetention,
        required=False,
    )

class IBlockDevice(IParent):
    delete_on_termination = schema.Bool(
        title="Indicates whether to delete the volume when the instance is terminated.",
        default=True,
        required=False
    )
    encrypted = schema.Bool(
        title="Specifies whether the EBS volume is encrypted.",
        required=False
    )
    iops = schema.Int(
        title="The number of I/O operations per second (IOPS) to provision for the volume.",
        description="The maximum ratio of IOPS to volume size (in GiB) is 50:1, so for 5,000 provisioned IOPS, you need at least 100 GiB storage on the volume.",
        min=100,
        max=20000,
        required=False
    )
    snapshot_id = schema.TextLine(
        title="The snapshot ID of the volume to use.",
        min_length=1,
        max_length=255,
        required=False
    )
    size_gib = schema.Int(
        title="The volume size, in Gibibytes (GiB).",
        description="This can be a number from 1-1,024 for standard, 4-16,384 for io1, 1-16,384 for gp2, and 500-16,384 for st1 and sc1.",
        min=1,
        max=16384,
        required=False
    )
    volume_type = schema.TextLine(
        title="The volume type, which can be standard for Magnetic, io1 for Provisioned IOPS SSD, gp2 for General Purpose SSD, st1 for Throughput Optimized HDD, or sc1 for Cold HDD.",
        description="Must be one of standard, io1, gp2, st1 or sc1.",
        constraint=isValidEBSVolumeType
    )

class IBlockDeviceMapping(IParent):
    @invariant
    def ebs_or_virtual_name(obj):
        if obj.ebs == None and obj.virtual_name == None:
            raise Invalid("Must set one of either ebs or virtual_name for block_device_mappings.")
        if obj.ebs != None and obj.virtual_name != None:
            raise Invalid("Can not set both ebs and virtual_name for block_device_mappings.")
        return True

    device_name = schema.TextLine(
        title="The device name exposed to the EC2 instance",
        required=True,
        min_length=1,
        max_length=255
    )
    ebs = schema.Object(
        title="Amazon Ebs volume",
        schema=IBlockDevice,
        required=False
    )
    virtual_name = schema.TextLine(
        title="The name of the virtual device.",
        description="The name must be in the form ephemeralX where X is a number starting from zero (0), for example, ephemeral0.",
        min_length=1,
        max_length=255,
        required=False
    )

class IASGRollingUpdatePolicy(INamed):
    """
AutoScalingRollingUpdate Policy
    """
    enabled = schema.Bool(
        title="Enable an UpdatePolicy for the ASG",
        description="",
        default=True,
        required=False,
    )
    max_batch_size = schema.Int(
        title="Maximum batch size",
        description="",
        default=1,
        min=1,
        required=False,
    )
    min_instances_in_service = schema.Int(
        title="Minimum instances in service",
        description="",
        default=0,
        min=0,
        required=False,
    )
    pause_time = schema.TextLine(
        title="Minimum instances in service",
        description="Must be in the format PT#H#M#S",
        required=False,
        default='',
    )
    wait_on_resource_signals = schema.Bool(
        title="Wait for resource signals",
        description="",
        default=False
    )

class IECSCapacityProvider(INamed, IDeployable):
    target_capacity = schema.Int(
        title="Target Capacity",
        min=1,
        max=100,
        required=False,
        default=100,
    )
    minimum_scaling_step_size = schema.Int(
        title="Minimum Scaling Step Size",
        min=1,
        max=10000,
        required=False,
        default=1,
    )
    maximum_scaling_step_size = schema.Int(
        title="Maximum Scaling Step Size",
        min=1,
        max=10000,
        required=False,
        default=10000,
    )

class IECSASGConfiguration(INamed):
    cluster = PacoReference(
        title='Cluster',
        required=True,
        str_ok=False,
        schema_constraint='IECSCluster'
    )
    log_level = schema.Choice(
        title="Log Level",
        vocabulary=vocabulary.log_levels,
        default='error',
        required=False,
    )
    capacity_provider = schema.Object(
        title="Capacity Provider",
        required=False,
        schema=IECSCapacityProvider,
    )

class ISSHAccess(INamed):
    @invariant
    def valid_users_groups(obj):
        "Ensure users and groups exist in ec2.yaml"
        if len(obj.users) != 0 or len(obj.groups) != 0:
            project = get_parent_by_interface(obj, IProject)
            if 'ec2' not in project.resource:
                raise Invalid("Must create a resrouce/ec2.yaml file to specify users and groups for SSH.")
            ec2_users = project.resource['ec2'].users
            ec2_groups = project.resource['ec2'].groups
            for user in obj.users:
                if user not in ec2_users:
                    raise Invalid(f"User with name '{user}' not found in resource/ec2.yaml users.")
            for group in obj.groups:
                if group not in ec2_groups:
                    raise Invalid(f"Group with name '{group}' not found in resource/ec2.yaml groups.")

        return True

    users = schema.List(
        title="User",
        description="Must match a user declared in resource/ec2.yaml",
        value_type=schema.TextLine(title="User"),
        required=False,
        default=[],
    )
    groups = schema.List(
        title="Groups",
        description="Must match a group declared in resource/ec2.yaml",
        value_type=schema.TextLine(title="Group"),
        required=False,
        default=[],
    )

class IASG(IResource, IMonitorable):
    """
An AutoScalingGroup (ASG) contains a collection of Amazon EC2 instances that are treated as a
logical grouping for the purposes of automatic scaling and management.

The Paco ASG resource provisions an AutoScalingGroup as well as LaunchConfiguration and TargetGroups
for that ASG.


.. sidebar:: Prescribed Automation

    ASGs use Paco's **LaunchBundles**. A LaunchBundle is a zip file of code and configuration files that is
    automatically created and stored in an S3 Bucket that the ASG has read permissions to. Paco adds BASH code
    to the UserData script for the ASG's LaunchConfiguration that will iterate through all of the LaunchBundles
    and download and run them. For example, if you specify in-host metrics for an ASG, it will have a LaunchBundle
    created with the necessary CloudWatch agent configuration and a BASH script to install and configure the agent.

    ``launch_options``: Options to add actions to newly launched instances: ``ssm_agent``, ``update_packages`` and
    ``cfn_init_config_sets``. The ``ssm_agent`` field will install the SSM Agent and is true by default.
    Paco's **LaunchBundles** feature requires the SSM Agent installed and running. The ``update_packages`` field will
    perform a operating system package update (``yum update`` or ``apt-get update``). This happens immediately after the
    ``user_data_pre_script`` commands, but before the LaunchBundle commands and ``user_data_script`` commands.
    The ``cfn_init_config_sets`` field is a list of CfnInitConfigurationSets that will be run at launch.

    ``cfn_init``: Contains CloudFormationInit (cfn-init) configuration. Paco allows reading cfn-init
    files from the filesystem, and also does additional validation checks on the configuration to ensure
    it is correct. The ``launch_options`` has a ``cfn_init_config_sets`` field to specify which
    CfnInitConfigurationSets you want to automatically call during instance launch with a LaunchBundle.

    ``ebs_volume_mounts``: Adds an EBS LaunchBundle that mounts all EBS Volumes
    to the EC2 instance launched by the ASG. If the EBS Volume is unformatted, it will be formatted to the
    specified filesystem. **This feature only works with "self-healing" ASGs**. A "self-healing" ASG is an ASG
    with ``max_instances`` set to 1. Trying to launch a second instance in the ASG will fail to mount the EBS Volume
    as it can only be mounted to one instance at a time.

    ``eip``: Adds an EIP LaunchBundle which will attach an Elastic IP to a launched instance.
    **This feature only works with "self-healing" ASGs**. A "self-healing" ASG is an ASG
    with ``max_instances`` set to 1. Trying to launch a second instance in the ASG will fail to attach the EIP
    as it can only be mounted to one instance at a time.

    ``efs_mounts``: Adds an EFS LaunchBundle that mounts all EFS locations. A SecurityGroup
    must still be manually configured to allow the ASG instances to network access to the EFS filesystem.

    ``monitoring``: Any fields specified in the ``metrics`` or ``log_sets`` fields will add a CloudWatchAgent LaunchBundle
    that will install a CloudWatch Agent and configure it to collect all specified metrics and log sources.

    ``secrets``: Adds a policy to the Instance Role which allows instances to access the specified secrets.

    ``ssh_access``:  Grants users and groups SSH access to the instances.

.. code-block:: yaml
    :caption: example ASG configuration

    type: ASG
    order: 30
    enabled: true
    associate_public_ip_address: false
    cooldown_secs: 200
    ebs_optimized: false
    health_check_grace_period_secs: 240
    health_check_type: EC2
    availability_zone: 1
    ebs_volume_mounts:
      - volume: paco.ref netenv.mynet.applications.app.groups.storage.resources.my_volume
        enabled: true
        folder: /var/www/html
        device: /dev/xvdf
        filesystem: ext4
    efs_mounts:
      - enabled: true
        folder: /mnt/wp_efs
        target: paco.ref netenv.mynet.applications.app.groups.storage.resources.my_efs
    instance_iam_role:
      enabled: true
      policies:
        - name: DNSRecordSet
          statement:
            - effect: Allow
              action:
                - route53:ChangeResourceRecordSets
              resource:
                - 'arn:aws:route53:::hostedzone/HHIHkjhdhu744'
    instance_ami: paco.ref function.aws.ec2.ami.latest.amazon-linux-2
    instance_ami_type: amazon
    instance_key_pair: paco.ref resource.ec2.keypairs.my_keypair
    instance_monitoring: true
    instance_type: t2.medium
    desired_capacity: 1
    max_instances: 3
    min_instances: 1
    rolling_update_policy:
      max_batch_size: 1
      min_instances_in_service: 1
      pause_time: PT3M
      wait_on_resource_signals: false
    target_groups:
      - paco.ref netenv.mynet.applications.app.groups.web.resources.alb.target_groups.cloud
    security_groups:
      - paco.ref netenv.mynet.network.vpc.security_groups.web.asg
    segment: private
    termination_policies:
      - Default
    scaling_policy_cpu_average: 60
    ssh_access:
      users:
        - bdobbs
      groups:
        - developers
    launch_options:
        update_packages: true
        ssm_agent: true
        cfn_init_config_sets:
        - "InstallApp"
    cfn_init:
      config_sets:
        InstallApp:
          - "InstallApp"
      configurations:
        InstallApp:
          packages:
            yum:
              python3: []
          users:
            www-data:
              uid: 2000
              home_dir: /home/www-data
          files:
            "/etc/systemd/system/pypiserver.service":
              content_file: ./pypi-config/pypiserver.service
              mode: '000755'
              owner: root
              group: root
          commands:
            00_pypiserver:
              command: "/bin/pip3 install pypiserver"
            01_passlib_dependency:
              command: "/bin/pip3 install passlib"
            02_prep_mount:
               command: "chown www-data:www-data /var/pypi"
          services:
            sysvinit:
              pypiserver:
                enabled: true
                ensure_running: true
    monitoring:
      enabled: true
      collection_interval: 60
      metrics:
        - name: swap
          measurements:
            - used_percent
        - name: disk
          measurements:
            - free
          resources:
            - '/'
            - '/var/www/html'
          collection_interval: 300
    user_data_script: |
      echo "Hello World!"


AutoScalingGroup Rolling Update Policy
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When changes are applied to an AutoScalingGroup that modify the configuration of newly launched instances,
AWS can automatically launch instances with the new configuration and terminate old instances that have stale configuration.
This can be configured so that there is no interruption of service as the new instances gradually replace old ones.
This configuration is set with the ``rolling_update_policy`` field.

The rolling update policy must be able to work within the minimum/maximum number of instances in the ASG.
Consider the following ASG configuration.

.. code-block:: yaml
    :caption: example ASG configuration

    type: ASG
    max_instances: 2
    min_instances: 1
    desired_capacity: 1
    rolling_update_policy:
      max_batch_size: 1
      min_instances_in_service: 1
      pause_time: PT0S # default setting
      wait_on_resource_signals: false # default setting

This will normally run a single instance in the ASG. The ASG is never allowed to launch more than 2 instances at one time.
When an update happens, a new batch of instances is launched - in this example just one instance. There wil be only 1 instance
in service, but the capacity will be at 2 instances will the new instance is launched. After the instance
is put into service by the ASG, it will immediately terminate the old instance.

The ``wait_on_resource_signals`` can be set to tell AWS CloudFormation to wait on making changes to the AutoScalingGroup configuration
until a new instance is finished configuring and installing applications and is ready for service. If this field is enabled,
then the ``pause_time`` default is PT05 (5 minutes). If CloudFormation does not get a SUCCESS signal within the ``pause_time``
then it will mark the new instance as failed and terminate it.

If you use ``pause_time`` with the default ``wait_on_resource_signals: false`` then AWS will simply wait for the full
duration of the pause time and then consider the instance ready. ``pause_time`` is in format PT#H#M#S, where each # is the number of
hours, minutes, and seconds, respectively. The maximum ``pause_time`` is one hour. For example:

.. code-block:: yaml

    pause_time: PT0S # 0 seconds
    pause_time: PT5M # 5 minutes
    pause_time: PT2M30S # 2 minutes and 30 seconds

ASGs will use default settings for a rolling update policy. If you do not want to use an update policies at all, then
you must disable the ``rolling_update_policy`` explicitly:

.. code-block:: yaml

    type: ASG
    rolling_update_policy:
      enabled: false

With no rolling update policy, when you make configuration changes, then existing instances with old configuration will
continue to run and instances with the new configuration will not happen until the AutoScalingGroup needs to launch new
instances. You must be careful with this approach as you can not know 100% that your new configuration launches instances
proprely until some point in the future when new instances are requested by the ASG.

.. sidebar:: Prescribed Automation

    Paco can help you send signals to CloudFormation when using ``wait_on_resource_signals``.
    If you set ``wait_on_resource_signals: true`` then Paco will automatically grant the needed ``cloudformation:SignalResource`` and
    ``cloudformation:DescribeStacks`` to the IAM Role associated with the instance for you. Paco also provides an
    ``ec2lm_signal_asg_resource`` BASH function available in your ``user_data_script`` that you can run to signal the instance is
    ready: ``ec2lm_signal_asg_resource SUCCESS`` or ``ec2lm_signal_asg_resource SUCCESS``.

    If you want to wait until load balancer health checks are passing before an instance is considered healthy, then send the SUCCESS
    signal to CloudFormation, you will need to configure this yourself.

        .. code-block:: bash
            :caption: example ASG signalling using ELB health checks

            'until [ "$state" == "\"InService\"" ]; do state=$(aws --region ${AWS::Region} elb describe-instance-health
            --load-balancer-name ${ElasticLoadBalancer}
            --instances $(curl -s http://169.254.169.254/latest/meta-data/instance-id)
            --query InstanceStates[0].State); sleep 10; done'


See the AWS documentation for more information on how `AutoScalingRollingUpdate Policy`_ configuration is used.

.. _AutoScalingRollingUpdate Policy: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-attribute-updatepolicy.html#cfn-attributes-updatepolicy-replacingupdate

    """
    @invariant
    def min_instances(obj):
        if obj.rolling_update_policy != None:
            if obj.rolling_update_policy != None and obj.rolling_update_policy.min_instances_in_service >= obj.max_instances:
                raise Invalid("ASG rolling_update_policy.min_instances_in_service must be less than max_instances.")
        if obj.min_instances > obj.max_instances:
            raise Invalid("ASG min_instances must be less than or equal to max_instances.")
        if obj.desired_capacity > obj.max_instances:
            raise Invalid("ASG desired_capacity must be less than or equal to max_instances.")

    associate_public_ip_address = schema.Bool(
        title="Associate Public IP Address",
        description="",
        default=False,
        required=False,
    )
    availability_zone = schema.TextLine(
        # Can be: all | 1 | 2 | 3 | 4 | ...
        title='Availability Zones to launch instances in.',
        default='all',
        required=False,
        constraint=IsValidASGAvailabilityZone
    )
    block_device_mappings = schema.List(
        title="Block Device Mappings",
        value_type=schema.Object(
            title="Block Device Mapping",
            schema=IBlockDeviceMapping
        ),
        required=False
    )
    cfn_init = schema.Object(
        title="CloudFormation Init",
        schema=ICloudFormationInit,
        required=False
    )
    cooldown_secs = schema.Int(
        title="Cooldown seconds",
        description="",
        default=300,
        required=False,
    )
    desired_capacity = schema.Int(
        title="Desired capacity",
        description="",
        default=1,
        required=False,
    )
    desired_capacity_ignore_changes = schema.Bool(
        title="Ignore changes to the desired_capacity after the ASG is created.",
        description="",
        default=False,
        required=False,
    )
    dns = schema.List(
        title="DNS domains to create to resolve to one of the ASGs EC2 Instances",
        value_type=schema.Object(IDNS),
        required=False
    )

    ebs_optimized = schema.Bool(
        title="EBS Optimized",
        description="",
        default=False,
        required=False,
    )
    ebs_volume_mounts = schema.List(
        title='Elastic Block Store Volume Mounts',
        value_type= schema.Object(IEBSVolumeMount),
        required=False,
    )
    ecs = schema.Object(
        title="ECS Configuration",
        schema=IECSASGConfiguration,
        required=False,
    )
    efs_mounts = schema.List(
        title='Elastic Filesystem Configuration',
        value_type=schema.Object(IEFSMount),
        required=False,
    )
    eip = PacoReference(
        title="Elastic IP or AllocationId to attach to instance at launch",
        required=False,
        str_ok=True,
        schema_constraint='IEIP'
    )
    health_check_grace_period_secs = schema.Int(
        title="Health check grace period in seconds",
        description="",
        default=300,
        required=False,
    )
    health_check_type = schema.TextLine(
        title="Health check type",
        description="Must be one of: 'EC2', 'ELB'",
        default='EC2',
        constraint = isValidHealthCheckType,
        required=False,
    )
    instance_iam_role = schema.Object(
        IRole,
        required=False
    )
    instance_ami = PacoReference(
        title="Instance AMI",
        description="",
        str_ok=True,
        required=False,
        schema_constraint='IFunction'
    )
    instance_ami_ignore_changes = schema.Bool(
        title="Do not update the instance_ami after creation.",
        description="",
        default=False,
        required=False,
    )
    instance_ami_type = schema.TextLine(
        title="The AMI Operating System family",
        description="Must be one of amazon, centos, suse, debian, ubuntu, microsoft or redhat.",
        constraint = isValidInstanceAMIType,
        default="amazon",
        required=False,
    )
    instance_key_pair = PacoReference(
        title="Key pair to connect to launched instances",
        description="",
        required=False,
        schema_constraint='IEC2KeyPair'
    )
    instance_monitoring = schema.Bool(
        title="Instance monitoring",
        description="",
        default=False,
        required=False,
    )
    instance_type = schema.TextLine(
        title="Instance type",
        description="",
        constraint = isValidInstanceSize,
        required=False,
    )
    launch_options = schema.Object(
        title='EC2 Launch Options',
        schema=IEC2LaunchOptions,
        required=True,
    )
    lifecycle_hooks = schema.Object(
        title='Lifecycle Hooks',
        schema=IASGLifecycleHooks,
        required=False
    )
    load_balancers = schema.List(
        title="Target groups",
        description="",
        value_type=PacoReference(
            title="Paco reference",
            schema_constraint='ITargetGroup'
        ),
        required=False,
    )
    max_instances = schema.Int(
        title="Maximum instances",
        description="",
        default=2,
        required=False,
    )
    min_instances = schema.Int(
        title="Minimum instances",
        description="",
        default=1,
        required=False,
    )
    scaling_policies = schema.Object(
        title='Scaling Policies',
        schema=IASGScalingPolicies,
        required=False,
    )
    scaling_policy_cpu_average = schema.Int(
        title="Average CPU Scaling Polciy",
        # Default is 0 == disabled
        default=0,
        min=0,
        max=100,
        required=False,
    )
    secrets = schema.List(
        title='List of Secrets Manager References',
        value_type=PacoReference(
            title='Secrets Manager Reference',
            schema_constraint='ISecretsManagerSecret'
        ),
        required=False
    )
    security_groups = schema.List(
        title="Security groups",
        description="",
        value_type=PacoReference(
            title="Paco reference",
            schema_constraint='ISecurityGroup'
        ),
        required=False,
    )
    segment = schema.TextLine(
        title="Segment",
        description="",
        required=False,
    )
    ssh_access = schema.Object(
        title="SSH Access",
        description="",
        schema=ISSHAccess,
        required=False,
    )
    target_groups = schema.List(
        title="Target groups",
        description="",
        value_type=PacoReference(
            title="Paco reference",
            schema_constraint='ITargetGroup'
        ),
        required=False,
    )
    termination_policies = schema.List(
        title="Terminiation policies",
        description="",
        value_type=schema.TextLine(
            title="Termination policy",
            description=""
        ),
        required=False,
    )
    user_data_pre_script = schema.Text(
        title="User data pre-script",
        description="",
        default="",
        required=False,
    )
    user_data_script = schema.Text(
        title="User data script",
        description="",
        default="",
        required=False,
    )
    rolling_update_policy = schema.Object(
        title="Rolling Update Policy",
        description="",
        schema=IASGRollingUpdatePolicy,
        required=True
    )

# Containers

# ECS

class IPortMapping(IParent):
    "Port Mapping"
    container_port = schema.Int(
        title="Container Port",
        min=0,
        max=65535,
        required=False,
    )
    host_port = schema.Int(
        title="Host Port",
        min=0,
        max=65535,
        required=False,
    )
    protocol = schema.Choice(
        title="Protocol",
        description="Must be either 'tcp' or 'udp'",
        vocabulary=vocabulary.network_protocols,
        default='tcp',
    )

class IECSMountPoint(IParent):
    "ECS TaskDefinition Mount Point"
    container_path = schema.TextLine(
        title="The path on the container to mount the host volume at.",
        required=False,
    )
    read_only = schema.Bool(
        title="Read Only",
        required=False,
        default=False,
    )
    source_volume = schema.TextLine(
        title="The name of the volume to mount.",
        description="Must be a volume name referenced in the name parameter of task definition volume.",
        required=False,
    )

class IECSVolumesFrom(IParent):
    "VoumesFrom"
    read_only = schema.Bool(
        title="Read Only",
        required=False,
        default=False,
    )
    source_container = schema.TextLine(
        title="The name of another container within the same task definition from which to mount volumes.",
        required=True,
    )

class IECSLogging(INamed, ICloudWatchLogRetention):
    "ECS Logging Configuration"
    driver = schema.Choice(
        title="Log Driver",
        description="One of awsfirelens, awslogs, fluentd, gelf, journald, json-file, splunk, syslog",
        vocabulary=vocabulary.ecs_log_drivers,
        required=True,
    )

class IECSTaskDefinitionSecret(IParent):
    """A Name/ValueFrom pair of Paco references to Secrets Manager secrets"""
    name = schema.TextLine(
        title="Name",
        required=True,
    )
    value_from = PacoReference(
        title="Paco reference to Secrets manager",
        required=True,
        str_ok=True
    )

class IECSContainerDependency(IParent):
    "ECS Container Dependency"
    container_name = schema.TextLine(
        title="Container Name",
        description="Must be an existing container name.",
        required=True,
    )
    condition = schema.Choice(
        title="Condition",
        description="Must be one of COMPLETE, HEALTHY, START or SUCCESS",
        required=True,
        vocabulary=vocabulary.ecs_container_conditions,
    )

class IDockerLabels(INamed, IMapping):
    taggedValue('contains', 'mixed')

class IECSHostEntry(IParent):
    "ECS Host Entry"
    hostname = schema.TextLine(
        title="Hostname",
        required=True,
    )
    ip_address = schema.TextLine(
        title="IP Address",
        required=True,
    )

class IECSHealthCheck(INamed):
    "ECS Health Check"
    command = schema.List(
        title="A string array representing the command that the container runs to determine if it is healthy. The string array must start with CMD to execute the command arguments directly, or CMD-SHELL to run the command with the container's default shell.",
        required=True,
        value_type=schema.TextLine(
            title="Command Part",
        )
    )
    retries = schema.Int(
        title="Retries",
        min=1,
        max=10,
        default=3,
        required=False,
    )
    timeout = schema.Int(
        title="The time period in seconds to wait for a health check to succeed before it is considered a failure.",
        min=2,
        max=60,
        default=5,
        required=False,
    )
    interval = schema.Int(
        title="The time period in seconds between each health check execution.",
        min=5,
        max=300,
        default=30,
        required=False,
    )
    start_period = schema.Int(
        title="The optional grace period within which to provide containers time to bootstrap before failed health checks count towards the maximum number of retries.",
        min=0,
        max=300,
        required=False,
    )

class IECSUlimit(IParent):
    "ECS Ulimit"
    name = schema.Choice(
        title="The type of the ulimit",
        vocabulary=vocabulary.ecs_ulimit,
        required=True,
    )
    hard_limit = schema.Int(
        title="The hard limit for the ulimit type.",
        required=True,
        min=1,
    )
    soft_limit = schema.Int(
        title="The soft limit for the ulimit type.",
        required=True,
        min=1,
    )

class IECSContainerDefinition(INamed):
    "ECS Container Definition"
    command = schema.List(
        title="Command (Docker CMD)",
        description="List of strings",
        value_type=schema.Text(),
        required=False,
    )
    depends_on = schema.List(
        title="Depends On",
        description="List of ECS Container Dependencies",
        value_type=schema.Object(IECSContainerDependency),
        required=False,
        default=[],
    )
    disable_networking = schema.Bool(
        title="Disable Networking",
        description="",
        required=False,
        default=False,
    )
    dns_search_domains = schema.List(
        title="List of DNS search domains. Maps to 'DnsSearch' in Docker.",
        required=False,
        default=[],
    )
    dns_servers = schema.List(
        title="List of DNS servers. Maps to 'Dns' in Docker.",
        required=False,
        default=[],
    )
    docker_labels = schema.Object(
        title="A key/value map of labels. Maps to 'Labels' in Docker.",
        required=False,
        schema=IDockerLabels,
    )
    docker_security_options = schema.List(
        title="List of custom labels for SELinux and AppArmor multi-level security systems.",
        description="Must be a list of no-new-privileges, apparmor:PROFILE, label:value, or credentialspec:CredentialSpecFilePath",
        value_type=schema.Choice(
            vocabulary=vocabulary.ecs_docker_security_options,
        ),
        required=False,
        default=[],
    )
    cpu = schema.Int(
        title="Cpu units",
        required=False,
    )
    entry_point = schema.List(
        title="Entry Pont (Docker ENTRYPOINT)",
        description="List of strings",
        value_type=schema.Text(),
        required=False,
    )
    environment = schema.List(
        title='List of environment name value pairs.',
        value_type=schema.Object(INameValuePair),
        required=False
    )
    essential = schema.Bool(
        title="Essential",
        required=False,
        default=False,
        # ToDo: constraint all tasks must have at least one essential
    )
    extra_hosts = schema.List(
        title="List of hostnames and IP address mappings to append to the /etc/hosts file on the container.",
        required=False,
        default=[],
        value_type=schema.Object(IECSHostEntry),
    )
    health_check = schema.Object(
        title="The container health check command and associated configuration parameters for the container. This parameter maps to 'HealthCheck' in Docker.",
        required=False,
        schema=IECSHealthCheck,
    )
    hostname = schema.TextLine(
        title="Hostname to use for your container. This parameter maps to 'Hostname' in Docker.",
        required=False,
    )
    image = PacoReference(
        title="The image used to start a container. This string is passed directly to the Docker daemon.",
        description="If a paco.ref is used to ECR, then the image_tag field will provide that tag used.",
        required=True,
        str_ok=True,
        schema_constraint='IECRRepository',
    )
    image_tag = schema.TextLine(
        title="Tag used for the ECR Repository Image",
        required=False,
        default="latest",
    )
    interactive = schema.Bool(
        title="When this parameter is true, this allows you to deploy containerized applications that require stdin or a tty to be allocated. This parameter maps to 'OpenStdin' in Docker.",
        required=False,
    )
    logging = schema.Object(
        title="Logging Configuration",
        schema=IECSLogging,
        required=False,
    )
    memory = schema.Int(
        title="The amount (in MiB) of memory to present to the container. If your container attempts to exceed the memory specified here, the container is killed.",
        min=4,
        required=False,
        # ToDo: constraints - required if no task-level memory, must be greater than memory_reservation
    )
    memory_reservation = schema.Int(
        title="The soft limit (in MiB) of memory to reserve for the container. When system memory is under heavy contention, Docker attempts to keep the container memory to this soft limit.",
        required=False,
        min=4,
    )
    mount_points = schema.List(
        title="The mount points for data volumes in your container.",
        value_type=schema.Object(IECSMountPoint),
        required=False,
    )
    port_mappings = schema.List(
        title="Port Mappings",
        value_type=schema.Object(IPortMapping),
        default=[],
        required=False,
    )
    privileged = schema.Bool(
        title="Give the container elevated privileges on the host container instance (similar to the root user).",
        required=False,
        default=False,
    )
    pseudo_terminal = schema.Bool(
        title="Allocate a TTY. This parameter maps to 'Tty' in Docker.",
        required=False,
    )
    readonly_root_filesystem = schema.Bool(
        title="Read-only access to its root file system. This parameter maps to 'ReadonlyRootfs' in Docker.",
        required=False,
    )
    start_timeout = schema.Int(
        title="Time duration (in seconds) to wait before giving up on resolving dependencies for a container.",
        min=1,
        default=300,
        required=False,
    )
    stop_timeout = schema.Int(
        title="Time duration (in seconds) to wait before the container is forcefully killed if it doesn't exit normally on its own.",
        min=1,
        max=120,
        default=30,
        required=False,
    )
    secrets = schema.List(
        title='List of name, value_from pairs to secret manager Paco references.',
        value_type=schema.Object(IECSTaskDefinitionSecret),
        required=False
    )
    ulimits =schema.List(
        title="List of ulimits to set in the container. This parameter maps to 'Ulimits' in Docker",
        value_type=schema.Object(IECSUlimit),
        required=False,
        default=[],
    )
    user = schema.TextLine(
        title="The user name to use inside the container. This parameter maps to 'User' in Docker.",
        required=False,
    )
    volumes_from = schema.List(
        title="Volumes to mount from another container (Docker VolumesFrom).",
        value_type=schema.Object(IECSVolumesFrom),
        default=[],
        required=False,
    )
    working_directory = schema.TextLine(
        title="The working directory in which to run commands inside the container. This parameter maps to 'WorkingDir' in Docker.",
        required=False,
    )

class IECSContainerDefinitions(INamed, IMapping):
    "Container for `ECSContainerDefinition`_ objects."
    taggedValue('contains', 'IECSContainerDefinition')

class IECSTaskDefinitions(INamed, IMapping):
    "Container for `ECSTaskDefinition`_ objects."
    taggedValue('contains', 'IECSTaskDefinition')

class IECSVolume(IParent):
    "ECS Volume"
    # docker_volume_configuration
    # host
    name = schema.TextLine(
        title="Name",
        min_length=1,
        max_length=255,
        required=True,
        # ToDo: constraint: only letters (uppercase and lowercase), numbers, and hyphens are allowed
    )

class IECSTaskDefinition(INamed):
    "ECS Task Definition"
    container_definitions = schema.Object(
        title="Container Definitions",
        schema=IECSContainerDefinitions,
        required=True,
    )
    volumes = schema.List(
        title="Volume definitions for the task",
        value_type=schema.Object(IECSVolume),
        default=[],
        required=False,
    )
    network_mode = schema.Choice(
        title="Network Mode",
        vocabulary=vocabulary.ecs_network_modes,
        description="Must be one of awsvpc, bridge, host or none",
        required=False,
        default='bridge',
    )

class IECSLoadBalancer(INamed):
    "ECS Load Balancer"
    container_name = schema.TextLine(
        title="Container Name",
        # ToDO: constraint for valid task def container definition name
    )
    container_port = schema.Int(
        title="Container Port",
        min=0,
        max=65535,
        required=True,
    )
    target_group = PacoReference(
        title="Target Group",
        required=True,
        schema_constraint="ITargetGroup"
    )

class IECSServicesContainer(IMapping):
    "Container for `ECSService`_ objects."
    taggedValue('contains', 'IECSService')

class IECSService(INamed):
    "ECS Service"
    deployment_controller = schema.Choice(
        title="Deployment Controller",
        vocabulary=vocabulary.ecs_deployment_types,
        description="One of ecs, code_deploy or external",
        default='ecs',
        required=False,
    )
    deployment_minimum_healthy_percent = schema.Int(
        title="Deployment Minimum Healthy Percent",
        min=1,
        max=100,
        required=False,
        default=100,
    )
    deployment_maximum_percent = schema.Int(
        title="Deployment Maximum Percent",
        min=1,
        required=False,
        default=200,
    )
    desired_count = schema.Int(
        title="Desried Count",
        min=0,
        required=False,
        # ToDo: constraint require if schedulingStrategy=REPLICA
    )
    health_check_grace_period_seconds = schema.Int(
        title="Health Check Grace Period (seconds)",
        min=0,
        max=2147483647,
        required=False,
        default=0,
    )
    task_definition = schema.TextLine(
        title="Task Definition",
        required=False,
        # ToDo: constraint for valid task def name
        # ToDo: constraint if using ECS deployment controller
    )
    load_balancers = schema.List(
        title="Load Balancers",
        value_type=schema.Object(IECSLoadBalancer),
        required=False,
        default=[],
    )
    hostname = schema.TextLine(
        title="Container hostname",
        required=False
    )

class IECSCluster(IResource):
    """
ECS Cluster
    """

class IECSServices(IResource):
    """
ECS Services and TaskDefinitions
    """
    cluster = PacoReference(
        title='Cluster',
        required=True,
        str_ok=False,
        schema_constraint='IECSCluster'
    )
    task_definitions = schema.Object(
        title="Task Definitions",
        description="",
        schema=IECSTaskDefinitions,
        required=True,
    )
    services = schema.Object(
        title="Service",
        description="",
        schema=IECSServicesContainer,
        required=True,
    )
    service_discovery_namespace_name = schema.TextLine(
        title="Service Discovery Namespace",
        description="",
        required=False,
        default='',
    )
    secrets_manager_access = schema.List(
        title="List Secrets Manager secret Paco references",
        description="",
        value_type=PacoReference(
            title="SecretsManagerSecret",
            schema_constraint='ISecretsManagerSecret',
        ),
        required=False
    )

# ECR: Elastic Container Repository
class IECRRepository(IResource):
    """
Elastic Container Registry (ECR) Repository is a fully-managed Docker container registry.


.. sidebar:: Prescribed Automation

    ``cross_account_access``: Adds a Repository Policy that grants full access to the listed AWS Accounts.

.. code-block:: yaml
    :caption: Example ECRRepository

    type: ECRRepository
    enabled: true
    order: 10
    repository_name: 'ecr-example'
    cross_account_access:
      - paco.ref accounts.dev
      - paco.ref accounts.tools

"""
    cross_account_access = schema.List(
        title="Accounts to grant access to this ECR.",
        description="",
        value_type=PacoReference(
            title="Account Reference",
            schema_constraint='IAccount'
        ),
        required=False,
    )
    repository_name = schema.TextLine(
        title="Repository Name",
        required=True,
    )
    lifecycle_policy_text = schema.TextLine(
        title="Lifecycle Policy",
        required=False,
    )
    lifecycle_policy_registry_id = schema.TextLine(
        title="Lifecycle Policy Registry Id",
        required=False,
    )
    repository_policy = schema.Object(
        title="Repository Policy",
        schema=IPolicy,
        required=False,
    )
    account = PacoReference(
        title="Account the ECR Repository belongs to",
        required=False,
        schema_constraint='IAccount',
    )

# IoT Analytics

# Different from ICloudWatchLogRetention.expire_events_after_days in that it is
# not constrained to fixed periods - this can be any X number of days. If set
# to 0 then it will be considered 'Unlimited' by IoC Analytics Storage.
class IStorageRetention(Interface):
    expire_events_after_days = schema.Int(
        title="Expire Events After Days",
        description="Must be 1 or greater. If set to an explicit 0 then it is considered unlimited.",
        default=0,
        required=False,
    )

class IIotAnalyticsStorage(INamed, IStorageRetention):
    @invariant
    def is_either_customer_or_service(obj):
        "Validate that either customer or service options are set."
        if (obj.bucket != None and obj.key_prefix == '') or (obj.bucket == None and obj.key_prefix != ''):
            raise Invalid("Must set both bucket and key_prefix for customer managed storage bucket.")
        if obj.expire_events_after_days > 0:
            if obj.bucket != None or obj.key_prefix != '':
                raise Invalid("Can not set expire_events_after_days for a customer managed S3 Bucket")

    bucket = PacoReference(
        title='S3 Bucket',
        required=False,
        schema_constraint='IS3Bucket'
    )
    key_prefix = schema.TextLine(
        title="Key Prefix for S3 Bucket",
        required=False,
        default="",
        constraint=isValidStorageKeyPrefix,
    )

class IAttributes(INamed, IMapping):
    """
Dictionary of Attributes
    """
    taggedValue('contains', 'mixed')

class IIoTPipelineActivity(INamed):
    """
Each activity must have an ``activity_type`` and supply fields specific for that type.
There is an implicit Channel activity before all other activities and an an implicit Datastore
activity after all other activities.

.. code-block:: yaml
    :caption: All example types for IoTAnalyticsPipeline pipeline_activities

    activity_type: lambda
    batch_size: 1
    function: paco.ref netenv.mynet[...]mylambda

    activity_type: add_attributes
    attributes:
      key1: hello
      key2: world

    activity_type: remove_attributes
    attribute_list:
      - key1
      - key2

    activity_type: select_attributes
    attribute_list:
      - key1
      - key2

    activity_type: filter
    filter: "attribute1 > 40 AND attribute2 < 20"

    activity_type: math
    attribute: "attribute1"
    math: "attribute1 - 10"

    activity_type: device_registry_enrich
    attribute: "attribute1"
    thing_name: "mything"

    activity_type: device_shadow_enrich
    attribute: "attribute1"
    thing_name: "mything"

"""
    @invariant
    def is_correct_type_schema(obj):
        "Validate that fields are set for the activity_type"
        field_types = {
            'lambda': {
                'batch_size': False,
                'function': True,
            },
            'add_attributes': {
                'attributes': True,
            },
            'remove_attributes': {
                'attribute_list': True,
            },
            'select_attributes': {
                'attribute_list': True,
            },
            'filter': {
                'filter': True,
            },
            'math': {
                'attribute': True,
                'math': True,
            },
            'device_registry_enrich': {
                'attribute': True,
                'thing_name': True,
            },
            'device_shadow_enrich': {
                'attribute': True,
                'thing_name': True,
            },
        }
        field_list = [
            'attributes',
            'attribute_list',
            'attribute',
            'batch_size',
            'filter',
            'function',
            'math',
            'thing_name',
        ]
        allowed = field_types[obj.activity_type]
        for field in field_list:
            if field not in allowed:
                if getattr(obj, field, None):
                    raise Invalid(f"Activity {obj.name} of activity_type: {obj.activity_type} has inapplicable field '{field}'.")
            else:
                if not getattr(obj, field, None) and allowed[field] == True:
                    raise Invalid(f"Activity {obj.name} of activity_type: {obj.activity_type} is missing field '{field}'.")

    activity_type = schema.TextLine(
        title='Activity Type',
        required=True,
    )
    attributes = schema.Object(
        title="Attributes",
        required=False,
        schema=IAttributes,
    )
    attribute_list = schema.List(
        title="Attribute List",
        required=False,
    )
    attribute = schema.TextLine(
        title="Attribute",
        required=False,
    )
    batch_size = schema.Int(
        title="Batch Size",
        min=1,
        max=1000,
        required=False,
    )
    filter = schema.TextLine(
        title="Filter",
        required=False,
    )
    function = PacoReference(
        title='Lambda function',
        required=False,
        schema_constraint='ILambda'
    )
    math = schema.TextLine(
        title="Math",
        required=False,
    )
    thing_name = schema.TextLine(
        title="Thing Name",
        required=False,
    )

class IIoTPipelineActivities(INamed, IMapping):
    "Container for `IoTPipelineActivity`_ objects."
    taggedValue('contains', 'IIoTPipelineActivity')

class IDatasetVariable(INamed):
    double_value = schema.Float(
        title="Double Value",
        required=False,
    )
    output_file_uri_value = schema.TextLine(
        title="Output file URI value",
        description="The URI of the location where dataset contents are stored, usually the URI of a file in an S3 bucket.",
        required=False,
    )
    string_value = schema.Text(
        title="String Value",
        required=False,
    )

class IDatasetVariables(INamed, IMapping):
    "Container for `DatasetVariables`_ objects."
    taggedValue('contains', 'IDatasetVariables')

class IDatasetContainerAction(INamed):
    image_arn = schema.TextLine(
        title="Image ARN",
        required=True,
    )
    resource_compute_type = schema.Choice(
        title="Resource Compute Type",
        vocabulary=vocabulary.iot_dataset_container_types,
        description="Either ACU_1 (vCPU=4, memory=16 GiB) or ACU_2 (vCPU=8, memory=32 GiB)",
        required=True,
    )
    resource_volume_size_gb = schema.Int(
        title="Resource Volume Size in GB",
        min=1,
        max=50,
        required=True
    )
    variables = schema.Object(
        title="Variables",
        schema=IDatasetVariables,
        required=True,
    )

class IDatasetQueryAction(INamed):
    filters = schema.List(
        title="Filters",
        required=False,
        default=[],
    )
    sql_query = schema.TextLine(
        title="Sql Query Dataset Action object",
        required=True,
    )

class IDatasetS3Destination(IParent):
    bucket = PacoReference(
        title='S3 Bucket',
        required=True,
        schema_constraint='IS3Bucket'
    )
    key = schema.TextLine(
        title="Key",
        required=True,
    )

class IDatasetContentDeliveryRule(INamed):
    s3_destination = schema.Object(
        title="S3 Destination",
        required=False,
        schema=IDatasetS3Destination,
    )

class IDatasetContentDeliveryRules(INamed, IMapping):
    "Container for `DatasetContentDeliveryRule`_ objects."
    taggedValue('contains', 'IDatasetContentDeliveryRule')

class IDatasetTrigger(IParent):
    schedule_expression = schema.TextLine(
        title="Schedule Expression",
        required=False,
    )
    triggering_dataset = schema.TextLine(
        title="Triggering Dataset",
        required=False
    )

class IIoTDataset(INamed, IStorageRetention):
    container_action = schema.Object(
        title="Dataset Container action",
        required=False,
        schema=IDatasetContainerAction,
    )
    query_action = schema.Object(
        title="SQL Query action",
        required=False,
        schema=IDatasetQueryAction,
    )
    content_delivery_rules = schema.Object(
        title="Content Delivery Rules",
        schema=IDatasetContentDeliveryRules,
        required=False,
    )
    triggers = schema.List(
        title="Triggers",
        value_type=schema.Object(IDatasetTrigger),
        required=False,
        default=[],
    )
    version_history = schema.Int(
        title="How many versions of dataset contents are kept. 0 indicates Unlimited. If not specified or set to null, only the latest version plus the latest succeeded version (if they are different) are kept for the time period specified by expire_events_after_days field.",
        min=0,
        max=1000,
        required=False,
    )

class IIoTDatasets(INamed, IMapping):
    "Container for `IoTDataset`_ objects."
    taggedValue('contains', 'IIoTDataset')

class IIoTAnalyticsPipeline(IResource, IMonitorable):
    """
An IoTAnalyticsPipeline composes four closely related resources: IoT Analytics Channel, IoT Analytics Pipeline,
IoT Analytics Datastore and IoT Analytics Dataset.

An IoT Analytics Pipeline begins with a Channel. A Channel is an S3 Bucket of raw incoming messages.
A Channel provides an ARN that an IoTTopicRule can send MQTT messages to. These messages can later be re-processed
if the analysis pipeline changes. Use the ``channel_storage`` field to configure the Channel storage.

Next the Pipeline applies a series of ``pipeline_activities`` to the incoming Channel messages. After any message
modifications have been made, they are stored in a Datastore.

A Datastore is S3 Bucket storage of messages that are ready to be analyzed. Use the ``datastore_storage`` field to configure
the Datastore storage. The ``datastore_name`` is an optional field to give your Datastore a fixed name, this can
be useful if you use Dataset SQL Query analysis which needs to use the Datastore name in a SELECT query. However,
if you use ``datastore_name`` it doesn't vary by Environment - if you use name then it is recommended to use different
Regions and Accounts for each IoTAnalytics environment.

Lastly the Datastore can be analyzed and have the resulting output saved as a Dataset. There may be multiple Datasets
to create different analysis of the data. Datasets can be analyzed on a managed host running a Docker container or
with an SQL Query to create subsets of a Datastore suitable for analysis with tools such as AWS QuickSight.

.. sidebar:: Prescribed Automation

    **IoTAnalyticsPipeline Role** Every IoTAnalyticsPipeline has an IAM Role associated with it. This Role will
    have access to every S3 Bucket that is referenced by a Channel, Datastore or Dataset.

    ``pipeline_activities``: Every list of activities beings with an implicit Channel activity and ends with a
    Datastore activity.


.. code-block:: yaml
    :caption: example IoTAnalyticsPipeline configuration

    type: IoTAnalyticsPipeline
    title: My IoT Analytics Pipeline
    order: 100
    enabled: true
    channel_storage:
      bucket: paco.ref netenv.mynet.applications.app.groups.iot.resources.iotbucket
      key_prefix: raw_input/
    pipeline_activities:
      adddatetime:
        activity_type: lambda
        function: paco.ref netenv.mynet.applications.app.groups.iot.resources.iotfunc
        batch_size: 10
      filter:
        activity_type: filter
        filter: "temperature > 0"
    datastore_name: example
    datastore_storage:
      expire_events_after_days: 30
    datasets:
      hightemp:
        query_action:
          sql_query: "SELECT * FROM example WHERE temperature > 20"
        content_delivery_rules:
          s3temperature:
            s3_destination:
              bucket: paco.ref netenv.mynet.applications.app.groups.iot.resources.iotbucket
              key: "/HighTemp/!{iotanalytics:scheduleTime}/!{iotanalytics:versionId}.csv"
        expire_events_after_days: 3
        version_history: 5

    """
    channel_storage = schema.Object(
        title="IoT Analytics Channel raw storage",
        schema=IIotAnalyticsStorage,
        required=False,
    )
    datastore_name = schema.TextLine(
        title="Datastore name",
        required=False,
    )
    datastore_storage = schema.Object(
        title="IoT Analytics Datastore storage",
        schema=IIotAnalyticsStorage,
        required=False,
    )
    pipeline_activities = schema.Object(
        title="IoT Analytics Pipeline Activies",
        schema=IIoTPipelineActivities,
        required=False
    )
    datasets = schema.Object(
        title="IoT Analytics Datasets",
        schema=IIoTDatasets,
        required=True,
    )

# IoT Core

class IIoTVariables(INamed, IMapping):
    taggedValue('contains', 'mixed')

class IIoTPolicy(IResource):
    """An IoT Policy is a special IoT-specific Policy that grants IoT Things the
ability to perform operations on IoT resources.

The ``policy_json`` is a file containing a valid JSON IoT Policy document.

The ``variables`` field contains variables available for replacement in the document.
The special variable names ``AWS::Region`` and ``AWS::AccountId`` will be replaced by the
region name and account id where the resource belongs. Any variable name with a ``:`` character
in it will not be replace, so that all IoT Policy Variables can be used.

.. code-block:: yaml
    :caption: example IoTPolicy

    type: IoTPolicy
    enabled: true
    order: 100
    policy_json: ./iot-policy.json
    variables:
      connect_action: "iot:Connect"
      sensor_topic_arn: paco.ref netenv.anet.applications.iotapp.groups.app.resources.iottopic.arn

.. code-block:: yaml
    :caption: Example ./iot-policy.json policy_json file

    {
        "Version": "2012-10-17",
        "Statement": [
            { "Effect": "Allow",
              "Action": [ "${connect_action}" ],
              "Resource": [  "arn:aws:iot:${AWS::Region}:${AWS::AccountId}:client/${iot:Connection.Thing.ThingName}" ]
            },
            { "Effect": "Allow",
              "Action": [ "iot:Publish" ],
              "Resource": [ "${sensor_topic_arn}" ]
            }
        ]
    }

"""
    policy_json = StringFileReference(
        title="IoT Policy document.",
        required=True,
        constraint=isValidJSONOrNone
    )
    variables = schema.Dict(
        title="IoT Policy replacement variables",
        default={},
        required=False
    )

class IIoTTopicRuleLambdaAction(IParent):
    function = PacoReference(
        title='Lambda function',
        required=True,
        schema_constraint='ILambda'
    )

class IIoTTopicRuleIoTAnalyticsAction(IParent):
    pipeline = PacoReference(
        title='IoT Analytics pipeline',
        required=True,
        schema_constraint='IIoTAnalyticsPipeline'
    )

class IIoTTopicRuleAction(IParent):
    awslambda = schema.Object(
        title="Lambda Action",
        required=False,
        schema=IIoTTopicRuleLambdaAction,
    )
    iotanalytics = schema.Object(
        title="IoT Analytics Action",
        required=False,
        schema=IIoTTopicRuleIoTAnalyticsAction,
    )

class IIoTTopicRule(IResource, IMonitorable):
    """
IoTTopicRule allows you to create a list of actions that will be triggered from a
MQTT message coming in to IoT Core.

.. sidebar:: Prescribed Automation

    **IoTTopicRule Role** Every IoTTopicRule will have a Role created that it can assume to perform any actions
    that it has. For example, it will be allowed to call a Lambda or an IoTAnalyticsPipeline.

.. code-block:: yaml
    :caption: example IoTTopicRule configuration

    type: IoTTopicRule
    title: Rule to take action for MQTT messages sent to 'sensor/example'
    order: 20
    enabled: true
    actions:
      - awslambda:
          function: paco.ref netenv.mynet.applications.app.groups.app.resources.iotlambda
      - iotanalytics:
          pipeline: paco.ref netenv.mynet.applications.app.groups.app.resources.analyticspipeline
    aws_iot_sql_version: '2016-03-23'
    rule_enabled: true
    sql: "SELECT * FROM 'sensor/example'"

"""
    actions = schema.List(
        title="Actions",
        description="An IoTTopicRule must define at least one action.",
        required=True,
        value_type=schema.Object(IIoTTopicRuleAction),
        default=[],
    )
    aws_iot_sql_version = schema.TextLine(
        title="AWS IoT SQL Version",
        default="2016-03-23",
        required=False,
    )
    rule_enabled = schema.Bool(
        title="Rule is Enabled",
        default=True,
        required=False,
    )
    sql = schema.Text(
        title="SQL statement used to query the topic",
        description="Must be a valid Sql statement",
        required=True
    )

# Lambda

class ILambdaVariable(IParent):
    """
    Lambda Environment Variable
    """
    key = schema.TextLine(
        title='Variable Name',
        required=True,
        constraint=isValidLambdaVariableName
    )
    value = PacoReference(
        title='String Value or a Paco Reference to a resource output',
        required=True,
        str_ok=True,
        schema_constraint='Interface'
    )

class ILambdaEnvironment(IParent):
    """
Lambda Environment
    """
    variables = schema.List(
        title="Lambda Function Variables",
        value_type=schema.Object(ILambdaVariable),
        required=False,
    )

class ILambdaFunctionCode(IParent):
    """The deployment package for a Lambda function."""

    @invariant
    def is_either_s3_or_zipfile(obj):
        "Validate that either zipfile or s3 bucket is set."
        if obj.zipfile == None and not (obj.s3_bucket and obj.s3_key):
            raise Invalid("Either zipfile or s3_bucket and s3_key must be set. Or zipfile file is an empty file.")
        if obj.zipfile and obj.s3_bucket:
            raise Invalid("Can not set both zipfile and s3_bucket")
        if obj.zipfile and len(obj.zipfile) > 4096:
            raise Invalid("Too bad, so sad. Limit of inline code of 4096 characters exceeded. File is {} chars long.".format(len(obj.zipfile)))

    zipfile = LocalPath(
        title="The function code as a local file or directory.",
        description="Maximum of 4096 characters.",
        required=False,
    )
    s3_bucket = PacoReference(
        title="An Amazon S3 bucket in the same AWS Region as your function",
        required=False,
        str_ok=True,
        schema_constraint='IS3Bucket'
    )
    s3_key = schema.TextLine(
        title="The Amazon S3 key of the deployment package.",
        required=False,
    )


class ILambdaVpcConfig(INamed):
    """
Lambda Environment
    """
    segments = schema.List(
        title="VPC Segments to attach the function",
        description="",
        value_type=PacoReference(
            title="Segment",
            schema_constraint='ISegment',
        ),
        required=False
    )
    security_groups = schema.List(
        title="List of VPC Security Group Ids",
        value_type=PacoReference(
            schema_constraint='ISecurityGroup'
        ),
        required=False
    )

class ILambda(IResource, ICloudWatchLogRetention, IMonitorable):
    """
Lambda Functions allow you to run code without provisioning servers and only
pay for the compute time when the code is running.

The code for the Lambda function can be specified in one of three ways in the ``code:`` field:

 * S3 Bucket artifact: Supply an``s3_bucket`` and ``s3_key`` where you have an existing code artifact file.

 * Local file: Supply the ``zipfile`` as a path to a local file on disk. This will be inlined into
   CloudFormation and has a size limitation of only 4 Kb.

 * Local directory: Supply the ``zipfile`` as a path to a directory on disk. This directory will be packaged
   into a zip file and Paco will create an S3 Bucket where it will upload and manage Lambda deployment artifacts.

.. code-block:: yaml
    :caption: Lambda code from S3 Bucket or local disk

    code:
        s3_bucket: my-bucket-name
        s3_key: 'myapp-1.0.zip'

    code:
        zipfile: ./lambda-dir/my-lambda.py

    code:
        zipfile: ~/code/my-app/lambda_target/

.. sidebar:: Prescribed Automation

    ``expire_events_after_days``: Sets the Retention for the Lambda execution Log Group.

    ``log_group_names``: Creates CloudWatch Log Group(s) prefixed with '<env>-<appname>-<groupname>-<lambdaname>-'
    (or for Environment-less applications like Services it will be '<appname>-<groupname>-<lambdaname>-')
    and grants permission for the Lambda role to interact with those Log Group(s). The ``expire_events_after_days``
    field will set the Log Group retention period. Paco will also add a comma-seperated Environment Variable
    named PACO_LOG_GROUPS to the Lambda with the expanded names of the Log Groups.

    ``sdb_cache``: Create a SimpleDB Domain and IAM Policy that grants full access to that domain. Will
    also make the domain available to the Lambda function as an environment variable named ``SDB_CACHE_DOMAIN``.

    ``sns_topics``: Subscribes the Lambda to SNS Topics. For each Paco reference to an SNS Topic,
    Paco will create an SNS Topic Subscription so that the Lambda function will recieve all messages sent to that SNS Topic.
    It will also create a Lambda Permission granting that SNS Topic the ability to publish to the Lambda.

    **Lambda Permissions** Paco will check all resources in the Application for any: S3Bucket configured
    to notify this Lambda, EventsRule to invoke this Lambda, IoTAnalyticsPipeline activities to invoke this Lambda.
    These resources will automatically gain a Lambda Permission to be able to invoke the Lambda.

.. code-block:: yaml
    :caption: Lambda function resource YAML

    type: Lambda
    enabled: true
    order: 1
    title: 'My Lambda Application'
    description: 'Checks the Widgets Service and applies updates to a Route 53 Record Set.'
    code:
        s3_bucket: my-bucket-name
        s3_key: 'myapp-1.0.zip'
    environment:
        variables:
        - key: 'VAR_ONE'
          value: 'hey now!'
        - key: 'VAR_TWO'
          value: 'Hank Kingsley'
    iam_role:
        enabled: true
        policies:
          - name: DNSRecordSet
            statement:
              - effect: Allow
                action:
                  - route53:ChangeResourceRecordSets
                resource:
                  - 'arn:aws:route53:::hostedzone/AJKDU9834DUY934'
    handler: 'myapp.lambda_handler'
    memory_size: 128
    runtime: 'python3.7'
    timeout: 900
    expire_events_after_days: 90
    log_group_names:
      - AppGroupOne
    sns_topics:
      - paco.ref netenv.app.applications.app.groups.web.resources.snstopic
    vpc_config:
        segments:
          - paco.ref netenv.app.network.vpc.segments.public
        security_groups:
          - paco.ref netenv.app.network.vpc.security_groups.app.function

"""
    code = schema.Object(
        title="The function deployment package.",
        schema=ILambdaFunctionCode,
        required=True,
    )
    description=schema.TextLine(
        title="A description of the function.",
        required=True,
    )
    environment = schema.Object(
        title="Lambda Function Environment",
        schema=ILambdaEnvironment,
        default=None,
        required=False,
    )
    iam_role = schema.Object(
        title="The IAM Role this Lambda will execute as.",
        required=True,
        schema=IRole,
    )
    layers = schema.List(
        title="Layers",
        value_type=schema.TextLine(),
        description="Up to 5 Layer ARNs",
        constraint=isListOfLayerARNs
    )
    log_group_names = schema.List(
        title="Log Group names",
        value_type=schema.TextLine(),
        description="List of Log Group names",
        required=False,
        default=[]
    )
    handler = schema.TextLine(
        title="Function Handler",
        required=True,
    )
    memory_size = schema.Int(
        title="Function memory size (MB)",
        min=128,
        max=3008,
        default=128,
        required=False,
    )
    reserved_concurrent_executions = schema.Int(
        title="Reserved Concurrent Executions",
        default=0,
        required=False,
    )
    runtime = schema.TextLine(
        title="Runtime environment",
        required=True,
        # dotnetcore1.0 | dotnetcore2.1 | go1.x | java8 | nodejs10.x | nodejs8.10 | provided | python2.7 | python3.6 | python3.7 | ruby2.5
        default='python3.7',
    )
    # The amount of time that Lambda allows a function to run before stopping it. The default is 3 seconds. The maximum allowed value is 900 seconds.
    timeout = schema.Int(
        title="Max function execution time in seconds.",
        description="Must be between 0 and 900 seconds.",
        min=0,
        max=900,
        required=False,
    )
    sdb_cache = schema.Bool(
        title="SDB Cache Domain",
        required=False,
        default=False,
    )
    sns_topics = schema.List(
        title="List of SNS Topic Paco references or SNS Topic ARNs to subscribe the Lambda to.",
        value_type=PacoReference(
            str_ok=True,
            schema_constraint='ISNSTopic'
        ),
        required=False,
    )
    vpc_config = schema.Object(
        title="Vpc Configuration",
        required=False,
        schema=ILambdaVpcConfig
    )

# API Gateway

class IApiGatewayMethodMethodResponseModel(Interface):
    content_type = schema.TextLine(
        title="Content Type",
        required=False,
    )
    model_name = schema.TextLine(
        title="Model name",
        default="",
        required=False,
    )

class IApiGatewayMethodMethodResponse(Interface):
    status_code = schema.TextLine(
        title="HTTP Status code",
        description="",
        required=True,
    )
    response_models = schema.List(
        title="The resources used for the response's content type.",
        description="""Specify response models as key-value pairs (string-to-string maps),
with a content type as the key and a Model Paco name as the value.""",
        value_type=schema.Object(title="Response Model", schema = IApiGatewayMethodMethodResponseModel),
        required=False,
    )

class IApiGatewayMethodIntegrationResponse(Interface):
    content_handling = schema.TextLine(
        title="Specifies how to handle request payload content type conversions.",
        description="""Valid values are:

CONVERT_TO_BINARY: Converts a request payload from a base64-encoded string to a binary blob.

CONVERT_TO_TEXT: Converts a request payload from a binary blob to a base64-encoded string.

If this property isn't defined, the request payload is passed through from the method request
to the integration request without modification.
""",
        required=False
    )
    response_parameters = schema.Dict(
        title="Response Parameters",
        default={},
        required=False,
    )
    response_templates = schema.Dict(
        title="Response Templates",
        default={},
        required=False,
    )
    selection_pattern = schema.TextLine(
        title="A regular expression that specifies which error strings or status codes from the backend map to the integration response.",
        required=False,
    )
    status_code = schema.TextLine(
        title="The status code that API Gateway uses to map the integration response to a MethodResponse status code.",
        description  = "Must match a status code in the method_respones for this API Gateway REST API.",
        required=True,
    )

class IApiGatewayMethodIntegration(IParent):
    integration_responses = schema.List(
        title="Integration Responses",
        value_type=schema.Object(IApiGatewayMethodIntegrationResponse),
        required=False,
    )
    request_parameters = schema.Dict(
        title="The request parameters that API Gateway sends with the backend request.",
        description="""Specify request parameters as key-value pairs (string-to-string mappings),
with a destination as the key and a source as the value. Specify the destination by using the
following pattern `integration.request.location.name`, where `location` is query string, path,
or header, and `name` is a valid, unique parameter name.

The source must be an existing method request parameter or a static value. You must
enclose static values in single quotation marks and pre-encode these values based on
their destination in the request.
        """,
        default={},
        required=False,
    )
    integration_http_method = schema.TextLine(
        title="Integration HTTP Method",
        description="Must be one of ANY, DELETE, GET, HEAD, OPTIONS, PATCH, POST or PUT.",
        default="POST",
        constraint = isValidHttpMethod,
        required=False,
    )
    integration_type = schema.TextLine(
        title="Integration Type",
        description="Must be one of AWS, AWS_PROXY, HTTP, HTTP_PROXY or MOCK.",
        constraint = isValidApiGatewayIntegrationType,
        default="AWS",
        required=True,
    )
    integration_lambda = PacoReference(
        title="Integration Lambda",
        required=False,
        schema_constraint='ILambda'
    )
    uri = schema.TextLine(
        title="Integration URI",
        required=False,
    )


class IApiGatewayMethod(IResource):
    "API Gateway Method"
    authorization_type = schema.TextLine(
        title="Authorization Type",
        description="Must be one of NONE, AWS_IAM, CUSTOM or COGNITO_USER_POOLS",
        constraint = isValidApiGatewayAuthorizationType,
        required=True,
    )
    http_method = schema.TextLine(
        title="HTTP Method",
        description="Must be one of ANY, DELETE, GET, HEAD, OPTIONS, PATCH, POST or PUT.",
        constraint = isValidHttpMethod,
        required=False,
    )
    resource_id = schema.TextLine(
        title="Resource Id",
        required=False,
    )
    integration = schema.Object(
        title="Integration",
        schema = IApiGatewayMethodIntegration,
        required=False,
    )
    method_responses = schema.List(
        title="Method Responses",
        description="List of ApiGatewayMethod MethodResponses",
        value_type=schema.Object(IApiGatewayMethodMethodResponse),
        required=False,
    )
    request_parameters = schema.Dict(
        title="Request Parameters",
        description="""Specify request parameters as key-value pairs (string-to-Boolean mapping),
        with a source as the key and a Boolean as the value. The Boolean specifies whether
        a parameter is required. A source must match the format method.request.location.name,
        where the location is query string, path, or header, and name is a valid, unique parameter name.""",
        default={},
        required=False,
    )

class IApiGatewayModel(IResource):
    content_type = schema.TextLine(
        title="Content Type",
        required=False,
    )
    description=schema.Text(
        title="Description",
        required=False,
    )
    schema = schema.Dict(
        title="Schema",
        description='JSON format. Will use null({}) if left empty.',
        default={},
        required=False,
    )

class IApiGatewayResource(IResource):
    parent_id = schema.TextLine(
        title="Id of the parent resource. Default is 'RootResourceId' for a resource without a parent.",
        default="RootResourceId",
        required=False,
    )
    path_part = schema.TextLine(
        title="Path Part",
        required=True,
    )
    rest_api_id = schema.TextLine(
        title="Name of the API Gateway REST API this resource belongs to.",
        readonly = True,
    )

class IApiGatewayStage(IResource):
    "API Gateway Stage"
    deployment_id = schema.TextLine(
        title="Deployment ID",
        required=False,
    )
    description=schema.Text(
        title="Description",
        required=False,
    )
    stage_name = schema.TextLine(
        title="Stage name",
        required=False,
    )

class IApiGatewayModels(INamed, IMapping):
    "Container for `ApiGatewayModel`_ objects."
    taggedValue('contains', 'IApiGatewayModel')

class IApiGatewayMethods(INamed, IMapping):
    "Container for `ApiGatewayMethod`_ objects."
    taggedValue('contains', 'IApiGatewayMethod')

class IApiGatewayResources(INamed, IMapping):
    "Container for `ApiGatewayResource`_ objects."
    taggedValue('contains', 'IApiGatewayResource')

class IApiGatewayStages(INamed, IMapping):
    "Container for `ApiGatewayStage`_ objects"
    taggedValue('contains', 'IApiGatewayStages')

class IApiGatewayRestApi(IResource):
    """
An Api Gateway Rest API resource.

Intended to allow provisioning of all API Gateway REST API resources (currently only parital field support).

.. code-block:: yaml
    :caption: API Gateway REST API example

    type: ApiGatewayRestApi
    order: 10
    enabled: true
    fail_on_warnings: true
    description: "My REST API"
    endpoint_configuration:
      - 'REGIONAL'
    models:
      emptyjson:
        content_type: 'application/json'
    methods:
      get:
        http_method: GET
        integration:
          integration_type: AWS
          integration_lambda: paco.ref netenv.mynet.applications.app.groups.restapi.resources.mylambda
          integration_responses:
            - status_code: '200'
              response_templates:
                'application/json': ''
          request_parameters:
            "integration.request.querystring.my_id": "method.request.querystring.my_id"
        authorization_type: NONE
        request_parameters:
          "method.request.querystring.my_id": false
          "method.request.querystring.token": false
        method_responses:
          - status_code: '200'
            response_models:
              - content_type: 'application/json'
                model_name: 'emptyjson'
      post:
        http_method: POST
        integration:
          integration_type: AWS
          integration_lambda: paco.ref netenv.mynet.applications.app.groups.restapi.resources.mylambda
          integration_responses:
            - status_code: '200'
              response_templates:
                'application/json': ''
        authorization_type: NONE
        method_responses:
          - status_code: '200'
            response_models:
              - content_type: 'application/json'
                model_name: 'emptyjson'
    stages:
      prod:
        deployment_id: 'prod'
        description: 'Prod Stage'
        stage_name: 'prod'

    """
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
        title="API Key Source Type",
        description="Must be one of 'HEADER' to read the API key from the X-API-Key header of a request or 'AUTHORIZER' to read the API key from the UsageIdentifierKey from a Lambda authorizer.",
        constraint = isValidApiKeySourceType,
        required=False,
    )
    binary_media_types = schema.List(
        title="Binary Media Types. The list of binary media types that are supported by the RestApi resource, such as image/png or application/octet-stream. By default, RestApi supports only UTF-8-encoded text payloads.",
        description="Duplicates are not allowed. Slashes must be escaped with ~1. For example, image/png would be image~1png in the BinaryMediaTypes list.",
        constraint = isValidBinaryMediaTypes,
        value_type=schema.TextLine(
            title="Binary Media Type"
        ),
        required=False,
    )
    body = schema.Text(
        title="Body. An OpenAPI specification that defines a set of RESTful APIs in JSON or YAML format. For YAML templates, you can also provide the specification in YAML format.",
        description="Must be valid JSON.",
        required=False,
    )
    body_file_location = StringFileReference(
        title="Path to a file containing the Body.",
        description="Must be valid path to a valid JSON document.",
        required=False,
    )
    body_s3_location = schema.TextLine(
        title="The Amazon Simple Storage Service (Amazon S3) location that points to an OpenAPI file, which defines a set of RESTful APIs in JSON or YAML format.",
        description="Valid S3Location string to a valid JSON or YAML document.",
        required=False,
    )
    clone_from = schema.TextLine(
        title="CloneFrom. The ID of the RestApi resource that you want to clone.",
        required=False,
    )
    description=schema.Text(
        title="Description of the RestApi resource.",
        required=False,
    )
    endpoint_configuration = schema.List(
        title="Endpoint configuration. A list of the endpoint types of the API. Use this field when creating an API. When importing an existing API, specify the endpoint configuration types using the `parameters` field.",
        description="List of strings, each must be one of 'EDGE', 'REGIONAL', 'PRIVATE'",
        value_type=schema.TextLine(
            title="Endpoint Type",
            constraint = isValidEndpointConfigurationType
        ),
        required=False,
    )
    fail_on_warnings = schema.Bool(
        title="Indicates whether to roll back the resource if a warning occurs while API Gateway is creating the RestApi resource.",
        default=False,
        required=False,
    )
    methods = schema.Object(
        schema = IApiGatewayMethods,
        required=False,
    )
    minimum_compression_size = schema.Int(
        title="An integer that is used to enable compression on an API. When compression is enabled, compression or decompression is not applied on the payload if the payload size is smaller than this value. Setting it to zero allows compression for any payload size.",
        description="A non-negative integer between 0 and 10485760 (10M) bytes, inclusive.",
        default=None,
        required=False,
        min=0,
        max=10485760,
    )
    models = schema.Object(
        schema = IApiGatewayModels,
        required=False,
    )
    parameters = schema.Dict(
        title="Parameters. Custom header parameters for the request.",
        description="Dictionary of key/value pairs that are strings.",
        value_type=schema.TextLine(title="Value"),
        default={},
        required=False,
    )
    policy = schema.Text(
        title="""A policy document that contains the permissions for the RestApi resource, in JSON format. To set the ARN for the policy, use the !Join intrinsic function with "" as delimiter and values of "execute-api:/" and "*".""",
        description="Valid JSON document",
        constraint = isValidJSONOrNone,
        required=False,
    )
    resources = schema.Object(
        schema = IApiGatewayResources,
        required=False,
    )
    stages = schema.Object(
        schema = IApiGatewayStages,
        required=False,
    )

# Route53

class IRoute53Resource(INamed):
    """
The ``resource/route53.yaml`` file manages AWS Route 53 hosted zones.

Provision Route 53 with:

.. code-block:: bash

    paco provision resource.route53

.. code-block:: yaml
    :caption: Example resource/route53.yaml file

    hosted_zones:
      example:
        enabled: true
        domain_name: example.com
        account: aim.ref accounts.prod

    """
    hosted_zones = schema.Dict(
        title="Hosted Zones",
        value_type=schema.Object(IRoute53HostedZone),
        default=None,
        required=False,
    )

class IRoute53HealthCheck(IResource):
    """Route53 Health Check"""
    @invariant
    def is_load_balancer_or_domain_name_or_ip_address(obj):
        if obj.domain_name == None and obj.load_balancer == None and obj.ip_address == None:
            raise Invalid("Must set either domain_name, load_balancer or ip_address field.")
        count = 0
        if obj.domain_name != None:
            count += 1
        if obj.load_balancer != None:
            count += 1
        if obj.ip_address != None:
            count += 1
        if count > 1:
            raise Invalid("Can set only one of the domain_name, load_balancer and ip_address fields.")

    @invariant
    def is_match_string_health_check(obj):
        if getattr(obj, 'match_string', None) != None:
            if obj.health_check_type not in ('HTTP', 'HTTPS'):
                raise Invalid("If match_string field supplied, health_check_type must be HTTP or HTTPS.")

    domain_name = schema.TextLine(
        title="Fully Qualified Domain Name",
        description="Either this or the load_balancer field can be set but not both.",
        required=False
    )
    enable_sni = schema.Bool(
        title="Enable SNI",
        required=False,
        default=False
    )
    failure_threshold = schema.Int(
        title="Number of consecutive health checks that an endpoint must pass or fail for Amazon Route 53 to change the current status of the endpoint from unhealthy to healthy or vice versa.",
        min=1,
        max=10,
        required=False,
        default=3,
    )
    health_check_type = schema.TextLine(
        title="Health Check Type",
        description="Must be one of HTTP, HTTPS or TCP",
        required=True,
        constraint=isValidRoute53HealthCheckType,
    )
    health_checker_regions = schema.List(
        title="Health checker regions",
        description="List of AWS Region names (e.g. us-west-2) from which to make health checks.",
        required=False,
        value_type=schema.TextLine(title="AWS Region"),
        constraint=isValidHealthCheckAWSRegionList,
    )
    ip_address = PacoReference(
        title="IP Address",
        str_ok=True,
        required=False,
        schema_constraint='IEIP'
    )
    load_balancer = PacoReference(
        title="Load Balancer Endpoint",
        str_ok=True,
        required=False,
        schema_constraint='ILBApplication'
    )
    latency_graphs = schema.Bool(
        title="Measure latency and display CloudWatch graph in the AWS Console",
        required=False,
        default=False,
    )
    match_string = schema.TextLine(
        title="String to match in the first 5120 bytes of the response",
        min_length=1,
        max_length=255,
        required=False,
    )
    port = schema.Int(
        title="Port",
        min=1,
        max=65535,
        required=False,
        default=80,
    )
    request_interval_fast = schema.Bool(
        title="Fast request interval will only wait 10 seconds between each health check response instead of the standard 30",
        default=False,
        required=False,
    )
    resource_path = schema.TextLine(
        title="Resource Path",
        description="String such as '/health.html'. Path should return a 2xx or 3xx. Query string parameters are allowed: '/search?query=health'",
        max_length=255,
        default="/",
        required=False,
    )


# CodeCommit

class ICodeCommitUsers(INamed):
    """
Container for `CodeCommitUser`_ objects.
    """
    taggedValue('contains', 'ICodeCommitUser')

class ICodeCommitUser(INamed):
    """
CodeCommit User
    """
    username = schema.TextLine(
        title="CodeCommit Username",
        required=False,
    )
    public_ssh_key = schema.TextLine(
        title="CodeCommit User Public SSH Key",
        default=None,
        required=False,
    )
    permissions = schema.Choice(
        title='Permissions',
        description="Must be one of ReadWrite or ReadOnly",
        required=False,
        vocabulary=vocabulary.codecommit_permissions,
        default='ReadWrite',
    )

class ICodeCommitRepository(INamed, IDeployable):
    """
CodeCommit Repository
    """
    repository_name = schema.TextLine(
        title="Repository Name",
        required=False,
    )
    account = PacoReference(
        title="Account this repo belongs to.",
        required=True,
        schema_constraint='IAccount'
    )
    region = schema.TextLine(
        title="AWS Region",
        required=False,
    )
    description=schema.TextLine(
        title="Repository Description",
        required=False,
    )
    external_resource = schema.Bool(
        title='Boolean indicating whether the CodeCommit repository already exists or not',
        default=False,
        required=False,
    )
    users = schema.Dict(
        title="CodeCommit Users",
        value_type=schema.Object(ICodeCommitUser),
        default=None,
        required=False,
    )

class ICodeCommitRepositoryGroup(INamed, IMapping):
    """
Container for `CodeCommitRepository`_ objects.
    """
    taggedValue('contains', 'ICodeCommitRepository')

class ICodeCommit(INamed, IMapping):
    """
Container for `CodeCommitRepositoryGroup`_ objects.
    """
    taggedValue('contains', 'ICodeCommitRepositoryGroup')


class IConfig(IResource):
    """
AWS Config
"""
    delivery_frequency = schema.Choice(
        title="Delivery Frequency",
        required=False,
        default='One_Hour',
        vocabulary=vocabulary.aws_config_delivery_frequencies,
    )
    global_resources_region = schema.TextLine(
        title="Region to record Global resource changes",
        description='Must be a valid AWS Region name',
        constraint = isValidAWSRegionName,
        required=True,
    )
    locations = schema.List(
        title="Locations",
        value_type=schema.Object(IAccountRegions),
        default=[],
        required=False,
    )
    s3_bucket_logs_account = PacoReference(
        title="Account to contain the S3 Bucket that AWS Config records to",
        description='Must be an paco.ref to an account',
        required=True,
        schema_constraint='IAccount'
    )

class IConfigResource(INamed):
    """
Global AWS Config configuration
    """
    config = schema.Object(
        title="AWS Config",
        schema=IConfig,
        default=None,
        required=True,
    )


class ICloudTrail(IResource):
    """
The ``resource/cloudtrail.yaml`` file specifies CloudTrail resources.

AWS CloudTrail logs all AWS API activity. Monitor and react to changes in your AWS accounts with CloudTrail.
A CloudTrail can be used to set-up a multi-account CloudTrail that sends logs from every account into a single S3 Bucket.

.. code-block:: bash

    paco provision resource.cloudtrail

.. sidebar:: Prescribed Automation

    ``enable_kms_encryption``: Encrypt the CloudTrai logs with a Customer Managed Key (CMK). Paco will create
    a CMK for the CloudTrail in the same account as the ``s3_bucket_account``.

    ``kms_users``: A list of either IAM User names or paco references to ``resource/iam.yaml`` users. These
    users will have access to the CMK to decrypt and read the CloudTrail logs.

.. code-block:: yaml
    :caption: example resource/cloudtrail.yaml configuration

    trails:
      mycloudtrail:
        enabled: true
        region: 'us-west-2'
        cloudwatchlogs_log_group:
          expire_events_after_days: '14'
          log_group_name: CloudTrail
        enable_log_file_validation: true
        include_global_service_events: true
        is_multi_region_trail: true
        enable_kms_encryption: true
        kms_users:
          - bob@example.com
          - paco.ref resource.iam.users.sallysmith
        s3_bucket_account: paco.ref accounts.security
        s3_key_prefix: cloudtrails

"""
    accounts = schema.List(
        title="Accounts to enable this CloudTrail in. Leave blank to assume all accounts.",
        description="",
        value_type=PacoReference(
            title="Account Reference",
            schema_constraint='IAccount'
        ),
        required=False,
    )
    cloudwatchlogs_log_group = schema.Object(
        title="CloudWatch Logs LogGroup to deliver this trail to.",
        required=False,
        default=None,
        schema = ICloudWatchLogGroup,
    )
    enable_kms_encryption = schema.Bool(
        title="Enable KMS Key encryption",
        default=False,
    )
    kms_users = schema.List(
        title="IAM Users with access to CloudTrail bucket",
        value_type=PacoReference(
            title="KMS User",
            str_ok=True,
            schema_constraint='IIAMUser'
        )
    )
    enable_log_file_validation = schema.Bool(
        title="Enable log file validation",
        default=True,
        required=False,
    )
    include_global_service_events = schema.Bool(
        title="Include global service events",
        default=True,
        required=False,
    )
    is_multi_region_trail = schema.Bool(
        title="Is multi-region trail?",
        default=True,
        required=False,
    )
    region = schema.TextLine(
        title="Region to create the CloudTrail",
        default="",
        description='Must be a valid AWS Region name or empty string',
        constraint = isValidAWSRegionNameOrNone,
        required=False,
    )
    s3_bucket_account = PacoReference(
        title="Account which will contain the S3 Bucket that the CloudTrails will be stored in",
        description='Must be an paco.ref to an account',
        required=True,
        schema_constraint='IAccount'
    )
    s3_key_prefix = schema.TextLine(
        title="S3 Key Prefix specifies the Amazon S3 key prefix that comes after the name of the bucket.",
        description="Do not include a leading or trailing / in your prefix. They are provided already.",
        default="",
        max_length = 200,
        constraint = isValidS3KeyPrefix,
        required=False,
    )

class ICloudTrails(INamed, IMapping):
    """
Container for `CloudTrail`_ objects.
    """
    taggedValue('contains', 'ICloudTrail')

class ICloudTrailResource(INamed):
    """
Global CloudTrail configuration
    """
    trails = schema.Object(
        title="CloudTrails",
        schema = ICloudTrails,
        default=None,
        required=False,
    )

class ICloudFrontCookies(INamed):
    forward = schema.TextLine(
        title="Cookies Forward Action",
        constraint = isValidCloudFrontCookiesForward,
        default='all',
        required=False
    )
    whitelisted_names = schema.List(
        title="White Listed Names",
        value_type=schema.TextLine(),
        required=False
    )

class ICloudFrontForwardedValues(INamed):
    query_string = schema.Bool(
        title="Forward Query Strings",
        default=True,
        required=False
    )
    cookies = schema.Object(
        title="Forward Cookies",
        schema = ICloudFrontCookies,
        required=False
    )
    headers = schema.List(
        title="Forward Headers",
        value_type=schema.TextLine(),
        default=['*'],
        required=False
    )

class ICloudFrontDefaultCacheBehavior(INamed):
    allowed_methods = schema.List(
        title="List of Allowed HTTP Methods",
        value_type=schema.TextLine(),
        default=[ 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT' ],
        required=False
    )
    cached_methods = schema.List(
        title="List of HTTP Methods to cache",
        value_type=schema.TextLine(),
        default=[ 'GET', 'HEAD', 'OPTIONS' ],
        required=False
    )
    # These default, Max, Min, and Default TTL values specifically configure
    # Cloudfront to use the Origin's cache-control header values when they
    # exist. Changing these values will force Cloudfront to modify any
    # Cache-Control header with the new values.
    default_ttl = schema.Int(
        title="Default TTL",
        default=86400
    )
    max_ttl = schema.Int(
        title="Maximum TTL",
        default=31536000
    )
    min_ttl = schema.Int(
        title="Minimum TTL",
        default=0
    )
    target_origin = PacoReference(
        title="Target Origin",
        schema_constraint='ICloudFrontOrigin'
    )
    viewer_protocol_policy = schema.TextLine(
        title="Viewer Protocol Policy",
        constraint = isValidCFViewerProtocolPolicy,
        default='redirect-to-https'
    )
    forwarded_values = schema.Object(
        title="Forwarded Values",
        schema = ICloudFrontForwardedValues,
        required=False
    )
    compress = schema.Bool(
        title="Compress certain files automatically",
        required=False,
        default=False
    )

class ICloudFrontCacheBehavior(ICloudFrontDefaultCacheBehavior):
    path_pattern = schema.TextLine(
        title="Path Pattern",
        required=True
    )

class ICloudFrontViewerCertificate(INamed):
    certificate = PacoReference(
        title="Certificate Reference",
        required=False,
        schema_constraint='IAWSCertificateManager'
    )
    ssl_supported_method = schema.TextLine(
        title="SSL Supported Method",
        constraint = isValidCFSSLSupportedMethod,
        required=False,
        default='sni-only'
    )
    minimum_protocol_version = schema.TextLine(
        title="Minimum SSL Protocol Version",
        constraint = isValidCFMinimumProtocolVersion,
        required=False,
        default='TLSv1.1_2016'
    )

class ICloudFrontCustomErrorResponse(Interface):
    error_caching_min_ttl = schema.Int(
        title="Error Caching Min TTL",
        required=False,
        default=300,
    )
    error_code = schema.Int(
        title="HTTP Error Code",
        required=False
    )
    response_code = schema.Int(
        title="HTTP Response Code",
        required=False
    )
    response_page_path = schema.TextLine(
        title="Response Page Path",
        required=False
    )

class ICloudFrontCustomOriginConfig(INamed):
    http_port = schema.Int(
        title="HTTP Port",
        required=False
    )
    https_port = schema.Int(
        title="HTTPS Port",
        required=False,
    )
    protocol_policy = schema.TextLine(
        title="Protocol Policy",
        constraint = isValidCFProtocolPolicy,
        required=True,
    )
    ssl_protocols = schema.List(
        title="List of SSL Protocols",
        value_type=schema.TextLine(),
        constraint = isValidCFSSLProtocol,
        required=True,
    )
    read_timeout = schema.Int(
        title="Read timeout",
        min=4,
        max=60,
        default=30,
        required=False,
    )
    keepalive_timeout = schema.Int(
        title="HTTP Keepalive Timeout",
        min=1,
        max=60,
        default=5,
        required=False,
    )

class ICloudFrontOrigin(INamed):
    """
CloudFront Origin Configuration
    """
    s3_bucket = PacoReference(
        title="Origin S3 Bucket Reference",
        required=False,
        schema_constraint='IS3Bucket'
    )
    domain_name = PacoReference(
        title="Origin Resource Reference",
        str_ok=True,
        required=False,
        schema_constraint='IRoute53HostedZone'
    )
    custom_origin_config = schema.Object(
        title="Custom Origin Configuration",
        schema = ICloudFrontCustomOriginConfig,
        required=False,
    )

class ICloudFrontFactory(INamed):
    """CloudFront Factory"""
    domain_aliases = schema.List(
        title="List of DNS for the Distribution",
        value_type=schema.Object(IDNS),
        required=False,
    )
    viewer_certificate = schema.Object(
        title="Viewer Certificate",
        schema = ICloudFrontViewerCertificate,
        required=False,
    )

class ICloudFront(IResource, IDeployable, IMonitorable):
    """
CloudFront CDN Configuration
    """
    domain_aliases = schema.List(
        title="List of DNS for the Distribution",
        value_type=schema.Object(IDNS),
        required=False,
    )
    default_root_object = schema.TextLine(
        title="The default path to load from the origin.",
        default='',
        required=False,
    )
    default_cache_behavior = schema.Object(
        title="Default Cache Behavior",
        schema = ICloudFrontDefaultCacheBehavior,
        required=False,
    )
    cache_behaviors = schema.List(
        title='List of Cache Behaviors',
        value_type=schema.Object(ICloudFrontCacheBehavior),
        required=False
    )
    viewer_certificate = schema.Object(
        title="Viewer Certificate",
        schema = ICloudFrontViewerCertificate,
        required=False,
    )
    price_class = schema.TextLine(
        title="Price Class",
        constraint = isValidCFPriceClass,
        default='All',
        required=False,
    )
    custom_error_responses = schema.List(
        title="List of Custom Error Responses",
        value_type=schema.Object(ICloudFrontCustomErrorResponse),
        default=None,
        required=False,
    )
    origins = schema.Dict(
        title="Map of Origins",
        value_type=schema.Object(ICloudFrontOrigin),
        required=False,
    )
    webacl_id = schema.TextLine(
        title="WAF WebACLId",
        required=False,
    )
    factory = schema.Dict(
        title="CloudFront Factory",
        value_type=schema.Object(ICloudFrontFactory),
        default=None,
        required=False,
    )

# Pinpoint

class IPinpointEmailChannel(Interface):
    "Pinpoint Email Channel"
    enable_email = schema.Bool(
        title="Enable Email",
        required=False,
        default=True,
    )
    from_address = schema.TextLine(
        title="The verified email address that you want to send email from when you send email through the channel.",
        required=False,
    )

class IPinpointSMSChannel(Interface):
    "Pinpoint SMS Channel"
    enable_sms = schema.Bool(
        title="Enable SMS",
        required=False,
        default=True,
    )
    # ToDo: constraints and invariants
    sender_id = schema.TextLine(
        title="The identity that you want to display on recipients' devices when they receive messages from the SMS channel.",
        required=False,
    )
    short_code = schema.TextLine(
        title="The registered short code that you want to use when you send messages through the SMS channel.",
        required=False,
    )

class IPinpointApplication(IResource):
    """Amazon Pinpoint is a flexible and scalable outbound and inbound marketing communications service.
You can connect with customers over channels like email, SMS, push, or voice.

A Pinpoint Application is a collection of related settings, customer information, segments, campaigns,
and other types of Amazon Pinpoint resources.

Currently AWS Pinpoint only supports general configuration suitable for sending transactional messages.

.. sidebar:: Prescribed Automation

    ``email_channel``: Will build an ARN to a Simple Email Service Verified Email in the same account and region.

.. code-block:: yaml
    :caption: example Pinpoint Application configuration

    type: PinpointApplication
    enabled: true
    order: 20
    title: "My SaaS Transactional Message Service"
    email_channel:
        enable_email: true
        from_address: "bob@example.com"
    sms_channel:
        enable_sms: true
        sender_id: MyUniqueName

"""
    sms_channel = schema.Object(
        title="SMS Channel",
        schema=IPinpointSMSChannel,
        required=False
    )
    email_channel = schema.Object(
        title="Email Channel",
        schema=IPinpointEmailChannel,
        required=False
    )

# RDS Schemas

class IDBParameters(IMapping):
    "A dict of database parameters"
    # ToDo: constraints for parameters ...(huge!)

class IDBParameterGroup(IResource):
    """
DBParameterGroup
    """
    description=schema.Text(
        title="Description",
        required=False
    )
    family = schema.TextLine(
        title="Database Family",
        required=True
        # ToDo: constraint for this is fairly complex and can change
    )
    parameters = schema.Object(
        title="Database Parameter set",
        schema=IDBParameters,
        required=True
    )

class IDBClusterParameterGroup(IDBParameterGroup):
    """
DBCluster Parameter Group
    """
    pass

class IRDSOptionConfiguration(Interface):
    """
Option groups enable and configure features that are specific to a particular DB engine.
    """
    option_name = schema.TextLine(
        title='Option Name',
        required=False,
    )
    option_settings = schema.List(
        title='List of option name value pairs.',
        value_type=schema.Object(INameValuePair),
        required=False,
    )
    option_version = schema.TextLine(
        title='Option Version',
        required=False,
    )
    port = schema.TextLine(
        title='Port',
        required=False,
    )
    # - DBSecurityGroupMemberships
    #   A list of DBSecurityGroupMembership name strings used for this option.
    # - VpcSecurityGroupMemberships
    #   A list of VpcSecurityGroupMembership name strings used for this option.


class IRDS(IMonitorable):
    """
RDS common fields shared by both DBInstance and DBCluster
    """
    @invariant
    def password_or_snapshot_or_secret(obj):
        count = 0
        if obj.db_snapshot_identifier:
            count += 1
        if obj.master_user_password:
            count += 1
        if obj.secrets_password:
            count += 1
        if count > 1:
            raise Invalid("Can only set one of db_snapshot_identifier, master_user_password or secrets_password for RDS.")
        elif count < 1:
            raise Invalid("Must set one of db_snapshot_identifier, master_user_password or secrets_password for RDS.")
        return True

    @invariant
    def valid_engine_version(obj):
        "Validate engine version is supported for the engine type"
        if obj.engine_version not in gen_vocabulary.rds_engine_versions[obj.engine]:
            raise Invalid("Engine Version is not support by AWS RDS")
        return True

    backup_preferred_window = schema.TextLine(
        title="Backup Preferred Window",
        required=False,
    )
    backup_retention_period = schema.Int(
        title="Backup Retention Period in days",
        required=False,
    )
    cloudwatch_logs_exports = schema.List(
        title="List of CloudWatch Logs Exports",
        value_type=schema.TextLine(
            title="CloudWatch Log Export",
        ),
        required=False,
        # ToDo: Constraint that depends upon the database type
    )
    db_snapshot_identifier = schema.TextLine(
        title="DB Snapshot Identifier to restore from",
        description="Must be the ARN of a valid database snapshot.",
        required=False,
    )
    deletion_protection = schema.Bool(
        title="Deletion Protection",
        default=False,
        required=False
    )
    dns = schema.List(
        title="DNS domains to create to resolve to the connection Endpoint",
        value_type=schema.Object(IDNS),
        required=False
    )
    engine_version = schema.TextLine(
        title="RDS Engine Version",
        required=False,
    )
    kms_key_id = PacoReference(
        title="Enable Storage Encryption",
        required=False,
        schema_constraint='Interface'
    )
    maintenance_preferred_window = schema.TextLine(
        title="Maintenance Preferred Window",
        required=False,
    )
    master_username = schema.TextLine(
        title="Master Username",
        required=False,
    )
    master_user_password = schema.TextLine(
        title="Master User Password",
        required=False,
    )
    primary_domain_name = PacoReference(
        title="Primary Domain Name",
        str_ok=True,
        required=False,
        schema_constraint='IRoute53HostedZone'
    )
    primary_hosted_zone = PacoReference(
        title="Primary Hosted Zone",
        required=False,
        schema_constraint='IRoute53HostedZone'
    )
    port = schema.Int(
        title="DB Port",
        required=False,
    )
    secrets_password = PacoReference(
        title="Secrets Manager password",
        required=False,
        schema_constraint='ISecretsManagerSecret'
    )
    security_groups = schema.List(
        title="List of VPC Security Group Ids",
        value_type=PacoReference(
            schema_constraint='ISecurityGroup'
        ),
        required=False,
    )
    segment = PacoReference(
        title="Segment",
        required=False,
        schema_constraint='ISegment'
    )

class IRDSInstance(IResource, IRDS):
    """
RDS DB Instance
    """
    allow_major_version_upgrade = schema.Bool(
        title="Allow major version upgrades",
        required=False,
    )
    auto_minor_version_upgrade = schema.Bool(
        title="Automatic minor version upgrades",
        required=False,
    )
    db_instance_type = schema.TextLine(
        title="RDS Instance Type",
        required=False,
    )
    license_model = schema.TextLine(
        title="License Model",
        required=False,
    )
    option_configurations = schema.List(
        title="Option Configurations",
        value_type=schema.Object(IRDSOptionConfiguration),
        required=False,
    )
    parameter_group = PacoReference(
        title="RDS Parameter Group",
        required=False,
        schema_constraint='IDBParameterGroup'
    )
    publically_accessible = schema.Bool(
        title="Assign a Public IP address",
        required=False,
    )
    storage_encrypted = schema.Bool(
        title="Enable Storage Encryption",
        required=False,
    )
    storage_type = schema.TextLine(
        title="DB Storage Type",
        required=False,
    )
    storage_size_gb = schema.Int(
        title="DB Storage Size in Gigabytes",
        required=False,
    )

class IRDSMultiAZ(IRDSInstance):
    """
RDS with MultiAZ capabilities. When you provision a Multi-AZ DB Instance, Amazon RDS automatically creates a
primary DB Instance and synchronously replicates the data to a standby instance in a different Availability Zone (AZ).
    """
    multi_az = schema.Bool(
        title="Multiple Availability Zone deployment",
        default=False,
        required=False,
    )

class IRDSMysql(IRDSMultiAZ):
    """RDS for MySQL"""

class IRDSDBInstanceEventNotifications(INamed):
    """
DB Instance Event Notifications
    """
    groups = schema.List(
        title="Groups",
        value_type=schema.TextLine(title="Group"),
        required=True,
    )
    event_categories = schema.List(
        title="Event Categories",
        value_type=schema.Choice(
            title="Event Category",
            vocabulary=vocabulary.rds_instance_event_categories,
        ),
        required=True,
    )

class IRDSClusterDefaultInstance(INamed, IMonitorable):
    """
Default configuration for a DB Instance that belongs to a DB Cluster.
    """
    # Note: IRDSClusterDefaultInstance is the same as IRDSClusterInstance except it provides default values for fields.
    # (otherwise the instance-level field defaults would shadow cluster-level specific settings)

    allow_major_version_upgrade = schema.Bool(
        title="Allow major version upgrades",
        required=False,
    )
    auto_minor_version_upgrade = schema.Bool(
        title="Automatic minor version upgrades",
        required=False,
    )
    # ToDo: Add an invariant to check that az is within the number in the segment
    availability_zone = schema.Int(
        title='Availability Zone where the instance will be provisioned.',
        description="Must be one of 1, 2, 3 ...",
        required=False,
        min=0,
        max=10,
    )
    # ToDO: invariant - this is required at either default or instance-level
    db_instance_type = schema.TextLine(
        title="DB Instance Type",
        required=False,
    )
    enable_performance_insights = schema.Bool(
        title="Enable Performance Insights",
        required=False,
        default=False,
    )
    enhanced_monitoring_interval_in_seconds = schema.Int(
        title="Enhanced Monitoring interval in seconds. This will enable enhanced monitoring unless set to 0.",
        description="Must be one of 0, 1, 5, 10, 15, 30, 60.",
        default=0,
        required=False,
        constraint=isValidEnhancedMonitoringInterval,
    )
    event_notifications = schema.Object(
        title="DB Instance Event Notifications",
        required=False,
        schema=IRDSDBInstanceEventNotifications,
    )
    parameter_group = PacoReference(
        title="DB Parameter Group",
        required=False,
        schema_constraint='IDBParameterGroup'
    )
    publicly_accessible = schema.Bool(
        title="Assign a Public IP address",
        required=False,
        default=False,
    )

class IRDSClusterInstance(INamed, IMonitorable):
    """
DB Instance that belongs to a DB Cluster.
    """
    allow_major_version_upgrade = schema.Bool(
        title="Allow major version upgrades",
        required=False,
    )
    auto_minor_version_upgrade = schema.Bool(
        title="Automatic minor version upgrades",
        required=False,
    )
    # ToDo: Add an invariant to check that az is within the number in the segment
    availability_zone = schema.Int(
        title='Availability Zone where the instance will be provisioned.',
        description="Must be one of 1, 2, 3 ...",
        required=False,
        min=0,
        max=10,
    )
    # ToDO: invariant - this is required at either default or instance-level
    db_instance_type = schema.TextLine(
        title="DB Instance Type",
        required=False,
    )
    enable_performance_insights = schema.Bool(
        title="Enable Performance Insights",
        required=False,
    )
    enhanced_monitoring_interval_in_seconds = schema.Int(
        title="Enhanced Monitoring interval in seconds. This will enable enhanced monitoring unless set to 0.",
        description="Must be one of 0, 1, 5, 10, 15, 30, 60.",
        required=False,
        constraint=isValidEnhancedMonitoringInterval,
    )
    event_notifications = schema.Object(
        title="DB Instance Event Notifications",
        required=False,
        schema=IRDSDBInstanceEventNotifications,
    )
    parameter_group = PacoReference(
        title="DB Parameter Group",
        required=False,
        schema_constraint='IDBParameterGroup'
    )
    publicly_accessible = schema.Bool(
        title="Assign a Public IP address",
        required=False,
    )

class IRDSClusterInstances(INamed, IMapping):
    """
Container for `RDSClusterInstance`_ objects.
    """
    taggedValue('contains', 'IRDSClusterInstances')


class IRDSDBClusterEventNotifications(INamed):
    """
Event Notifications for a DB Cluster
    """
    groups = schema.List(
        title="Groups",
        value_type=schema.TextLine(title="Group"),
        required=True,
    )
    event_categories = schema.List(
        title="Event Categories",
        value_type=schema.Choice(
            title="Event Category",
            vocabulary=vocabulary.rds_cluster_event_categories,
        ),
        required=True,
    )

class IRDSAurora(IResource, IRDS):
    """
RDS Aurora DB Cluster
    """
    availability_zones = schema.TextLine(
        title='Availability Zones to launch instances in.',
        description="Must be one of all, 1, 2, 3 ...",
        default='all',
        required=False,
        constraint=IsValidASGAvailabilityZone
    )
    backtrack_window_in_seconds = schema.Int(
        title="Backtrack Window in seconds. Disabled when set to 0.",
        description="Maximum is 72 hours (259,200 seconds).",
        min=0,
        max=259200,
        default=0,
        required=False,
    )
    cluster_event_notifications = schema.Object(
        title="Cluster Event Notifications",
        required=False,
        schema=IRDSDBClusterEventNotifications,
    )
    cluster_parameter_group = PacoReference(
        title="DB Cluster Parameter Group",
        required=False,
        schema_constraint='IDBClusterParameterGroup'
    )
    db_instances = schema.Object(
        title="DB Instances",
        required=True,
        schema=IRDSClusterInstances,
    )
    default_instance = schema.Object(
        title="Default DB Instance configuration",
        required=False,
        schema=IRDSClusterDefaultInstance,
    )
    enable_http_endpoint = schema.Bool(
        title="Enable an HTTP endpoint to provide a connectionless web service API for running SQL queries",
        default=False,
        required=False,
    )
    enable_kms_encryption = schema.Bool(
        title="Enable KMS Key encryption. Will create one KMS-CMK key dedicated to each DBCluster.",
        default=False,
    )
    engine_mode = schema.Choice(
        title="Engine Mode",
        description="Must be one of provisioned, serverless, parallelquery, global, or multimaster.",
        vocabulary=vocabulary.rds_cluster_engine_mode,
        required=False,
    )
    read_dns = schema.List(
        title="DNS domains to create to resolve to the connection Read Endpoint",
        value_type=schema.Object(IDNS),
        required=False
    )
    restore_type = schema.Choice(
        title="Restore Type",
        description="Must be one of full-copy or copy-on-write",
        default='full-copy',
        vocabulary=vocabulary.rds_restore_types,
        required=False,
    )
    use_latest_restorable_time = schema.Bool(
        title="Restore the DB cluster to the latest restorable backup time",
        required=False,
        default=False,
    )

class IRDSMysqlAurora(IRDSAurora):
    """
RDS MySQL Aurora Cluster
    """
    # ToDo: constraint
    database_name = schema.TextLine(
        title="Database Name to create in the cluster",
        description="Must be a valid database name for the DB Engine. Must contain 1 to 64 letters or numbers. Can't be MySQL reserved word.",
        required=False,
        min_length=1,
        max_length=64,
    )

class IRDSPostgresqlAurora(IRDSAurora):
    """
RDS PostgreSQL Aurora Cluster
    """
    # ToDo: constraint
    database_name = schema.TextLine(
        title="Database Name to create in the cluster",
        description="Must be a valid database name for the DB Engine. Must contain 1 to 63 letters, numbers or underscores. Must begin with a letter or an underscore. Can't be PostgreSQL reserved word.",
        required=False,
        min_length=1,
        max_length=63,
    )

class IRDSPostgresql(IRDSMultiAZ):
    """RDS for Postgresql"""

# Cache schemas

class IElastiCache(Interface):
    """
Base ElastiCache Interface
    """
    # ToDo: Invariant for cache_clusters
    # - This parameter is not used if there is more than one node group (shard). You should use ReplicasPerNodeGroup instead.
    # - If AutomaticFailoverEnabled is true, the value of this parameter must be at least 2.
    @invariant
    def cluster_layout(obj):
        "One of PrimaryClusterId, NumCacheClusters, NumNodeGroups or ReplicasPerNodeGroup are required"
        if obj.cache_clusters == None and obj.number_of_read_replicas == None:
            raise Invalid("Must supply either cache_clusters or number_of_read_replicas.")

    at_rest_encryption = schema.Bool(
        title="Enable encryption at rest",
        required=False,
    )
    auto_minor_version_upgrade = schema.Bool(
        title="Enable automatic minor version upgrades",
        required=False,
    )
    automatic_failover_enabled = schema.Bool(
        title="Specifies whether a read-only replica is automatically promoted to read/write primary if the existing primary fails",
        required=False,
    )
    az_mode = schema.TextLine(
        title="AZ mode",
        constraint=isValidAZMode,
        required=False,
    )
    cache_clusters = schema.Int(
        title="Number of Cache Clusters",
        required=False,
        min=1,
        max=6
    )
    cache_node_type = schema.TextLine(
        title="Cache Node Instance type",
        description="",
        required=False,
    )
    description=schema.Text(
        title="Replication Description",
        required=False,
    )
    engine = schema.TextLine(
        title="ElastiCache Engine",
        required=False
    )
    engine_version = schema.TextLine(
        title="ElastiCache Engine Version",
        required=False
    )
    maintenance_preferred_window = schema.TextLine(
        title='Preferred maintenance window',
        required=False,
    )
    number_of_read_replicas = schema.Int(
        title="Number of read replicas",
        required=False,
    )
    parameter_group = PacoReference(
        title='Parameter Group name',
        str_ok=True,
        required=False,
        schema_constraint='Interface'
    )
    port = schema.Int(
        title="Port",
        required=False,
    )
    security_groups = schema.List(
        title="List of Security Groups",
        value_type=PacoReference(
            schema_constraint='ISecurityGroup'
        ),
        required=False,
    )
    segment = PacoReference(
        title="Segment",
        required=False,
        schema_constraint='ISegment'
    )


class IElastiCacheRedis(IResource, IElastiCache, IMonitorable):
    """
Redis ElastiCache Interface
    """
    cache_parameter_group_family = schema.TextLine(
        title='Cache Parameter Group Family',
        constraint=isRedisCacheParameterGroupFamilyValid,
        required=False
    )
    snapshot_retention_limit_days = schema.Int(
        title="Snapshot Retention Limit in Days",
        required=False,
    )
    snapshot_window = schema.TextLine(
        title="The daily time range (in UTC) during which ElastiCache begins taking a daily snapshot of your node group (shard).",
        required=False,
        # ToDo: constraint for "windows"
    )

class IESAdvancedOptions(IMapping):
    "A dict of ElasticSearch key-value advanced options"
    # ToDo: constraints for options

class IEBSOptions(Interface):
    # this is not IDeployable so it can have a different title to desribce it's configuration purpose
    enabled = schema.Bool(
        title="Specifies whether Amazon EBS volumes are attached to data nodes in the Amazon ES domain.",
        required=False
    )
    iops = schema.Int(
        title="The number of I/O operations per second (IOPS) that the volume supports.",
        required=False
    )
    volume_size_gb = schema.Int(
        title="The size (in GiB) of the EBS volume for each data node.",
        description="The minimum and maximum size of an EBS volume depends on the EBS volume type and the instance type to which it is attached.",
        required=False,
    )
    volume_type = schema.TextLine(
        title="The EBS volume type to use with the Amazon ES domain.",
        description="Must be one of: standard, gp2, io1, st1, or sc1",
        required=False,
        constraint=isValidEBSVolumeType
    )

class IElasticsearchCluster(Interface):
    dedicated_master_count = schema.Int(
        title="The number of instances to use for the master node.",
        description="If you specify this field, you must specify true for the dedicated_master_enabled field.",
        required=False,
        min=1,
    )
    dedicated_master_enabled =schema.Bool(
        title="Indicates whether to use a dedicated master node for the Amazon ES domain.",
        required=False,
    )
    # ToDo: add constraint for instance types
    dedicated_master_type = schema.TextLine(
        title="The hardware configuration of the computer that hosts the dedicated master node",
        description="Valid Elasticsearch instance type, such as m3.medium.elasticsearch. See https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/aes-supported-instance-types.html",
        required=False,
    )
    instance_count = schema.Int(
        title="The number of data nodes (instances) to use in the Amazon ES domain.",
        required=False,
    )
    # ToDo: add constraint for instance types
    instance_type = schema.TextLine(
        title="The instance type for your data nodes.",
        description="Valid Elasticsearch instance type, such as m3.medium.elasticsearch. See https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/aes-supported-instance-types.html",
        required=False,
    )
    # ToDo: invariant to only allow if zone_awareness_enabled: true
    zone_awareness_availability_zone_count = schema.Int(
        title="If you enabled multiple Availability Zones (AZs), the number of AZs that you want the domain to use.",
        default=2,
        required=False,
        min=2,
        max=3,
    )
    zone_awareness_enabled = schema.Bool(
        title="Enable zone awareness for the Amazon ES domain.",
        required=False
    )

class IElasticsearchDomain(IResource, IMonitorable):
    """
Amazon Elasticsearch Service (Amazon ES) is a managed service for Elasticsearch clusters.
An Amazon ES domain is synonymous with an Elasticsearch cluster. Domains are clusters with the
settings, instance types, instance counts, and storage resources that you specify.

.. sidebar:: Prescribed Automation

    ``segment``: Including the segment will place the Elasticsearch cluster within the Availability
    Zones for that segment. If an Elasticsearch ServiceLinkedRole is not already provisioned for that
    account and region, Paco will create it for you. This role is used by AWS to place the Elasticsearch
    cluster within the subnets that belong that segment and VPC.

    If segment is not set, then you will have a public Elasticsearch cluster with an endpoint.

.. code-block:: yaml
    :caption: example Elasticsearch configuration

    type: ElasticsearchDomain
    order: 10
    title: "Elasticsearch Domain"
    enabled: true
    access_policies_json: ./es-config/es-access.json
    advanced_options:
      indices.fielddata.cache.size: ""
      rest.action.multi.allow_explicit_index: "true"
    cluster:
      instance_count: 2
      zone_awareness_enabled: false
      instance_type: "t2.micro.elasticsearch"
      dedicated_master_enabled: true
      dedicated_master_type: "t2.micro.elasticsearch"
      dedicated_master_count: 2
    ebs_volumes:
      enabled: true
      iops: 0
      volume_size_gb: 10
      volume_type: 'gp2'
    segment: web
    security_groups:
      - paco.ref netenv.mynet.network.vpc.security_groups.app.search

    """
    # ToDo: this could be direct references to IAM things and Paco could generate the JSON?
    access_policies_json = StringFileReference(
        title="Policy document that specifies who can access the Amazon ES domain and their permissions.",
        required=False,
        constraint=isValidJSONOrNone
    )
    advanced_options = schema.Object(
        title="Advanced Options",
        schema=IESAdvancedOptions,
        required=False
    )
    ebs_volumes = schema.Object(
        title="EBS volumes that are attached to data nodes in the Amazon ES domain.",
        required=False,
        schema=IEBSOptions,
    )
    cluster = schema.Object(
        title="Elasticsearch Cluster configuration",
        schema=IElasticsearchCluster,
        required=False,
    )
    # ToDo: provide option to set the UpgradeElasticsearchVersion update policy to true
    # during stack updates to allow for no downtime upgrades
    elasticsearch_version = schema.TextLine(
        title="The version of Elasticsearch to use, such as 2.3.",
        default="1.5",
        required=False,
    )
    # ToDo: encrypt at rest
    #encrypt_at_rest_enabled
    #encrypt_at_rest_kms_key
    # ToDo: log publishing
    #log_publishing_log_group
    #log_publising_enabled
    node_to_node_encryption = schema.Bool(
        title="Enable node-to-node encryption",
        required=False,
    )
    snapshot_start_hour = schema.Int(
        title="The hour in UTC during which the service takes an automated daily snapshot of the indices in the Amazon ES domain.",
        min=0,
        max=23,
        required=False,
    )
    security_groups = schema.List(
        title="List of Security Groups",
        value_type=PacoReference(
            schema_constraint='ISecurityGroup'
        ),
        required=False,
    )
    segment = schema.TextLine(
        title="Segment",
        required=False,
    )

class IIAMUserProgrammaticAccess(IEnablable):
    """
IAM User Programmatic Access Configuration
    """
    access_key_1_version = schema.Int(
        title='Access key version id',
        default=0,
        required=False
    )
    access_key_2_version = schema.Int(
        title='Access key version id',
        default=0,
        required=False
    )

class IIAMUserPermission(INamed, IDeployable):
    """
IAM User Permission
    """
    type = schema.TextLine(
        title="Type of IAM User Access",
        description="A valid Paco IAM user access type: Administrator, CodeCommit, etc.",
        required=False,
    )

class IIAMUserPermissionAdministrator(IIAMUserPermission):
    """
Administrator IAM User Permission
    """
    accounts = CommaList(
        title='Comma separated list of Paco AWS account names this user has access to',
        required=False,
    )
    read_only = schema.Bool(
        title='Enabled ReadOnly access',
        default=False,
        required=False,
    )


class IIAMUserPermissionCodeCommitRepository(IParent):
    """
CodeCommit Repository IAM User Permission Definition
    """
    codecommit = PacoReference(
        title='CodeCommit Repository Reference',
        required=False,
        schema_constraint='ICodeCommitRepository'
    )
    permission = schema.TextLine(
        title='Paco Permission policy',
        constraint = isPacoCodeCommitPermissionPolicyValid,
        required=False,
    )
    console_access_enabled = schema.Bool(
        title='Console Access Boolean',
        required=False,
    )
    public_ssh_key = schema.TextLine(
        title="CodeCommit User Public SSH Key",
        default=None,
        required=False,
    )

class IIAMUserPermissionCodeCommit(IIAMUserPermission):
    """
CodeCommit IAM User Permission
    """
    repositories = schema.List(
        title='List of repository permissions',
        value_type=schema.Object(IIAMUserPermissionCodeCommitRepository),
        required=False,
    )

class IIAMUserPermissionCodeBuildResource(IParent):
    """
CodeBuild Resource IAM User Permission Definition
    """
    codebuild = PacoReference(
        title='CodeBuild Resource Reference',
        required=False,
        schema_constraint='Interface'
    )
    permission = schema.TextLine(
        title='Paco Permission policy',
        constraint = isPacoCodeCommitPermissionPolicyValid,
        required=False,
    )
    console_access_enabled = schema.Bool(
        title='Console Access Boolean',
        required=False,
    )

class IIAMUserPermissionCodeBuild(IIAMUserPermission):
    """
CodeBuild IAM User Permission
    """
    resources = schema.List(
        title='List of CodeBuild resources',
        value_type=schema.Object(IIAMUserPermissionCodeBuildResource),
        required=False
    )

class IIAMUserPermissionCustomPolicy(IIAMUserPermission):
    """
Custom IAM User Permission
    """
    accounts = CommaList(
        title='Comma separated list of Paco AWS account names this user has access to',
        required=False,
    )
    managed_policies = schema.List(
        title="AWS Managed Policies",
        value_type=schema.Choice(
            title="Managed policies",
            vocabulary=gen_vocabulary.iam_managed_policies,
        ),
        required=False,
        default=[],
    )
    policies = schema.List(
        title="Policies",
        value_type=schema.Object(
            schema=IPolicy
        ),
        required=False,
    )

class IIAMUserPermissions(INamed, IMapping):
    """
Container for IAM User Permission objects.
    """
    taggedValue('contains', 'mixed')

class IIAMUser(INamed, IDeployable):
    """
IAM User represents a user that will exist in one account, but can also
have delegate IAM Roles in other accounts that they are allowed to assume.

.. code-block:: yaml
    :caption: example IAM User

    enabled: true
    account: paco.ref accounts.master
    username: yourusername
    description: 'Your Name - Paco Administrator'
    console_access_enabled: true
    programmatic_access:
      enabled: true
      access_key_1_version: 1
      access_key_2_version: 0
    account_whitelist: all
    permissions:
      administrator:
        type: Administrator
        accounts: all
      custom:
        accounts: dev
        managed_policies:
           - 'AWSDirectConnectReadOnlyAccess'
           - 'AmazonGlacierReadOnlyAccess'
        policies:
          - name: "AWS Polly full access"
            statement:
              - effect: Allow
                action:
                  - 'polly:*'
                resource:
                  - '*'

    """
    account = PacoReference(
        title="Paco account reference to install this user",
        required=True,
        schema_constraint='IAccount',
    )
    username = schema.TextLine(
        title='IAM Username',
        required=False,
    )
    description=schema.TextLine(
        title='IAM User Description',
        required=False,
    )
    console_access_enabled = schema.Bool(
        title='Console Access Boolean'
    )
    programmatic_access = schema.Object(
        title='Programmatic Access',
        schema = IIAMUserProgrammaticAccess,
        required=False,
    )
    permissions = schema.Object(
        title='Paco IAM User Permissions',
        schema = IIAMUserPermissions,
        required=False,
    )
    account_whitelist = CommaList(
        title='Comma separated list of Paco AWS account names this user has access to',
        required=False,
    )

class IIAMUsers(INamed, IMapping):
    """
Container for `IAMUser`_ objects.
    """
    taggedValue('contains', 'IIAMUser')


class IIAMResource(INamed):
    """
IAM Resource contains IAM Users who can login and have different levels of access to the AWS Console and API.
    """
    users = schema.Object(
        title='IAM Users',
        schema=IIAMUsers,
        required=False,
    )

class IIAMUserResource(IResource):
    """
IAM User
    """
    allows = schema.List(
        title="Resources to allow this user to access.",
        description="",
        required=True,
        value_type=PacoReference(
            title="Paco reference",
            schema_constraint='Interface',
        ),
    )
    programmatic_access = schema.Object(
        title='Programmatic Access',
        schema = IIAMUserProgrammaticAccess,
        required=False,
    )
    account = PacoReference(
        title="The account where Pipeline tools will be provisioned.",
        required=False,
        schema_constraint=IAccount
    )

class IDeploymentPipelineConfiguration(INamed):
    """
Deployment Pipeline General Configuration
    """
    artifacts_bucket = PacoReference(
        title="Artifacts S3 Bucket Reference",
        description="",
        required=False,
        schema_constraint=IS3Bucket,
    )
    account = PacoReference(
        title="The account where Pipeline tools will be provisioned.",
        required=False,
        schema_constraint=IAccount
    )

class IDeploymentPipelineStageAction(INamed, IEnablable, IMapping):
    """
Deployment Pipeline Source Stage
    """
    taggedValue('contains', 'mixed')
    type = schema.TextLine(
        title='The type of DeploymentPipeline Source Stage',
        required=False,
    )
    run_order = schema.Int(
        title='The order in which to run this stage',
        min=1,
        max=999,
        default=1,
        required=False,
    )

class IDeploymentPipelineSourceCodeCommit(IDeploymentPipelineStageAction):
    """
CodeCommit DeploymentPipeline Source Stage
    """
    taggedValue('contains', 'mixed')
    codecommit_repository = PacoReference(
        title='CodeCommit Respository',
        required=False,
        schema_constraint='ICodeCommitRepository'
    )
    deployment_branch_name = schema.TextLine(
        title="Deployment Branch Name",
        description="",
        default="",
        required=False,
    )

class IDeploymentPipelinePacoCreateThenDeployImage(IDeploymentPipelineStageAction):
    """Paco CreateThenDeployImage Action"""
    taggedValue('contains', 'mixed')
    resource_name = schema.TextLine(
        title="Name of an external resource identifier",
        description="",
        required=True,
        default="",
    )

class IDeploymentPipelineLambdaInvoke(IDeploymentPipelineStageAction):
    """Lambad Invocation Action"""
    taggedValue('contains', 'mixed')
    target_lambda = PacoReference(
        title='Lambda function',
        required=True,
        schema_constraint='ILambda',
    )
    user_parameters = schema.TextLine(
        title="User Parameters string that can be processed by the Lambda",
        description="",
        required=False,
        default="",
    )

class IDeploymentPipelineSourceECR(IDeploymentPipelineStageAction):
    """Amazon ECR DeploymentPipeline Source Stage

This Action is triggered whenever a new image is pushed to an Amazon ECR repository.

.. code-block:: yaml

  pipeline:
    type: DeploymentPipeline
    stages:
      source:
        ecr:
          type: ECR.Source
          enabled: true
          repository:  paco.ref netenv.mynet.applications.myapp.groups.ecr.resources.myecr
          image_tag: "latest"

    """
    taggedValue('contains', 'mixed')
    repository = PacoReference(
        title="An ECRRepository ref or the name of the an ECR repository.",
        required=True,
        str_ok=True,
    )
    image_tag = schema.TextLine(
        title='The name of the tag used for the image.',
        default="latest",
        required=False,
    )

class IDeploymentPipelineSourceGitHub(IDeploymentPipelineStageAction):
    """GitHub DeploymentPipeline Source Stage

To configure a GitHub source, first create an OAuth Personal Access Token in your GitHub account with the scopes
``repo`` and ``admin:repoHook``. See the AWS documentation on how to `Configure Your Pipeline to Use a Personal Access Token`_.

Create a secrets_manager resource in your network environment and set your GitHub personal access token there:

secrets_manager:
  group:
    app:
      github_token:
        enabled: true

After you provision the secret, you must set your GitHub token. You can use `paco set` to do this, or apply
the secret using the Secrets Manager AWS Console.

.. code-block:: bash

  paco set netenv.<netenv-name>.<env-name>.<region>.secrets_manager.<group-name>.<application-name>.github_token

Assign the secert to the ``github_access_token`` GitHub action field by using the secrets_manager reference:

.. code-block:: yaml

  pipeline:
    type: DeploymentPipeline
    stages:
      source:
        github:
          type: GitHub.Source
          enabled: true
          deployment_branch_name: "staging"
          github_access_token: paco.ref netenv.mynet.secrets_manager.group.app.github_token
          github_owner: example
          github_repository: example-app
          poll_for_source_changes: true

"""
    taggedValue('contains', 'mixed')
    deployment_branch_name = schema.TextLine(
        title="The name of the branch where source changes are to be detected.",
        description="",
        default="master",
        required=False
    )
    github_owner = schema.TextLine(
        title='The name of the GitHub user or organization who owns the GitHub repository.',
        required=True
    )
    github_repository = schema.TextLine(
        title='The name of the repository where source changes are to be detected.',
        required=True
    )
    github_access_token = PacoReference(
        title='Secrets Manager Secret with a GitHub access token',
        required=True,
        schema_constraint='ISecretsManagerSecret',
        str_ok=True
    )
    poll_for_source_changes = schema.Bool(
        title='Poll for Source Changes',
        required=False,
        default=True,
    )

class IDeploymentPipelineBuildCodeBuild(IDeploymentPipelineStageAction):
    """
CodeBuild DeploymentPipeline Build Stage
    """
    taggedValue('contains', 'mixed')
    deployment_environment = schema.TextLine(
        title="Deployment Environment",
        description="",
        default="",
        required=False,
    )
    buildspec = schema.TextLine(
        title="buildspec.yml filename",
        required=False,
    )
    codebuild_image = schema.TextLine(
        title='CodeBuild Docker Image',
        required=False,
    )
    codebuild_compute_type = schema.TextLine(
        title='CodeBuild Compute Type',
        constraint = isValidCodeBuildComputeType,
        required=False,
    )
    codecommit_repo_users = schema.List(
        title="CodeCommit Users",
        required=False,
        value_type=PacoReference(
            title="CodeCommit User",
            schema_constraint='ICodeCommitUser'
        )
    )
    timeout_mins = schema.Int(
        title='Timeout in Minutes',
        min=5,
        max=480,
        default=60,
        required=False,
    )
    role_policies = schema.List(
        title='Project IAM Role Policies',
        value_type=schema.Object(IPolicy),
        required=False,
    )
    privileged_mode = schema.Bool(
        title='Privileged Mode',
        default=False,
        required=False
    )
    secrets = schema.List(
        title='List of PacoReferences to Secrets Manager secrets',
        required=False,
        value_type=PacoReference(
            title="Secret Manager Secret"
        )
    )

class IDeploymentPipelineDeployS3(IDeploymentPipelineStageAction):
    """
Amazon S3 Deployment Provider
    """
    taggedValue('contains', 'mixed')
    # BucketName: Required
    bucket = PacoReference(
        title="S3 Bucket Reference",
        required=False,
        schema_constraint='IS3Bucket'
    )
    # Extract: Required: Required if Extract = false
    extract = schema.Bool(
        title="Boolean indicating whether the deployment artifact will be unarchived.",
        default=True,
        required=False,
    )
    # ObjectKey: Required if Extract = false
    object_key = schema.TextLine(
        title="S3 object key to store the deployment artifact as.",
        required=False,
    )
    input_artifacts = schema.List(
        title="Input Artifacts",
        required=False,
        value_type=schema.TextLine(
            title="Stage.Action",
        )
    )
    # KMSEncryptionKeyARN: Optional
    # This is used internally for now.
    #kms_encryption_key_arn = schema.TextLine(
    #    title="The KMS Key Arn used for artifact encryption.",
    #    required=False
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

class IDeploymentPipelineManualApproval(IDeploymentPipelineStageAction):
    """
ManualApproval DeploymentPipeline
    """
    taggedValue('contains', 'mixed')
    manual_approval_notification_email = schema.List(
        title="Manual Approval Notification Email List",
        description="",
        value_type=schema.TextLine(
            title="Manual approval notification email",
            description="",
            default="",
            required=False,
        ),
        required=False
    )

class ICodeDeployMinimumHealthyHosts(INamed):
    """
CodeDeploy Minimum Healthy Hosts
    """
    type = schema.TextLine(
        title="Deploy Config Type",
        default="HOST_COUNT",
        required=False,
    )
    value = schema.Int(
        title="Deploy Config Value",
        default=0,
        required=False,
    )


class IDeploymentPipelineDeployCodeDeploy(IDeploymentPipelineStageAction):
    """
CodeDeploy DeploymentPipeline Deploy Stage
    """
    auto_scaling_group = PacoReference(
        title="ASG Reference",
        required=False,
        schema_constraint='IASG'
    )
    auto_rollback_enabled = schema.Bool(
        title="Automatic rollback enabled",
        description="",
        default=True
    )
    minimum_healthy_hosts = schema.Object(
        title="The minimum number of healthy instances that should be available at any time during the deployment.",
        schema = ICodeDeployMinimumHealthyHosts,
        required=False
    )
    deploy_style_option = schema.TextLine(
        title="Deploy Style Option",
        description="",
        default="WITH_TRAFFIC_CONTROL",
        required=False,
    )
    deploy_instance_role = PacoReference(
        title="Deploy Instance Role Reference",
        required=False,
        schema_constraint='IRole'
    )
    elb_name = schema.TextLine(
        title="ELB Name",
        description="",
        default="",
        required=False,
    )
    alb_target_group = PacoReference(
        title="ALB Target Group Reference",
        required=False,
        schema_constraint='ITargetGroup'
    )

class IDeploymentPipelineDeployECS(IDeploymentPipelineStageAction):
    """
ECS DeploymentPipeline Deploy Stage
    """
    cluster = PacoReference(
        title="ECS Cluster",
        required=True,
        str_ok=False,
        schema_constraint='IECSCluster'
    )
    service = PacoReference(
        title='ECS Service',
        required=True,
        str_ok=False,
        schema_constraint='IECSService'
    )

class IDeploymentPipelineSourceStage(INamed, IMapping):
    """
A map of DeploymentPipeline source stage actions
    """
    taggedValue('contains', 'mixed')

class IDeploymentPipelineBuildStage(INamed, IMapping):
    """
A map of DeploymentPipeline build stage actions
    """
    taggedValue('contains', 'mixed')

class IDeploymentPipelineDeployStage(INamed, IMapping):
    """
A map of DeploymentPipeline deploy stage actions
    """
    taggedValue('contains', 'mixed')

class ICodePipelineStage(INamed, IMapping):
    "Container for different types of DeploymentPipelineStageAction objects."
    taggedValue('contains', 'mixed')

class ICodePipelineStages(INamed, IMapping):
    "Container for `CodePipelineStage`_ objects."
    taggedValue('contains', 'ICodePipelineStage')

class IDeploymentPipeline(IResource):
    """
DeploymentPipeline creates AWS CodePipeline resources configured to act
as CI/CDs to deploy code and assets to application resources. DeploymentPipelines allow you
to express complex CI/CDs with minimal configuration.

A DeploymentPipeline has a number of Actions for three pre-defined Stages: source, build and deploy.
The currently supported list of actions for each stage is:

.. code-block:: yaml
    :caption: Current Actions available by Stage

    source:
      type: CodeCommit.Source
      type: ECR.Source
      type: GitHub.Source
    build:
      type: CodeBuild.Build
    deploy:
      type: CodeDeploy.Deploy
      type: ECS.Deploy
      type: ManualApproval

DeploymentPipelines can be configured to work cross-account and will automatically encrypt
the artifacts S3 Bucket with a KMS-CMK key that can only be accessed by the pipeline.
The ``configuration`` field lets you set the account that the DeploymentPipeline's CodePipeilne
resource will be created in and also specify the S3 Bucket to use for artifacts.

.. code-block:: yaml
    :caption: Configure a DeploymentPipeline to run in the tools account

    configuration:
      artifacts_bucket: paco.ref netenv.mynet.applications.myapp.groups.cicd.resources.artifacts
      account: paco.ref accounts.tools


DeploymentPipeline caveats - there are a few things to consider when creating pipelines:

  * You need to create an S3 Bucket that will be configured to for artifacts. Even pipelines
    which don't create artifacts will need this resource to hold ephemeral files created by CodePipeline.

  * A pipeline that deploys artifacts to an AutoScalingGroup will need the ``artifacts_bucket`` to
    allow the IAM Instance Role to read from the bucket.

  * A pipeline with an ``ECR.Source`` source must be in the same account as the ECR Repository.

  * A pipeline with an ``ECR.Source`` source must have at least one image alreaay created in it before
    it can be created.

  * A pipeline that is building Docker images needs to set ``privileged_mode: true``.

  * If you are using a manual approval step before deploying, pay attention to the
    ``run_order`` field. Normally you will want the approval action to happen before the deploy action.

.. code-block:: yaml
    :caption: Example S3 Bucket for a DeploymentPipeline that deploys to an AutoScalingGroup

    type: S3Bucket
    enabled: true
    order: 10
    bucket_name: "artifacts"
    deletion_policy: "delete"
    account: paco.ref accounts.tools
    versioning: true
    policy:
      - aws:
          - paco.sub '${paco.ref netenv.mynet.applications.myapp.groups.container.resources.asg.instance_iam_role.arn}'
        effect: 'Allow'
        action:
          - 's3:Get*'
          - 's3:List*'
        resource_suffix:
          - '/*'
          - ''

.. code-block:: yaml
    :caption: Example DeploymentPipeline to deploy to ECS when an ECR Repository is updated

    type: DeploymentPipeline
    order: 10
    enabled: true
    configuration:
      artifacts_bucket: paco.ref netenv.mynet.applications.myapp.groups.cicd.resources.artifacts
      account: paco.ref accounts.tools
    source:
      ecr:
        type: ECR.Source
        repository: paco.ref netenv.mynet.applications.myapp.groups.container.resources.ecr_example
        image_tag: latest
    deploy:
      ecs:
        type: ECS.Deploy
        cluster: paco.ref netenv.mynet.applications.myapp.groups.container.resources.ecs_cluster
        service: paco.ref netenv.mynet.applications.myapp.groups.container.resources.ecs_config.services.simple_app

.. code-block:: yaml
    :caption: Example DeploymentPipeline to pull from GitHub, build a Docker image and then deploy from an ECR Repo

    type: DeploymentPipeline
    order: 20
    enabled: true
    configuration:
      artifacts_bucket: paco.ref netenv.mynet.applications.myapp.groups.cicd.resources.artifacts
      account: paco.ref accounts.tools
    source:
      github:
        type: GitHub.Source
        deployment_branch_name: "prod"
        github_access_token: paco.ref netenv.mynet.secrets_manager.myapp.github.token
        github_owner: MyExample
        github_repository: MyExample-FrontEnd
        poll_for_source_changes: false
    build:
      codebuild:
        type: CodeBuild.Build
        deployment_environment: "prod"
        codebuild_image: 'aws/codebuild/standard:4.0'
        codebuild_compute_type: BUILD_GENERAL1_MEDIUM
        privileged_mode: true # To allow docker images to be built
        codecommit_repo_users:
          - paco.ref resource.codecommit.mygroup.myrepo.users.MyCodeCommitUser
        secrets:
          - paco.ref netenv.mynet.secrets_manager.myapp.github.ssh_private_key
        role_policies:
          - name: AmazonEC2ContainerRegistryPowerUser
            statement:
              - effect: Allow
                action:
                  - ecr:GetAuthorizationToken
                  - ecr:BatchCheckLayerAvailability
                  - ecr:GetDownloadUrlForLayer
                  - ecr:GetRepositoryPolicy
                  - ecr:DescribeRepositories
                  - ecr:ListImages
                  - ecr:DescribeImages
                  - ecr:BatchGetImage
                  - ecr:GetLifecyclePolicy
                  - ecr:GetLifecyclePolicyPreview
                  - ecr:ListTagsForResource
                  - ecr:DescribeImageScanFindings
                  - ecr:InitiateLayerUpload
                  - ecr:UploadLayerPart
                  - ecr:CompleteLayerUpload
                  - ecr:PutImage
                resource:
                  - '*'
    deploy:
      ecs:
        type: ECS.Deploy
        cluster: paco.ref netenv.mynet.applications.myapp.groups.container.resources.cluster
        service: paco.ref netenv.mynet.applications.myapp.groups.container.resources.services.services.frontend


.. code-block:: yaml
    :caption: Example DeploymentPipeline to pull from CodeCommit, build an app artifact and then deploy to an ASG using CodeDeploy

    type: DeploymentPipeline
    order: 30
    enabled: true
    configuration:
      artifacts_bucket: paco.ref netenv.mynet.applications.myapp.groups.cicd.resources.artifacts
      account: paco.ref accounts.tools
    source:
      codecommit:
        type: CodeCommit.Source
        codecommit_repository: paco.ref resource.codecommit.mygroup.myrepo
        deployment_branch_name: "prod"
    build:
      codebuild:
        type: CodeBuild.Build
        deployment_environment: "prod"
        codebuild_image: 'aws/codebuild/amazonlinux2-x86_64-standard:1.0'
        codebuild_compute_type: BUILD_GENERAL1_SMALL
    deploy:
      approval:
        type: ManualApproval
        run_order: 1
        manual_approval_notification_email:
          - bob@example.com
          - sally@example.com
      codedeploy:
        type: CodeDeploy.Deploy
        run_order: 2
        alb_target_group: paco.ref netenv.mynet.applications.myapp.groups.backend.resources.alb.target_groups.api
        auto_scaling_group: paco.ref netenv.mynet.applications.myapp.groups.backend.resources.api
        auto_rollback_enabled: true
        minimum_healthy_hosts:
          type: HOST_COUNT
          value: 0
        deploy_style_option: WITHOUT_TRAFFIC_CONTROL

    """
    @invariant
    def stages_or_sourcebuildeploy(obj):
        "Either use stages or source/build/deploy"
        if obj.stages != None:
            if obj.source != None or obj.build != None or obj.deploy != None:
                raise Invalid("Can only specify stages field or the source/build/deploy fields but not both.")

    configuration = schema.Object(
        title='Deployment Pipeline General Configuration',
        schema=IDeploymentPipelineConfiguration,
        required=False,
    )
    source = schema.Object(
        title='Deployment Pipeline Source Stage',
        schema=IDeploymentPipelineSourceStage,
        required=False,
    )
    build = schema.Object(
        title='Deployment Pipeline Build Stage',
        schema=IDeploymentPipelineBuildStage,
        required=False,
    )
    deploy = schema.Object(
        title='Deployment Pipeline Deploy Stage',
        schema=IDeploymentPipelineDeployStage,
        required=False,
    )
    stages = schema.Object(
        title='Stages',
        schema=ICodePipelineStages,
        required=False,
    )

class IDeploymentGroupS3Location(IParent):
    bucket = PacoReference(
        title="S3 Bucket revision location",
        required=False,
        schema_constraint='IS3Bucket'
    )
    bundle_type = schema.TextLine(
        title="Bundle Type",
        description="Must be one of JSON, tar, tgz, YAML or zip.",
        required=False,
        constraint=isValidDeploymentGroupBundleType
    )
    key = schema.TextLine(
        title="The name of the Amazon S3 object that represents the bundled artifacts for the application revision.",
        required=True
    )

class ICodeDeployDeploymentGroups(INamed, IMapping):
    taggedValue('contains', 'mixed')

class ICodeDeployDeploymentGroup(INamed, IDeployable):
    ignore_application_stop_failures = schema.Bool(
        title="Ignore Application Stop Failures",
        required=False,
    )
    revision_location_s3 = schema.Object(
        title="S3 Bucket revision location",
        required=False,
        schema=IDeploymentGroupS3Location
    )
    autoscalinggroups = schema.List(
        title="AutoScalingGroups that CodeDeploy automatically deploys revisions to when new instances are created",
        required=False,
        value_type=PacoReference(
            title="AutoScalingGroup",
            schema_constraint='IASG'
        )
    )
    role_policies = schema.List(
        title="Policies to grant the deployment group role",
        required=False,
        value_type=schema.Object(IPolicy),
    )

class ICodeDeployApplication(IResource):
    """
CodeDeploy Application creates CodeDeploy Application and Deployment Groups for that application.

This resource can be used when you already have another process in-place to put deploy artifacts
into an S3 Bucket. If you also need to build artifacts, use `DeploymentPipeline`_ instead.

.. sidebar:: Prescribed Automation

    **CodeDeploy Service Role**: The AWS CodeDeploy service needs a Service Role that it is allowed to
    assume to allow the service to run in your AWS Account. Paco will automatically create such a service
    role for every CodeDeploy Application.

.. code-block:: yaml
    :caption: Example CodeDeployApplication resource YAML

    type: CodeDeployApplication
    order: 40
    compute_platform: "Server"
    deployment_groups:
      deployment:
        title: "My Deployment Group description"
        ignore_application_stop_failures: true
        revision_location_s3: paco.ref netenv.mynet.applications.app.groups.deploybucket
        autoscalinggroups:
          - paco.ref netenv.mynet.applications.app.groups.web

It can be convienent to install the CodeDeploy agent on your instances using CloudFormationInit.

.. code-block:: yaml
    :caption: Example ASG configuration for cfn_init to install CodeDeploy agent

    launch_options:
      cfn_init_config_sets:
        - "InstallCodeDeploy"
    cfn_init:
      config_sets:
        InstallCodeDeploy:
          - "InstallCodeDeploy"
      files:
        "/tmp/install_codedeploy.sh":
          source: https://aws-codedeploy-us-west-2.s3.us-west-2.amazonaws.com/latest/install
          mode: '000700'
          owner: root
          group: root
      commands:
        01_install_codedeploy:
          command: "/tmp/install_codedeploy.sh auto > /var/log/cfn-init-codedeploy.log 2>&1"
      services:
        sysvinit:
          codedeploy-agent:
            enabled: true
            ensure_running: true

"""
    compute_platform = schema.TextLine(
        title="Compute Platform",
        description="Must be one of Lambda, Server or ECS",
        constraint=isValidCodeDeployComputePlatform,
        required=True
    )
    deployment_groups = schema.Object(
        title="CodeDeploy Deployment Groups",
        schema=ICodeDeployDeploymentGroups,
        required=True,
    )

class IEFS(IResource):
    """
AWS Elastic File System (EFS) resource.

.. code-block:: yaml
    :caption: Example EFS resource

    type: EFS
    order: 20
    enabled: true
    encrypted: false
    segment: private
    security_groups:
      - paco.ref netenv.mynet.network.vpc.security_groups.cloud.content

    """
    encrypted = schema.Bool(
        title='Encryption at Rest',
        default=False
    )
    security_groups = schema.List(
        title="Security groups",
        description="`SecurityGroup`_ the EFS belongs to",
        value_type=PacoReference(
            title="Paco reference",
            schema_constraint='ISecurityGroup'
        ),
        required=True,
    )
    segment = schema.TextLine(
        title="Segment",
        description="",
        required=False,
    )

# AWS Backup

class IBackupPlanRule(INamed):
    schedule_expression = schema.TextLine(
        title="Schedule Expression",
        description="Must be a valid Schedule Expression.",
        required=False
    )
    lifecycle_delete_after_days = schema.Int(
        title="Delete after days",
        required=False,
        min=1
    )
    lifecycle_move_to_cold_storage_after_days = schema.Int(
        title="Move to cold storage after days",
        description="If Delete after days value is set, this value must be smaller",
        required=False,
        min=1
    )

class IBackupSelectionConditionResourceType(IParent):
    condition_type = schema.TextLine(
        title="Condition Type",
        description="String Condition operator must be one of: StringEquals, StringNotEquals, StringEqualsIgnoreCase, StringNotEqualsIgnoreCase, StringLike, StringNotLike.",
        required=True,
        constraint=isValidStringConditionOperator
    )
    condition_key = schema.TextLine(
        title="Tag Key",
        required=True,
        min_length=1
    )
    condition_value = schema.TextLine(
        title="Tag Value",
        required=True,
        min_length=1
    )

class IBackupPlanSelection(IParent):
    title=schema.TextLine(
        title="Title",
        default="",
        required=True,
    )
    tags = schema.List(
        title="List of condition resource types",
        required=False,
        value_type=schema.Object(IBackupSelectionConditionResourceType)
    )
    resources = schema.List(
        title="Backup Plan Resources",
        value_type=PacoReference(
            title="Resource",
            schema_constraint='Interface'
        ),
        required=False,
    )

class IBackupPlan(IResource):
    """
AWS Backup Plan
    """
    plan_rules = schema.List(
        title="Backup Plan Rules",
        value_type=schema.Object(IBackupPlanRule),
        required=True,
    )
    selections = schema.List(
        title="Backup Plan Selections",
        value_type=schema.Object(IBackupPlanSelection),
        required=False
    )

class IBackupPlans(INamed, IMapping):
    """
Container for `BackupPlan`_ objects.
    """
    taggedValue('contains', 'IBackupPlan')

class IBackupVault(IResource):
    """
An AWS Backup Vault.
    """
    notification_events = schema.List(
        title="Notification Events",
        description="Each notification event must be one of BACKUP_JOB_STARTED, BACKUP_JOB_COMPLETED, RESTORE_JOB_STARTED, RESTORE_JOB_COMPLETED, RECOVERY_POINT_MODIFIED",
        value_type=schema.TextLine(
            title="Notification Event"
        ),
        constraint=isValidBackupNotification,
        required=False
    )
    notification_group = schema.TextLine(
        title="Notification Group",
        required=False
    )
    plans = schema.Object(
        title="Backup Plans",
        schema=IBackupPlans,
        required=False
    )

class IBackupVaults(INamed, IMapping):
    """
Container for `BackupVault` objects.
    """
    taggedValue('contains', 'IBackupVault')

