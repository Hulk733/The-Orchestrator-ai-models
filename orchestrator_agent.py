from core.memory_engine import recall_context, store_context
from core.debug_engine import auto_fix
import json

class OrchestratorAgent:
    def __init__(self):
        self.memory = {}
        with open("datasetmanifest.json", "r") as f:
            self.dataset_manifest = json.load(f)

    def route_task(self, input_text):
        if "UI" in input_text or "design" in input_text:
            agent = "blueprint"
        elif "build" in input_text or "code" in input_text:
            agent = "builder"
        elif "APK" in input_text or "deploy" in input_text:
            agent = "integrator"
        elif "document" in input_text:
            agent = "scribe"
        else:
            agent = "featuresmith"

        self.memory[agent] = store_context(agent, input_text)
        result = self.delegate(agent, input_text)
        return auto_fix(result)

    def delegate(self, agent, task):
        print(f"[Orchestrator] Delegating to: {agent}")
        return f"{agent} working on: {task}"
