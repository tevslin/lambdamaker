# LambdaMaker

**LambdaMaker** is a simple, modular Python utility that automates the creation, packaging, configuration, and deployment of AWS Lambda functions using only standard Python and `boto3`.

## 🚀 Features

- Package Python-based Lambda functions from local code and dependencies
- Create an IAM role with appropriate permissions
- Deploy the Lambda function to AWS
- Set environment variables from a `.env` file
- Optionally configure S3 bucket triggers for Lambda execution
- Supports a JSON config file for consistent and repeatable deployment

## 📦 Installation

> LambdaMaker will be available on PyPI shortly. You will be able to install it with:

```bash
pip install lambdamaker
```

## ⚙️ Requirements

- You must have valid AWS credentials configured in `~/.aws` (via `aws configure` or similar).
- If using S3 triggers, the S3 bucket must already exist.

## 🔧 Configuration

Use a `config.json` file in your working directory. Example:

```json
{
  "lambda_name": "s3lambda",
  "entry_file": "s3lambda.py",
  "entry_func": "lambda_handler",
  "mylib_files": ["s3lambda.py"],
  "output_dir": ".",
  "memory_size": 128,
  "timeout": 120,
  "ephemeral_storage": 512,
  "role_name": "s3lambda",
  "s3_buckets": ["*"],
  "trigger_bucket": null,
  "trigger_filetypes": null
}
```

- The `entry_file` must be either listed in `mylib_files` or included in your `requirements.txt`.
- `my.env` uses standard `.env` file format:

```dotenv
API_KEY=abcdef123456
DEBUG=true
ENVIRONMENT=production
```

Environment variables defined here will be injected into your Lambda runtime.

## ✅ Example Usage

### About `replace`
The `replace` parameter (default `False`) controls whether existing AWS resources (like the Lambda function or IAM role) should be updated if they already exist.
- When `replace=False`, existing resources are left untouched.
- When `replace=True`, the tool will overwrite existing configurations and Lambda code.

Use `replace=True` cautiously in production environments.

```python
from lambdamaker import (
    create_iam_role,
    create_lambda_zip,
    create_or_update_lambda,
    configure_s3_trigger
)

create_iam_role()
create_lambda_zip()
create_or_update_lambda()
configure_s3_trigger()
```

Or call the main function:

```python
from lambdamaker import main
main()  # safer default: replace=False
```

## 🔐 IAM and Security

The tool will:
- Automatically create an IAM role if it doesn't exist
- Attach AWSLambdaBasicExecutionRole
- Optionally grant access to S3 buckets (full or restricted)

## 🪣 S3 Triggers

To enable S3 triggers:
- Set `trigger_bucket` to a valid bucket name
- Set `trigger_filetypes` to a list of suffixes like `[".json", ".mp4"]`

The tool will:
- Add invoke permission for the bucket
- Create a trigger per suffix
- Preserve triggers for other Lambda functions on the bucket

## 📄 License

MIT License

---

Contributions and issue reports are welcome. PyPI publishing is coming soon!


