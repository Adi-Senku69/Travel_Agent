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
import os

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

TRUSTCALL_INSTRUCTION = """Create or update the memory (JSON doc) to incorporate information from the following conversation only if necessary. Do not change the organization rules. If no changes are necessary then return None"""

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

chatbot_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a travel assistant. Help answer questions based on the profile. Analyze the profile and give relevant suggestions according to the profile.
    The order of precedence for suggestions is likes, dislikes and then preferences. Adhere to the organizational rules for budget and other corporate matters.
    The itinerary must be in a well structured format with the most likely to visit places first. Do not provide more than 5 suggestions. Take into account if there is any meetings when providing the time for leisure activities. You are essentially a travel concierge.
    If there is some ambiguity in the question posed by the user, analyze the history to make some inferences, if that also does not work then ask a follow up question to rectify the ambiguity.
    Behave like a concierge, providing follow up suggestions after providing the answer. Provide emoji's in the output.

    Tool Call Instructions:
    Analyze the travel requirements carefully.
    To retrieve the flight data, use the flight_data tool call. The parameters of this tool, must first be generated from the prompt and then the travel requirements in the profile, and then if there is some ambiguity, clarify with the user. Use the current date and time to make real time booking suggestions. Make sure to adhere to all the organizational rules. When using departure token provide all the details including the departure token. If there are no flights, for the given query, then provide that as output and ask the user for clarification. For the return flight, unless the user specifies, use the date of departure as outbound date and keep the arrival date from 1-2 days from the outbound date.

    To get hotel data, use the get_hotel_data tool, and all the parameters to this tool must be acquired from the prompt and the travel requirements and the user preferences and the organizational rules. Any ambiguity present, clarify with the user.

    To get weather data, use the get_weather tool to get real time weather data. This tool can also forecast the weather for upto 3 days. Use this tool to account for the weather when generating itinerary, places to visit etc. if asked by the user. If the user asks to find the weather use this tool directly.

    Action Instructions:
    If for some reason a flight is canceled use the get_flight_data tool to get flight data, with the same arrival and departure id but new dates.
    Do the same for hotel rebooking also by using get_hotel_data tool.


    Answer questions only related to travelling.
    Use the current date and time for real time suggestions. This is the current date and time: {date_time}
    Summary of the conversation (can be empty also): {summary}
    Reply from the tools for tool calls(can be empty also). If the reply from the tools is 'There are no such flights for the given criteria.' Then return do not perform any more tool calls: {reply}
    If there is a reply from the tool calls, then provide the output based on the reply from the tool.
    Profile: {profile}
    Organization Rules: {organization}
    Travel Requirements: {travel_requirements}
    """),
    ("placeholder", "{messages}"),
    ("human", "{input}")

])

def chatbot(state: TravelAgent):
    prompt = state['prompt']
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
                    state['output'] = reply
                    state['messages'] = [("ai", reply)]
                    return state
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