from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.models.organization import Organization
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: str = "ENGINEER"  # ENGINEER, REVIEWER, AUDITOR, ADMIN
    organization_name: Optional[str] = "Zyntrix Engineering Labs"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/bootstrap", response_model=dict)
async def bootstrap_default_tenant(db: AsyncSession = Depends(get_db)):
    """Bootstrap the initial authoritative tenant organization and admin/engineer user."""
    org_res = await db.execute(select(Organization).limit(1))
    org = org_res.scalars().first()
    
    created_org = False
    if not org:
        org = Organization(
            name="Zyntrix Engineering Labs",
            slug="zyntrix-labs",
            description="Authoritative regulatory engineering test facility",
        )
        db.add(org)
        await db.flush()
        created_org = True

    user_res = await db.execute(select(User).where(User.email == "engineer@zyntrix.io"))
    user = user_res.scalars().first()

    created_user = False
    if not user:
        user = User(
            email="engineer@zyntrix.io",
            hashed_password=hash_password("ZyntrixPassword2026!"),
            full_name="Lead Regulatory Compliance Engineer",
            role="ADMIN",
            organization_id=org.id,
            organization_name=org.name,
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        created_user = True
    else:
        if not user.organization_id:
            user.organization_id = org.id
            await db.commit()

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role, "org_id": org.id})

    return {
        "status": "bootstrapped" if (created_org or created_user) else "already_bootstrapped",
        "organization": {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
        },
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": org.id,
        },
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user under an organization."""
    # Check if email exists
    user_res = await db.execute(select(User).where(User.email == payload.email))
    if user_res.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Find or create organization
    org_res = await db.execute(
        select(Organization).where(Organization.name == payload.organization_name)
    )
    org = org_res.scalars().first()
    if not org:
        slug = payload.organization_name.lower().replace(" ", "-")
        org = Organization(name=payload.organization_name, slug=slug)
        db.add(org)
        await db.flush()

    valid_roles = {"ENGINEER", "REVIEWER", "AUDITOR", "ADMIN"}
    role = payload.role.upper() if payload.role.upper() in valid_roles else "ENGINEER"

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=role,
        organization_id=org.id,
        organization_name=org.name,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role, "org_id": org.id})

    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": org.id,
            "organization_name": org.name,
        },
    )


@router.post("/login", response_model=TokenResponse)
async def login_json(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate with email and password returning JWT bearer token."""
    user_res = await db.execute(select(User).where(User.email == payload.email))
    user = user_res.scalars().first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    token = create_access_token(
        {"sub": user.id, "email": user.email, "role": user.role, "org_id": user.organization_id}
    )

    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "organization_id": user.organization_id,
            "organization_name": user.organization_name,
        },
    )


@router.post("/token", response_model=TokenResponse)
async def login_oauth2(
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2 compatible token endpoint for form submissions."""
    return await login_json(LoginRequest(email=username, password=password), db=db)


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve profile and organization metadata for the authenticated user."""
    org_name = current_user.organization_name
    if current_user.organization_id and not org_name:
        org_res = await db.execute(
            select(Organization).where(Organization.id == current_user.organization_id)
        )
        org = org_res.scalars().first()
        if org:
            org_name = org.name

    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "organization_id": current_user.organization_id,
        "organization_name": org_name,
        "is_active": current_user.is_active,
        "is_superuser": current_user.is_superuser,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
