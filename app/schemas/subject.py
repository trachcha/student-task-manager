from pydantic import BaseModel, ConfigDict


class SubjectCreate(BaseModel):
    name: str


class SubjectUpdate(BaseModel):
    name: str


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
