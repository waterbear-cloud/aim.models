from setuptools import setup

with open('README.md') as f:
    long_description = f.read()
    long_description += '\n\n'
with open('CHANGELOG.md') as f:
    long_description += f.read()

setup(
    name='paco.models',
    version='6.2.1',
    description='paco.models: Semantic cloud infrastructure configuration file format and object model',
    author='Waterbear Cloud',
    author_email='hello@waterbear.cloud',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/waterbear-cloud/paco.models',
    install_requires=['Setuptools', 'ruamel.yaml', 'zope.schema'],
    packages=[
        'paco.models',
    ],
    keywords=['AWS','Cloud','Infrastructure as Code'],
    classifiers=[
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Development Status :: 5 - Production/Stable',
    ],
    include_package_data=True,
    zip_safe=False,
    package_dir={'': 'src'},
)
