import random
import sys

def load_and_shuffle_questions(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split the content into questions. Assuming each question ends with a newline character.
    questions = content.strip().split('\n\n')
    
    # Shuffle the questions to randomize their order
    random.shuffle(questions)
    
    return questions

def select_questions(questions, count=15):
    # Ensure we only select up to the number of questions available, with a maximum of 15
    return questions[:min(len(questions), count)]

def renumber_questions(questions, start_number=1):
    renumbered_questions = []
    for i, question in enumerate(questions, start=start_number):
        # Skip renumbering for the separator
        if "THIS IS THE SEPARATOR" in question:
            renumbered_questions.append(question)
        else:
            # Replace the original number with the new one
            period_index = question.find('.')
            if period_index != -1:
                new_question = f"{i}. " + question[period_index+2:]
                renumbered_questions.append(new_question)
    return renumbered_questions

def main(file1, file2):
    # Load and shuffle questions from both files
    questions_bank_1 = load_and_shuffle_questions(file1)
    questions_bank_2 = load_and_shuffle_questions(file2)
    
    # Select 15 questions from each bank
    selected_questions_1 = select_questions(questions_bank_1)
    selected_questions_2 = select_questions(questions_bank_2)
    
    # Insert the separator between the questions from the two banks
    separator = "0. THIS IS THE SEPARATOR"
    combined_questions = selected_questions_1 + [separator] + selected_questions_2
    
    # Renumber the combined questions list, excluding the separator from renumbering
    final_questions = renumber_questions(combined_questions)
    
    # Save the selected questions and separator to a new file
    with open('shuffledquestions.txt', 'w', encoding='utf-8') as output_file:
        for question in final_questions:
            output_file.write(question + '\n\n')

    print("Shuffled questions have been saved to shuffledquestions.txt")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <path_to_test_bank_1> <path_to_test_bank_2>")
        sys.exit(1)
    
    file_path_1 = sys.argv[1]
    file_path_2 = sys.argv[2]
    
    main(file_path_1, file_path_2)
