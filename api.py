from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from fastapi.responses import RedirectResponse

from database import Base, engine, SessionLocal
from models import User
from schemas import UserCreate, UserLogin, Token
from auth import get_password_hash, verify_password, create_access_token
from authlib.integrations.starlette_client import OAuth
import settings

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="supersecret")

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"msg": "User created successfully"}


@app.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = "http://127.0.0.1:8001/auth/google"
    print("DEBUG redirect_uri:", redirect_uri)
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/google")
async def auth_google(request: Request):
    token = await oauth.google.authorize_access_token(request)
    resp = await oauth.google.get(
        "https://openidconnect.googleapis.com/v1/userinfo",  # повний URL
        token=token
    )
    user_info = resp.json()
    django_url = (
        "http://127.0.0.1:8000/auth/login/from_fastapi?"
        f"email={user_info['email']}&"
        f"name={user_info.get('name', '')}&"
        f"picture={user_info.get('picture', '')}&"
        f"sub={user_info.get('sub', '')}"
    )

    return RedirectResponse(django_url)
    db = SessionLocal()
    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        user = User(
            email=user_info["email"],
            )
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return {"user": user_info}

@app.get("/", response_class=HTMLResponse)
async def homepage():
    html = """
    <html>
        <head><title>Login Demo</title></head>
        <body style="font-family:sans-serif; text-align:center; margin-top:100px;">
            <h1>Авторизація</h1>
            <a href="/login/google">
                <button style="font-size:20px; padding:10px 20px; background:#4285F4; color:white; border:none; border-radius:5px;">
                    Увійти через Google
                </button>
            </a>
        </body>
    </html>
    """
    return HTMLResponse(content=html)