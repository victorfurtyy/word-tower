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
        return "com_acento.txt"  # Modo caótico usa dicionário normal
    else:
        return "sem_acento.txt"  # Default to easy

def load_dictionary(difficulty: str) -> set[str]:
    """
    Loads the dictionary file based on difficulty into a set for fast lookups.
    """
    dict_file = get_dict_file(difficulty)
    dict_path = DICT_PATH / dict_file
    
    print(f"Loading {difficulty} dictionary from: {dict_path}")
    try:
        with dict_path.open(encoding="utf-8") as f:
            return {line.strip().lower() for line in f if line.strip()}
    except FileNotFoundError:
        print(f"ERROR: Dictionary file {dict_file} not found.")
        return set()

# Store dictionaries for all difficulties
DICTIONARIES = {
    "normal": load_dictionary("normal"),
    "easy": load_dictionary("easy"),
    "caotic": load_dictionary("normal")  # Usa o mesmo que normal
}

print(f"Normal dictionary: {len(DICTIONARIES['normal'])} words loaded")
print(f"Easy dictionary: {len(DICTIONARIES['easy'])} words loaded")
print(f"Caotic dictionary: {len(DICTIONARIES['caotic'])} words loaded")
print("Ready to play!")

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
    dict_to_use = DICTIONARIES.get(difficulty.lower(), DICTIONARIES["easy"])
    if not dict_to_use:
        return "casa"  # Fallback word
    
    return random.choice(list(dict_to_use))

def get_random_letter_from_word(word: str) -> str:
    """
    Returns a random letter from the word, excluding accented letters like â, ô, ç, etc.
    Used for caotic mode. Keeps trying until it finds a valid letter.
    """
    # Letras válidas (sem acentos)
    valid_letters = "abcdefghijklmnopqrstuvwxyz"
    
    # Filtra apenas letras válidas da palavra
    valid_chars = [char for char in word.lower() if char in valid_letters]
    
    # Se não houver letras válidas na palavra, tenta outras palavras
    if not valid_chars:
        # Usa uma palavra aleatória do dicionário até encontrar uma com letras válidas
        attempts = 0
        max_attempts = 100  # Evita loop infinito
        
        while attempts < max_attempts:
            random_word = get_random_word("normal")
            valid_chars = [char for char in random_word.lower() if char in valid_letters]
            
            if valid_chars:
                return random.choice(valid_chars)
            
            attempts += 1
        
        # Fallback final se ainda não encontrou
        return "a"
    
    return random.choice(valid_chars)