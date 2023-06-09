import json
from typing import Any, Tuple, Type

from dateutil.tz import gettz, tzfile
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class MyCustomSource(EnvSettingsSource):
    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        if field_name == "tz":
            return gettz(value)
        return value
        # return json.loads(value)


class Settings(BaseSettings):
    app_name: str = "lockoff"
    klubmodul_username: str = ""
    klubmodul_password: str = ""
    klubmodul_country_id: int = 1
    klubmodul_club_id: int = 2002
    nonce_size: int = 4
    digest_size: int = 10
    secret: bytes = "changeme"
    opticon_url: str = "loop://?logging=debug"
    display_url: str = "loop://?logging=debug"
    db_member: str = "/db_member.json"
    db_dayticket: str = "/db_dayticket.json"
    certificate: bytes = ""
    key: bytes = ""
    certificate_password: bytes = ""
    wwdr_certificate: bytes = ""
    mailtrap_token: str = ""
    basic_auth_username: bytes = ""
    basic_auth_password: bytes = ""
    current_season: int = 2023
    prod: bool = False
    tz: tzfile = gettz("Europe/Copenhagen")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (MyCustomSource(settings_cls),)


settings = Settings()
