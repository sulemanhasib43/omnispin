# Welcome to OMNISPIN

![omnispin](images/omnispin.png)

This is a Zero to Jupyter Hub deployment on Kubernetes(EKS) using AWS CDK in Python.

Acknowledgements: Many thanks to Talha Bin Mansoor, Kashan Baig and Fahad Mustafa for their guidance and code reviews.

## Pre-Requisites and Assumptions  

1. AWS CodeStar Connection Setup with GitHub.
2. Existing Route53 Hosted Zone. It's not mandatroy to pre-exist you can create by adding R53 construct in this code but for this implementation I am assuming it's already there.
3. AWS Cognito Pool should exist to allow authentication into JupyterHub. You should have one test user to verify authentication.
4. JupyterHub uses image with Teradata Kernel but you can use a different image.

## The Implementation

### Self-Mutated Pipeline

I am using AWS Cloud Development Kit (CDK) to create IaC and deploy them using CDK Pipelines which are self-mutated (meaning they will update themselves first). The idea is that after first `cdk deploy` each push to github repository will automatically update the pipeline and then deploy the changes to resources, etc. There is the concept of stages in pipelines. Stage 1 is self-mutated pipeline where cdk builds the artifacts (CloudFormation Templates) and updates the pipeline itself and then subsetquent stages are executed.

### Stages

There are four stages i.e., EKS Deploy, Zero to JupyterHub(Z2JH) Deploy, Create Route53 Records and Create VPC Peering with DataBase.

### EFS Storage

I am using EFS Storage to allow a decoupled Stoage Solution from K8s Nodes. This adds elasticity and sclability to our infrastructure.

### File Structure

* `cdk_pipeline` is the directory where our app exists.
  * [pipeline_stack.py](cdk_pipeline/pipeline_stack.py) has self-mutated pipeline and subsequent stages are appended.
  * [pipeline_app_stage.py](cdk_pipeline/pipeline_app_stage.py) has subsequent stage constructs.
  * [eks_cluster_deploy.py](cdk_pipeline/eks_cluster_deploy.py) creates cluster, adds auto-scaling group, deploys cluster-auto scaler, deploys EFS CSI Driver with EFS File System and Storage Class.
  * [z2jh_deploy.py](cdk_pipeline/z2jh_deploy.py) deploys [Zero To JupyterHub](https://z2jh.jupyter.org/en/stable/) using Helm Charts.
  * [r53_lb_record.py](cdk_pipeline/r53_lb_record.py) creates Route53 Record pointing to JupyterHub LoadBalancer.
  * [td_peering_connection.py](cdk_pipeline/td_peering_connection.py) creates a VPC Peering Connection to Teradata VantageCloud VPC in order to establish DB connection from Jupyter Notebooks to VatageCloud.
  * [cluster_props.py](cdk_pipeline/cluster_props.py) is a file where all the commonly used variables are created. Which then can be referrenced in multiple stages.
* `config` has yaml files which provide evironment(development stage e.g. dev, staging and prod) specific configurations. Configurations which are common across mulitple environments are kept in `common.yaml`.
* `etc` has all the Helm Values or Mainfests which are used by solution.
* `utils` has two files `config_util.py` responsible for getting values from config yamls depending on environment and adding git information and the other file is `stack_util.py` which is responsible for adding tags to pipeline stages.
* `.flake8` is a configuration file for linting support for python files using `flake8`.

### VSCode Extensions

```text
    Name: Flake8
    Id: ms-python.flake8
    Description: Linting support for python files using `flake8`.
    Version: 2023.4.0
    Publisher: Microsoft
    VS Marketplace Link: https://marketplace.visualstudio.com/items?itemName=ms-python.flake8
```

```text
    Name: Black Formatter
    Id: ms-python.black-formatter
    Description: Formatting support for python files using `black`.
    Version: 2022.6.0
    Publisher: Microsoft
    VS Marketplace Link: https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter
```

## CDK

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```shell
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```shell
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```powershell
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```shell
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```shell
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!

## For first time deployement

`cdk deploy -c stage="dev"` for Dev Account
`cdk deploy -c stage="prod"` for Prod Account

## Subsequent deployments

Once CDK pipeline is created; as soon as you push to git the pipeline will trigger automatically
