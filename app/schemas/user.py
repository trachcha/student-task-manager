from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=3)
    password: str = Field(min_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    unsorted_label: str
    unsorted_position: int


class UserPreferencesUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    unsorted_label: str = Field(min_length=1, max_length=200)
