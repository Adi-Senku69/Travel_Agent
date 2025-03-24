# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.ai_travel_assistant import AITravelAssistant
from config import config

app = FastAPI(title="AI Travel Assistant API")

# initialize the travel assistant
assistant = AITravelAssistant(config)

class QueryRequest(BaseModel):
    user_id: str
    message: str

class QueryResponse(BaseModel):
    response: str

@app.post("/api/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    try:
        response = await assistant.process_user_query(request.user_id, request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")

# Add an endpoint for trip registration with proactive alerts
class TripRegistrationRequest(BaseModel):
    user_id: str
    trip_details: dict

@app.post("/api/register-trip")
async def register_trip(request: TripRegistrationRequest):
    try:
        # This would need a notification callback implementation
        # and ProactiveAlertSystem setup
        return {"status": "Trip registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register trip: {str(e)}")

if __name__== "_main_":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0",port=8080)
