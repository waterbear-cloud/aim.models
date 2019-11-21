from aim.models import schemas
from aim.models import vocabulary
from aim.models.exceptions import InvalidCFNMapping, InvalidAWSResourceName
from aim.models.locations import get_parent_by_interface
from functools import partial
from zope.interface import implementer
from zope.schema.fieldproperty import FieldProperty
from aim.models.references import Reference, get_model_obj_from_ref
import json
import hashlib
import troposphere
import zope.schema
import zope.schema.interfaces


def interface_seen(seen, iface):
    """Return True if interface already is seen.
    """
    for seen_iface in seen:
        if seen_iface.extends(iface):
            return True
    return False

def most_specialized_interfaces(context):
    """Get interfaces for an object without any duplicates.

    Interfaces in a declaration for an object may already have been seen
    because it is also inherited by another interface.
    """
    declaration = zope.interface.providedBy(context)
    seen = []
    for iface in declaration.flattened():
        if interface_seen(seen, iface):
            continue
        seen.append(iface)
    return seen

def marshall_fieldname_to_troposphere_value(obj, props, troposphere_name, field_name):
    """
    Return a value that can be used in a troposphere Properties dict.

    If field_name is a tuple, the first item is the field_name in the schema and the
    second item is the attribute (typically a @property) to return the modified value.
    """

    if type(field_name) == type(tuple()):
        mapping_field_name = field_name[0]
        mapping_attr_name = field_name[1]
    else:
        mapping_field_name = field_name
        mapping_attr_name = field_name

    for interface in most_specialized_interfaces(obj):
        fields = zope.schema.getFields(interface)
        if mapping_field_name in fields:
            # Field provides type information to help convert to Troposphere type
            field = fields[mapping_field_name]
            value = getattr(obj, mapping_attr_name)
            if zope.schema.interfaces.IBool.providedBy(field) and props[troposphere_name][0] == type(str()):
                if value:
                    return 'true'
                else:
                    return 'false'
            if isinstance(field, zope.schema.Text) and props[troposphere_name][0] == type(dict()):
                try:
                    return json.loads(value)
                except TypeError:
                    return None
            if value == {} or value == []:
                return None
            else:
                return value
        elif hasattr(obj, mapping_field_name):
            # supplied as a base property or attribute - these should return
            # types that troposphere expects
            value = getattr(obj, mapping_field_name)
            if value == {} or value == []:
                return None
            else: return value
        else:
            # Shouldn't get here unless the cfn_mapping is incorrect
            raise InvalidCFNMapping

def get_all_fields(obj):
    """
    Introspect an object for schemas it implements
    and return a dict of {fieldname: field_obj}
    """
    fields = {}
    try:
        # all interfaces implemented by obj
        interfaces = obj.__provides__.__iro__
    except AttributeError:
        # object without interfaces like a plain dict
        return {}
    for interface in interfaces:
        fields.update(zope.schema.getFields(interface))
    return fields

class CFNExport():
    @property
    def cfn_export_dict(self):
        "CloudFormation export dictionary suitable for use in troposphere templates"
        result = {}
        for key, value in self.cfn_mapping.items():
            value = marshall_fieldname_to_troposphere_value(
                self,
                self.troposphere_props,
                key,
                value
            )
            if value != None:
                result[key] = value
        return result

def md5sum(filename=None, str_data=None):
    """Computes and returns an MD5 sum in hexdigest format on a file or string"""
    d = hashlib.md5()
    if filename != None:
        with open(filename, mode='rb') as f:
            for buf in iter(partial(f.read, 128), b''):
                d.update(buf)
    elif str_data != None:
        d.update(bytearray(str_data, 'utf-8'))
    else:
        raise AttributeError("md5sum: Filename or String data expected")

    return d.hexdigest()

@implementer(schemas.IParent)
class Parent(CFNExport):
    "One base class to rule them all"

    def obj_hash(self):
        fields = get_all_fields(self)
        str_data = ''
        for name, obj in fields.items():
            if isinstance(obj, (str, zope.schema.TextLine, zope.schema.Text)):
                value = getattr(self, name)
            if isinstance(obj, (int, float, zope.schema.Int, zope.schema.Float)):
                value = getattr(self, name)
                value = str(value)

            if value != None:
                str_data += value
                value = None
        hash_data = md5sum(str_data=str_data)
        return hash_data

    def __init__(self, __parent__):
        self.__parent__ = __parent__

    @property
    def aim_ref_list(self):
        "List of aim.ref parts"
        obj = self
        parts = []

        # special case for global buckets
        if get_parent_by_interface(obj, schemas.IGlobalResources) and schemas.IS3Bucket.providedBy(obj):
            account = obj.account.split('.')[-1:][0]
            parts = ['resource','s3','buckets', account, obj.region, obj.name]
            return '.'.join(parts)

        parent = obj.__parent__
        while parent != None:
            parts.append(obj.name)
            obj = parent
            parent = obj.__parent__
        parts.reverse()
        return parts

    @property
    def aim_ref_parts(self):
        "Bare aim.ref string to the object"
        parts = self.aim_ref_list
        return '.'.join(parts)

    @property
    def aim_ref(self):
        "aim.ref string to the object"
        return 'aim.ref ' + self.aim_ref_parts

@implementer(schemas.ITitle)
class Title():
    title = FieldProperty(schemas.INamed["title"])

@implementer(schemas.INamed)
class Named(Parent):
    """
    An item which has a name and an optional title.
    A name is a unique, human-readable id.

    Every model is location-aware. This means it has a
    __name__ and __parent__. This lets the object live in
    a hiearchy such as a URL tree for a web application, object database
    or filesystem. AIM uses for the web app.
    """
    name = FieldProperty(schemas.INamed["name"])
    title = FieldProperty(schemas.INamed["title"])

    def __init__(self, name, __parent__):
        super().__init__(__parent__)
        self.name = name
        self.__name__ = self.name

    @property
    def title_or_name(self):
        "It's a Plone classic!"
        if len(self.title) > 0:
            return self.title
        return self.name


@implementer(schemas.IName)
class Name():
    name = FieldProperty(schemas.IName["name"])

@implementer(schemas.IDeployable)
class Deployable():
    """
    A deployable resource
    """
    enabled = FieldProperty(schemas.IDeployable["enabled"])

    def is_enabled(self):
        """
        Returns True in a deployed state, otherwise False.
        Will walk up the tree, and if anything is set to "enabled: false"
        this will return False.
        """
        state = self.enabled
        # if current resource is already "enabled: false" simlpy return that
        if not state: return False

        context = self
        while context is not None:
            override = getattr(context, 'enabled', True)
            # once we encounter something higher in the tree with "enabled: false"
            # the lower resource is always False and we return that
            if not override: return False
            context = getattr(context, '__parent__', None)

        # walked right to the top and enabled is still true
        return True

@implementer(schemas.INameValuePair)
class NameValuePair():
    name = FieldProperty(schemas.INameValuePair['name'])
    value = FieldProperty(schemas.INameValuePair['value'])

class Regionalized():
    "Mix-in to allow objects to identify which account and region they are deployed in"

    @property
    def account_name(self):
        account_cont = get_parent_by_interface(self, schemas.IAccountContainer)
        if account_cont != None:
            return account_cont.name
        env_region = get_parent_by_interface(self, schemas.IEnvironmentRegion)
        project = get_parent_by_interface(self)
        if env_region != None:
            return get_model_obj_from_ref(env_region.network.aws_account, project).name
        raise AttributeError('Could not determine account for {}'.format(self.name))

    @property
    def region_name(self):
        # ALlow an object to override it's region_name
        # for example, Route53HealthCheck hard-codes Metrics to us-east-1
        if hasattr(self, 'overrode_region_name'):
            return self.overrode_region_name
        # region the resource is deployed in
        region = get_parent_by_interface(self, schemas.IRegionContainer)
        if region != None:
            return region.name
        # Global buckets have a region field
        if schemas.IS3Bucket.providedBy(self):
            return self.region
        raise AttributeError('Could not determine region for {}'.format(self.name))

    @property
    def region_full_name(self):
        return vocabulary.aws_regions[self.region_name]['full_name']

    @property
    def region_short_name(self):
        return vocabulary.aws_regions[self.region_name]['short_name']

@implementer(schemas.IDNSEnablable)
class DNSEnablable():
    dns_enabled = FieldProperty(schemas.IDNSEnablable['dns_enabled'])

    def is_dns_enabled(self):
        """
        Returns True in a deployed state, otherwise False.
        Will walk up the tree, and if anything is set to "enabled: false"
        this will return False.
        """
        state = self.dns_enabled
        # if current resource is already "enabled: false" simlpy return that
        if not state: return False

        context = self
        while context is not None:
            override = getattr(context, 'dns_enabled', True)
            # once we encounter something higher in the tree with "enabled: false"
            # the lower resource is always False and we return that
            if not override: return False
            context = getattr(context, '__parent__', None)

        # walked right to the top and enabled is still true
        return True

@implementer(schemas.IType)
class Type():
    type = FieldProperty(schemas.IType['type'])

@implementer(schemas.IResource)
class Resource(Type, Named, Deployable, Regionalized, DNSEnablable):
    "Resource"
    order = FieldProperty(schemas.IResource['order'])
    change_protected = FieldProperty(schemas.IResource['change_protected'])

    def resolve_ref(self, ref):
        return self.resolve_ref_obj.resolve_ref(ref)

    def get_account(self):
        """
        Return the Account object that this resource is provisioned to
        """
        env_reg = get_parent_by_interface(self, schemas.IEnvironmentRegion)
        project = get_parent_by_interface(self, schemas.IProject)
        return get_model_obj_from_ref(env_reg.network.aws_account, project)

    # Resource Name methods

    def big_join(self, str_list, separator_ch, camel_case=False, none_value_ok=False):
        # Camel Case
        new_str = ""
        first = True
        for str_item in str_list:
            if none_value_ok == True and str_item == None:
                continue
            if first == False:
                new_str += separator_ch
            if camel_case == True:
                new_str += str_item[0].upper()+str_item[1:]
            else:
                new_str += str_item
            first = False
        return new_str

    def resource_name_filter(self, name, filter_id, hash_long_names):
        "Checks a name against a filter and raises an InvalidAWSResourceName if it is not a valid AWS name"
        message = None
        max_name_len = None
        if filter_id in [
            'EC2.ElasticLoadBalancingV2.LoadBalancer.Name',
            'EC2.ElasticLoadBalancingV2.TargetGroup.Name']:
            if len(name) > 32:
                max_name_len = 32
                message = "Name must not be longer than 32 characters.",
            elif filter_id.find('LoadBalancer') != -1 and name.startswith('internal-'):
                message = "Name must not start with 'internal-'"
            elif name[-1] == '-' or name[0] == '-':
                message = "Name must not begin or end with a dash."
        elif filter_id in [
            'IAM.Role.RoleName',
            'IAM.ManagedPolicy.ManagedPolicyName']:
            if len(name) > 255:
                max_name_len = 255
                message = "Name must not be longer than 255 characters."
        elif filter_id == 'IAM.Policy.PolicyName':
            if len(name) > 128:
                max_name_len = 128
                message = "Name must not be longer than 128 characters."
        elif filter_id == 'ElastiCache.ReplicationGroup.ReplicationGroupId':
            if len(name) > 40:
                max_name_len = 255
                message = "ReplicationGroupId must be 40 characters or less"
        elif filter_id == 'SecurityGroup.GroupName':
            pass
        else:
            message = 'Unknown filter_id'

        if max_name_len != None and hash_long_names == True:
            message = None
            name_hash = md5sum(str_data=name)[:8].upper()
            name = name_hash + '-' + name[((max_name_len-9)*-1):]

        if message != None:
            raise InvalidAWSResourceName(
                message="{}: {}: {}".format(
                        filter_id,
                        message,
                        name,
                )
            )
        return name

    def resource_char_filter(self, ch, filter_id, remove_invalids=False):
        # Universal check
        if ch.isalnum() == True:
            return ch
        # SecurityGroup Group Name
        # Constraints for EC2-VPC: a-z, A-Z, 0-9, spaces, and ._-:/()#,@[]+=&;{}!$*
        if filter_id == 'SecurityGroup.GroupName':
            if ch in ' ._-:/()#,@[]+=&;{}!$*':
                return ch
        elif filter_id in [
            'IAM.Role.RoleName',
            'IAM.ManagedPolicy.ManagedPolicyName',
            'IAM.Policy.PolicyName']:
            if ch in '_+=,.@-.':
                return ch
        elif filter_id == 'ElastiCache.ReplicationGroup.ReplicationGroupId':
            if ch in '-':
                return ch
        elif filter_id in [
            'EC2.ElasticLoadBalancingV2.LoadBalancer.Name',
            'EC2.ElasticLoadBalancingV2.TargetGroup.Name']:
            # Only alphanum and dases are allowed
            pass
        else:
            raise StackException(AimErrorCode.Unknown, message="Invalid filter Id: "+filter_id)

        if remove_invalids == True:
            return ''

        # By default return a '-' for invalid characters
        return '-'

    def create_cfn_logical_id(self, camel_case=False):
        "The logical ID must be alphanumeric (A-Za-z0-9) and unique within the template."
        name = self.type + self.name
        return self.create_resource_name(name, remove_invalids=True, camel_case=camel_case).replace('-', '')

    def create_resource_name(
        self,
        name,
        remove_invalids=False,
        filter_id=None,
        hash_long_names=False,
        camel_case=False):
        """
        Resource names are only alphanumberic (A-Za-z0-9) and dashes.
        Invalid characters are removed or changed into a dash.
        """
        def normalize(name, remove_invalids, filter_id, camel_case):
            uppercase_next_char = False
            new_name = ''
            for ch in name:
                if filter_id != None:
                    ch = self.resource_char_filter(ch, filter_id, remove_invalids)
                    if ch == '' and camel_case == True:
                        uppercase_next_char = True
                elif ch.isalnum() == True:
                    ch = ch
                elif remove_invalids == False:
                    ch = '-'
                elif remove_invalids == True:
                    ch = ''
                    if camel_case == True:
                        uppercase_next_char = True

                if remove_invalids == True and ch != '' and uppercase_next_char == True:
                    new_name += ch.upper()
                    uppercase_next_char = False
                else:
                    new_name += ch
            return new_name

        if name.isalnum() == True:
            new_name = name
        else:
            new_name = normalize(
                name,
                remove_invalids=remove_invalids,
                filter_id=filter_id,
                camel_case=camel_case
            )
        if filter_id != None:
            new_name = self.resource_name_filter(
                new_name,
                filter_id,
                hash_long_names
            )

        return new_name

    def create_resource_name_join(
        self,
        name_list,
        separator,
        camel_case=False,
        filter_id=None,
        hash_long_names=False
    ):
        name = self.big_join(name_list, separator, camel_case)
        return self.create_resource_name(
            name,
            filter_id=filter_id,
            hash_long_names=hash_long_names,
            camel_case=camel_case
        )


@implementer(schemas.IAccountRef)
class AccountRef():
    account = FieldProperty(schemas.IAccountRef['account'])


@implementer(schemas.IAccountContainer)
class AccountContainer(Named, Regionalized, dict):
    pass

@implementer(schemas.IRegionContainer)
class RegionContainer(Named, Regionalized, dict):
    alarm_sets = FieldProperty(schemas.IRegionContainer['alarm_sets'])
