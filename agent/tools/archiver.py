import os
import shutil
import zipfile
from pathlib import Path

def create_zip_archive(file_paths: list[str], output_filename: str = "documents.zip") -> str:
    if not file_paths:
        raise ValueError("Cannot create a zip archive from an empty file list.")

    output_path = Path(output_filename)
    
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for file in file_paths:
            path_obj = Path(file)
            if path_obj.exists():
                zipf.write(path_obj, arcname=path_obj.name)

    return str(output_path.resolve())

def cleanup_temp_files(folder_path: str = "./temp_downloads") -> None:
    shutil.rmtree(folder_path, ignore_errors=True)