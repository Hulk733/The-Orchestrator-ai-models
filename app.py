import gradio as gr
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import json
from orchestrator_agent import OrchestratorAgent
from websocket_server import WebSocketServer

# Initialize Flask app and SocketIO
flask_app = Flask(__name__)
flask_app.config['SECRET_KEY'] = 'empirion_secret_key'
socketio = SocketIO(flask_app, cors_allowed_origins="*")

# Initialize orchestrator
agent = OrchestratorAgent()

# WebSocket server instance
ws_server = None

def handle_input(user_input):
    """Handle Gradio interface input"""
    result = agent.route_task(user_input)
    
    # Format response for Gradio
    if isinstance(result, dict):
        formatted_result = f"Task ID: {result.get('task_id', 'N/A')}\n"
        formatted_result += f"Agent: {result.get('agent', 'N/A')}\n"
        formatted_result += f"Confidence: {result.get('confidence', 0):.2f}\n"
        formatted_result += f"Result: {result.get('result', 'N/A')}"
        return formatted_result
    else:
        return str(result)

def handle_input_with_context(user_input, context_json="{}"):
    """Handle input with additional context"""
    try:
        context = json.loads(context_json) if context_json else {}
    except json.JSONDecodeError:
        context = {}
    
    result = agent.route_task(user_input, context)
    return json.dumps(result, indent=2)

# Flask API endpoints
@flask_app.route('/api/task', methods=['POST'])
def api_task():
    """API endpoint for task processing"""
    try:
        data = request.get_json()
        if not data or 'task' not in data:
            return jsonify({'error': 'Task is required'}), 400
        
        task = data['task']
        context = data.get('context', {})
        
        result = agent.route_task(task, context)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/agents', methods=['GET'])
def api_agents():
    """Get list of available agents"""
    try:
        agents_info = {}
        for agent_name in agent.dataset_manifest.keys():
            agents_info[agent_name] = agent.get_agent_info(agent_name)
        
        return jsonify(agents_info)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/agent/<agent_name>/memory', methods=['GET'])
def api_agent_memory(agent_name):
    """Get memory for specific agent"""
    try:
        memory = agent.get_agent_memory(agent_name)
        return jsonify({'agent': agent_name, 'memory': memory})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/system/status', methods=['GET'])
def api_system_status():
    """Get system status"""
    try:
        status = agent.get_system_status()
        return jsonify(status)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/tasks/history', methods=['GET'])
def api_task_history():
    """Get task history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = agent.get_task_history(limit)
        return jsonify(history)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# SocketIO event handlers
@socketio.on('connect')
def handle_connect():
    """Handle SocketIO client connection"""
    print(f"SocketIO client connected: {request.sid}")
    emit('connection_established', {
        'message': 'Connected to Empirion AI Orchestrator',
        'client_id': request.sid
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle SocketIO client disconnection"""
    print(f"SocketIO client disconnected: {request.sid}")

@socketio.on('task_request')
def handle_socketio_task(data):
    """Handle task request via SocketIO"""
    try:
        task = data.get('task', '')
        context = data.get('context', {})
        
        if not task:
            emit('error', {'message': 'Task is required'})
            return
        
        result = agent.route_task(task, context)
        emit('task_response', result)
        
        # Broadcast to all clients
        socketio.emit('task_completed', {
            'task': task,
            'agent': result.get('agent'),
            'status': 'completed'
        })
    
    except Exception as e:
        emit('error', {'message': str(e)})

@socketio.on('agent_status_request')
def handle_agent_status():
    """Handle agent status request via SocketIO"""
    try:
        agents_info = {}
        for agent_name in agent.dataset_manifest.keys():
            agents_info[agent_name] = agent.get_agent_info(agent_name)
        
        emit('agent_status_response', {'agents': agents_info})
    
    except Exception as e:
        emit('error', {'message': str(e)})

def start_websocket_server():
    """Start the WebSocket server in a separate thread"""
    global ws_server
    ws_server = WebSocketServer(host='0.0.0.0', port=8765)
    ws_server.run()

def start_flask_socketio():
    """Start Flask-SocketIO server"""
    socketio.run(flask_app, host='0.0.0.0', port=5001, debug=False)

# Create Gradio interfaces
with gr.Blocks(title="Empirion AI Orchestrator") as demo:
    gr.Markdown("# 🧠 Empirion AI Orchestrator")
    gr.Markdown("Intelligent task delegation and agent coordination system")
    
    with gr.Tab("Simple Interface"):
        with gr.Row():
            with gr.Column():
                input_text = gr.Textbox(
                    label="Command Input",
                    placeholder="Enter your task or command...",
                    lines=3
                )
                submit_btn = gr.Button("Execute Task", variant="primary")
            
            with gr.Column():
                output_text = gr.Textbox(
                    label="Response",
                    lines=10,
                    interactive=False
                )
        
        submit_btn.click(handle_input, inputs=input_text, outputs=output_text)
    
    with gr.Tab("Advanced Interface"):
        with gr.Row():
            with gr.Column():
                adv_input_text = gr.Textbox(
                    label="Command Input",
                    placeholder="Enter your task or command...",
                    lines=3
                )
                context_input = gr.Textbox(
                    label="Context (JSON)",
                    placeholder='{"priority": "high", "user": "admin"}',
                    lines=2
                )
                adv_submit_btn = gr.Button("Execute with Context", variant="primary")
            
            with gr.Column():
                adv_output_text = gr.Textbox(
                    label="Detailed Response (JSON)",
                    lines=15,
                    interactive=False
                )
        
        adv_submit_btn.click(
            handle_input_with_context, 
            inputs=[adv_input_text, context_input], 
            outputs=adv_output_text
        )
    
    with gr.Tab("System Status"):
        status_btn = gr.Button("Refresh Status")
        status_output = gr.JSON(label="System Status")
        
        def get_status():
            return agent.get_system_status()
        
        status_btn.click(get_status, outputs=status_output)
    
    gr.Markdown("""
    ## API Endpoints
    - **POST** `/api/task` - Submit tasks via API
    - **GET** `/api/agents` - Get agent information
    - **GET** `/api/system/status` - Get system status
    - **WebSocket** `ws://localhost:8765` - Real-time communication
    - **SocketIO** `http://localhost:5001` - Real-time web interface
    """)

if __name__ == "__main__":
    # Start WebSocket server in background thread
    ws_thread = threading.Thread(target=start_websocket_server, daemon=True)
    ws_thread.start()
    
    # Start Flask-SocketIO in background thread
    flask_thread = threading.Thread(target=start_flask_socketio, daemon=True)
    flask_thread.start()
    
    # Launch Gradio interface
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
