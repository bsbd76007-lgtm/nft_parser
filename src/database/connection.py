import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from src.config import DATABASE_URL
from src.database.models import Base


def prepare_database_url(url: str) -> tuple[str, dict]:
    if not url:
        return "", {}
    
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    connect_args = {}
    
    if 'sslmode' in query_params:
        sslmode = query_params.pop('sslmode')[0]
        
        if sslmode == 'require':
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connect_args['ssl'] = ssl_context
        elif sslmode in ('verify-ca', 'verify-full'):
            ssl_context = ssl.create_default_context()
            if sslmode == 'verify-full':
                ssl_context.check_hostname = True
            connect_args['ssl'] = ssl_context
        elif sslmode == 'prefer':
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            connect_args['ssl'] = ssl_context
    
    new_query = urlencode(query_params, doseq=True) if query_params else ""
    
    new_parsed = parsed._replace(
        scheme="postgresql+asyncpg",
        query=new_query
    )
    
    return urlunparse(new_parsed), connect_args


if DATABASE_URL.startswith("sqlite"):
    database_url = DATABASE_URL
    connect_args = {}
else:
    database_url, connect_args = prepare_database_url(DATABASE_URL)

engine = create_async_engine(
    database_url,
    poolclass=NullPool,
    echo=False,
    connect_args=connect_args
) if database_url else None

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
) if engine else None


async def init_db():
    if engine:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def get_session():
    if async_session:
        async with async_session() as session:
            yield session


async def get_db_session() -> AsyncSession:
    if async_session:
        return async_session()
    return None
