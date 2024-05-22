from typing import Union
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth, OAuthError
from starlette.config import Config
import httpx


config = Config('.env')  # read config from .env file
oauth = OAuth(config)
oauth.register(
    name='google',
    client_id = '770804898230-52ii9hgj9evb6h5qnp890m73nfoua6p7.apps.googleusercontent.com',
    client_secret = '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',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="secret-string")
github_client_id = "Ov23lioHbweyfYT6hzGp"
github_client_secret = "8292d0763fb7aa3e79d7a2057086df96c2b93cb0"



@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.route('/google_login')
async def login(request: Request):
    # absolute url for callback
    # we will define it below
    redirect_uri = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.route('/github-login')
async def github_login(request: Request):
    return RedirectResponse(f"https://github.com/login/oauth/authorize?client_id={github_client_id}", status_code=302)

@app.route('/github-code')
async def github_code(request: Request, code:str):
    params = {
        'client_id': github_client_id,
        'client_secret': github_client_secret,
        'code': code
    }
    headers = {'Accept': 'application/json'}
    async with httpx.AsyncClient() as client:
        response = await client.post(url="https://github.com/login/oauth/access_token", params=params, headers=headers)
    response_json = response.json()
    access_token = response_json['access_token']
    async with httpx.AsyncClient() as client:
        headers.update({'Authorization': f'Bearer {access_token}'})
        response = await client.get('https://api.github.com/user', headers=headers)
        
    return response.json()

@app.route('/auth')
async def auth(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as error:
        return HTMLResponse(f'<h1>{error.error}</h1>')
    user = token.get('userinfo')
    if user:
        request.session['user'] = dict(user)
    return RedirectResponse(url='/')

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)