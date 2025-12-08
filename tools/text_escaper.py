def escape(text):
    # escapes characters, if these characters are already escaped, they are used as usual
    # \[privet\]\(www.google.com\) -> [privet](www.google.com)

    return text.translate(str.maketrans({"!": r"\!",
                                            "^": r"\^",
                                            "#": r"\#",
                                            ".": r"\.",
                                            "-": r"\-",
                                            "(": r"\(",
                                            ")": r"\)",
                                            "[": r'\[',
                                            "]": r'\]'})).replace(r'\\', '')
