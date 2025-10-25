####################################################################################################
# main function that's the root of the system

from APP.Configration import APP
from APP.Routes import Student_Routes, Agent_Routes, WebSearch_Routes

@APP.get("/")
def root():
    return {"Message": "Hello Everyone"}

# Register routers
APP.include_router(Student_Routes.router)
APP.include_router(Agent_Routes.router)
APP.include_router(WebSearch_Routes.router)

# git clone <repo link>
# mv <repo name>/* .
# pip install -r requirements.txt

# Run with: uvicorn main:APP --reload
# if receive error try to activate .venv before even if already activated by: source .venv/bin/activate
# if also have an error try running from current position by: python -m uvicorn main:APP --reload

# open fastAPI doc by: http://127.0.0.1:8000/docs
####################################################################################################