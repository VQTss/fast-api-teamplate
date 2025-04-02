from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from app.models.schemas import EmbedResponse, IdentifyResponse, Base64EmbedRequest, Base64IdentifyRequest, ResponseSuccess, IdentifyResponse_New
from app.database.crud import save_embedding, find_closest_matches, find_closest_match_single_face, get_embeddings_by_person_id
from app.database.connection import get_db, API_UPLOAD
from app.dependencies import get_face_recognition_service
from app.utils.validation import validate_image_file, validate_base64_image
from app.services.face_recognition import FaceRecognitionService
import cv2
import numpy as np
import os
from  app.database.setup import reset_database
import base64
import httpx
router = APIRouter()


@router.post("/embed", response_model=str)
async def embed_face(
    person_id: str = Form(...),
    image: UploadFile = File(...),
    db=Depends(get_db),
    face_service: FaceRecognitionService = Depends(
        get_face_recognition_service)
):

    # Validate that the uploaded file is an image
    validate_image_file(image)

    try:
        image_data = await image.read()

        image_array = np.frombuffer(image_data, np.uint8)

        decoded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if decoded_image is None:
            raise HTTPException(
                status_code=400, detail="Could not decode image.")
        embedding = face_service.embed(decoded_image)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating embedding: {str(e)}")

    try:
        save_embedding(db, person_id, embedding)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save embedding: {str(e)}")

    return ResponseSuccess(code=200,status="success",message="Create users success")


@router.post("/identify", response_model=IdentifyResponse)
async def identify_faces(
    image: UploadFile = File(...),
    db=Depends(get_db),
    face_service: FaceRecognitionService = Depends(
        get_face_recognition_service)
):
    # Validate that the uploaded file is an image
    validate_image_file(image)
    try:
        image_data = await image.read()

        image_array = np.frombuffer(image_data, np.uint8)

        decoded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if decoded_image is None:
            raise HTTPException(
                status_code=400, detail="Could not decode image.")
        identified_faces = face_service.identify(decoded_image)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating embedding: {str(e)}")

    try:
        matches = find_closest_matches(db, identified_faces)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to identify face: {str(e)}")

    return IdentifyResponse(matches=matches, face_detected=len(matches) != 0)


@router.post("/identify-face", response_model=IdentifyResponse)
async def identifySingleFace(
    image: UploadFile = File(...),
    db=Depends(get_db),
    face_service: FaceRecognitionService = Depends(
        get_face_recognition_service)
):
    # Validate that the uploaded file is an image
    validate_image_file(image)
    try:
        image_data = await image.read()
        image_array = np.frombuffer(image_data, np.uint8)
        decoded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if decoded_image is None:
            raise HTTPException(
                status_code=400, detail="Could not decode image.")

        identified_face = face_service.identifySingleFace(decoded_image)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating embedding: {str(e)}")

    try:
        match = find_closest_match_single_face(db, identified_face)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to identify face: {str(e)}")

    return IdentifyResponse(matches=[match], face_detected=match is not None)



@router.post("/create-user", response_model=ResponseSuccess)
async def embed_face_base64(
    request: Base64EmbedRequest,
    db=Depends(get_db),
    face_service: FaceRecognitionService = Depends(get_face_recognition_service)
):
    validate_base64_image(request.image_base64)
    
    try:
        base64_str = request.image_base64.split(",")[-1]
        image_data = base64.b64decode(base64_str)
        image_array = np.frombuffer(image_data, np.uint8)
        decoded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if decoded_image is None:
            raise HTTPException(status_code=400, detail="Could not decode image.")
        embedding = face_service.embed(decoded_image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")
    
    file_upload_payload = {
        "base64String": request.image_base64,  
        "idDatabase": str(request.person_id),  
        "directory": "FACE"
    }
    try:
        async with httpx.AsyncClient() as client:
            file_upload_response = await client.post(API_UPLOAD, json=file_upload_payload)
        if file_upload_response.status_code != 201:
            raise HTTPException(status_code=500, detail="Failed to save image file externally.")
        file_upload_data = file_upload_response.json()
        file_path = file_upload_data.get("path")
        print("file_path",file_upload_response.json())
        if not file_path:
            raise HTTPException(status_code=500, detail="External API did not return a file path.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"External API error: {str(e)}")

    try:
        data_save = save_embedding(db, request.person_id, embedding, imageURL=file_path)
        print(data_save)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save embedding: {str(e)}")

    return ResponseSuccess(code=200,status="success",message="Create users success")




@router.post("/recognize", response_model=IdentifyResponse_New)
async def identify_faces_base64(
    request: Base64IdentifyRequest,
    db=Depends(get_db),
    face_service: FaceRecognitionService = Depends(get_face_recognition_service)
):
    # Xác thực chuỗi base64
    validate_base64_image(request.image_base64)
    
    try:
        base64_str = request.image_base64.split(",")[-1]
        image_data = base64.b64decode(base64_str)
        image_array = np.frombuffer(image_data, np.uint8)
        decoded_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if decoded_image is None:
            raise HTTPException(status_code=400, detail="Could not decode image.")
        identified_faces = face_service.identify(decoded_image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")
    
    try:
        matches = find_closest_matches(db, identified_faces)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to identify face: {str(e)}")
    
    return IdentifyResponse_New(person_id=matches[0].person_id, face_detected=len(matches) != 0, year="2002",gender=1)


@router.get("/reset-database")
def reset_database_endpoint():
    try:
        reset_database()
        return {"message": "Database reset successful."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database reset failed: {str(e)}")
    
    

@router.get("/embeddings/{person_id}")
def get_person_embeddings(person_id: str, db=Depends(get_db)):
    data = get_embeddings_by_person_id(db, person_id)
    if not data:
        raise HTTPException(status_code=404, detail="Person ID not found")

    return {"person_id": person_id, "records": data}