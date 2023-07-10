from typing import Any

from dateutil.tz import gettz, tzfile
from pydantic_settings import BaseSettings

# from pydantic.env_settings import SettingsSourceCallable


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

    class Config:
        # parse tz field as a dateutil.tz
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str) -> Any:
            if field_name == "tz":
                return gettz(raw_val)
            return cls.json_loads(raw_val)


settings = Settings()
