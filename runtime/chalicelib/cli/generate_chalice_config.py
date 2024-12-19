import hashlib
import pathlib

import chalicelib.config as config_module

BUF_SIZE = 65536

CLI_PATH = pathlib.Path(__file__).parent
RUNTIME_PATH = CLI_PATH.parent.parent
CHALICE_CONF_DIR = RUNTIME_PATH / ".chalice"
CHALICE_CONF_PATH = CHALICE_CONF_DIR / "config.json"
CHALICE_CONF_BACKUP_PATH = CHALICE_CONF_DIR / "config.json.bak"


def generate_chalice_config() -> None:
    if not CHALICE_CONF_DIR.exists():
        CHALICE_CONF_DIR.mkdir()

    if CHALICE_CONF_PATH.exists():
        CHALICE_CONF_PATH.rename(CHALICE_CONF_BACKUP_PATH)

    CHALICE_CONF_PATH.write_text(
        data=config_module.config.chalice_config.model_dump_json(
            indent=2,
            exclude_none=True,
            by_alias=True,
        )
    )

    if CHALICE_CONF_BACKUP_PATH.exists():
        curr_file_md5 = hashlib.md5(string=CHALICE_CONF_PATH.read_bytes(), usedforsecurity=False).hexdigest()
        backup_file_md5 = hashlib.md5(string=CHALICE_CONF_BACKUP_PATH.read_bytes(), usedforsecurity=False).hexdigest()

        if curr_file_md5 == backup_file_md5:
            print("No changes detected in chalice config.")
            CHALICE_CONF_BACKUP_PATH.unlink()
        else:
            print("Chalice config updated.")
    else:
        print("Chalice config generated.")


cli_funcs = [generate_chalice_config]
