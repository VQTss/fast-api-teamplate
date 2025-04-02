from pydantic import BaseModel
from typing import List, Tuple, Optional
from fastapi import UploadFile, File


class Person(BaseModel):
    id: int
    name: str

class EmbedRequest(BaseModel):
    name: str
    image: UploadFile  = File(...)

class EmbedResponse(BaseModel):
    person: Person

class IdentifyRequest(BaseModel):
    image: UploadFile = File(...)

class Match(BaseModel):
    person_id: str
    confidence: Optional[float] = None
    bbox: Optional[List[float]] = None

class IdentifyResponse(BaseModel):
    matches: List[Match]
    face_detected: bool
    year: str
    gender: int

class IdentifyResponse_New(BaseModel):
    person_id: str
    face_detected: bool
    year: str
    gender: int

    
class Face(BaseModel):
    bbox: List[float]
    embeddings: List[float]


class Base64EmbedRequest(BaseModel):
    person_id: str
    image_base64: str

class Base64IdentifyRequest(BaseModel):
    image_base64: str

class ResponseSuccess(BaseModel):
    code: int
    status: str
    message: str