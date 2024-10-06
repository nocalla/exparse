import re
from pathlib import Path


def regex_substitution(text: str, substitutions: list[tuple]) -> str:
    # Apply all match subtitutions to the text
    for regex, replacement in substitutions:
        text = re.sub(regex, replacement, text, flags=re.MULTILINE)
    return text


def test_current_data(text: str, error_flag: bool = False) -> None:
    """
    Debugging function to test the current state of a string being worked on
    by writing it to a text file.

    :param data: the string to be written to the file
    :type data: str
    :param error_flag: whether or not to raise an error on calling the function
    :type error_flag: bool
    :raises NotImplementedError: Error to bring the run to a halt.
    """
    test_path = Path("output", "test.txt")
    with open(test_path, "w") as f:
        f.write(text)
    if error_flag:
        raise NotImplementedError
