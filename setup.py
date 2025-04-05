from setuptools import setup, find_packages

setup(
    name='lambdamaker',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['boto3'],
    description='A utility for packaging and deploying AWS Lambda functions from config.',
    author='Tom Evslin',
    url='https://github.com/tevslin/lambdamaker',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
