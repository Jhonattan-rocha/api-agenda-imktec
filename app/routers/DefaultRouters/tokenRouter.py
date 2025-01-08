from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.CustomControllers import GenericController
from app.database import database
from datetime import timedelta

from app.schemas.DefaultSchemas import Token
from app.controllers.DefaultControllers import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.DefaultModels.userModel import User
from app.models.DefaultModels.userProfileModel import UserProfile
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes 
import globals
import base64

router = APIRouter(prefix="/crud")

# Função para criptografar a chave AES com a chave pública RSA
def encrypt_with_public_key(public_key_pem: str, aes_key: bytes) -> bytes:
    public_key = serialization.load_pem_public_key(public_key_pem.encode())
    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_key


# Rota para gerar o token
@router.post("/token/{public_key}", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(database.get_db),
    public_key: str = None
):
    result = await db.execute(
        select(User)
        .options(joinedload(User.profile).joinedload(UserProfile.permissions))
        .where(User.email == form_data.username)
    )
    user = result.scalars().first()

    if user:
        hash_password = (
            hashlib.sha256(user.salt.encode()).hexdigest() +
            hashlib.sha256(form_data.password.encode()).hexdigest()
        )
        user_password = hashlib.sha256(hash_password.encode()).hexdigest()

        if not user or user.password != user_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Gerar chave AES e IV <----
        aes_key = globals.aes_key
        iv = globals.iv

        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Public key is required"
            )

        # Criptografar a chave AES com a chave pública do cliente
        try:
            encrypted_aes_key = encrypt_with_public_key(base64.b64decode(public_key.encode()).decode(), aes_key)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to encrypt AES key: {str(e)}"
            )

        # Preparar dados para o cliente
        encrypted_aes_key_base64 = base64.b64encode(encrypted_aes_key).decode()
        iv_base64 = base64.b64encode(iv).decode()

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"id": user.id, "email": user.email}, expires_delta=access_token_expires
        )

        generic_controller = GenericController("ProductCategory")
        aux = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "lang": user.lang,
                "profile": generic_controller.serialize_item(user.profile) if user.profile else user.profile,
            },
            "crypt_token": encrypted_aes_key_base64,  # Chave AES criptografada
            "iv": iv_base64  # IV para criptografia AES
        }
        return aux

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Incorrect username or password, user not found",
        headers={"WWW-Authenticate": "Bearer"},
    )
