from pydantic import BaseModel

class ITError(BaseModel):
    error_message: str
    status_code: int

    def __init__(self, error_message: str, status_code: int):
        self.error_message = error_message
        self.status_code = status_code