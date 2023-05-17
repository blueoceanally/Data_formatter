import streamlit as st
import pandas as pd
import os
import sys

from datetime import datetime
from streamlit_ace import st_ace, KEYBINDINGS, LANGUAGES, THEMES

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from table_formatter import OpenAIFormatter
from utils import *
from streamlit_utils import *

os.environ["OPENAI_API_KEY"] = ""

state_dict = {
    'reformat': False,
    'gen_code_done': False,
    'gen_code': False,
    "run_code": False,
    'code_string': "",
    'openai_api_key': "",
}


def show_column_map(template_df, input_df, col_name_map):
    """
    Show the generated column mapping from the input dataframe to the template dataframe.
    - If the column only has one option, it will just show the mapping and disable the selection.
    - If the column has multiple options, it will show the selection and let the user to choose.
    - If the column has no option found, it will show all columns in input dataframe.
    :param template_df: the template dataframe
    :param col_name_map: the column name mapping from input dataframe to template dataframe
    :return: Selected column names
    """
    template_cols = template_df.columns.values.tolist()
    input_cols = input_df.columns.values.tolist()
    selected_value = [0]*len(template_cols)
    for idx, col in enumerate(template_cols):
        map_col1, map_col2, map_col3 = st.columns([5, 1, 5], gap="small")
        if col not in col_name_map:
            selected_value[idx] = map_col1.selectbox("", input_cols)
            map_col2.write("->")
            map_col3.selectbox("", [col], disabled=True)
        elif type(col_name_map[col]) == list:
            selected_value[idx] = map_col1.selectbox("", col_name_map[col])
            map_col2.write(":arrow_right:")
            map_col3.selectbox("", [col], disabled=True)
        else:
            selected_value[idx] = map_col1.selectbox("", [col_name_map[col]], disabled=True)
            map_col2.markdown("<br><br>            --->", unsafe_allow_html=True)
            map_col3.selectbox("", [col], disabled=True)

    return selected_value


def search_existing_map_code(table_formatter, template_file_name, input_file_name):
    """
    Search for existing map code in the saved database.
    :param table_formatter: the table formatter
    """
    database = load_file("saved/index.txt")
    file_name = table_formatter.search_for_existing_map(template_file_name, input_file_name, database)
    try:
        map_code_string = load_file(file_name.strip("\n").strip("`"))
        st.session_state['code_string'] = map_code_string
        st.write("Found existing map code")
        st.session_state['gen_code_done'] = True
        st.session_state['gen_code'] = True
    except Exception as e:
        st.write("Generating new map code")


def reset_session_state():
    for key in state_dict:
        if key != 'openai_api_key':
            st.session_state[key] = state_dict[key]

map_code_suffix = """
    
output_df = input_df[template_df.columns]
"""

st.set_page_config(page_title="DataFormatter Demo", page_icon=":robot_face:", layout="wide")

# initialize session state
init_session_state(state_dict)
st.header("DataFormatter Demo")

# Setup sidebar
st.sidebar.text_input("OpenAI API Key", type="password", key="openai_api_key")
template_file = st.sidebar.file_uploader("Choose a template file", on_change=reset_session_state)
input_file = st.sidebar.file_uploader("Choose a input file", on_change=reset_session_state)

st.sidebar.button("Reformat", on_click=lambda: st.session_state.update({'reformat': True}))

# Main page
# Show template and input files
col1, col2 = st.columns(2)
if template_file is not None:
    # Load template dataframe and display
    template_df = pd.read_csv(template_file)
    col1.subheader("Template Table")
    col1.write(template_df)
if input_file is not None:
    # Load input dataframe and display
    input_df = pd.read_csv(input_file)
    col2.subheader("Input Table")
    col2.write(input_df)

if st.session_state['reformat']:
    # Analyze the input columns and fine the mapping to the template columns
    llm = load_llm(st.session_state['openai_api_key'])
    table_formatter = OpenAIFormatter(template_df, llm)
    col_name_map = table_formatter.get_column_map(input_df)

    with st.container():
        # Show the column mapping result and let the user choose if there are multiple options
        st.subheader(f"Mapping Columns from {input_file.name} to columns in {template_file.name}")
        selected_value = show_column_map(template_df, input_df, col_name_map)

        def generate_map_button_callback():
            st.session_state['gen_code'] = True
        st.button("Generate map code", on_click=generate_map_button_callback)

    # Generate the map code for each column
    if st.session_state['gen_code']:
        if not st.session_state['gen_code_done']:
            search_existing_map_code(table_formatter, template_file.name, input_file.name)

        if not st.session_state['gen_code_done']:
            update_map = {}
            template_cols = template_df.columns.values.tolist()
            for idx, col in enumerate(template_cols):
                update_map[col] = selected_value[idx]
            my_bar = st.progress(0, text="Generating code...")
            map_code_string = ""
            total_steps = len(update_map)
            idx = 0
            for key, value in update_map.items():
                map_code_string += table_formatter.generate_map_functions(input_df, key, value)
                idx += 1
                my_bar.progress(idx / total_steps, text="Generating code...")
            st.session_state['gen_code_done'] = True
            st.session_state['code_string'] = map_code_string

        map_code_string = st.session_state['code_string']
        content = st_ace(map_code_string, language="python", auto_update=True)

        def run_code_button_callback():
            st.session_state['run_code'] = True
        st.button("Run code", on_click=run_code_button_callback)
    if st.session_state['run_code']:
        # Run
        exec(content+map_code_suffix)
        file_name = f"saved/{input_file.name.split('.')[0]}-{template_file.name.split('.')[0]}.txt"
        save_file(content, file_name)
        save_file(f"File name for mapping {input_file.name} to {template_file.name}: {file_name}\n",
                  "saved/index.txt",
                  "a")
        st.subheader("Processed Table")
        st.write(output_df)
        csv = convert_df(output_df)
        st.download_button(
            label="Download processed table as CSV",
            data=csv,
            file_name='output_df.csv',
            mime='text/csv',
        )

