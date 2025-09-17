import pathlib
import random

DICT_PATH = pathlib.Path(__file__).parent.parent / "assets" / "dicts"

def get_dict_file(difficulty: str) -> str:
    """
    Returns the appropriate dictionary file based on difficulty.
    """
    if difficulty.lower() == "normal":
        return "com_acento.txt"
    elif difficulty.lower() == "easy":
        return "sem_acento.txt"
    elif difficulty.lower() == "caotic":
        return "com_acento.txt"
    else:
        return "sem_acento.txt"

def load_dictionary(difficulty: str) -> set[str]:
    """
    Loads the dictionary file based on difficulty.
    """
    dict_file = get_dict_file(difficulty)
    dict_path = DICT_PATH / dict_file
    try:
        with dict_path.open(encoding="utf-8") as f:
            return {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        print(f"ERROR: Dictionary file {dict_file} not found.")
        return set()

DICTIONARIES = {
    "normal": load_dictionary("normal"),
    "easy": load_dictionary("easy"),
    "caotic": load_dictionary("normal")
}

def verify_word(word: str, difficulty: str = "normal") -> bool:
    """
    Checks if the word exists in the dictionary for the given difficulty.
    """
    dict_to_use = DICTIONARIES.get(difficulty.lower(), DICTIONARIES["easy"])
    return word.lower() in dict_to_use

def get_random_word(difficulty: str = "normal") -> str:
    """
    Returns a random word from the dictionary to start a new game.
    """
    dict_to_use = DICTIONARIES.get(difficulty.lower(), DICTIONARIES["normal"])
    if not dict_to_use:
        return "casa"
    
    return random.choice(list(dict_to_use))

def get_random_letter_from_word(word: str) -> str:
    """
    Returns a random letter from the word, excluding accented letters like â, ô, ç, etc.
    Used for caotic mode.
    """
    valid_letters = "abcdefghijklmnopqrstuvwxyz"
    valid_chars = [char for char in word.lower() if char in valid_letters]
    return random.choice(valid_chars)