from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from schemas import oauth2User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def authenticate(token: Annotated[str, Depends(oauth2_scheme)]) -> oauth2User:
    return oauth2User(login="johndoe", id="3cdaefd2-ca39-46af-ae95-9bea4cdb304e")