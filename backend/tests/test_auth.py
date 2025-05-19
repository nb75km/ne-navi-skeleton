# Tests for authentication and user registration
import pytest
import pytest_asyncio # Required for async fixtures
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.minutes_maker.app.main import app
from backend.common.models.user import User
# Import AsyncSessionLocal from the correct path
from backend.common.deps import AsyncSessionLocal 

@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncClient: # Added return type hint
    async with AsyncClient(app=app, base_url="http://testserver") as ac: # Changed base_url for clarity
        yield ac

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession: # Added return type hint and made it async
    async with AsyncSessionLocal() as session:
        yield session
        # Clean up: Rollback any changes made during the test to keep DB clean
        # This is important if tests write to the actual dev DB.
        # For a dedicated test DB, transactions might be handled differently or reset per test.
        await session.rollback() 

@pytest.mark.asyncio
async def test_successful_user_registration(client: AsyncClient, db_session: AsyncSession):
    """Test successful user registration and DB verification."/""
    email = "testuser_successful@example.com"
    password = "strongpassword123"
    
    response = await client.post("/auth/register", json={
        "email": email,
        "password": password
    })
    assert response.status_code == status.HTTP_201_CREATED
    response_data = response.json()
    assert response_data["email"] == email
    assert "id" in response_data
    assert "hashed_password" not in response_data

    # Verify user in database
    user_in_db = await db_session.execute(
        select(User).where(User.email == email)
    )
    user = user_in_db.scalar_one_or_none()
    assert user is not None
    assert user.email == email
    assert user.hashed_password is not None
    assert user.hashed_password != password # Ensure password is hashed

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db_session: AsyncSession):
    """Test registration with a duplicate email address."/""
    email = "duplicate_test@example.com"
    password = "password123"

    # First, register a user
    response1 = await client.post("/auth/register", json={
        "email": email,
        "password": password
    })
    assert response1.status_code == status.HTTP_201_CREATED
    
    # Ensure the first user is committed to DB before testing duplicate
    # Querying the user will implicitly use the session and its transaction handling
    user_in_db = await db_session.execute(
        select(User).where(User.email == email)
    )
    assert user_in_db.scalar_one_or_none() is not None

    # Attempt to register another user with the same email
    response2 = await client.post("/auth/register", json={
        "email": email,
        "password": "anotherpassword"
    })
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    # More specific error detail check could be added here, e.g.
    # assert response2.json()["detail"] == "REGISTER_USER_ALREADY_EXISTS"

@pytest.mark.asyncio
async def test_successful_user_login(client: AsyncClient, db_session: AsyncSession):
    """Test successful user login."/""
    email = "login_test_user@example.com"
    password = "login_password123"

    # 1. Register user first
    register_response = await client.post("/auth/register", json={
        "email": email,
        "password": password
    })
    assert register_response.status_code == status.HTTP_201_CREATED
    user_id = register_response.json()["id"]

    # Verify user in database (optional, but good for sanity check)
    user_in_db = await db_session.execute(
        select(User).where(User.id == user_id)
    )
    assert user_in_db.scalar_one_or_none() is not None
    await db_session.commit() # Ensure user is committed before login attempt

    # 2. Attempt login
    # fastapi-users /auth/jwt/login endpoint expects form data
    login_response = await client.post("/auth/jwt/login", data={
        "username": email, # 'username' is the default field for email in fastapi-users login
        "password": password
    })
    
    assert login_response.status_code == status.HTTP_200_OK # fastapi-users returns 200 for login, not 204
    response_data = login_response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_incorrect_password(client: AsyncClient, db_session: AsyncSession):
    """Test login with incorrect password."/""
    email = "wrong_pass_user@example.com"
    password = "correct_password"

    # 1. Register user
    register_response = await client.post("/auth/register", json={
        "email": email,
        "password": password
    })
    assert register_response.status_code == status.HTTP_201_CREATED
    await db_session.commit() # Ensure user is committed

    # 2. Attempt login with wrong password
    login_response = await client.post("/auth/jwt/login", data={
        "username": email,
        "password": "wrong_password"
    })
    assert login_response.status_code == status.HTTP_400_BAD_REQUEST
    # The error detail for fastapi-users is typically {"detail": "LOGIN_BAD_CREDENTIALS"}
    assert login_response.json()["detail"] == "LOGIN_BAD_CREDENTIALS"

@pytest.mark.asyncio
async def test_login_non_existent_user(client: AsyncClient):
    """Test login with a non-existent email."/""
    login_response = await client.post("/auth/jwt/login", data={
        "username": "nonexistent@example.com",
        "password": "any_password"
    })
    assert login_response.status_code == status.HTTP_400_BAD_REQUEST
    assert login_response.json()["detail"] == "LOGIN_BAD_CREDENTIALS"

@pytest.mark.asyncio
async def test_get_current_user_me_authenticated(client: AsyncClient, db_session: AsyncSession):
    """Test accessing /users/me with a valid token."/""
    email = "me_user@example.com"
    password = "password_me"

    # 1. Register user
    register_response = await client.post("/auth/register", json={
        "email": email,
        "password": password
    })
    assert register_response.status_code == status.HTTP_201_CREATED
    user_id = register_response.json()["id"]
    await db_session.commit() # Ensure user is committed

    # 2. Login to get token
    login_response = await client.post("/auth/jwt/login", data={
        "username": email,
        "password": password
    })
    assert login_response.status_code == status.HTTP_200_OK
    access_token = login_response.json()["access_token"]

    # 3. Access /users/me with token
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = await client.get("/users/me", headers=headers)
    
    assert me_response.status_code == status.HTTP_200_OK
    me_data = me_response.json()
    assert me_data["email"] == email
    assert me_data["id"] == user_id
    assert "hashed_password" not in me_data

@pytest.mark.asyncio
async def test_get_current_user_me_unauthenticated(client: AsyncClient):
    """Test accessing /users/me without a token."/""
    me_response = await client.get("/users/me")
    # fastapi-users typically returns 401 Unauthorized
    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED 
    assert me_response.json()["detail"] == "Unauthorized" # Or specific message from your setup

@pytest.mark.asyncio
async def test_get_current_user_me_invalid_token(client: AsyncClient):
    """Test accessing /users/me with an invalid token."/""
    headers = {"Authorization": "Bearer invalidtoken123"}
    me_response = await client.get("/users/me", headers=headers)
    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert me_response.json()["detail"] == "Unauthorized" # Or specific error from your setup
