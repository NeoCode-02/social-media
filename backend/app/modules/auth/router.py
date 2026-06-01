from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.rate_limit import rate_limit
from app.modules.auth import service
from app.modules.auth.oauth import oauth
from app.modules.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendCodeRequest,
    TicketResponse,
    TokenResponse,
    VerifyEmailRequest,
)
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        max_age=settings.refresh_token_ttl_seconds,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.refresh_cookie_name, path="/api/auth", httponly=True)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
    dependencies=[rate_limit(10, 60, "register")],
)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    await service.register_user(db, data)
    return MessageResponse(detail="Registered. Check your email for a verification code.")


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(
    data: VerifyEmailRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    user = await service.verify_email(db, data.email, data.code)
    access, refresh = await service.issue_tokens(user)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access)


@router.post(
    "/resend-code",
    response_model=MessageResponse,
    dependencies=[rate_limit(5, 300, "resend")],
)
async def resend_code(
    data: ResendCodeRequest, db: AsyncSession = Depends(get_db)
) -> MessageResponse:
    await service.request_email_code(db, data.email)
    return MessageResponse(detail="If the account exists and is unverified, a code was sent.")


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[rate_limit(10, 60, "login")],
)
async def login(
    data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    user = await service.authenticate(db, data.email, data.password)
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    access, refresh = await service.issue_tokens(user)
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=access)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(request: Request, response: Response) -> TokenResponse:
    token = request.cookies.get(settings.refresh_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token"
        )
    access, new_refresh = await service.rotate_refresh(token)
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=access)


@router.post("/logout", response_model=MessageResponse)
async def logout(request: Request, response: Response) -> MessageResponse:
    token = request.cookies.get(settings.refresh_cookie_name)
    if token:
        await service.revoke_refresh(token)
    _clear_refresh_cookie(response)
    return MessageResponse(detail="Logged out")


@router.get("/ws-ticket", response_model=TicketResponse)
async def get_ws_ticket(user: User = Depends(get_current_user)) -> TicketResponse:
    ticket = await service.issue_ws_ticket(user)
    return TicketResponse(ticket=ticket)


# --- Google OAuth ---------------------------------------------------------


def _require_google_configured() -> None:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured",
        )


@router.get("/google/login")
async def google_login(request: Request):
    _require_google_configured()
    redirect_uri = f"{settings.oauth_redirect_base}{settings.api_prefix}/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: AsyncSession = Depends(get_db)):
    _require_google_configured()
    token = await oauth.google.authorize_access_token(request)
    info = token.get("userinfo") or {}
    sub, email = info.get("sub"), info.get("email")
    if not sub or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Google profile incomplete"
        )
    user = await service.get_or_create_oauth_user(db, "google", sub, email, info.get("name", ""))
    access, refresh = await service.issue_tokens(user)
    # Hand the SPA its access token via URL fragment; refresh stays in cookie.
    redirect = RedirectResponse(url=f"{settings.frontend_url}/auth/callback#access_token={access}")
    _set_refresh_cookie(redirect, refresh)
    return redirect
