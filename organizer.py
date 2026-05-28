from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

import os
import shutil
import anthropic

client = anthropic.Anthropic()

#define tools for file organization
tools = [
    {
        "name": "list_files",
        "description": "List all files in a directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Path to the directory"}
            },
            "required": ["directory"]
        }
    },
    {
        "name": "move_file",
        "description": "Move a file to a destination folder. Creates the folder if it doesn't exist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Full path to the source file"},
                "dest_folder": {"type": "string", "description": "Full path to the destination folder"}
            },
            "required": ["src", "dest_folder"]
        }
    },
    {
        "name": "get_file_metadata",
        "description": "Get the extension, size, and modified date of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Full path to the file"}
            },
            "required": ["filepath"]
        }
    }
]

#function to list files in a directory
def list_files(directory):
    if not os.path.exists(directory):
        return f"Directory {directory} does not exist."
    
    files = []
    for f in os.listdir(directory):
        full_path = os.path.join(directory, f)
        if os.path.isfile(full_path):
            files.append(full_path)

    return files if files else f"No files found."

#function to move a file to a destination folder, creating the folder if it doesn't exist
def move_file(src, dst_folder):
    if not os.path.exists(src):
        return f"File {src} does not exist."
    
    os.makedirs(dst_folder, exist_ok=True)
    dst_path = os.path.join(dst_folder, os.path.basename(src))

    #avoid overwriting existing files by appending _duplicate to the filename
    if os.path.exists(dst_path):
        base, ext = os.path.splitext(os.path.basename(src))
        dst_path = os.path.join(dst_folder, f"{base}_duplicate{ext}")

    shutil.move(src, dst_path)
    return f"Moved {src} to {dst_folder}"

#function to get file metadata
def get_file_metadata(filepath):
    if not os.path.exists(filepath):
        return f"Error: File '{filepath}' does not exist."
    
    stat = os.stat(filepath)
    _, ext = os.path.splitext(filepath)

    return {
        "extension": ext.lower() if ext else "no_extension",
        "size_kb": round(stat.st_size / 1024, 2),
        "last_modified": os.path.getmtime(filepath)
    }

#tool router
def handle_tools(content_blocks, log_callback=None):
    results = []
    
    for block in content_blocks:
        if block.type != "tool_use":
            continue

        name = block.name
        inputs = block.input

        if log_callback:
            log_callback(f"{name}: {inputs}")

        if name == "list_files":
            result = list_files(inputs["directory"])
        elif name == "move_file":
            result = move_file(inputs["src"], inputs["dest_folder"])
        elif name == "get_file_metadata":
            result = get_file_metadata(inputs["filepath"])
        else:
            result = f"Unknown tool: {name}"

        results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": str(result)
        })
    return results

def run_batch(target_folder, files, log_callback=None):
    file_list = "\n".join([os.path.join(target_folder, f) for f in files])

    existing_folders = {}
    for f in os.listdir(target_folder):
        full_path = os.path.join(target_folder, f)
        if os.path.isdir(full_path):
            contents = os.listdir(full_path)[:10]
            existing_folders[f] = contents

    folder_str = "" 
    if existing_folders:
        for folder_name, contents in existing_folders.items():
            sample = ", ".join(contents) if contents else "empty"
            folder_str += f" - {folder_name}/ (contains: {sample})\n"
    else:
        folder_str = "None\n"

    messages = [
        {
            "role": "user",
            "content": (
                f"Please organize these files into subfolders inside {target_folder}:\n"
                f"{file_list}\n\n"
                f"Existing subfolders and a sample of their contents:\n{folder_str}\n"
                "1. Use existing folders when the file clearly belongs there based on name or type\n"
                "2. Only create a new subfolder if no existing one is a good match\n"
                "3. Check metadata if you need to identify file types\n"
                "4. When done, give me a brief summary of what you moved and where."
            )
        }
    ]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system="You are a file organizer. Be concise. Do not use markdown formatting in your summary. Just plain text.",
            tools=tools,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "Batch complete"
        
        if response.stop_reason == "tool_use":
            tool_results = handle_tools(response.content, log_callback)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            return f"Unexpected stop reason: {response.stop_reason}"

def run_organizer(target_folder, log_callback=None):
    if not os.path.exists(target_folder):
        return "Folder does not exist"
    
    files = [f for f in os.listdir(target_folder) if os.path.isfile(os.path.join(target_folder, f))]

    if not files:
        return "No files to organize in the selected folder"
    
    chunk_size = 50
    chunks = [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]

    if log_callback and len(chunks) > 1:
        log_callback(f"Large folder detected - processing in {len(chunks)} batches of {chunk_size} files")

    all_summaries = []

    for i, chunk in enumerate(chunks):
        if log_callback and len(chunks) > 1:
            log_callback(f"Processing batch {i + 1} of {len(chunks)}")

        summary = run_batch(target_folder, chunk, log_callback)
        all_summaries.append(summary)

    return "\n\n".join(all_summaries)

#entry point
if __name__ == "__main__":
    folder = input("Enter the folder path to organize: ").strip()
    run_organizer(folder)