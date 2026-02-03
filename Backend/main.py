from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime
from typing import Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Big Five OCEAN API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = MongoClient(MONGO_URL)
db = client["bigfive"]  
ocean_collection = db["ocean_scores"]  
tasks_collection = db["tasks"]         

print("=" * 60)
print("🚀 FastAPI Backend Started!")
print(f"📊 MongoDB Connected: {MONGO_URL}")
print(f"📦 Database: bigfive")
print(f"📁 Collection: ocean_scores")
print("=" * 60)

# Data models
class OceanScores(BaseModel):
    openness: float
    conscientiousness: float
    extraversion: float
    agreeableness: float
    neuroticism: float

class OceanData(BaseModel):
    report_id: str
    timestamp: str
    ocean_scores: OceanScores
    ocean_normalized: OceanScores

class TaskItem(BaseModel):
    task_name: str
    importance_kk: float
    required_time_trk: float
    available_time_tak: float
    report_id: str
    created_at: Optional[str] = None

from pfactor import calculate_p_factor
from memory.retention import calculate_retention, calculate_retention_from_timestamp

from memory.confidece import calculate_confidence
from memory.reconstruction import reconstruct_memory
from memory.priority import calculate_priority
from memory.linguistic import generate_npc_response

@app.post("/api/save-ocean-scores")
async def save_ocean_scores(data: OceanData):
    
    try:
        print("\n" + "=" * 60)
        print("RECEIVED DATA FROM FRONTEND")
        print("=" * 60)
        print(f"Report ID: {data.report_id}")
        print(f"Timestamp: {data.timestamp}")
        
        # Calculate P-Factor
        ocean_dict = {
            "openness": data.ocean_normalized.openness,
            "conscientiousness": data.ocean_normalized.conscientiousness,
            "extraversion": data.ocean_normalized.extraversion,
            "agreeableness": data.ocean_normalized.agreeableness,
            "neuroticism": data.ocean_normalized.neuroticism
        }
        p_factor = calculate_p_factor(ocean_dict)
        print(f"\n🧠 Calculated P-Factor: {p_factor}")
        
        # Calculate Retention for logging (but don't store it)
        retention_val, phase, _ = calculate_retention(p_factor, days=0)
        print(f"📊 Calculated Retention (Day 0): {retention_val}")
        
        # Calculate Confidence based on retention
        conf_val, conf_label = calculate_confidence(retention_val) 
        print(f"   Confidence: {conf_val} ({conf_label})")
        
        recon_msg = reconstruct_memory(retention_val)
        print(f"   Reconstruction: {recon_msg}")
        
        # Priority Calculation
        prio_val, prio_msg = calculate_priority(0.8, 2.0, 5.0)
        print(f"   Priority: {prio_msg}")

        # Trigger initial linguistic generation
        base_memory = "Initial data ingestion and personality assessment."
        response_text = generate_npc_response(base_memory, conf_label, phase, retention_val)

        # Prepare document for MongoDB without retention fields
        document = {
            "report_id": data.report_id,
            "timestamp": data.timestamp,
            "p_factor": p_factor,
            "priority_mock": prio_val,
            "ocean_scores": data.ocean_scores.dict(),
            "ocean_normalized": data.ocean_normalized.dict(),
            "saved_at": datetime.now().isoformat(),
            "last_linguistic_response": response_text,
            "confidence_at_generation": conf_val,
            "retention_at_generation": retention_val,
            "generation_timestamp": datetime.now().isoformat()
        }
        
        # Insert into MongoDB
        result = ocean_collection.insert_one(document)
        
        print(f"\n✅ SAVED TO MONGODB")
        print(f"   MongoDB ID: {result.inserted_id}")
        print("=" * 60 + "\n")
        
        return {
            "success": True,
            "message": "OCEAN scores saved successfully",
            "data": {
                "mongodb_id": str(result.inserted_id),
                "report_id": data.report_id,
                "p_factor": p_factor
            }
        }
    except Exception as e:
        print(f"\n ERROR SAVING TO MONGODB: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/simulate-memory")
async def simulate_memory(p_factor: float, days: float, strength: float = 2.8):
    
    try:
        # Using boilerplate functions now
        ret_val, phase, _ = calculate_retention(p_factor)
        ret_msg = (ret_val, phase)
        conf_val, conf_label = calculate_confidence(0.5) 
        
        return {
            "success": True,
            "inputs": {
                "p_factor": p_factor,
                "days_passed": days,
                "memory_strength": strength
            },
            "results": {
                "retention_msg": ret_msg,
                "confidence_score": conf_val,
                "confidence_label": conf_label
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get-ocean-scores/{report_id}")
async def get_ocean_scores(report_id: str):
    
    try:
        print(f"\n Searching for report_id: {report_id}")
        
        result = ocean_collection.find_one({"report_id": report_id})
        
        if not result:
            print(f" Report not found: {report_id}\n")
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Convert ObjectId to string
        result["_id"] = str(result["_id"])
        
        print(f"Found report: {report_id}")
        print(f"   Normalized scores: O={result['ocean_normalized']['openness']:.3f}, "
              f"C={result['ocean_normalized']['conscientiousness']:.3f}, "
              f"E={result['ocean_normalized']['extraversion']:.3f}, "
              f"A={result['ocean_normalized']['agreeableness']:.3f}, "
              f"N={result['ocean_normalized']['neuroticism']:.3f}\n")
        
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f" Error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/all-ocean-scores")
async def get_all_ocean_scores():

    try:
        results = list(ocean_collection.find().sort("saved_at", -1))
        
        # Convert ObjectId to string
        for result in results:
            result["_id"] = str(result["_id"])
        
        print(f"\n📊 Retrieved {len(results)} OCEAN score records from MongoDB\n")
        
        return {
            "success": True,
            "count": len(results),
            "data": results
        }
    except Exception as e:
        print(f" Error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/delete-ocean-scores/{report_id}")
async def delete_ocean_scores(report_id: str):
   
    try:
        result = ocean_collection.delete_one({"report_id": report_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Report not found")
        
        print(f"🗑️ Deleted report: {report_id}\n")
        
        return {
            "success": True,
            "message": f"Report {report_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f" Error: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save-task")
async def save_task(task: TaskItem):
    
    try:
        task_dict = task.dict()
        task_dict["created_at"] = datetime.now().isoformat()
        
        # Ensure numeric types
        task_dict["importance_kk"] = float(task_dict["importance_kk"])
        task_dict["required_time_trk"] = float(task_dict["required_time_trk"])
        task_dict["available_time_tak"] = float(task_dict["available_time_tak"])
        
        result = tasks_collection.insert_one(task_dict)
        print(f"📝 Task Assigned: {task.task_name} | ID: {result.inserted_id}")
        
        return {
            "success": True,
            "message": "Task saved successfully",
            "task_id": str(result.inserted_id)
        }
    except Exception as e:
        print(f" Error saving task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get-tasks/{report_id}")
async def get_tasks(report_id: str):
   
    try:
        tasks = list(tasks_collection.find({"report_id": report_id}).sort("created_at", -1))
        for t in tasks:
            t["_id"] = str(t["_id"])
        
        return {
            "success": True,
            "tasks": tasks
        }
    except Exception as e:
        print(f" Error fetching tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-npc-response/{report_id}")
async def generate_response(report_id: str, base_memory: str = "The last assigned task"):
    
    try:
        # Find the most recent record for this report_id
        report = ocean_collection.find_one({"report_id": report_id}, sort=[("saved_at", -1)])
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Calculate current retention
        start_time = datetime.fromisoformat(report["saved_at"])
        retention, debug, phase = calculate_retention_from_timestamp(report["p_factor"], start_time)
        
        # Calculate confidence
        conf_val, conf_label = calculate_confidence(retention)
        
        # Generate Linguistic Response
        response_text = generate_npc_response(base_memory, conf_label, phase, retention)
        
        # Persist to DB - Target the specific document using its unique _id
        update_data = {
            "last_linguistic_response": response_text,
            "confidence_at_generation": conf_val,
            "retention_at_generation": retention,
            "generation_timestamp": datetime.now().isoformat()
        }
        
        ocean_collection.update_one({"_id": report["_id"]}, {"$set": update_data})
        
        print(f"🗣️ Generated Response for {report_id}: {response_text[:30]}...")
        
        return {
            "success": True,
            "response": response_text,
            "metadata": {
                "confidence_label": conf_label,
                "confidence_score": conf_val,
                "retention_val": retention,
                "phase": phase
            }
        }
    except Exception as e:
        print(f" Generation Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    
    return {
        "message": "Big Five OCEAN API with MongoDB",
        "status": "running",
        "database": "MongoDB connected",
        "endpoints": {
            "POST /api/save-ocean-scores": "Save OCEAN test results to MongoDB",
            "GET /api/get-ocean-scores/{report_id}": "Get results by report ID",
            "GET /api/all-ocean-scores": "Get all saved results",
            "DELETE /api/delete-ocean-scores/{report_id}": "Delete results by report ID",
            "POST /api/save-task": "Assign a task to an NPC",
            "GET /api/get-tasks/{report_id}": "Get all tasks for a specific NPC",
            "POST /api/generate-npc-response/{report_id}": "Generate linguistic NPC response"
        }
    }

@app.get("/health")
async def health_check():
   
    try:
        # Test MongoDB connection
        client.server_info()
        return {
            "status": "healthy",
            "mongodb": "connected",
            "database": "bigfive",
            "collection": "ocean_scores"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "mongodb": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    print("\n Starting FastAPI server...")
    print(" Server will run on: http://localhost:8000")
    print(" API docs available at: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)