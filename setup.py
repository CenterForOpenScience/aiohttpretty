from setuptools import setup, find_packages


def parse_requirements(requirements):
    with open(requirements) as f:
        return [l.strip('\n') for l in f if l.strip('\n') and not l.startswith('#')]


# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt')
requirements = [str(ir.req) for ir in install_reqs]

setup(
    name='aiohttpretty',
    version='0.0.1',
    description='AioHTTPretty',
    author='',
    author_email='',
    url='https://github.com/CenterForOpenScience/aiohttpretty',
    packages=find_packages(exclude=('tests*', )),
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
)
