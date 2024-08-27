from fastapi.param_functions import Form
from fastapi.security import OAuth2PasswordRequestForm


class OAuth2PasswordRequestCustomForm(OAuth2PasswordRequestForm):
    def __init__(self, username: str = Form(), password: str = Form()):
        return super().__init__(
            username=username, password=password, scope=""
        )
