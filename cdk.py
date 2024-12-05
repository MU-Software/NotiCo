import json
import os
import pathlib
import typing

import aws_cdk
import chalice.api
import chalice.cdk

import runtime.chalicelib.config as config_module

RUNTIME_DIR = pathlib.Path(__file__).parent / "runtime"
DOCKER_TAG = os.environ.get("DOCKER_TAG", "latest")


class CDKStackKeywordArguments(typing.TypedDict):
    analytics_reporting: typing.NotRequired[bool | None]
    cross_region_references: typing.NotRequired[bool | None]
    description: typing.NotRequired[str | None]
    env: typing.NotRequired[aws_cdk.Environment | dict[str, typing.Any] | None]
    permissions_boundary: typing.NotRequired[aws_cdk.PermissionsBoundary | None]
    stack_name: typing.NotRequired[str | None]
    suppress_template_indentation: typing.NotRequired[bool | None]
    synthesizer: typing.NotRequired[aws_cdk.IStackSynthesizer | None]
    tags: typing.NotRequired[dict[str, str] | None]
    termination_protection: typing.NotRequired[bool | None]


class SamTemplateType(typing.TypedDict):
    Resources: dict[str, dict[str, typing.Any]]
    Properties: dict[str, typing.Any]
    Outputs: dict[str, typing.Any]


class DockerizedChaliceKeywordArguments(typing.TypedDict):
    source_dir: typing.NotRequired[str]
    stage_config: typing.NotRequired[dict[str, typing.Any]]
    preserve_logical_ids: typing.NotRequired[bool]


class DockerizedChalice(chalice.cdk.Chalice):
    ecr_repo: aws_cdk.aws_ecr.Repository

    def __init__(
        self,
        scope: aws_cdk.App,
        id: str,
        ecr_repo: aws_cdk.aws_ecr.Repository,
        **kwargs: typing.Unpack[DockerizedChaliceKeywordArguments],
    ) -> None:
        self.ecr_repo: aws_cdk.aws_ecr.Repository = ecr_repo
        super().__init__(scope, id, **kwargs)

    def _generate_sam_template_with_assets(self, chalice_out_dir: str, package_id: str) -> str:
        sam_template_path = os.path.join(self._sam_package_dir, "sam.json")
        sam_template_with_assets_path = os.path.join(chalice_out_dir, "%s.sam_with_assets.json" % package_id)

        with open(sam_template_path) as sam_template_file:
            sam_template: SamTemplateType = json.load(sam_template_file)

            for function_logical_id, function in self._filter_resources(sam_template, "AWS::Serverless::Function"):
                handler = function["Properties"]["Handler"]
                for key in ("Runtime", "CodeUri", "Handler"):
                    function["Properties"].pop(key, None)

                function["Properties"].update(
                    {
                        "PackageType": "Image",
                        "ImageUri": f"{self.ecr_repo.repository_uri}:{DOCKER_TAG}",
                        "ImageConfig": {"Command": [handler]},
                    }
                )

                if function_logical_id != "APIHandler":
                    # make sure the function has an output
                    sam_template["Outputs"].update(
                        {
                            f"{function_logical_id}Name": {"Value": {"Ref": function_logical_id}},
                            f"{function_logical_id}Arn": {"Value": {"Fn::GetAtt": [function_logical_id, "Arn"]}},
                        }
                    )

        pathlib.Path(sam_template_with_assets_path).write_text(json.dumps(sam_template, indent=2))
        return sam_template_with_assets_path

    def _filter_resources(
        self, template: SamTemplateType, resource_type: str
    ) -> list[tuple[str, dict[str, typing.Any]]]:
        return [(k, v) for k, v in template["Resources"].items() if v["Type"] == resource_type]


class NoticoQueue(aws_cdk.Stack):
    queue: aws_cdk.aws_sqs.Queue

    def __init__(
        self,
        scope: aws_cdk.App,
        id: str,
        config: config_module.Config,
        **kwargs: typing.Unpack[CDKStackKeywordArguments],
    ) -> None:
        super().__init__(scope=scope, id=id, **kwargs)
        self.queue = aws_cdk.aws_sqs.Queue(
            scope=self,
            id=config.infra.queue_name,
            queue_name=config.infra.queue_name,
            visibility_timeout=aws_cdk.Duration.seconds(amount=config.infra.queue_visibility_timeout_second),
            fifo=True,
            dead_letter_queue=aws_cdk.aws_sqs.DeadLetterQueue(
                max_receive_count=config.infra.queue_max_receive_count,
                queue=aws_cdk.aws_sqs.Queue(
                    scope=self,
                    id=config.infra.dlq_name,
                    queue_name=config.infra.dlq_name,
                    visibility_timeout=aws_cdk.Duration.seconds(amount=config.infra.dlq_visibility_timeout_second),
                    fifo=True,
                ),
            ),
        )


class NotiCoS3(aws_cdk.Stack):
    s3_bucket: aws_cdk.aws_s3.Bucket

    def __init__(
        self,
        scope: aws_cdk.App,
        id: str,
        config: config_module.Config,
        **kwargs: typing.Unpack[CDKStackKeywordArguments],
    ) -> None:
        super().__init__(scope=scope, id=id, **kwargs)
        self.s3_bucket = aws_cdk.aws_s3.Bucket(
            scope=self,
            id=config.infra.ecr_repo_name,
            bucket_name=config.infra.s3_bucket_name,
        )


class NotiCoEcr(aws_cdk.Stack):
    ecr_repo: aws_cdk.aws_ecr.Repository

    def __init__(
        self,
        scope: aws_cdk.App,
        id: str,
        config: config_module.Config,
        **kwargs: typing.Unpack[CDKStackKeywordArguments],
    ) -> None:
        super().__init__(scope=scope, id=id, **kwargs)
        self.ecr_repo = aws_cdk.aws_ecr.Repository(
            scope=self,
            id=config.infra.ecr_repo_name,
            repository_name=config.infra.ecr_repo_name,
            removal_policy=aws_cdk.RemovalPolicy.DESTROY,
            lifecycle_rules=[
                aws_cdk.aws_ecr.LifecycleRule(
                    max_image_count=3,
                    tag_status=aws_cdk.aws_ecr.TagStatus.ANY,
                ),
            ],
        )


class NotiCoApp(aws_cdk.Stack):
    def __init__(
        self,
        scope: aws_cdk.App,
        id: str,
        queue: aws_cdk.aws_sqs.Queue,
        ecr_repo: aws_cdk.aws_ecr.Repository,
        s3_bucket: aws_cdk.aws_s3.Bucket,
        config: config_module.Config,
        **kwargs: typing.Unpack[CDKStackKeywordArguments],
    ) -> None:
        super().__init__(scope=scope, id=id, **kwargs)

        app = DockerizedChalice(
            scope=self,
            id=config.infra.lambda_name,
            source_dir=RUNTIME_DIR.resolve().absolute().as_posix(),
            ecr_repo=ecr_repo,
            stage_config={
                "automatic_layer": True,
                "environment_variables": config.env_vars,
            },
        )
        app_default_role = app.get_role("DefaultRole")
        queue.grant_consume_messages(grantee=app_default_role)
        s3_bucket.grant_read(identity=app_default_role)
        app_default_role.add_to_principal_policy(
            statement=aws_cdk.aws_iam.PolicyStatement(
                actions=["ses:SendEmail", "SES:SendRawEmail"],
                resources=["*"],
                effect=aws_cdk.aws_iam.Effect.ALLOW,
            ),
        )


if __name__ == "__main__":
    config = config_module.config
    app = aws_cdk.App()
    notico_queue = NoticoQueue(scope=app, id="notico-queue", config=config)
    notico_ecr = NotiCoEcr(scope=app, id="notico-ecr", config=config)
    notico_s3 = NotiCoS3(scope=app, id="notico-s3", config=config)
    notico_app = NotiCoApp(
        scope=app,
        id="notico-app",
        config=config,
        queue=notico_queue.queue,
        ecr_repo=notico_ecr.ecr_repo,
        s3_bucket=notico_s3.s3_bucket,
    )
    notico_app.add_dependency(notico_queue)
    notico_app.add_dependency(notico_ecr)
    notico_app.add_dependency(notico_s3)
    app.synth()
