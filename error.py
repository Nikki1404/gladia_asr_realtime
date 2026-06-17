import re
DIGIT_WORDS = {
    "zero": "0", "oh": "0", "o": "0",
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9"
}

REPEAT_WORDS = {
    "double": 2,
    "triple": 3,
    "quadruple": 4,
    "quintuple": 5
}

NUMBER_WORDS = {
    "zero": 0, "oh": 0, "o": 0,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}

MAGNITUDE_WORDS = {"hundred", "thousand", "lakh", "million"}

NUMERIC_CUE_WORDS = {
    "number", "numbers", "digit", "digits", "code", "otp", "pin", "passcode",
    "id", "account", "reference", "ticket", "invoice", "amount", "mobile",
    "phone", "contact", "serial", "zip", "postcode", "address", "plate",
    "card", "cvv", "expiry", "transaction"
}

NON_NUMERIC_FOLLOW_WORDS = {
    "time", "times", "day", "days", "week", "weeks", "month", "months",
    "year", "years", "person", "people", "thing", "things", "way"
}


def spoken_number_to_int(tokens):
    if not tokens:
        return None

    total = 0
    current = 0
    used = False

    for token in tokens:
        t = token.lower()

        if t == "and":
            continue
        elif t in NUMBER_WORDS:
            current += NUMBER_WORDS[t]
            used = True
        elif t == "hundred":
            if current == 0:
                current = 1
            current *= 100
            used = True
        elif t == "thousand":
            if current == 0:
                current = 1
            total += current * 1000
            current = 0
            used = True
        elif t == "lakh":
            if current == 0:
                current = 1
            total += current * 100000
            current = 0
            used = True
        elif t == "million":
            if current == 0:
                current = 1
            total += current * 1000000
            current = 0
            used = True
        else:
            return None

    return total + current if used else None


def tokenize_text(text):
    return re.findall(r"\d+|[A-Za-z]+|[^\w\s]", text)


def is_word_token(tok):
    return re.fullmatch(r"[A-Za-z]+", tok or "") is not None


def is_numericish_token(tok):
    if tok.isdigit():
        return True
    low = tok.lower()
    return low in DIGIT_WORDS or low in REPEAT_WORDS or low in NUMBER_WORDS or low in MAGNITUDE_WORDS


def has_numeric_context(tokens, start, end):
    left_window = tokens[max(0, start - 4):start]
    right_window = tokens[end:min(len(tokens), end + 4)]
    window = left_window + right_window

    for tok in window:
        low = tok.lower()
        if tok.isdigit():
            return True
        if low in NUMERIC_CUE_WORDS:
            return True
        if low in REPEAT_WORDS:
            return True

    if any(is_numericish_token(tok) for tok in left_window):
        return True
    if any(is_numericish_token(tok) for tok in right_window):
        return True

    return False


def should_convert_number_phrase(tokens, start, end):
    phrase = [t.lower() for t in tokens[start:end] if is_word_token(t)]
    if not phrase:
        return False

    if any(t in REPEAT_WORDS for t in phrase):
        return True

    if end < len(tokens):
        nxt = tokens[end].lower()
        if nxt in NON_NUMERIC_FOLLOW_WORDS and not has_numeric_context(tokens, start, end):
            return False

    if has_numeric_context(tokens, start, end):
        return True

    if len(phrase) >= 2:
        return True

    return False


def normalize_numeric_phrases_context_aware(text):
    if not text:
        return text

    tokens = tokenize_text(text)
    result = []
    i = 0

    while i < len(tokens):
        tok = tokens[i]
        low = tok.lower()

        if low in REPEAT_WORDS and i + 1 < len(tokens):
            if should_convert_number_phrase(tokens, i, min(i + 2, len(tokens))):
                nxt = tokens[i + 1].lower()
                repeat_count = REPEAT_WORDS[low]

                if nxt in DIGIT_WORDS:
                    result.append(DIGIT_WORDS[nxt] * repeat_count)
                    i += 2
                    continue

                if tokens[i + 1].isdigit() and len(tokens[i + 1]) == 1:
                    result.append(tokens[i + 1] * repeat_count)
                    i += 2
                    continue

        if tok.isdigit() and len(tok) == 1:
            digit_seq = [tok]
            j = i + 1

            while j < len(tokens):
                cur = tokens[j].lower()

                if tokens[j].isdigit() and len(tokens[j]) == 1:
                    digit_seq.append(tokens[j])
                    j += 1
                    continue

                if cur in DIGIT_WORDS:
                    digit_seq.append(DIGIT_WORDS[cur])
                    j += 1
                    continue

                if cur in REPEAT_WORDS and j + 1 < len(tokens):
                    nxt = tokens[j + 1].lower()
                    repeat_count = REPEAT_WORDS[cur]

                    if nxt in DIGIT_WORDS:
                        digit_seq.append(DIGIT_WORDS[nxt] * repeat_count)
                        j += 2
                        continue

                    if tokens[j + 1].isdigit() and len(tokens[j + 1]) == 1:
                        digit_seq.append(tokens[j + 1] * repeat_count)
                        j += 2
                        continue

                break

            if len(digit_seq) > 1:
                result.append("".join(digit_seq))
                i = j
                continue

        if low in NUMBER_WORDS or low in MAGNITUDE_WORDS or low == "and":
            j = i
            phrase_tokens = []

            while j < len(tokens):
                t = tokens[j].lower()
                if t in NUMBER_WORDS or t in MAGNITUDE_WORDS or t == "and":
                    phrase_tokens.append(t)
                    j += 1
                else:
                    break

            if should_convert_number_phrase(tokens, i, j):
                value = spoken_number_to_int(phrase_tokens)
                if value is not None:
                    result.append(str(value))
                    i = j
                    continue

        result.append(tok)
        i += 1

    text = " ".join(result)
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"\s*-\s*", " - ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text


if __name__ == "__main__":
    text = "Twenty thirty four"
    print(normalize_numeric_phrases_context_aware(text))
