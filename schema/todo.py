from pydantic import BaseModel


class CreateTodo(BaseModel):
    title: str
    body: str

class ShowTodo(BaseModel):
    title: str
    body: str

    class Config:
        from_attributes = True