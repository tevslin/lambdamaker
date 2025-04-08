# LambdaMaker

**LambdaMaker** is a simple, modular Python utility that automates the creation, packaging, configuration, and deployment of AWS Lambda functions, especially those processing and/or triggered from s3, using only standard Python and `boto3`.

## 🚀 Features

- Package Python-based Lambda functions from local code and dependencies
- Create an IAM role with appropriate permissions
- Deploy the Lambda function to AWS
- Set environment variables from a `.env` file
- Optionally configure S3 bucket triggers for Lambda execution
- Supports a JSON config file for consistent and repeatable deployment

## 📦 Installation

You can install LambdaMaker directly from PyPI:

```bash
pip install lambdamaker
```

## ⚙️ Requirements

LambdaMaker was developed and tested using **Python 3.12**, which is currently supported by AWS Lambda. However, the version can be configured (see `python_version` below).

- You must have valid AWS credentials configured in `~/.aws` (via `aws configure` or similar).
- If using S3 triggers, the S3 bucket must already exist.
- Docker must be installed and running if `use_docker` is set to `true`. If Docker Desktop is required, ensure it is manually started before running.
- If `openai`, `pydantic`, or other compiled dependencies are used, setting `use_docker` is strongly recommended.

## 🔧 Configuration

All routines look for `config.json`, `requirements.txt`, and `my.env` in the **same working directory** by default. You can override this by passing a `working_dir` parameter to any of the functions.

By default, any additional Python source files specified under `mylib_files` in the configuration will be copied from a directory named `mylib` in the user's home folder (`$HOME/mylib`). You may override this by passing the `mylib_dir` parameter with a different path.

If you're using the example project in the `mylambda` folder in this repository, you can run the tool using `working_dir="mylambda"` and `mylib_dir="."` to pick up `helloworld.py` from the same folder.

### Common Parameters

- `replace` (bool, default: `False`): If `True`, existing AWS resources such as the Lambda function, IAM role, or S3 triggers will be updated or replaced. If `False`, existing resources are left untouched.
- `working_dir` (Path or str, optional): Specifies the directory where `config.json`, `requirements.txt`, and `my.env` are located. Defaults to the current working directory.
- `mylib_dir` (Path or str, optional): Directory from which to copy the files listed under `mylib_files`. Defaults to `$HOME/mylib`.
- `use_docker` (bool, default: `False`): Enables Docker-based builds to ensure compatibility with AWS Lambda Linux environment, particularly for packages requiring native binaries. When set to `true`, Docker must be running or the user will be prompted.
- `python_version` (str, default: "3.12"): Specifies the Python runtime for both Docker image used during zip creation and the AWS Lambda deployment.

### Example `config.json`

```json
{
  "lambda_name": "s3lambda",
  "entry_file": "helloworld.py",
  "entry_func": "lambda_handler",
  "mylib_files": ["helloworld.py"],
  "output_dir": ".",
  "memory_size": 128,
  "timeout": 120,
  "ephemeral_storage": 512,
  "role_name": "s3lambda",
  "s3_buckets": ["*"],
  "trigger_bucket": null,
  "trigger_filetypes": [],
  "use_docker": false,
  "python_version": "3.12"
}
```

- The `entry_file` must be either listed in `mylib_files` or included in your `requirements.txt`.
- `my.env` uses standard `.env` file format:

```dotenv
USERNAME=World
```

Environment variables defined here will be injected into your Lambda runtime.

## ✅ Example Usage

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

To use the included sample from the `/mylambda` folder:

```python
main(working_dir="mylambda", mylib_dir="mylambda")
```

## 🔐 IAM and Security

The tool will:
- Automatically create an IAM role if it doesn't exist
- Attach AWSLambdaBasicExecutionRole
- Optionally grant access to S3 buckets (full or restricted)

## 🙣 S3 Triggers

To enable S3 triggers:
- Set `trigger_bucket` to a valid bucket name
- Set `trigger_filetypes` to a list of suffixes like `[".json", ".mp4"]`

The tool will:
- Add invoke permission for the bucket
- Create a trigger per suffix
- Preserve triggers for other Lambda functions on the bucket

---

## 📄 License

MIT License

---

Contributions and issue reports are welcome!
