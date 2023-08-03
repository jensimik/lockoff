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
        elif field_name == "admin_user_ids":
            if value:
                return [int(v) for v in value.split()]
        return value
        # return json.loads(value)


class Settings(BaseSettings):
    app_name: str = "lockoff"
    klubmodul_username: str = ""
    klubmodul_password: str = ""
    klubmodul_base_url: str = ""
    klubmodul_admin_user_id: int = 3535  # change to your own user_id for the admin user
    hash_salt: str = "changeme"
    nonce_size: int = 4
    digest_size: int = 10
    dl_nonce_size: int = 2
    dl_digest_size: int = 5
    dl_secret: bytes = "changeme"
    secret: bytes = "changeme"
    jwt_secret: str = ""
    opticon_url: str = "loop://?logging=debug"
    display_url: str = "loop://?logging=debug"
    admin_user_ids: list[int] = [1]
    db_file: str = "/db/lockoff.db3"
    redis_url: str = "redis://localhost"
    certificate: bytes = ""
    key: bytes = ""
    certificate_password: bytes = ""
    wwdr_certificate: bytes = ""
    current_season: int = 2023
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
