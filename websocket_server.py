import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Dict, Set
from orchestrator_agent import OrchestratorAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.orchestrator = OrchestratorAgent()
        self.message_handlers = {
            'task_request': self.handle_task_request,
            'agent_status': self.handle_agent_status,
            'memory_query': self.handle_memory_query,
            'system_info': self.handle_system_info
        }

    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client {websocket.remote_address} connected. Total clients: {len(self.clients)}")
        
        # Send welcome message
        welcome_msg = {
            'type': 'connection_established',
            'message': 'Connected to Empirion AI Orchestrator',
            'timestamp': datetime.now().isoformat(),
            'client_id': id(websocket)
        }
        await websocket.send(json.dumps(welcome_msg))

    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.clients.discard(websocket)
        logger.info(f"Client {websocket.remote_address} disconnected. Total clients: {len(self.clients)}")

    async def broadcast_message(self, message: Dict):
        """Broadcast message to all connected clients"""
        if self.clients:
            message['timestamp'] = datetime.now().isoformat()
            message_json = json.dumps(message)
            await asyncio.gather(
                *[client.send(message_json) for client in self.clients],
                return_exceptions=True
            )

    async def handle_task_request(self, websocket, data: Dict):
        """Handle task delegation requests"""
        try:
            task_input = data.get('task', '')
            if not task_input:
                await self.send_error(websocket, "Task input is required")
                return

            # Process task through orchestrator
            result = self.orchestrator.route_task(task_input)
            
            response = {
                'type': 'task_response',
                'task_id': data.get('task_id', ''),
                'result': result,
                'status': 'completed'
            }
            
            await websocket.send(json.dumps(response))
            
            # Broadcast task completion to other clients
            broadcast_msg = {
                'type': 'task_completed',
                'task': task_input,
                'agent': 'orchestrator',
                'status': 'completed'
            }
            await self.broadcast_message(broadcast_msg)
            
        except Exception as e:
            logger.error(f"Error handling task request: {e}")
            await self.send_error(websocket, f"Task processing failed: {str(e)}")

    async def handle_agent_status(self, websocket, data: Dict):
        """Handle agent status requests"""
        try:
            agent_name = data.get('agent', 'all')
            
            if agent_name == 'all':
                # Return status of all agents
                agents_status = {}
                for agent in self.orchestrator.dataset_manifest.keys():
                    agents_status[agent] = {
                        'status': 'active',
                        'last_task': 'N/A',
                        'memory_entries': len(self.orchestrator.memory.get(agent, []))
                    }
            else:
                agents_status = {
                    agent_name: {
                        'status': 'active' if agent_name in self.orchestrator.dataset_manifest else 'unknown',
                        'memory_entries': len(self.orchestrator.memory.get(agent_name, []))
                    }
                }
            
            response = {
                'type': 'agent_status_response',
                'agents': agents_status
            }
            
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            logger.error(f"Error handling agent status request: {e}")
            await self.send_error(websocket, f"Agent status request failed: {str(e)}")

    async def handle_memory_query(self, websocket, data: Dict):
        """Handle memory query requests"""
        try:
            agent_name = data.get('agent')
            if not agent_name:
                await self.send_error(websocket, "Agent name is required for memory query")
                return
            
            from memory_engine import recall_context
            memory_data = recall_context(agent_name)
            
            response = {
                'type': 'memory_response',
                'agent': agent_name,
                'memory': memory_data
            }
            
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            logger.error(f"Error handling memory query: {e}")
            await self.send_error(websocket, f"Memory query failed: {str(e)}")

    async def handle_system_info(self, websocket, data: Dict):
        """Handle system information requests"""
        try:
            system_info = {
                'connected_clients': len(self.clients),
                'available_agents': list(self.orchestrator.dataset_manifest.keys()),
                'server_status': 'running',
                'uptime': 'N/A'  # Could be implemented with server start time
            }
            
            response = {
                'type': 'system_info_response',
                'info': system_info
            }
            
            await websocket.send(json.dumps(response))
            
        except Exception as e:
            logger.error(f"Error handling system info request: {e}")
            await self.send_error(websocket, f"System info request failed: {str(e)}")

    async def send_error(self, websocket, error_message: str):
        """Send error message to client"""
        error_response = {
            'type': 'error',
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        }
        await websocket.send(json.dumps(error_response))

    async def handle_message(self, websocket, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](websocket, data)
            else:
                await self.send_error(websocket, f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            await self.send_error(websocket, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(websocket, f"Message handling failed: {str(e)}")

    async def handle_client(self, websocket, path):
        """Handle individual client connections"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {websocket.remote_address} connection closed")
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

    def run(self):
        """Run the WebSocket server"""
        try:
            asyncio.run(self.start_server())
        except KeyboardInterrupt:
            logger.info("WebSocket server stopped by user")
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")

if __name__ == "__main__":
    server = WebSocketServer()
    server.run()
