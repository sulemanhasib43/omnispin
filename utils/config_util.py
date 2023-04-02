from typing import Dict
import re
from benedict import benedict
import os

# Load configuration and merge common conf and specific stage config.


def load_config(stage: str) -> Dict:
    # Load common file
    try:
        common_config = benedict.from_yaml("config/common.yaml")
    except ValueError:
        print("No config found in config/common.yaml.")
        common_config = benedict([])

    # Load stage specific file
    try:
        env_config = benedict.from_yaml("config/" + stage + ".yaml")
    except ValueError:
        print("No config found in config/" + stage + ".yaml")
        env_config = benedict([])

    # merge the configs
    common_config.merge(env_config)

    # extract stage to set env
    common_config["stage"] = stage

    return common_config


def add_commit_info_to_config(config: Dict) -> Dict:

    config["tags"]["git:repo"] = re.sub(
        r"[^a-zA-Z0-9 _.:/=+\-@]+", "", os.environ.get("GIT_REPO", "local")
    )
    config["tags"]["git:branch"] = re.sub(
        r"[^a-zA-Z0-9 _.:/=+\-@]+", "", os.environ.get("GIT_BRANCH", "local")
    )
    config["tags"]["git:commitid"] = re.sub(
        r"[^a-zA-Z0-9 _.:/=+\-@]+", "", os.environ.get("GIT_COMMIT_ID", "local")
    )
    config["tags"]["git:commitmessage"] = re.sub(
        r"[^a-zA-Z0-9 _.:/=+\-@]+", "", os.environ.get("GIT_COMMIT_MESSAGE", "local")
    )
    config["tags"]["git:connectionarn"] = re.sub(
        r"[^a-zA-Z0-9 _.:/=+\-@]+", "", os.environ.get("GIT_CONNECTION_ARN", "local")
    )
    config["tags"]["git:authordate"] = re.sub(
        r"[^a-zA-Z0-9 _.:/=+\-@]+", "", os.environ.get("GIT_COMMIT_AUTHOR", "local")
    )

    return config
