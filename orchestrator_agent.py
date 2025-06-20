from memory_engine import recall_context, store_context
from debug_engine import auto_fix
import json
import re
from datetime import datetime
from typing import Dict, List, Optional

class OrchestratorAgent:
    def __init__(self):
        self.memory = {}
        self.task_history = []
        self.websocket_callbacks = []
        
        with open("datasetmanifest.json", "r") as f:
            self.dataset_manifest = json.load(f)
        
        # Load dataset configurations
        self.agent_datasets = {}
        self.load_agent_datasets()
        
        # Enhanced routing patterns
        self.routing_patterns = {
            "blueprint": ["ui", "design", "interface", "layout", "frontend", "visual"],
            "builder": ["build", "code", "develop", "implement", "create", "generate"],
            "integrator": ["deploy", "apk", "release", "publish", "integrate", "ci/cd"],
            "scribe": ["document", "write", "explain", "guide", "manual", "docs"],
            "featuresmith": ["feature", "functionality", "capability", "enhancement"],
            "vault": ["security", "auth", "encrypt", "protect", "secure", "vulnerability"],
            "juris": ["legal", "compliance", "privacy", "terms", "policy", "gdpr"],
            "sentinel": ["threat", "risk", "attack", "monitor", "detect", "analyze"],
            "guardian": ["ethics", "bias", "fairness", "responsible", "ai ethics"],
            "gemini": ["architecture", "pattern", "design pattern", "system design"],
            "scraper": ["scrape", "extract", "data", "web", "crawl", "collect"],
            "scheduler": ["schedule", "time", "calendar", "plan", "organize", "timeline"],
            "voicebox": ["voice", "speech", "audio", "speak", "listen", "command"]
        }

    def load_agent_datasets(self):
        """Load dataset configurations for all agents"""
        for agent, dataset_files in self.dataset_manifest.items():
            self.agent_datasets[agent] = {}
            for dataset_file in dataset_files:
                try:
                    with open(dataset_file.replace("datasets/", ""), "r") as f:
                        self.agent_datasets[agent] = json.load(f)
                except FileNotFoundError:
                    print(f"Warning: Dataset file {dataset_file} not found for agent {agent}")
                except json.JSONDecodeError:
                    print(f"Warning: Invalid JSON in dataset file {dataset_file} for agent {agent}")

    def add_websocket_callback(self, callback):
        """Add WebSocket callback for real-time updates"""
        self.websocket_callbacks.append(callback)

    def notify_websocket_clients(self, event_type: str, data: Dict):
        """Notify WebSocket clients of events"""
        for callback in self.websocket_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                print(f"WebSocket callback error: {e}")

    def analyze_intent(self, input_text: str) -> Dict:
        """Analyze user intent using enhanced pattern matching"""
        input_lower = input_text.lower()
        scores = {}
        
        for agent, patterns in self.routing_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern in input_lower:
                    score += 1
                # Boost score for exact matches
                if re.search(r'\b' + re.escape(pattern) + r'\b', input_lower):
                    score += 2
            scores[agent] = score
        
        # Find the agent with highest score
        best_agent = max(scores, key=scores.get) if max(scores.values()) > 0 else "featuresmith"
        confidence = scores[best_agent] / len(self.routing_patterns[best_agent])
        
        return {
            "agent": best_agent,
            "confidence": min(confidence, 1.0),
            "scores": scores,
            "fallback": confidence < 0.3
        }

    def route_task(self, input_text: str, context: Optional[Dict] = None) -> Dict:
        """Enhanced task routing with context and metadata"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Analyze intent
        intent_analysis = self.analyze_intent(input_text)
        agent = intent_analysis["agent"]
        
        # Store context and task history
        task_record = {
            "task_id": task_id,
            "input": input_text,
            "agent": agent,
            "timestamp": datetime.now().isoformat(),
            "context": context or {},
            "intent_analysis": intent_analysis
        }
        
        self.task_history.append(task_record)
        self.memory[agent] = store_context(agent, input_text)
        
        # Get agent capabilities and dataset info
        agent_info = self.get_agent_info(agent)
        
        # Delegate task
        result = self.delegate(agent, input_text, task_record)
        
        # Prepare response
        response = {
            "task_id": task_id,
            "agent": agent,
            "result": auto_fix(result),
            "confidence": intent_analysis["confidence"],
            "agent_info": agent_info,
            "timestamp": datetime.now().isoformat()
        }
        
        # Notify WebSocket clients
        self.notify_websocket_clients("task_completed", response)
        
        return response

    def get_agent_info(self, agent: str) -> Dict:
        """Get comprehensive agent information"""
        agent_data = self.agent_datasets.get(agent, {})
        
        return {
            "name": agent,
            "capabilities": agent_data.get("metadata", {}).get("capabilities", []),
            "tasks": agent_data.get("tasks", []),
            "dataset_version": agent_data.get("metadata", {}).get("version", "unknown"),
            "last_updated": agent_data.get("metadata", {}).get("last_updated", "unknown")
        }

    def delegate(self, agent: str, task: str, task_record: Dict) -> str:
        """Enhanced delegation with task context"""
        print(f"[Orchestrator] Delegating to: {agent} (Task ID: {task_record['task_id']})")
        
        # Get agent-specific data
        agent_data = self.agent_datasets.get(agent, {})
        
        # Simulate agent processing based on available data
        if agent_data:
            capabilities = agent_data.get("metadata", {}).get("capabilities", [])
            available_tasks = agent_data.get("tasks", [])
            
            response = f"[{agent.upper()}] Processing task: {task}\n"
            response += f"Available capabilities: {', '.join(capabilities)}\n"
            
            if available_tasks:
                response += f"Relevant task templates: {len(available_tasks)} available\n"
                # Find most relevant task template
                relevant_task = self.find_relevant_task(task, available_tasks)
                if relevant_task:
                    response += f"Using template: {relevant_task.get('description', 'N/A')}\n"
                    response += f"Estimated time: {relevant_task.get('estimated_time', 'N/A')}\n"
            
            response += f"Task delegated successfully to {agent}"
        else:
            response = f"[{agent.upper()}] Basic processing: {task}"
        
        return response

    def find_relevant_task(self, input_task: str, available_tasks: List[Dict]) -> Optional[Dict]:
        """Find the most relevant task template"""
        input_lower = input_task.lower()
        best_match = None
        best_score = 0
        
        for task in available_tasks:
            description = task.get("description", "").lower()
            task_id = task.get("id", "").lower()
            
            score = 0
            for word in input_lower.split():
                if word in description or word in task_id:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = task
        
        return best_match if best_score > 0 else None

    def get_task_history(self, limit: int = 10) -> List[Dict]:
        """Get recent task history"""
        return self.task_history[-limit:]

    def get_agent_memory(self, agent: str) -> List:
        """Get memory for specific agent"""
        return recall_context(agent)

    def get_system_status(self) -> Dict:
        """Get overall system status"""
        return {
            "total_agents": len(self.dataset_manifest),
            "active_agents": list(self.dataset_manifest.keys()),
            "total_tasks_processed": len(self.task_history),
            "memory_entries": {agent: len(self.memory.get(agent, [])) for agent in self.dataset_manifest.keys()},
            "last_task": self.task_history[-1] if self.task_history else None
        }
