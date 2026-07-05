from pydantic import BaseModel, ConfigDict, Field


class SubjectCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)


class SubjectUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)


class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class SubjectReorderRequest(BaseModel):
    subject_ids: list[int] = Field(min_length=1)
