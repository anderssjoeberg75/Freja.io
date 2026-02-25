from fastapi import APIRouter
from app.core.security import require_admin
from fastapi import Depends

router = APIRouter(dependencies=[Depends(require_admin)])

@router.get("/api/documents")
async def list_documents():
    from skills.document_analysis.tools import get_collection
    try:
        col = get_collection()
        total = col.count()
        if total == 0:
            return {"documents": [], "total_chunks": 0}

        all_meta = col.get(include=["metadatas"])["metadatas"]
        sources = {}
        for m in all_meta:
            src = m.get("source", "okänd")
            if src not in sources:
                sources[src] = {"chunks": 0, "hash": m.get("doc_hash", "")}
            sources[src]["chunks"] += 1

        docs = [{"name": name, **data} for name, data in sources.items()]
        return {"documents": docs, "total_chunks": total}
    except Exception as e:
        return {"documents": [], "total_chunks": 0, "error": str(e)}

@router.delete("/api/documents/{document_name:path}")
async def delete_document(document_name: str):
    from skills.document_analysis.tools import get_collection
    try:
        col = get_collection()
        col.delete(where={"source": document_name})
        return {"success": True, "message": f"Deleted {document_name}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


from fastapi import UploadFile, File
from skills.document_analysis.tools import ingest_document_impl
import os
from app.core.config import BASE_DIR
import aiofiles

@router.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Save temp file
        upload_dir = os.path.join(BASE_DIR, "data", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, file.filename)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
            
        # Ingest
        result = await ingest_document_impl(file_path, file.filename)
        
        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass
            
        if "Error" in result:
            return {"error": result}
        return {"success": True, "message": result}
        
    except Exception as e:
        return {"error": str(e)}
