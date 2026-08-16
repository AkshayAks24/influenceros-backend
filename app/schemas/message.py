from datetime import datetime
from pydantic import BaseModel, ConfigDict

class MessageCreate(BaseModel):
    receiver_id: int
    message: str

class MessageResponse(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    message: str
    is_read: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ConversationSummary(BaseModel):
    other_user_id: int
    other_user_name: str
    last_message: str
    last_message_at: datetime
    unread_count: int
    
    model_config = ConfigDict(from_attributes=True)
