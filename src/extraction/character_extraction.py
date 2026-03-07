def extract_characters(doc):
    characters = []

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            characters.append(ent.text)

    return characters