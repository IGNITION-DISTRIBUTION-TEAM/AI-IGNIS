import json
import os
from collections import defaultdict
import time
import numpy as np
import pandas as pd
import requests
import sseclient
import streamlit as st
from models.chart_event_data import ChartEventData
from models.data_agent_run_request import DataAgentRunRequest
from models.error_event_data import ErrorEventData
from models.message import Message
from models.message_content_item import MessageContentItem
from models.status_event_data import StatusEventData
from models.table_event_data import TableEventData
from models.text_content_item import TextContentItem
from models.text_delta_event_data import TextDeltaEventData
from models.thinking_delta_event_data import ThinkingDeltaEventData
from models.thinking_event_data import ThinkingEventData
from models.tool_result_event_data import ToolResultEventData
from models.tool_use_event_data import ToolUseEventData
import jwt
from datetime import datetime, timedelta, timezone
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.backends import default_backend
import urllib3
from db import get_JWT

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)

HOST = "pm58521.east-us-2.azure.snowflakecomputing.com"
DATABASE = "SNOWFLAKE_INTELLIGENCE"
SCHEMA = "AGENTS"
AGENT = "IGNITION_POLICIES_ASSISTANT"

db_token = get_JWT()

def agent_run() -> requests.Response:
    """Calls the REST API and returns a streaming client."""
    request_body = DataAgentRunRequest(
        model="claude-4-sonnet",
        messages=st.session_state.messages,
    )
    resp = requests.post(
        url=f"https://{HOST}/api/v2/databases/{DATABASE}/schemas/{SCHEMA}/agents/{AGENT}:run",
        data=request_body.to_json(),
        headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {db_token}",
        "X-Snowflake-Authorization-Token-Type": "KEYPAIR_JWT"
        },
        stream=True,
        verify=False,
    )
    if resp.status_code < 400:
        return resp  # type: ignore
    else:
        raise Exception(f"Failed request with status {resp.status_code}: {resp.text}")


def stream_events(response: requests.Response):
    content = st.container()
    # Content index to container section mapping
    content_map = defaultdict(content.empty)
    # Content index to text buffer
    buffers = defaultdict(str)
    spinner = st.spinner("Waiting for response...")
    spinner.__enter__()

    events = sseclient.SSEClient(response).events()
    for event in events:
        match event.event:
            case "response.status":
                spinner.__exit__(None, None, None)
                data = StatusEventData.from_json(event.data)
                spinner = st.spinner(data.message)
                spinner.__enter__()
            case "response.text.delta":
                data = TextDeltaEventData.from_json(event.data)
                buffers[data.content_index] += data.text
                content_map[data.content_index].write(buffers[data.content_index])
            case "response.thinking.delta":
                data = ThinkingDeltaEventData.from_json(event.data)
                buffers[data.content_index] += data.text
                content_map[data.content_index].expander(
                    "Thinking", expanded=True
                ).write(buffers[data.content_index])
            case "response.thinking":
                # Thinking done, close the expander
                data = ThinkingEventData.from_json(event.data)
                content_map[data.content_index].expander("Thinking").write(data.text)
            case "response.tool_use":
                data = ToolUseEventData.from_json(event.data)
                content_map[data.content_index].expander("Tool use").json(data)
            case "response.tool_result":
                data = ToolResultEventData.from_json(event.data)
                content_map[data.content_index].expander("Tool result").json(data)
            case "response.chart":
                data = ChartEventData.from_json(event.data)
                spec = json.loads(data.chart_spec)
                content_map[data.content_index].vega_lite_chart(
                    spec,
                    use_container_width=True,
                )
            case "response.table":
                data = TableEventData.from_json(event.data)
                data_array = np.array(data.result_set.data)
                column_names = [
                    col.name for col in data.result_set.result_set_meta_data.row_type
                ]
                content_map[data.content_index].dataframe(
                    pd.DataFrame(data_array, columns=column_names)
                )
            case "error":
                data = ErrorEventData.from_json(event.data)
                st.error(f"Error: {data.message} (code: {data.code})")
                # Remove last user message, so we can retry from last successful response.
                st.session_state.messages.pop()
                return
            case "response":
                data = Message.from_json(event.data)
                st.session_state.messages.append(data)
    spinner.__exit__(None, None, None)


def process_new_message(prompt: str) -> None:
    message = Message(
        role="user",
        content=[MessageContentItem(TextContentItem(type="text", text=prompt))],
    )
    render_message(message)
    st.session_state.messages.append(message)

    with st.chat_message("assistant"):
        with st.spinner("Sending request..."):
            response = agent_run()
        st.markdown(
            f"```request_id: {response.headers.get('X-Snowflake-Request-Id')}```"
        )
        stream_events(response)


def render_message(msg: Message):
    with st.chat_message(msg.role):
        for content_item in msg.content:
            match content_item.actual_instance.type:
                case "text":
                    st.markdown(content_item.actual_instance.text)
                case "chart":
                    spec = json.loads(content_item.actual_instance.chart.chart_spec)
                    st.vega_lite_chart(spec, use_container_width=True)
                case "table":
                    data_array = np.array(
                        content_item.actual_instance.table.result_set.data
                    )
                    column_names = [
                        col.name
                        for col in content_item.actual_instance.table.result_set.result_set_meta_data.row_type
                    ]
                    st.dataframe(pd.DataFrame(data_array, columns=column_names))
                case _:
                    st.expander(content_item.actual_instance.type).json(
                        content_item.actual_instance.to_json()
                    )
                    
col1, col2, col3 = st.columns([2,5,2], vertical_alignment="center")
    
with col2:
    with st.container(horizontal_alignment="center", vertical_alignment="top"):

        name = st.session_state['name']
        surname = st.session_state['surname']
    
        st.markdown(f"""
        <h2 style="
            text-align: center;
            background: linear-gradient(to right, #007BFF, #00FFFF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        ">
        Welcome {name} {surname}
        </h2>
        """, unsafe_allow_html=True)

        with st.container(horizontal_alignment="center", vertical_alignment="center"):
        
            if "messages" not in st.session_state:
                st.session_state.messages = []
            
            for message in st.session_state.messages:
                render_message(message)

        with st.container(horizontal_alignment="center", vertical_alignment="bottom"):
        
            if user_input := st.chat_input("How can I help you?"):
                process_new_message(prompt=user_input)
