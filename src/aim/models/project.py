import aim.models.applications
import aim.models.networks
import aim.models.resources
from aim.models import schemas
from aim.models.base import Named
from aim.models.schemas import IProject
from zope.interface import implementer
from zope.schema.fieldproperty import FieldProperty


@implementer(IProject)
class Project(Named, dict):
    """AIM Project"""
    aim_project_version = FieldProperty(schemas.IProject["aim_project_version"])

    def __init__(self, name, __parent__):
        super().__init__(name, __parent__)
        self.credentials = aim.models.project.Credentials('credentials', self)
        self.credentials.title = 'Administrator Credentials'
        self.__setitem__('credentials', self.credentials)

        self.network_environments = aim.models.networks.NetworkEnvironments(
            name='ne',
            __parent__=self
        )
        self.network_environments.title = 'Network Environments'
        self.__setitem__('ne', self.network_environments)

        self.accounts = aim.models.accounts.Accounts('accounts', self)
        self.accounts.title = 'Cloud Accounts'
        self.__setitem__('accounts', self.accounts)

        # Init an empty S3Resource in-case there is no Resources/S3.yaml
        self.__setitem__('s3', aim.models.resources.S3Resource())


    def find_object_from_cli(self, controller_type, component_name=None, config_name=None):
        found = None
        CONTROLLER_MAPPING = {
            'NetEnv' : 'ne'
        }
        found = self[CONTROLLER_MAPPING[controller_type]]
        if component_name:
            found = found[component_name]
        if config_name:
            found = found[config_name]
        return found

    def get_all_applications(self):
        """
        Return a list of all applications in the model
        """
        results = []
        for ne in self['ne'].values():
            for env in ne.values():
                for env_reg in env.env_regions.values():
                    for application in env_reg['applications'].values():
                        results.append(application)
        return results

@implementer(schemas.ICredentials)
class Credentials(Named, dict):
    """
    Object attrs:
        - aws_access_key_id : string : AWS Access Key ID
        - aws_secret_access_key : string : AWS Secret Access Key
        - aws_default_region : string : AWS Default Region
        - master_account_id : string : Master AWS Account ID
        - master_admin_iam_username : string : Master Account Admin IAM Username
    """

    aws_access_key_id = FieldProperty(schemas.ICredentials["aws_access_key_id"])
    aws_secret_access_key = FieldProperty(schemas.ICredentials["aws_secret_access_key"])
    aws_default_region = FieldProperty(schemas.ICredentials["aws_default_region"])
    master_account_id = FieldProperty(schemas.ICredentials["master_account_id"])
    master_admin_iam_username = FieldProperty(schemas.ICredentials["master_admin_iam_username"])

    @property
    def mfa_role_arn(self):
        return 'arn:aws:iam::' + self.master_account_id + ':mfa/' + self.master_admin_iam_username

    def __init__(self, name, __parent__):
        super().__init__(name, __parent__)

