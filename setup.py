from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='lambdamaker',
    version='0.2.0',
    packages=find_packages(),
    install_requires=['boto3'],
    python_requires='>3.11',
    description='Build and deploy Lambda function with optional S3 integration using simple config',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Tom Evslin',
    url='https://github.com/tevslin/lambdamaker',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    keywords='aws lambda deploy automation s3 cloud boto3',
)
