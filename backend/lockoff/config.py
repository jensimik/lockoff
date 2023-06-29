from typing import Any

from dateutil.tz import gettz, tzfile
from pydantic import BaseSettings
from pydantic.env_settings import SettingsSourceCallable


class Settings(BaseSettings):
    app_name: str = "lockoff"
    klubmodul_username: str
    klubmodul_password: str
    klubmodul_country_id: int = 1
    klubmodul_club_id: int = 2002
    nonce_size: int = 4
    digest_size: int = 10
    secret: bytes = "changeme"
    opticon_url: str = "loop://?logging=debug"
    display_url: str = "loop://?logging=debug"
    db_member: str = "/db_member.json"
    prod: bool = False
    tz: tzfile = gettz("Europe/Copenhagen")

    class Config:
        # parse tz field as a dateutil.tz
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "tz":
                return gettz(raw_val)
            return cls.json_loads(raw_val)

        # do not try to load from file
        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ) -> tuple[SettingsSourceCallable, ...]:
            return env_settings, init_settings


settings = Settings()
