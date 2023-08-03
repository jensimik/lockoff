import pytest
from lockoff.access_token import verify_dl_token, generate_dl_token, TokenError
from dateutil.relativedelta import relativedelta


@pytest.mark.parametrize(
    ["user_id"],
    (0, 1, 2, 3),
)
def test_dl_token(user_id):
    token = generate_dl_token(user_id=user_id)
    assert verify_dl_token(token) == user_id

    token_expired = generate_dl_token(user_id, expire_delta=relativedelta(hours=-10))
    with pytest.raises(TokenError):
        verify_dl_token(token_expired)
