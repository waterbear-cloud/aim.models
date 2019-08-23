"""
References
"""

import re, os, pathlib
import zope.schema
from aim.models import vocabulary
from aim.models.exceptions import InvalidAimReference
import ruamel.yaml
from ruamel.yaml.compat import StringIO
from zope.schema.interfaces import ITextLine
from zope.interface import implementer, Interface
from operator import itemgetter

class YAML(ruamel.yaml.YAML):
    def dump(self, data, stream=None, **kw):
        dumps = False
        if stream is None:
            dumps = True
            stream = StringIO()
        ruamel.yaml.YAML.dump(self, data, stream, **kw)
        if dumps:
            return stream.getvalue()

def is_ref(aim_ref):
    """Determines if the string value is an AIM Reference"""

    if aim_ref.startswith('aim.ref ') == False:
        return False
    ref_types = ["netenv", "resource", "accounts", "function", "service"]
    for ref_type in ref_types:
        if aim_ref.startswith('aim.ref %s.' % ref_type):
            return True
    return False

class FileReference(zope.schema.Text):
    """Path to a file on the filesystem"""

    def constraint(self, value):
        """
        Validate that the path resolves to a file on the filesystem
        """
        return True
        # ToDo: how to get the AIM HOME and change to that directory from here?
        #path = pathlib.Path(value)
        #return path.exists()


class TextReference(zope.schema.Text):

    def __init__(self, *args, **kwargs):
        self.str_ok = False
        if 'str_ok' in kwargs.keys():
            self.str_ok = kwargs['str_ok']
            del kwargs['str_ok']
        super().__init__(*args, **kwargs)

    def constraint(self, value):
        """
        Limit text to the format 'word.ref chars_here.more-chars.finalchars100'
        """
#        if value.find('patch.<account>.<region>.applications.patch.groups.lambda.resources.snstopic.arn') != -1:
        if self.str_ok and is_ref(value) == False:
            if isinstance(value, str) == False:
                return False
            return True

        return is_ref(value)

        match = re.match("(\w+)\.ref\s+(.*)", value)
        if match:
            ref_type, ref_value = match.groups()
            if ref_type not in ('resource','service','netenv','config', 'function'):
                return False
            for part in ref_value.split('.'):
                if not re.match("[\w-]+", part):
                    return False
            return True
        else:
            return False

class Reference():
    """
    Reference to something in the aim.model

    attributes:
      raw : original reference str : 'aim.ref netenv.aimdemo.network.vpc.security_groups.app.lb'
      type : reference type str : 'netenv'
      parts : list of ref parts : ['netenv', 'aimdemo', 'network', 'vpc', 'security_groups', 'app', 'lb']
      ref : reffered string : 'netenv.aimdemo.network.vpc.security_groups.app.lb'
    """

    def __init__(self, value):
        self.raw = value
        #match = re.match("aim\.ref\s+(.*)", value)
        self.ref = value.split(' ', 2)[1]
        self.parts = self.ref.split('.')
        self.type = self.parts[0]
        # resource_ref is the tail end of the reference that is
        # relevant to the Resource it references
        self.resource = None
        self.resource_ref = None
        self.region = None

        if self.type == 'netenv':
            if self.parts[3] in vocabulary.aws_regions.keys():
                self.region = self.parts[3]

        if is_ref(self.raw) == False:
            print("Invalid AIM Reference: %s" % (value))
            #raise StackException(AimErrorCode.Unknown)

    @property
    def last_part(self):
        return self.parts[-1]

    def next_part(self, search_ref):
        search_parts = search_ref.split('.')
        first_found = False
        for ref_part in self.parts:
            if first_found == True:
                if search_idx == len(search_parts):
                    return ref_part
                elif ref_part == search_parts[search_idx]:
                    search_idx += 1
            elif ref_part == search_parts[0]:
                first_found = True
                search_idx = 1

        return None

    def sub_part(self, part, value):
        self.raw = self.raw.replace(part, value)
        self.ref = self.ref.replace(part, value)
        self.parts = self.ref.split('.')

    def set_account_name(self, account_name):
        self.sub_part('<account>', account_name)

    def set_region(self, region):
        self.sub_part('<region>', region)

    def resolve(self, project, account_ctx=None):
        return resolve_ref(
            ref_str=None,
            project=project,
            account_ctx=account_ctx,
            ref=self
        )

def get_resolve_ref_obj(obj, ref, part_idx_start):
    """
    Traverses the reference parts looking for the last child that
    is a not a string. This object is expected to be a part of the
    model and should have a resolve_ref method that can be called.
    """
    for part_idx in range(part_idx_start, len(ref.parts)):
        try:
            next_obj = obj[ref.parts[part_idx]]
        except (TypeError, KeyError):
            next_obj = getattr(obj, ref.parts[part_idx], None)
        if next_obj != None and isinstance(next_obj, str) == False:
            obj = next_obj
        else:
            break

    ref.resource_ref = '.'.join(ref.parts[part_idx:])
    ref.resource = obj
    try:
        response = obj.resolve_ref(ref)
    except AttributeError:
        raise InvalidAimReference("Invalid AIM Reference for resource: {0}: '{1}'".format(type(obj), ref.raw))
    return response

def resolve_ref_outputs(ref, project_folder):
    key = ref.parts[0]
    outputs_path = pathlib.Path(
            os.path.join(
                project_folder,
                'Outputs',
                key+'.yaml'
            ))
    if outputs_path.exists() == False:
        return None

    yaml = YAML(typ="safe", pure=True)
    yaml.default_flow_sytle = False
    with open(outputs_path, "r") as output_fd:
        outputs_dict = yaml.load(output_fd)

    for part in ref.parts:
        if part not in outputs_dict.keys():
            break
        node = outputs_dict[part]
        outputs_dict = node
        if len(list(node.keys())) == 1 and '__name__' in node.keys():
            return node['__name__']

    return None

def resolve_ref(ref_str, project, account_ctx=None, ref=None):
    """Resolve a reference"""
    if ref == None:
        ref = Reference(ref_str)
    ref_value = None
    if ref.type == "resource":
        if ref.parts[1] == 's3':
            ref_value = get_resolve_ref_obj(project['s3'], ref, part_idx_start=2)
        else:
            ref_value = project[ref.parts[1]].resolve_ref(ref)
    elif ref.type == "service":
        if ref.parts[4] == 'applications':
            obj = project[ref.parts[1]]
            response = get_resolve_ref_obj(obj, ref, part_idx_start=4)
            ref_value = response
        else:
            ref_value = project[ref.parts[1]].resolve_ref(ref)
    elif ref.type == "netenv":
        # examples:
        # aim.ref netenv.aimdemo.applications.app.resources.webapp.name
        # aim.ref netenv.aimdemo.applications.app.resources.alb.dns.ssl_certificate.arn
        # aim.ref netenv.aimdemo.iam.app.roles.instance_role.name
        # aim.ref netenv.aimdemo.iam.app.roles.instance_role.arn
        # aim.ref netenv.aimdemo.iam.app.roles.instance_role.profile
        # aim.ref netenv.aimdemo.network.vpc.security_groups.app.bastion
        # aim.ref netenv.aimdemo.network.vpc.security_groups.app.webapp
        # aim.ref netenv.aimdemo.network.vpc.security_groups.app.webapp
        #
        # first two parts are transposed - flip them around before resolving
        #ref.parts[0], ref.parts[1] = ref.parts[1], ref.parts[0]
        obj = project['netenv'][ref.parts[1]][ref.parts[2]][ref.parts[3]]
        ref_value = get_resolve_ref_obj(obj, ref, 4)


    elif ref.type == "accounts":
        ref_value = resolve_accounts_ref(ref, project)
    elif ref.type == "function":
        ref_value = resolve_function_ref(ref, project, account_ctx)
    else:
        raise ValueError("Unsupported ref type: {}".format(ref.type))

    # If the reference returned a Stack, and that Stack has not been
    # modified by checking is_stack_cached(), then check the outputs
    # to see if a value is there and return it. Otherwise continue
    # to deal with waiting for new stack outputs.
    if 'home' in project.keys():
        value_type = "{}".format(type(ref_value))
        if value_type == "<class 'aim.stack_group.stack_group.Stack'>":
            if ref_value.is_stack_cached():
                outputs_value = resolve_ref_outputs(ref, project['home'])
                if outputs_value != None:
                    return outputs_value
    return ref_value


def resolve_function_ref(ref, project, account_ctx):
    if account_ctx == None:
        return None
    if ref.ref.startswith('function.aws.ec2.ami.latest'):
        ami_description = None
        ami_name = None
        if ref.last_part == 'amazon-linux-2':
            ami_description = "Amazon Linux 2 AMI*"
            ami_name = 'amzn2-ami-hvm-*'
        elif ref.last_part == 'amazon-linux':
            ami_description = "Amazon Linux AMI*"
            ami_name = 'amzn-ami-hvm-*'
        else:
            raise ValueError("Unsupported AMI Name: {}".format(ref.last_part))

        ec2_client = account_ctx.get_aws_client('ec2')
        filters = [ {
            'Name': 'name',
            'Values': [ami_name]
        },{
            'Name': 'description',
            'Values': [ami_description]
        },{
            'Name': 'architecture',
            'Values': ['x86_64']
        },{
            'Name': 'owner-alias',
            'Values': ['amazon']
        },{
            'Name': 'owner-id',
            'Values': ['137112412989']
        },{
            'Name': 'state',
            'Values': ['available']
        },{
            'Name': 'root-device-type',
            'Values': ['ebs']
        },{
            'Name': 'virtualization-type',
            'Values': ['hvm']
        },{
            'Name': 'hypervisor',
            'Values': ['xen']
        },{
            'Name': 'image-type',
            'Values': ['machine']
        } ]

        ami_list= ec2_client.describe_images(
            Filters=filters,
            Owners=[
                'amazon'
            ]
        )
        # Sort on Creation date Desc
        image_details = sorted(ami_list['Images'],key=itemgetter('CreationDate'),reverse=True)
        ami_id = image_details[0]['ImageId']
        return ami_id

def resolve_accounts_ref(ref, project):
    "Return an IAccount object from the model."
    try:
        account = project[ref.parts[0]][ref.parts[1]]
    except KeyError:
        raise InvalidAimReference("Can not resolve the reference '{}'".format(ref.raw))

    return account.resolve_ref(ref)

