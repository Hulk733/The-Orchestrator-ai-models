
import os
import shutil
from typing import List, Dict, Any
from pathlib import Path
import mimetypes
import json
from datetime import datetime

class FileManager:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        self.supported_types = {
            'text': ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
            'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv'],
            'archive': ['.zip', '.rar', '.tar', '.gz', '.7z']
        }
    
    def upload_file(self, file_path: str, filename: str = None) -> Dict[str, Any]:
        """Upload and process a file"""
        try:
            if not os.path.exists(file_path):
                return {"success": False, "error": "File not found"}
            
            if filename is None:
                filename = os.path.basename(file_path)
            
            # Create unique filename to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(filename)
            unique_filename = f"{name}_{timestamp}{ext}"
            
            destination = self.upload_dir / unique_filename
            shutil.copy2(file_path, destination)
            
            file_info = self.get_file_info(destination)
            
            return {
                "success": True,
                "filename": unique_filename,
                "path": str(destination),
                "info": file_info
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get detailed file information"""
        stat = file_path.stat()
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        return {
            "name": file_path.name,
            "size": stat.st_size,
            "size_human": self.format_file_size(stat.st_size),
            "type": self.get_file_category(file_path.suffix),
            "mime_type": mime_type,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "extension": file_path.suffix
        }
    
    def get_file_category(self, extension: str) -> str:
        """Determine file category based on extension"""
        extension = extension.lower()
        for category, extensions in self.supported_types.items():
            if extension in extensions:
                return category
        return "other"
    
    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def list_files(self) -> List[Dict[str, Any]]:
        """List all uploaded files"""
        files = []
        for file_path in self.upload_dir.iterdir():
            if file_path.is_file():
                files.append(self.get_file_info(file_path))
        return sorted(files, key=lambda x: x['modified'], reverse=True)
    
    def delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            file_path = self.upload_dir / filename
            if file_path.exists():
                file_path.unlink()
                return {"success": True, "message": f"File {filename} deleted"}
            else:
                return {"success": False, "error": "File not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def read_text_file(self, filename: str) -> Dict[str, Any]:
        """Read content of a text file"""
        try:
            file_path = self.upload_dir / filename
            if not file_path.exists():
                return {"success": False, "error": "File not found"}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
