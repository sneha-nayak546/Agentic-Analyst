with open('evaluate_nlp.py', 'r') as f:
    lines = f.readlines()

for i in range(len(lines)):
    line = lines[i]
    if line.strip() == "else:":
        # The next two lines need to be indented exactly 4 spaces more than the 'else:'
        indent = len(line) - len(line.lstrip())
        next_line_indent = len(lines[i+1]) - len(lines[i+1].lstrip())
        if next_line_indent <= indent:
            lines[i+1] = " " * (indent + 4) + lines[i+1].lstrip()
            lines[i+2] = " " * (indent + 4) + lines[i+2].lstrip()

with open('evaluate_nlp.py', 'w') as f:
    f.writelines(lines)
