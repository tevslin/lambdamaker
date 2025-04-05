
import json
import zipfile
import tempfile
import shutil
import subprocess
import time
from pathlib import Path
import boto3

def load_config(working_dir):
    with open(Path(working_dir) / "config.json") as f:
        return json.load(f)
    
def configure_s3_trigger(working_dir=Path.cwd(), replace=False):
    config = load_config(working_dir)
    lambda_name = config.get("lambda_name")
    bucket_name = config.get("trigger_bucket")
    file_types = config.get("trigger_filetypes")

    if not bucket_name or not file_types:
        print("No S3 trigger configuration found. Skipping trigger setup.")
        return

    print(f"Configuring S3 trigger for Lambda '{lambda_name}' on bucket '{bucket_name}' for types: {file_types}")

    # Retrieve and filter existing configuration first
    s3_client = boto3.client('s3')
    lambda_client = boto3.client('lambda')
    s3_client = boto3.client('s3')
    account_id = boto3.client('sts').get_caller_identity()['Account']
    region = boto3.session.Session().region_name
    lambda_arn = f"arn:aws:lambda:{region}:{account_id}:function:{lambda_name}"
    statement_id = f"S3InvokePermission-{bucket_name}"

    # Retrieve and filter existing configuration
    existing_config = s3_client.get_bucket_notification_configuration(Bucket=bucket_name)
    existing_lambdas = existing_config.get('LambdaFunctionConfigurations', [])

    # Check for existing configs for this Lambda
    existing_for_this_lambda = [conf for conf in existing_lambdas if conf['LambdaFunctionArn'] == lambda_arn]

    if existing_for_this_lambda and not replace:
        print(f"Triggers already exist for Lambda '{lambda_name}' in bucket '{bucket_name}'. Skipping update (replace=False).")
        return

    # Add invoke permission only if we are going to configure triggers
    try:
        lambda_client.add_permission(
            FunctionName=lambda_name,
            StatementId=statement_id,
            Action="lambda:InvokeFunction",
            Principal="s3.amazonaws.com",
            SourceArn=f"arn:aws:s3:::{bucket_name}"
        )
        print(f"Added permission for S3 to invoke Lambda '{lambda_name}' from bucket '{bucket_name}'.")
    except lambda_client.exceptions.ResourceConflictException:
        print(f"Permission already exists for S3 to invoke Lambda '{lambda_name}'.")
        print(f"Permission already exists for S3 to invoke Lambda '{lambda_name}'.")

    # Retrieve and filter existing configuration
    existing_config = s3_client.get_bucket_notification_configuration(Bucket=bucket_name)
    existing_lambdas = existing_config.get('LambdaFunctionConfigurations', [])

    # Check for existing configs for this Lambda
    existing_for_this_lambda = [conf for conf in existing_lambdas if conf['LambdaFunctionArn'] == lambda_arn]

    if existing_for_this_lambda and not replace:
        print(f"Triggers already exist for Lambda '{lambda_name}' in bucket '{bucket_name}'. Skipping update (replace=False).")
        return

    # Keep only configs that are not for this lambda
    retained_configs = [conf for conf in existing_lambdas if conf['LambdaFunctionArn'] != lambda_arn]

    # Add one config per suffix, with each trigger named for its file type
    for ext in file_types:
        ext_clean = ext.lstrip('.')
        retained_configs.append({
            'Id': ext_clean,
            'LambdaFunctionArn': lambda_arn,
            'Events': ['s3:ObjectCreated:*'],
            'Filter': {
                'Key': {
                    'FilterRules': [
                        {'Name': 'suffix', 'Value': ext_clean}
                    ]
                }
            }
        })

    s3_client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            'LambdaFunctionConfigurations': retained_configs
        }
    )

    print(f"Configured trigger(s) for Lambda '{lambda_name}' on bucket '{bucket_name}' with suffix filters: {file_types}")


def create_iam_role(working_dir=Path.cwd(), replace=False):
    config = load_config(working_dir)
    role_name = config["role_name"]
    restrict_buckets = config.get("s3_buckets")

    iam = boto3.client('iam')
    assume_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }

    try:
        role = iam.get_role(RoleName=role_name)
        if not replace:
            print(f"IAM role '{role_name}' already exists. Skipping creation.")
            return role['Role']['Arn']
        iam.delete_role(RoleName=role_name)
        print(f"Deleted existing IAM role '{role_name}'.")
    except iam.exceptions.NoSuchEntityException:
        print(f"IAM role '{role_name}' does not exist. Creating new role.")

    role = iam.create_role(
        RoleName=role_name,
        AssumeRolePolicyDocument=json.dumps(assume_policy)
    )
    print(f"Created IAM role '{role_name}'.")

    iam.attach_role_policy(
        RoleName=role_name,
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
    )
    print("Attached AWSLambdaBasicExecutionRole policy.")

    if restrict_buckets:
        bucket_arns = [f"arn:aws:s3:::{b}" for b in restrict_buckets]
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": bucket_arns}
            ]
        }
        print(f"Adding restricted S3 access policy for buckets: {restrict_buckets}")
    else:
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {"Effect": "Allow", "Action": ["s3:*"], "Resource": ["*"]}
            ]
        }
        print("Adding full S3 access policy.")

    iam.put_role_policy(
        RoleName=role_name,
        PolicyName="LambdaS3AccessPolicy",
        PolicyDocument=json.dumps(s3_policy)
    )
    print("Attached inline S3 access policy.")

    return role['Role']['Arn']

def create_lambda_zip(working_dir=Path.cwd(), mylib_dir=Path.home() / "mylib", replace=False):
    config = load_config(working_dir)
    zip_path = Path(working_dir) / f"{config['lambda_name']}.zip"
    requirements_path = Path(working_dir) / "requirements.txt"
    mylib_files = config.get("mylib_files", [])

    if zip_path.exists() and not replace:
        print(f"Lambda zip '{zip_path.name}' already exists. Skipping rebuild.")
        return zip_path
    if zip_path.exists():
        zip_path.unlink()
        print(f"Removed existing zip file '{zip_path.name}' before rebuild.")

    temp_dir = Path(tempfile.mkdtemp())

    for file in mylib_files:
        src = Path(mylib_dir) / file
        if src.exists():
            shutil.copy(src, temp_dir / file)
            print(f"Copied library file '{file}' from mylib.")
        else:
            print(f"Warning: library file '{file}' not found in '{mylib_dir}'.")

    if requirements_path.exists():
        print("Installing dependencies from requirements.txt...")
        subprocess.check_call([
            "pip", "install", "-r", str(requirements_path), "-t", str(temp_dir)
        ])

    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file_path in temp_dir.rglob('*'):
            zf.write(file_path, arcname=file_path.relative_to(temp_dir))
    print(f"Created Lambda zip package '{zip_path.name}'.")

    shutil.rmtree(temp_dir)
    return zip_path

def create_or_update_lambda(working_dir=Path.cwd(), mylib_dir=Path.home() / "mylib", replace=False):
    config = load_config(working_dir)
    lambda_client = boto3.client('lambda')
    lambda_name = config['lambda_name']
    zip_path = Path(working_dir) / f"{lambda_name}.zip"

    if not zip_path.exists():
        raise FileNotFoundError(f"Expected zip file '{zip_path}' not found. Run create_lambda_zip first.")

    try:
        role_arn = boto3.client('iam').get_role(RoleName=config['role_name'])['Role']['Arn']
    except boto3.client('iam').exceptions.NoSuchEntityException:
        raise ValueError(f"IAM role '{config['role_name']}' not found. Run create_iam_role first.")

    entry_func = f"{Path(config['entry_file']).stem}.{config['entry_func']}"

    env_vars = {}
    env_path = Path(working_dir) / "my.env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
        if env_vars:
            print("Environment variables to be set in Lambda:")
            for key in env_vars:
                print(f"  - {key}")

    def wait_until_ready():
        print("Waiting for Lambda to be ready for next update", end="", flush=True)
        for _ in range(40):  # max 10 minutes
            response = lambda_client.get_function(FunctionName=lambda_name)
            status = response['Configuration']['LastUpdateStatus']
            if status == 'Successful':
                print(" ✓")
                return
            elif status == 'Failed':
                raise RuntimeError(f"Previous update failed for Lambda '{lambda_name}'")
            print(".", end="", flush=True)
            time.sleep(15)
        print()
        raise TimeoutError(f"Lambda function '{lambda_name}' was not ready after 10 minutes")

    try:
        lambda_client.get_function(FunctionName=lambda_name)
        if not replace:
            print(f"Lambda function '{lambda_name}' already exists. Skipping update.")
            return

        lambda_client.update_function_configuration(
            FunctionName=lambda_name,
            Role=role_arn,
            Handler=entry_func,
            Timeout=config['timeout'],
            MemorySize=config['memory_size'],
            EphemeralStorage={'Size': config['ephemeral_storage']},
            Environment={"Variables": env_vars} if env_vars else {}
        )
        print(f"Updated configuration for Lambda function '{lambda_name}'.")

        wait_until_ready()

        lambda_client.update_function_code(
            FunctionName=lambda_name,
            ZipFile=zip_path.read_bytes(),
            Publish=True
        )
        print(f"Updated code for existing Lambda function '{lambda_name}'.")

    except lambda_client.exceptions.ResourceNotFoundException:
        lambda_client.create_function(
            FunctionName=lambda_name,
            Runtime='python3.11',
            Role=role_arn,
            Handler=entry_func,
            Code={'ZipFile': zip_path.read_bytes()},
            Timeout=config['timeout'],
            MemorySize=config['memory_size'],
            EphemeralStorage={'Size': config['ephemeral_storage']},
            Environment={"Variables": env_vars} if env_vars else {},
            Publish=True
        )
        print(f"Created new Lambda function '{lambda_name}'.")

def main(replace=False, working_dir=Path.cwd(), mylib_dir=Path.home() / "mylib"):
    create_iam_role(working_dir, replace)
    create_lambda_zip(working_dir, mylib_dir, replace)
    create_or_update_lambda(working_dir, mylib_dir, replace)
    configure_s3_trigger(working_dir)

if __name__ == '__main__':
    main(working_dir=r"C:\Users\tevsl\goldendome\s3deepgrams3")
