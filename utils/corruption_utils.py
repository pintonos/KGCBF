import random
import numpy as np


def get_invalid_characters():
    return "<>{}|\\^`\""

def insert_str(string, str_to_insert, index):
    if index == -1:
        return string + str_to_insert
    return string[:index] + str_to_insert + string[index:]


def get_random_special_characters(length=1):
    special_chars = ["$", "&", "%", "*", "§", "Ä", "Ö", "Ü", ";"]
    random_char_list = random.sample(special_chars, length)
    return "".join(random_char_list)


def get_random_characters(length=1):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    random_char_list = random.sample(chars, length)
    return "".join(random_char_list)


def random_replace_character(serialized_rdf, char, prob=0.5):
    char_pos = [pos for pos, c in enumerate(str(serialized_rdf)) if c == char]
    str_arr = np.array(list(str(serialized_rdf)))
    amount = int(len(char_pos) * prob)
    str_arr[random.sample(char_pos, amount)] = 'ERROR'
    serialized_rdf = str("".join(str_arr))
    return serialized_rdf