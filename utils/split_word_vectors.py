def split_file_into_four(original_file):
    # Determine the number of lines per file
    with open(original_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    total_lines = len(lines)
    lines_per_file = total_lines // 4
    
    # Split lines into four chunks
    for i in range(4):
        with open(f'word_vectors{i+1}.txt', 'w', encoding='utf-8') as file:
            # Calculate start and end index for slicing
            start_index = i * lines_per_file
            # For the last file, include any remaining lines due to integer division
            end_index = (i + 1) * lines_per_file if i != 3 else total_lines
            file.writelines(lines[start_index:end_index])

# Call the function
split_file_into_four('./word_vectors.txt')
