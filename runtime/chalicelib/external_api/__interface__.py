import functools
import typing

import chalicelib.config as config_module
import chalicelib.util.type_util as type_util
import httpx


class ExternalClientInterface:
    exc_cls: typing.ClassVar[type[Exception]]
    config: typing.ClassVar[config_module.ServiceConfig]

    def __init_subclass__(cls) -> None:
        type_util.check_classvar_initialized(cls, ["exc_cls", "config"])

    @functools.cached_property
    def session(self) -> httpx.Client:
        if not self.config.is_configured():
            raise self.exc_cls(f"{self.__class__.__name__} configuration is not set up properly.")

        return self.config.get_session()
