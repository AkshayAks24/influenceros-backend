from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CommentCreate(BaseModel):
    comment: str

class AuthorBasicInfo(BaseModel):
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)

class CommentResponse(BaseModel):
    id: int
    content_id: int
    author_id: int
    comment: str
    created_at: datetime
    author: AuthorBasicInfo
    
    model_config = ConfigDict(from_attributes=True)
