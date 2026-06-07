from pydantic import BaseModel


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class VapidPublicKeyOut(BaseModel):
    public_key: str
    configured: bool
