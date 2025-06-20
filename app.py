import gradio as gr
from agents.orchestrator_agent import OrchestratorAgent

agent = OrchestratorAgent()

def handle_input(user_input):
    return agent.route_task(user_input)

iface = gr.Interface(fn=handle_input,
                     inputs=gr.Textbox(label="Empirion Command Center"),
                     outputs="text",
                     title="Empirion AI Orchestrator",
                     description="Type a command and Empirion will delegate it intelligently.")
iface.launch()
