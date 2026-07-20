import os
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import HTTPException, Depends
from secrets import compare_digest
from dotenv import load_dotenv

load_dotenv()

security = HTTPBasic()

USERNAME = os.getenv("APP_USERNAME")
PASSWORD = os.getenv("APP_PASSWORD")

def user_authenticate(credentials: HTTPBasicCredentials=Depends(security)):
    is_username_correct = compare_digest(credentials.username, USERNAME)
    is_password_correct = compare_digest(credentials.password, PASSWORD)
    
    if not (is_username_correct and is_password_correct):
        raise HTTPException(status_code=401, detail="Unauthorized credentials", headers={"WWW-Authenticate":"Basic"})
    
    return credentials