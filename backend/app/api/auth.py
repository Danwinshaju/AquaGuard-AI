"""Account signup, login, logout, and current-user endpoints."""

from fastapi import APIRouter, HTTPException, Request, Response, status

from app.core.auth import (
    DUMMY_PASSWORD_HASH,
    SESSION_COOKIE,
    CurrentUser,
    create_account_session,
    new_user,
    session_token_hash,
    verify_password,
)
from app.db.repositories.auth import EmailAlreadyRegisteredError, auth_repository
from app.models import UserDocument
from app.schemas.auth import LoginRequest, SignupRequest, UserResponse

router = APIRouter()


def _public_user(user: UserDocument) -> UserResponse:
    return UserResponse(id=user.id, name=user.name, email=user.email, created_at=user.created_at)


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, response: Response) -> UserResponse:
    user = new_user(payload.name, payload.email, payload.password)
    try:
        await auth_repository.create_user(user)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    await create_account_session(response, user.id)
    return _public_user(user)


@router.post("/login", response_model=UserResponse)
async def login(payload: LoginRequest, response: Response) -> UserResponse:
    user = await auth_repository.get_user_by_email(payload.email)
    password_hash = user.password_hash if user is not None else DUMMY_PASSWORD_HASH
    password_is_valid = verify_password(payload.password, password_hash)
    if user is None or not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
        )
    await create_account_session(response, user.id)
    return _public_user(user)


@router.get("/me", response_model=UserResponse)
async def current_account(user: CurrentUser) -> UserResponse:
    return _public_user(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> Response:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        await auth_repository.delete_session(session_token_hash(token))
    response.delete_cookie(SESSION_COOKIE, path="/")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
