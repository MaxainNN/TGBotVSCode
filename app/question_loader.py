import json

def open_questions_file(path):
    with open(f'{path}', encoding='utf-8') as questions:
        return json.load(questions)