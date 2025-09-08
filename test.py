def read_text_file(filepath):
    if not filepath.endswith(('.txt', '.srt')):
        raise ValueError("Only .txt or .srt files are supported.")

    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def srt_to_lines(srt_text):
    lines = []
    for line in srt_text.splitlines():
        line = line.strip()
        # Skip empty lines, timestamps, and numeric indices
        if not line or line.isdigit() or "-->" in line:
            continue
        lines.append(line)
    return lines

sub_text = read_text_file("sharaf_SUB_sentenced.srt")
for line in srt_to_lines(sub_text):
    print(line)