import ast
import logging
import pandas as pd
from typing import Any, Dict, List, Optional, Union

from langchain.tools.python.tool import PythonAstREPLTool
from langchain import OpenAI
from langchain.prompts.prompt import PromptTemplate
from langchain.agents import load_tools, initialize_agent
from langchain.agents import AgentType
from langchain.memory import ConversationBufferWindowMemory
from langchain.base_language import BaseLanguageModel

_logger = logging.getLogger(__name__)


class OpenAIFormatter:
    COLUMN_MAP_DETECTOR_PROMPT = """
  Analyze the columns of template_df, and for each column in template_df, find the possible matching column from input_df based on the dataframe info provided below. Return a dictionary. Key is the column name from template_df and value is the column name in input_df. Only if there are ambiguous columns, list all of them as values.

This is the result of `print(template_df.head())`:
{template_df}

This is the result of `print(input_df.head())`:
{input_df}

Start Answer.
  """

    MAP_FUNCTIONG_GENERATOR_PROMPT = """
Check the column types and format of template_df.
Generate the Python code to generate a new column in input_df by mapping the column {input_col} in input_df. The result column name and data type needs to match the name and data type of column template_df[`{template_col}`].

This is the result of `print(template_df.head())`:
{template_df}

This is the result of `print(template_df.dtypes)`:
{template_df_type}

This is the result of `print(input_df.head())`:
{input_df}

Give the solution that comment as a prompt to Codex, it will generate the code for you like this:
```Python
Your answer
```

"""
    MAP_SEARCH_PROMPT = """
    Based on the following data:
    ```
    {database}
    ```
    Try to find the file name for mapping {input_df_name} to {template_df_name}. If you find it, return the file name. 
    if you cannot find it just return `none`.
"""

    def __init__(self, template: Union[pd.DataFrame, str], llm: Optional[BaseLanguageModel] = None, interactive: bool = False):
        self.template = template
        if isinstance(template, str):
            self.template_df = pd.read_csv(template)
        else:
            self.template_df = template
        self.interactive = interactive

        self.llm = llm if llm else OpenAI(temperature=0.1)

    def get_column_map(self, input_df):
        """
        Generate the column maps for the input dataframe based on the template dataframe.
        :param input_df: input dataframe to format
        """
        col_map_prompt_template = PromptTemplate(input_variables=["template_df", "input_df"], template=self.COLUMN_MAP_DETECTOR_PROMPT)
        map_prompt = col_map_prompt_template.format(
            template_df=str(self.template_df.head().to_markdown()),
            input_df=str(input_df.head().to_markdown())
        )

        col_name_map_text = self.llm(map_prompt)
        col_name_map = ast.literal_eval(col_name_map_text)
        return col_name_map

    def check_column_map(self, key, value):
        """
        Check the column map to make sure that it each column only have one candidates
        """
        if type(value) == list:
            _logger.warning(f"There are ambiguous columns ({value}) that can map to column {key} in the template.")
            if self.interactive:
                chosen_value = input(f"Please choose one from {value}: ")
                if not chosen_value in value:
                    raise NameError(f"The name you choose {chosen_value} is not in the list {value}")
                new_value = chosen_value
            else:
                _logger.warning(f"Choosing ({value[0]}) by default for {key} in the template.")
                new_value = value[0]
        else:
            new_value = value
        return new_value

    def search_for_existing_map(self, template_name: str, input_name: str, database: str) -> str:
        """
        Search for the existing column map in the database.
        """
        search_prompt_template = PromptTemplate(input_variables=["database", "input_df_name", "template_df_name"],
                                                template=self.MAP_SEARCH_PROMPT)
        map_prompt = search_prompt_template.format(
            database=database,
            template_df_name=str(template_name),
            input_df_name=str(input_name),
        )
        map_file_name = self.llm(map_prompt)
        return map_file_name

    def generate_map_functions(self, input_df: pd.DataFrame, template_col: str, input_col: str) -> str:
        """
        Generate the code to map the columns based on the format of the template dataframe.
        """
        map_fun_prompt_template = PromptTemplate(
            input_variables=["input_col", "template_col", "template_df", "template_df_type", "input_df"],
            template=self.MAP_FUNCTIONG_GENERATOR_PROMPT)
        map_fun_partial_prompt = map_fun_prompt_template.partial(
            template_df=str(self.template_df.head().to_markdown()),
            template_df_type=str(self.template_df.dtypes.to_markdown()),
            input_df=str(input_df.head().to_markdown())
        )
        input_df = input_df.copy()

        tools = [PythonAstREPLTool(
            locals={"template_df": self.template_df, "input_df": input_df}),
        ]

        memory = ConversationBufferWindowMemory( k=5, return_messages=True)

        agent_chain = initialize_agent(
            tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=False,
            memory=memory,
        )

        value = self.check_column_map(template_col, input_col)
        map_prompt = map_fun_partial_prompt.format(input_col=input_col, template_col=template_col)
        code = agent_chain.run(map_prompt)
        map_func_string = code + "\n"

        return map_func_string
