import pathlib
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
    sentry_dsn: str = ""
    klubmodul_username: str = ""
    klubmodul_password: str = ""
    klubmodul_base_url: str = "https://changeme.klub-modul.dk"
    klubmodul_admin_user_id: int = 3535  # change to your own user_id for the admin user
    apple_pass_certificate: pathlib.Path = pathlib.Path("/secret/apple-certificate.pem")
    apple_pass_key: pathlib.Path = pathlib.Path("/secret/apple-key.encrypted")
    apple_pass_key_password: bytes = ""
    apple_pass_wwdr_cert: pathlib.Path = pathlib.Path("/secret/apple-wwdr.pem")
    apple_pass_description: str = "Nørrebro klatreklub"
    apple_pass_logo_text: str = "Nørrebro klatreklub"
    apple_pass_organization_name: str = "Jens Davidsen"
    apple_pass_pass_type_identifier: str = "pass.dk.nkk.lockoff"
    apple_pass_team_identifier: str = "LLFSXFW7XK"
    apple_pass_latitude: float = 55.69942723771949
    apple_pass_longitude: float = 12.543439832016006
    apple_pass_relevant_text: str = "lets climb! 🐒"
    apple_pass_proximity_uuid: str = "812366E1-4479-404B-B4A1-110FBBA9F625"
    apple_pass_web_service_url: str = "https://lockoff-api.gnerd.dk/apple-wallet/"
    apple_apn_auth_key: pathlib.Path = pathlib.Path("/secret/apple-apn-auth-key.pem")
    apple_apn_key_id: str = ""
    walletpass_token: str = ""
    hash_salt: str = "changeme"
    nonce_size: int = 4
    digest_size: int = 10
    dl_nonce_size: int = 2
    dl_digest_size: int = 5
    dl_secret: bytes = "changeme"
    secret: bytes = "changeme"
    jwt_secret: str = ""
    opticon_url: str = "/dev/OPTICON"
    display_url: str = "/dev/DISPLAY"
    admin_user_ids: list[int] = [1]
    db_file: str = "/tmp/lockoff.db3"
    redis_url: str = "redis://localhost"
    google_service_account: pathlib.Path = pathlib.Path(
        "/secret/google-service-account.json"
    )
    google_issuer_id: str = ""
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
