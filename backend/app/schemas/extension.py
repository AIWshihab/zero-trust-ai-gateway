from datetime import datetime

from pydantic import BaseModel, Field


class ExtensionPairingTokenResponse(BaseModel):
    token: str
    expires_at: datetime
    gateway_api_base_url: str
    setup_session_id: str | None = None
    connect_url: str | None = None
    chrome_extension_store_url: str | None = None
    extension_id: str | None = None


class ExtensionRegisterDeviceRequest(BaseModel):
    pairing_token: str = Field(..., min_length=12)
    setup_session_id: str | None = Field(default=None, max_length=80)
    browser_name: str = Field(default="Unknown", max_length=80)
    extension_version: str = Field(default="0.1.0", max_length=32)
    user_agent: str = Field(default="", max_length=512)
    timezone: str = Field(default="", max_length=80)
    platform: str = Field(default="", max_length=120)
    device_label: str = Field(default="Browser extension", max_length=160)


class ExtensionRegisterDeviceResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    device_id: int
    gateway_api_base_url: str


class ExtensionSetupSessionResponse(BaseModel):
    setup_session_id: str
    status: str
    expires_at: datetime
    gateway_api_base_url: str
    connect_url: str
    chrome_extension_store_url: str | None = None
    extension_id: str | None = None
    device_id: int | None = None
    browser_name: str | None = None
    extension_version: str | None = None
    last_connected_at: datetime | None = None
