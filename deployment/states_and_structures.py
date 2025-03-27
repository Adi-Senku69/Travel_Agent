from langgraph.graph import MessagesState
from pydantic import BaseModel, Field
from typing import Literal, TypedDict

class Profile(BaseModel):
    travel_history: str = Field(description="The travel history of the employee.")
    preferences: str = Field(description="The preferences s (airlines, hotels, window/aisle, meal choice, etc.) of the employee.")
    role_specific_permissions: str = Field(description="The roles specific to this employee.")
    likes: str | None = Field(description="The likes of the employee.")
    dislikes: str | None = Field(description="The dislikes of the employee.")
    flight: str | None = Field(description="The flight details of the flight which the employee is taking.")
    hotel: str | None = Field(description="The hotel which the employee is staying.")

class TravelRequirements(BaseModel):
    destination: str = Field(description="The destination of travel the employee.")
    source: str | None = Field(description="The place from which the employee will start travelling")
    purpose: Literal['leisure', 'business'] = Field(description="The purpose of travel the employee.")
    date_of_departure: str = Field(description="The date of departure of the employee.")
    date_of_arrival: str = Field(description="The date of arrival of the employee.")
    duration: str = Field(description="The duration of travel the employee.")

class OrganizationalRules(BaseModel):
    travel_budgets: str = Field(description="The travel budgets of the organization for each cadre of employee")
    approval_hierarchies: str= Field(description="The approval hierarchies for each employee.")
    preferred_vendors: str = Field(description="The preferred vendors for the organization.")
    visa_requirements: str = Field(description="The type of visa requirements for the travel.")

class Traveller(BaseModel):
    name: str = Field(description="The name of the employee.")
    employee_id: str = Field(description="The ID of the employee.")
    profile: Profile = Field(description="The profile of the employee.")
    travel_requirements: TravelRequirements = Field(description="The travel requirements for the employee.")
    organizational_rules: OrganizationalRules = Field(description="The organizational rules for the employee.")

class Travellers(BaseModel):
    travellers: list[Traveller] = Field(description="The list of travellers.")

class SummaryGraphInput(TypedDict):
    summary: str
    text: str

class SummaryGraphOutput(TypedDict):
    summary_graph: str

class TravelAgent(MessagesState):
    profile: Traveller
    output: str
    prompt: str
    summary: str
    flight_data: str
    hotel_data: str
    weather_data: str
    summary_graph: str
    user_specification: str
    count: int
