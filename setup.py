#
# Copyright 2014  Didip Kerabat
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Setup script.
"""

from setuptools import setup, find_packages

with open('requirements.txt') as requirements:
    setup(
        name='supervisor-remote-logging',
        version='0.0.1',
        description='Stream supervisord logs various remote endpoints',
        author='Didip Kerabat',
        author_email='didipk@gmail.com',
        url='https://github.com/didip/supervisor-remote-logging',
        license='Apache 2.0',
        long_description=open('README.md').read(),

        packages=find_packages(exclude=['tests']),
        package_data={
            'forklift': [
                'README.md',
                'requirements.txt',
                'test_requirements.txt',
            ],
        },
        entry_points={
            'console_scripts': [
                'supervisor_remote_logging = supervisor_remote_logging:main',
            ],
        },

        install_requires=requirements.read().splitlines(),

        test_suite='tests',
        tests_require=requirements.read().splitlines(),
    )
