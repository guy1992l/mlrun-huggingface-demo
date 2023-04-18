import importlib

import mlrun


def assert_build():
    for module_name in [
        "transformers",
        "datasets",
        "optimum",
        "onnx",
        "onnxruntime",
        "onnxoptimizer",
    ]:
        module = importlib.import_module(module_name)
        print(module.__version__)


def create_and_set_project(
    git_source: str,
    name: str = "huggingface-mlrun-demo",
    default_image: str = None,
    user_project: bool = True,
    set_serving: bool = True,
):
    # get/create a project and register the data prep and trainer function in it
    project = mlrun.get_or_create_project(
        name=name, context="./", user_project=user_project
    )

    if project.default_image is None:
        if default_image is None:
            print("Building image for the demo:")
            image_builder = project.set_function(
                "src/project_setup.py",
                name="image-builder",
                handler="assert_build",
                kind="job",
                image="mlrun/ml-models",
                requirements=[
                    "transformers~=4.26.0",
                    "datasets~=2.10.1",
                    "optimum~=1.6.4",
                    "onnx~=1.10.1",
                    "onnxruntime~=1.11.1",
                    "onnxoptimizer~=0.3.8",
                ],
            )
            assert image_builder.deploy()
            default_image = image_builder.spec.image
        project.set_default_image(default_image)

    project.set_source(git_source, pull_at_runtime=True)

    project.set_function(
        "src/data_prep.py",
        name="data-prep",
        handler="prepare_dataset",
        kind="job",
    )
    project.set_function(
        "hub://hugging_face_classifier_trainer",
        name="hugging_face_classifier_trainer",
        kind="job",
    )
    project.set_function(
        "src/serving_test.py",
        name="server-tester",
        handler="model_server_tester",
        kind="job",
    )

    if set_serving:
        serving_function = mlrun.new_function(
            "serving-pretrained",
            kind="serving",
        )
        project.set_function(serving_function, with_repo=True)

        serving_function_staging = mlrun.new_function(
            "serving-trained-onnx",
            kind="serving",
        )
        project.set_function(serving_function_staging, with_repo=True)

    project.set_workflow("training_workflow", "src/training_workflow.py")
    project.save()

    return project
