from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Any
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr
import secrets
import os

from app.cores.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, UserLoginResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.utils.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user
from app.services.email_service import EmailService
from app.services.audit_service import AuditLogService

router = APIRouter()

# Durasi kedaluwarsa token verifikasi (24 jam)
VERIFICATION_TOKEN_EXPIRE_HOURS = 24


class ResendVerificationRequest(BaseModel):
    email: EmailStr

# Simple in-memory rate limiter for forgot password requests
forgot_password_requests = {}
resend_verification_requests = {}

def check_rate_limit(email: str, requests_dict: dict, max_requests: int = 5, hours: int = 1):
    now = datetime.utcnow()
    # Clean up old entries
    if email in requests_dict:
        requests_dict[email] = [req for req in requests_dict[email] if now - req < timedelta(hours=hours)]
    else:
        requests_dict[email] = []

    if len(requests_dict[email]) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail=f"Anda telah mencapai batas maksimal permintaan ({max_requests} kali per jam). Silakan coba lagi nanti."
        )
    
    requests_dict[email].append(now)

def check_forgot_pwd_rate_limit(email: str):
    check_rate_limit(email, forgot_password_requests)

def check_resend_verif_rate_limit(email: str):
    check_rate_limit(email, resend_verification_requests)


def _generate_and_send_verification(user: User, background_tasks: BackgroundTasks, db: Session):
    """Helper: generate token baru, simpan ke DB, kirim email verifikasi."""
    new_token = secrets.token_urlsafe(32)
    user.verification_token = new_token
    user.verification_token_created_at = datetime.utcnow()
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    verification_link = f"{frontend_url}/verify-email?token={new_token}"

    background_tasks.add_task(
        EmailService.send_verification_email,
        target_email=user.email,
        user_name=user.name,
        verification_link=verification_link,
    )


@router.post("/register", response_model=UserResponse)
def register_user(
    request: Request,
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Any:
    """
    Register user baru.
    FE mengirim JSON: { name, email, nim, phone, password }
    FE mengharapkan response: { id, name, email, nim, phone, role }
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        AuditLogService.create(
            db=db,
            action="auth.register.duplicate_email",
            actor_email=user_in.email,
            request=request,
            success=False,
        )
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="User dengan email ini sudah terdaftar.",
        )

    # Generate token verifikasi
    verification_token = secrets.token_urlsafe(32)

    user = User(
        name=user_in.name,
        email=user_in.email,
        nim=user_in.nim,
        phone=user_in.phone,
        password_hash=get_password_hash(user_in.password),
        is_verified=False,
        verification_token=verification_token,
        verification_token_created_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    AuditLogService.create(
        db=db,
        action="auth.register",
        actor=user,
        resource_type="user",
        resource_id=user.id,
        detail={"email": user.email, "role": user.role.value},
        request=request,
    )
    db.commit()

    # Kirim email verifikasi di background
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    verification_link = f"{frontend_url}/verify-email?token={verification_token}"

    background_tasks.add_task(
        EmailService.send_verification_email,
        target_email=user.email,
        user_name=user.name,
        verification_link=verification_link,
    )

    return user


@router.post("/login", response_model=UserLoginResponse)
def login_user(request: Request, login_data: UserLogin, db: Session = Depends(get_db)) -> Any:
    """
    Login user.
    FE mengirim JSON: { email, password }
    FE mengharapkan response: { id, name, email, nim, phone, role, token }
    (FE menyimpan seluruh objek ini ke authStore via login(user))
    """
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        AuditLogService.create(
            db=db,
            action="auth.login.failed",
            actor=user,
            actor_email=login_data.email,
            detail={"reason": "invalid_credentials"},
            request=request,
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=400, detail="Email atau password salah")

    if not user.is_verified:
        AuditLogService.create(
            db=db,
            action="auth.login.failed",
            actor=user,
            detail={"reason": "email_not_verified"},
            request=request,
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=403, detail="Email Anda belum diverifikasi. Silakan cek kotak masuk email Anda.")

    access_token = create_access_token(data={"sub": user.email})
    AuditLogService.create(
        db=db,
        action="auth.login.success",
        actor=user,
        resource_type="user",
        resource_id=user.id,
        request=request,
    )
    db.commit()

    return UserLoginResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        nim=user.nim,
        phone=user.phone,
        role=user.role,
        is_verified=user.is_verified,
        token=access_token,
    )


@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/verify-email")
def verify_email(request: Request, token: str, db: Session = Depends(get_db)):
    """
    Endpoint untuk verifikasi email berdasarkan token.
    Dipanggil dari frontend /verify-email?token=xyz
    """
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        AuditLogService.create(
            db=db,
            action="auth.email_verify.failed",
            detail={"reason": "invalid_token"},
            request=request,
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=400, detail="Token verifikasi tidak valid atau sudah kedaluwarsa.")

    # Cek apakah token sudah melewati batas waktu 24 jam
    if user.verification_token_created_at:
        token_age = datetime.utcnow() - user.verification_token_created_at
        if token_age > timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS):
            AuditLogService.create(
                db=db,
                action="auth.email_verify.failed",
                actor=user,
                detail={"reason": "expired_token"},
                request=request,
                success=False,
            )
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="Token verifikasi sudah kedaluwarsa. Silakan minta kirim ulang email verifikasi.",
            )

    user.is_verified = True
    user.verification_token = None
    user.verification_token_created_at = None
    AuditLogService.create(
        db=db,
        action="auth.email_verify.success",
        actor=user,
        resource_type="user",
        resource_id=user.id,
        request=request,
    )

    db.commit()
    return {"status": "success", "message": "Email berhasil diverifikasi. Anda sekarang dapat login."}


@router.post("/resend-verification")
def resend_verification(
    request: Request,
    body: ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Kirim ulang email verifikasi.
    FE mengirim JSON: { email }
    Cooldown 60 detik ditangani di sisi Frontend.
    """
    check_resend_verif_rate_limit(body.email)
    user = db.query(User).filter(User.email == body.email).first()
    AuditLogService.create(
        db=db,
        action="auth.verification_resend.requested",
        actor=user,
        actor_email=body.email,
        request=request,
    )
    db.commit()

    # Untuk keamanan, selalu kembalikan pesan sukses agar attacker
    # tidak bisa menggunakan endpoint ini untuk enumerasi email.
    success_msg = "Jika email terdaftar dan belum diverifikasi, kami telah mengirim ulang email verifikasi."

    if not user:
        return {"status": "success", "message": success_msg}

    if user.is_verified:
        return {"status": "success", "message": success_msg}

    # Rate limit sederhana: minimal 60 detik antar pengiriman
    if user.verification_token_created_at:
        elapsed = datetime.utcnow() - user.verification_token_created_at
        if elapsed < timedelta(seconds=60):
            raise HTTPException(
                status_code=429,
                detail="Harap tunggu 60 detik sebelum meminta kirim ulang.",
            )

    _generate_and_send_verification(user, background_tasks, db)

    return {"status": "success", "message": success_msg}


@router.post("/forgot-password")
def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    check_forgot_pwd_rate_limit(body.email)
    user = db.query(User).filter(User.email == body.email).first()
    AuditLogService.create(
        db=db,
        action="auth.forgot_password.requested",
        actor=user,
        actor_email=body.email,
        request=request,
    )
    db.commit()
    
    success_msg = "Jika email terdaftar, tautan untuk mengatur ulang kata sandi telah dikirim."

    if not user:
        # Return success even if user not found to prevent email enumeration
        return {"status": "success", "message": success_msg}

    # Cek rate limit untuk forgot password (minimal 60 detik)
    if user.reset_token_expires:
        # Token valid 15 menit, jadi kita hitung selisih dari 15 menit yang lalu jika masih berlaku.
        # Lebih aman simpan reset_token_created_at, atau hitung dari expires
        elapsed = (user.reset_token_expires - timedelta(minutes=15)) - datetime.utcnow()
        # Jika selisih < 60 detik, tolak
        if elapsed.total_seconds() > -60:
            raise HTTPException(
                status_code=429,
                detail="Harap tunggu 60 detik sebelum meminta reset password ulang."
            )

    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"

    background_tasks.add_task(
        EmailService.send_reset_password_email,
        target_email=user.email,
        user_name=user.name,
        reset_link=reset_link,
    )

    return {"status": "success", "message": success_msg}


@router.post("/reset-password")
def reset_password(request: Request, body: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == body.token).first()
    
    if not user:
        AuditLogService.create(
            db=db,
            action="auth.reset_password.failed",
            detail={"reason": "invalid_token"},
            request=request,
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=400, detail="Token reset password tidak valid atau sudah kedaluwarsa.")
        
    if not user.reset_token_expires or datetime.utcnow() > user.reset_token_expires:
        AuditLogService.create(
            db=db,
            action="auth.reset_password.failed",
            actor=user,
            detail={"reason": "expired_token"},
            request=request,
            success=False,
        )
        db.commit()
        raise HTTPException(status_code=400, detail="Token reset password sudah kedaluwarsa. Silakan minta tautan baru.")

    user.password_hash = get_password_hash(body.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    AuditLogService.create(
        db=db,
        action="auth.reset_password.success",
        actor=user,
        resource_type="user",
        resource_id=user.id,
        request=request,
    )
    db.commit()

    return {"status": "success", "message": "Kata sandi berhasil diatur ulang. Silakan login dengan kata sandi baru Anda."}
