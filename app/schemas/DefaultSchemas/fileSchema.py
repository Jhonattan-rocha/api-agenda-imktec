from pydantic import BaseModel

class PDF(BaseModel):
    template_id: str
    data: dict

class FileBase(BaseModel):
    filename: str
    originalname: str
    content_type: str
    file_path: str

class FileCreate(FileBase):
    id: int

class FileResponse(FileBase):
    id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
    