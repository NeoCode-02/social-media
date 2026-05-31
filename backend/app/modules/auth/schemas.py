from pydantic import BaseModel, EmailStr, Field

Username = Field(pattern=r"^[a-zA-Z0-9_]{3,32}$")
Password = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Username
    password: str = Password
    display_name: str = Field(min_length=1, max_length=64)


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(pattern=r"^\d{6}$")


class ResendCodeRequest(BaseModel):
    email: EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    detail: str
