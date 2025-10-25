####################################################################################################
# Display each student chat in a separated files
# Each student have a separated file for display his chat history with Edulga Agent

import os
import threading
from uuid import UUID
from pathlib import Path
from APP.Fake_Database import students

_write_lock = threading.Lock()

def Chat_Display_in_Markdown_file(id: UUID, index: int, Student_Query: str,
                                  Agent_Response: str, type: int, requests: int):

    # === Always anchor to the real project root ===
    # Go up until we reach the main project folder (adjust levels if needed)
    project_root = Path(__file__).resolve().parents[1]  # e.g., /home/user/MyProject/APP/ -> go up one level
    chat_dir = project_root / "Chat_Histories"

    # === Ensure directory exists ===
    chat_dir.mkdir(parents=True, exist_ok=True)

    # === File name and path ===
    student_name = students[index].name.replace(" ", "_")
    file_path = chat_dir / f"{student_name}_Chat_{id}.md"

    with _write_lock:
        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# Chat Log for {students[index].name}\n")
                f.write(f"**Student ID:** {id}\n\n")
                f.write("\n\n# ==================================================\n\n")
                f.flush()
                os.fsync(f.fileno())

        with open(file_path, "a", encoding="utf-8") as f:
            role = {1: "Architect", 2: "Sage", 3: "Maestro"}.get(type, "Agent")
            f.write(f"\tRequest Number: {requests}\n\n")
            f.write(f"\tStudent Query:\n\t{Student_Query}\n\n")
            f.write(f"\n{Agent_Response}\n")
            f.write("\n\n# ==================================================\n\n")
            f.flush()
            os.fsync(f.fileno())

    print(f"Chat written to: {file_path}")

####################################################################################################