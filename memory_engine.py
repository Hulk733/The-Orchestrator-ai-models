import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

MEMORY_DIR = "memory"

class MemoryEngine:
    def __init__(self, base_dir: str = MEMORY_DIR):
        self.base_dir = base_dir
        self.websocket_callbacks = []
        
    def add_websocket_callback(self, callback):
        """Add WebSocket callback for memory updates"""
        self.websocket_callbacks.append(callback)
    
    def notify_websocket_clients(self, event_type: str, data: Dict):
        """Notify WebSocket clients of memory events"""
        for callback in self.websocket_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                print(f"Memory WebSocket callback error: {e}")

def store_context(agent: str, data: Any, context: Optional[Dict] = None) -> List[Dict]:
    """Store context with enhanced metadata and WebSocket support"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    file_path = f"{MEMORY_DIR}/{agent}.json"
    
    memory_log = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                memory_log = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Corrupted memory file for agent {agent}, starting fresh")
            memory_log = []
    
    # Create enhanced memory entry
    memory_entry = {
        "id": f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "timestamp": datetime.now().isoformat(),
        "input": data,
        "context": context or {},
        "agent": agent,
        "type": "task_input"
    }
    
    memory_log.append(memory_entry)
    
    # Limit memory size (keep last 1000 entries)
    if len(memory_log) > 1000:
        memory_log = memory_log[-1000:]
    
    try:
        with open(file_path, "w") as f:
            json.dump(memory_log, f, indent=2)
    except Exception as e:
        print(f"Error saving memory for agent {agent}: {e}")
    
    return memory_log

def recall_context(agent: str, limit: Optional[int] = None, filter_type: Optional[str] = None) -> List[Dict]:
    """Recall context with filtering and limiting options"""
    file_path = f"{MEMORY_DIR}/{agent}.json"
    
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, "r") as f:
            memory_log = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Corrupted memory file for agent {agent}")
        return []
    except Exception as e:
        print(f"Error reading memory for agent {agent}: {e}")
        return []
    
    # Apply type filter if specified
    if filter_type:
        memory_log = [entry for entry in memory_log if entry.get("type") == filter_type]
    
    # Apply limit if specified
    if limit:
        memory_log = memory_log[-limit:]
    
    return memory_log

def store_task_result(agent: str, task_id: str, result: Any, metadata: Optional[Dict] = None) -> bool:
    """Store task result in memory"""
    os.makedirs(MEMORY_DIR, exist_ok=True)
    file_path = f"{MEMORY_DIR}/{agent}.json"
    
    memory_log = []
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                memory_log = json.load(f)
        except json.JSONDecodeError:
            memory_log = []
    
    # Create result entry
    result_entry = {
        "id": f"result_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "result": result,
        "metadata": metadata or {},
        "agent": agent,
        "type": "task_result"
    }
    
    memory_log.append(result_entry)
    
    # Limit memory size
    if len(memory_log) > 1000:
        memory_log = memory_log[-1000:]
    
    try:
        with open(file_path, "w") as f:
            json.dump(memory_log, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving task result for agent {agent}: {e}")
        return False

def get_memory_stats(agent: Optional[str] = None) -> Dict:
    """Get memory statistics for agent(s)"""
    if agent:
        # Stats for specific agent
        memory = recall_context(agent)
        return {
            "agent": agent,
            "total_entries": len(memory),
            "task_inputs": len([m for m in memory if m.get("type") == "task_input"]),
            "task_results": len([m for m in memory if m.get("type") == "task_result"]),
            "oldest_entry": memory[0].get("timestamp") if memory else None,
            "newest_entry": memory[-1].get("timestamp") if memory else None
        }
    else:
        # Stats for all agents
        stats = {}
        if os.path.exists(MEMORY_DIR):
            for filename in os.listdir(MEMORY_DIR):
                if filename.endswith('.json'):
                    agent_name = filename[:-5]  # Remove .json extension
                    stats[agent_name] = get_memory_stats(agent_name)
        return stats

def search_memory(agent: str, query: str, limit: int = 10) -> List[Dict]:
    """Search memory entries for specific content"""
    memory = recall_context(agent)
    query_lower = query.lower()
    
    matching_entries = []
    for entry in memory:
        # Search in input data
        input_str = str(entry.get("input", "")).lower()
        result_str = str(entry.get("result", "")).lower()
        
        if query_lower in input_str or query_lower in result_str:
            matching_entries.append(entry)
    
    return matching_entries[-limit:] if limit else matching_entries

def clear_memory(agent: str, confirm: bool = False) -> bool:
    """Clear memory for specific agent"""
    if not confirm:
        return False
    
    file_path = f"{MEMORY_DIR}/{agent}.json"
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        return True
    except Exception as e:
        print(f"Error clearing memory for agent {agent}: {e}")
        return False

def export_memory(agent: str, format: str = "json") -> Optional[str]:
    """Export memory in specified format"""
    memory = recall_context(agent)
    
    if format.lower() == "json":
        return json.dumps(memory, indent=2)
    elif format.lower() == "csv":
        # Simple CSV export
        import csv
        import io
        
        output = io.StringIO()
        if memory:
            fieldnames = ["timestamp", "type", "input", "result", "agent"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in memory:
                row = {
                    "timestamp": entry.get("timestamp", ""),
                    "type": entry.get("type", ""),
                    "input": str(entry.get("input", "")),
                    "result": str(entry.get("result", "")),
                    "agent": entry.get("agent", "")
                }
                writer.writerow(row)
        
        return output.getvalue()
    
    return None

# Backward compatibility functions
def store_context_simple(agent: str, data: Any) -> List[Dict]:
    """Simple context storage for backward compatibility"""
    return store_context(agent, data)

def recall_context_simple(agent: str) -> List[Dict]:
    """Simple context recall for backward compatibility"""
    return recall_context(agent)
