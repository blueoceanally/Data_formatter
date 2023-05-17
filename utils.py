import os
import pandas as pd
from langchain.llms import OpenAI


def save_file(file_string: str, file_name: str, mode: str = "w") -> None:
    """
    Save the string to a file.
    :param file_string: the string to save
    :param file_name: the name of the file to save to
    :param mode: the mode to open the file in
    """
    with open(file_name, mode) as f:
        f.write(file_string)


def load_file(file_name: str) -> str:
    """
    Load the contents of a file.
    :param file_name: the name of the file to load
    :return: the contents of the file as string
    """
    with open(file_name, "r") as f:
        return f.read()


def load_llm(key: str) -> OpenAI:
    """Logic for loading the chain you want to use should go here."""
    os.environ["OPENAI_API_KEY"] = key
    llm = OpenAI(temperature=0.2)
    os.environ["OPENAI_API_KEY"] = ""

    return llm






