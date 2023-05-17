import pandas as pd
from typing import Any, Dict
import streamlit as st


def init_session_state(state_dict: Dict[str, Any]) -> None:
    """
    Initialize the session state with the given state names
    :param state_dict: the dictionary of state names to initialize
    """
    for key in state_dict:
        if key not in st.session_state:
            st.session_state[key] = state_dict[key]


def update_openai_key(api_key):
    """
    Update the openai api key to the session_state
    :param api_key: the openai api key to update
    """
    st.session_state['openai_api_key'] = api_key

@st.cache_data
def convert_df(df: pd.DataFrame) -> str:
    """
    Convert a dataframe to a csv string
    :param df: the dataframe to convert
    """
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')