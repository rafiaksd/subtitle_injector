import os

folder_path = "summaries_direct/"  # ← Replace with your actual path

for root, dirs, files in os.walk(folder_path):
    for file in files:
        if "word" in file:
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
