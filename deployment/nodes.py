from prompt_llm import *
from states_and_structures import *
from utils import *
from tools import tools
from langchain_core.prompts import ChatPromptTemplate
from langgraph.constants import END
from datetime import datetime
from trustcall import create_extractor
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import SystemMessage, AIMessage, RemoveMessage, ToolMessage
from langgraph.store.base import BaseStore
import requests
import os

env_values = {"WEATHERAPI_KEY": os.environ.get("WEATHERAPI_KEY")}

def read_docs(state: SummaryGraphInput):
    PATH_TO_FILES = "./Data"
    dirs = os.listdir(PATH_TO_FILES)
    text = ""
    for dir in dirs:
        files = os.listdir(os.path.join(PATH_TO_FILES, dir))
        for file in files:
            if not file.endswith(".pdf"):
                text += read_csv_xlsx(os.path.join(os.path.join(PATH_TO_FILES, dir), file))
            else:
                text += read_pdf(os.path.join(os.path.join(PATH_TO_FILES, dir), file))

    return {'text': text}

def summarize(state: SummaryGraphInput):
    text = state['text']
    runnable_summarization = summarization_prompt | llm
    output = runnable_summarization.invoke({'input': text}).content
    with open("./summary/summary.txt", "w") as f:
        f.write(output)
    return {'summary_graph': output}

def add_travellers(state: TravelAgent, store:BaseStore):
    with open("./summary/summary.txt", "r") as f:
        data = f.read()
    trustcall_extractor = create_extractor(
    llm,
    tools=[Travellers],
    tool_choice="Travellers")
    system_msg = "Extract the profiles of all employees from the given data. {data}"
    trustcaller_system_message = SystemMessage(content=system_msg.format(data=data))
    result = trustcall_extractor.invoke({"messages": [trustcaller_system_message]})
    travellers =  result["messages"][0].tool_calls[0]['args']['travellers']
    for traveller in travellers:
        key = traveller.get("employee_id", None)
        if key is not None:
            namespace = ("memory", key.lower())
            store.put(namespace, "traveler", traveller)
    return state

def read_profile(state: TravelAgent, config: RunnableConfig, store: BaseStore):
    id = config['configurable']['user_id']
    namespace = ("memory", id)
    user_specification = state.get('user_specification')
    profile = store.get(namespace, "traveler")
    if user_specification is not None and profile is not None:
        extractor = create_extractor(
            llm,
            tools=[Traveller],
            tool_choice="Traveller"
        )
        result = extractor.invoke({"messages": [("system", "Update the travel specification."), ("human", user_specification)], 'existing': {"Traveller": profile}})
        updated_profile = result['responses'][0].model_dump()
        state['profile'] = updated_profile
        store.put(namespace, "traveller", updated_profile)
        return state
    state['profile'] = profile.value
    state['count'] = 0
    return state

def to_create_profile(state: TravelAgent, store: BaseStore, config: RunnableConfig):
    file_path = "../summary/summary.txt"
    if os.path.exists(file_path) and os.stat(file_path).st_size == 0:
        return "summary graph"
    elif not store.search(('memory', config['configurable']['user_id'])):
        return "add travellers"
    else:
        return "read profile"

def check_profiles(state: TravelAgent):
    profile = state['profile']
    if profile is None:
        return END
    else:
        return "chatbot"

def route_ai(state: TravelAgent):
    messages = state['messages']
    count = 0
    for message in messages:
        if isinstance(message, AIMessage) and count < 5:
            if message.content:
                count += 1
    print(count)
    if count >= 5:
        return "summarizer and updater"
    else:
        return END

def summarizer_and_updater(state: TravelAgent, config: RunnableConfig, store: BaseStore):
    messages = state['messages']
    summarization_prompt_inside = ChatPromptTemplate.from_messages([
    ("system", """You are an assistant, who helps in summarizing the conversation.
    Conversation: {messages}"""),
    ("human", "Summarize the conversation")
])
    runnable_summarizer = summarization_prompt_inside | llm
    extractor = create_extractor(
        llm,
        tools=[Traveller],
        tool_choice="Traveller"
    )
    summary = state.get('summary', "")
    output = runnable_summarizer.invoke({'messages': messages}).content
    summary += output
    deleted_messages = [RemoveMessage(id=message.id) for message in messages[:-4]]
    profile = state['profile']
    json_profile = {"Traveller": profile}

    result = extractor.invoke({"messages": [SystemMessage(content=TRUSTCALL_INSTRUCTION)] + messages, 'existing': json_profile})
    updated_profile = result['responses'][0].model_dump()
    store.put(("memory", config['configurable']['user_id']), 'traveler', updated_profile)
    state['summary'] = summary
    state['messages'] = deleted_messages
    return state


def chatbot(state: TravelAgent, store:BaseStore, config: RunnableConfig):
    id = config['configurable']['user_id']
    namespace = ("memory", id)
    hotel_status, weather_status = None, None

    if store.get(namespace, "Hotel_Alert") is not None:
        hotel_status = store.get(namespace, "Hotel_Alert").value
    if store.get(namespace, "Weather_Alert") is not None:
        weather_status = store.get(namespace, "Weather_Alert").value
    prompt = state['prompt']
    hotel_data = state.get('hotel_data')

    if hotel_status is not None and hotel_data:
        prompt = "Give me some other suggestions as the hotels have been canceled"
        store.put(namespace, "Hotel_Alert", {})

    elif weather_status is not None:
        prompt = "The weather is really bad, inform the user."
        store.put(namespace, "Weather_Alert", {})

    summary = state.get('summary', "")
    profile = state['profile']
    messages = state['messages']
    date_time = datetime.now()
    formatted_date_time = date_time.strftime("%Y-%m-%d %H:%M:%S")
    reply = state.get("flight_data", "")
        # print("Inside")
    last_instance = messages[-1]
    if isinstance(last_instance, ToolMessage):
        if messages[-2].tool_calls[0]['name'] == "get_flight_data":
            if  "error" not in last_instance.content.lower():
                reply = last_instance.content
                if 'There are no such flights for the given criteria.' in reply:
                        prompt = reply
                state['flight_data'] = reply
        elif messages[-2].tool_calls[0]['name'] == "get_hotel_data":
            reply = last_instance.content
            state['hotel_data'] = reply
        elif messages[-2].tool_calls[0]['name'] == "get_weather":
            reply = last_instance.content
            state['weather_data'] = reply

        messages.pop()
        messages.pop()
    # print(summary)
    runnable_chatbot = chatbot_prompt | llm.bind_tools(tools, parallel_tool_calls=False)
    output = runnable_chatbot.invoke({'input': prompt, 'summary': summary, "profile": str({"name": profile['name'] , "profile":profile['profile']}), "reply": reply, 'messages': messages, 'date_time': formatted_date_time, 'organization': profile['organizational_rules'], 'travel_requirements': profile['travel_requirements']})
    state['output'] = output.content
    state['messages'] = [output]
    return state

def route_to_update(state: TravelAgent):
    prompt = state['prompt']
    system_msg = "If the user provides some personal preferences, likes or dislikes, or something related to travel requirements such as destination, duration of the trip, type of trip, flight taken, hotel staying at, etc. then return 'true', else return 'false'. Do not provide any explanations."
    template = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("human", prompt)
    ])
    runnable_template = template | llm
    output = runnable_template.invoke({}).content
    if "true" in output:
        return "update profile"
    else:
        return END

def update_profile(state: TravelAgent, store:BaseStore, config: RunnableConfig):
    prompt = state['prompt']
    profile = state['profile']
    json_profile = {"Traveller": profile}

    trustcall_system_msg = "Update the profile based on based on the prompt. Update the dates if the user specifies a date. Update the places of stay and the flight taken also if needed."
    extractor = create_extractor(
        llm,
        tools=[Traveller],
        tool_choice='Traveller',
    )
    flight = profile.get('flight')
    hotel = profile.get('hotel')
    if flight is not None and hotel is not None:
        result = extractor.invoke({'messages':[("system", trustcall_system_msg),("human", prompt + state['flight_data'] + "Save the flight number" + state['hotel_data'])], 'existing': json_profile})
    elif flight is not None:
        result = extractor.invoke({'messages':[("system", trustcall_system_msg),("human", prompt + state['flight_data'] + "Save the flight number")], 'existing': json_profile})
    elif hotel is not None:
        result = extractor.invoke({'messages':[("system", trustcall_system_msg),("human", prompt + state['hotel_data'])], 'existing': json_profile})
    else:
        result = extractor.invoke({'messages':[("system", trustcall_system_msg),("human", prompt)], 'existing': json_profile})

    updated_profile = result['responses'][0].model_dump()
    store.put(("memory", config['configurable']['user_id']), 'traveler', updated_profile)
    state['profile'] = updated_profile
    return state

def fetch_flight_status(state: TravelGraphState) -> TravelGraphState:
    """Simulate fetching flight status."""
    state["flight_status"] = [{"flight": "AI-202", "status": "Delayed"}]
    return state

def fetch_hotel_availability(state: TravelGraphState) -> TravelGraphState:
    """Simulate fetching hotel availability."""
    state["hotel_status"] = [{"hotel": "Hilton", "status": "Fully Booked"}]
    return state

def fetch_booking_status(state: TravelGraphState) -> TravelGraphState:
    """Simulate fetching booking status."""
    state["booking_status"] = [{"reference": "BKG-12345", "status": "Cancelled"}]
    return state

def fetch_weather_status(state: TravelGraphState) -> TravelGraphState:
    """Fetch weather information using an API and update the state."""
    city = state.get("city", "Bangalore")
    API_KEY = env_values['WEATHERAPI_KEY']

    if not API_KEY:
        state["weather_status"] = [{"city": city, "condition": "Unknown", "temperature": "N/A"}]
        return state

    URL = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&aqi=no"
    response = requests.get(URL)

    if response.status_code == 200:
        data = response.json()
        state["weather_status"] = [{
            "city": city,
            "condition": data["current"]["condition"]["text"],
            "temperature": data["current"]["temp_c"],
        }]
    else:
        state["weather_status"] = [{"city": city, "condition": "Unknown", "temperature": "N/A"}]

    return state


def store_memory(state: TravelGraphState, store: BaseStore, config: RunnableConfig) -> TravelGraphState:
    user_id = config.get("configurable", {}).get("user_id", "default_user")
    namespace = ("memory", user_id)

    memory_updates = []

    for flight in state.get("flight_status", []):
        if flight.get("status") in ["Delayed", "Cancelled"]:
            alert = f"{flight['status']} - {flight['flight']}"
            store.put(namespace, "Flight_Alert", alert)
            memory_updates.append(alert)

    for booking in state.get("booking_status", []):
        if booking.get("status") == "Cancelled":
            alert = f"{booking['reference']} was cancelled!"
            store.put(namespace, "Booking_Alert", alert)
            memory_updates.append(alert)

    for hotel in state.get("hotel_status", []):
        if hotel.get("status") == "Fully Booked":
            alert = f"{hotel['hotel']} has no available rooms!"
            store.put(namespace, "Hotel_Alert", alert)
            memory_updates.append(alert)

    for weather in state.get("weather_status", []):
        if weather.get("condition") in ["Thunderstorm", "Heavy Rain", "Extreme Heat"]:
            alert = f"Severe weather in {weather['city']}: {weather['condition']}"
            store.put(namespace, "Weather_Alert", alert)
            memory_updates.append(alert)

    state["memory"] = merge_lists(state.get("memory", []), memory_updates)
    print("inside graph alert")
    return state
