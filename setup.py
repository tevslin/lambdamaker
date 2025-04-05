from setuptools import setup, find_packages

setup(
    name='lambdamaker',
    version='0.1.0',
    packages=find_packages(),
    install_requires=['boto3'],
    description='A utility for packaging and deploying AWS Lambda functions from config.',
    author='Your Name',
    author_email='your@email.com',
    url='https://github.com/yourusername/lambdamaker',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
