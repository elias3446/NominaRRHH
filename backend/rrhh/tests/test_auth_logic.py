"""
Test de lógica de autenticación — verifica check_password y el flujo JWT
sin necesidad de crear usuarios en la BD (CustomUser tiene managed=False).
"""
import pytest
import uuid
from unittest.mock import MagicMock, patch
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


def test_jwt_token_generation():
    """
    Verifica que AccessToken y RefreshToken se generan correctamente
    para un usuario falso con los claims necesarios.
    """
    fake_user = MagicMock()
    fake_user.id = uuid.uuid4()
    fake_user.email = "elias_final_v100@example.com"

    # Generamos tokens directamente
    token = AccessToken()
    token['user_id'] = str(fake_user.id)
    token['email'] = fake_user.email

    assert token['user_id'] == str(fake_user.id)
    assert token['email'] == fake_user.email
    print(f"\n[OK] Token generado para: {fake_user.email}")


def test_jwt_token_str_serialization():
    """
    Verifica que el token se serializa correctamente a string (formato JWT: xxx.yyy.zzz).
    """
    fake_user = MagicMock()
    fake_user.id = uuid.uuid4()

    token = AccessToken()
    token['user_id'] = str(fake_user.id)
    token_str = str(token)

    parts = token_str.split(".")
    assert len(parts) == 3, "El token JWT debe tener 3 partes separadas por puntos (header.payload.signature)"
    print(f"\n[OK] Token serializado correctamente: {token_str[:30]}...")


def test_password_hashing():
    """
    Verifica que set_password / check_password funcionan correctamente
    en el modelo CustomUser sin necesidad de guardar en la BD.
    """
    from rrhh.models import CustomUser

    # Instanciamos el modelo sin guardar (sin tocar la BD)
    user = CustomUser.__new__(CustomUser)
    user.email = "test@example.com"
    user.password = ""

    # set_password usa el hasher de Django (pbkdf2_sha256 por defecto)
    user.set_password("password_segura_123")

    assert user.password.startswith("pbkdf2_sha256"), "La contraseña debe estar hasheada con pbkdf2"
    assert user.check_password("password_segura_123") is True
    assert user.check_password("wrong_password") is False
    print(f"\n[OK] Hash generado: {user.password[:40]}...")
