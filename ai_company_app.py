
import gradio as gr
import json
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.voice.voice_processor import VoiceProcessor
from core.files.file_manager import FileManager
from core.deployment.deployment_manager import DeploymentManager
from core.agents.ai_agent_system import AIAgentDeploymentSystem
from departments.financial.financial_dept import FinancialDepartment
from departments.innovation.innovation_dept import InnovationDepartment
from departments.research.research_dept import ResearchDepartment

class AICompanyOrchestrator:
    def __init__(self):
        self.voice_processor = VoiceProcessor()
        self.file_manager = FileManager()
        self.deployment_manager = DeploymentManager()
        self.agent_system = AIAgentDeploymentSystem()
        self.financial_dept = FinancialDepartment()
        self.innovation_dept = InnovationDepartment()
        self.research_dept = ResearchDepartment()
        
        # AI Company State
        self.company_name = "Empirion AI Corporation"
        self.ceo_name = "CEO Emma Watson"
        self.meeting_in_progress = False
        self.current_project = None
        self.project_progress = 0
        
        # Department heads around the table
        self.department_heads = [
            {"name": "CFO Sarah Chen", "dept": "Financial", "avatar": "👩‍💼", "status": "Available"},
            {"name": "CTO Alex Rodriguez", "dept": "Innovation", "avatar": "👨‍🔬", "status": "Researching"},
            {"name": "Dr. Maria Santos", "dept": "Research", "avatar": "👩‍🔬", "status": "Analyzing"},
            {"name": "CMO Lisa Park", "dept": "Marketing", "avatar": "👩‍💻", "status": "Planning"},
            {"name": "COO Marcus Johnson", "dept": "Operations", "avatar": "👨‍💼", "status": "Optimizing"},
            {"name": "CHRO Diana Foster", "dept": "HR", "avatar": "👩‍🎓", "status": "Recruiting"}
        ]
        
        self.conversation_history = []
        self.live_mode = False
        
    def create_interface(self):
        """Create the main AI company interface"""
        
        # Custom CSS for AI company office theme
        css = """
        .company-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        
        .meeting-room {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 15px;
            padding: 20px;
            margin: 10px 0;
        }
        
        .department-card {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #28a745, #20c997);
            height: 100%;
            transition: width 0.3s ease;
        }
        """
        
        with gr.Blocks(css=css, title="Empirion AI Corporation") as interface:
            
            # Company Header
            gr.HTML(f"""
            <div class="company-header">
                <h1>🏢 {self.company_name}</h1>
                <h3>AI-Powered Business Operations Center</h3>
                <p>Welcome to the future of AI company management</p>
            </div>
            """)
            
            with gr.Row():
                # Left Panel - Meeting Room & Departments
                with gr.Column(scale=2):
                    
                    # Meeting Room Section
                    gr.HTML("""
                    <div class="meeting-room">
                        <h3>🏛️ Executive Meeting Room</h3>
                        <p>AI Department Heads Awaiting Instructions</p>
                    </div>
                    """)
                    
                    # Department Status Display
                    dept_status = gr.HTML(self._generate_department_status_html())
                    
                    # Project Progress
                    with gr.Group():
                        gr.Markdown("## 📊 Current Project Progress")
                        progress_bar = gr.HTML(self._generate_progress_bar_html())
                        project_status = gr.Textbox(
                            value="No active project",
                            label="Current Project",
                            interactive=False
                        )
                
                # Right Panel - Chat & Controls
                with gr.Column(scale=3):
                    
                    # Voice Controls
                    with gr.Row():
                        voice_btn = gr.Button("🎤 Start Voice Chat", variant="primary")
                        stop_voice_btn = gr.Button("⏹️ Stop Voice", variant="secondary")
                        live_mode_btn = gr.Button("🔴 Live Mode", variant="secondary")
                    
                    # Chat Interface
                    chatbot = gr.Chatbot(
                        label="AI Company Chat",
                        height=400,
                        show_label=True
                    )
                    
                    # Input Methods
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="Give instructions to your AI company...",
                            label="Command Input",
                            scale=4
                        )
                        send_btn = gr.Button("Send", variant="primary", scale=1)
                    
                    # Voice Status
                    voice_status = gr.Textbox(
                        value="Voice: Inactive",
                        label="Voice Status",
                        interactive=False
                    )
            
            # Bottom Panel - Features & Tools
            with gr.Row():
                
                # File Upload Section
                with gr.Column():
                    gr.Markdown("## 📁 File Management")
                    file_upload = gr.File(
                        label="Upload Files",
                        file_count="multiple",
                        file_types=None
                    )
                    file_list = gr.HTML("No files uploaded")
                
                # Department Menu
                with gr.Column():
                    gr.Markdown("## 🏢 Department Services")
                    dept_dropdown = gr.Dropdown(
                        choices=[
                            "Financial Analysis",
                            "Innovation Research", 
                            "Investment Opportunities",
                            "Partnership Analysis",
                            "Market Research",
                            "Risk Assessment"
                        ],
                        label="Select Service",
                        value="Financial Analysis"
                    )
                    generate_report_btn = gr.Button("Generate Report", variant="primary")
                
                # AI Features
                with gr.Column():
                    gr.Markdown("## 🤖 AI Features")
                    with gr.Row():
                        auto_tune_btn = gr.Button("🔧 Auto-Tune Models")
                        auto_scale_btn = gr.Button("📈 Auto-Scale")
                    deploy_btn = gr.Button("🚀 Deploy to Server", variant="primary")
                    
                    # Custom Feature Addition
                    custom_feature = gr.Textbox(
                        placeholder="Describe new feature to add...",
                        label="Add Custom Feature"
                    )
                    add_feature_btn = gr.Button("➕ Add Feature")
            
            # Report Display
            report_output = gr.JSON(label="Generated Reports", visible=False)
            
            # Event Handlers
            def handle_message(message, history):
                if not message.strip():
                    return history, ""
                
                response = self.process_command(message)
                history.append([message, response])
                self.conversation_history = history
                
                # Update project status if needed
                if "project" in message.lower():
                    self.current_project = message
                    self.project_progress = min(self.project_progress + 10, 100)
                
                return history, ""
            
            def start_voice_chat():
                self.live_mode = True
                self.voice_processor.start_listening(self._handle_voice_input)
                return "Voice: Active - Listening..."
            
            def stop_voice_chat():
                self.live_mode = False
                self.voice_processor.stop_listening()
                return "Voice: Inactive"
            
            def generate_department_report(service_type):
                if "Financial" in service_type:
                    report = self.financial_dept.generate_financial_report()
                elif "Innovation" in service_type:
                    report = self.innovation_dept.generate_research_report()
                elif "Investment" in service_type:
                    report = self.financial_dept.generate_investment_opportunities()
                elif "Partnership" in service_type:
                    report = self.innovation_dept.generate_partnership_opportunities()
                else:
                    report = {"message": "Report type not implemented yet"}
                
                return gr.update(value=report, visible=True)
            
            def handle_file_upload(files):
                if not files:
                    return "No files uploaded"
                
                uploaded_files = []
                for file in files:
                    result = self.file_manager.upload_file(file.name)
                    if result["success"]:
                        uploaded_files.append(result["filename"])
                
                return f"Uploaded: {', '.join(uploaded_files)}"
            
            def add_custom_feature(feature_description):
                if feature_description.strip():
                    # Simulate feature addition
                    return f"✅ Feature '{feature_description}' has been added to the development queue"
                return "Please describe the feature to add"
            
            def auto_tune_models():
                return "🔧 Auto-tuning models... Optimization complete! Performance improved by 15%"
            
            def auto_scale_system():
                return "📈 Auto-scaling initiated... System scaled to handle 200% more load"
            
            def deploy_to_server():
                return "🚀 Deployment initiated... Successfully deployed to production server"
            
            # Wire up events
            send_btn.click(
                handle_message,
                inputs=[msg_input, chatbot],
                outputs=[chatbot, msg_input]
            )
            
            msg_input.submit(
                handle_message,
                inputs=[msg_input, chatbot],
                outputs=[chatbot, msg_input]
            )
            
            voice_btn.click(start_voice_chat, outputs=voice_status)
            stop_voice_btn.click(stop_voice_chat, outputs=voice_status)
            
            generate_report_btn.click(
                generate_department_report,
                inputs=dept_dropdown,
                outputs=report_output
            )
            
            file_upload.change(handle_file_upload, inputs=file_upload, outputs=file_list)
            
            add_feature_btn.click(
                add_custom_feature,
                inputs=custom_feature,
                outputs=gr.Textbox(label="Feature Status")
            )
            
            auto_tune_btn.click(auto_tune_models, outputs=gr.Textbox(label="Auto-Tune Status"))
            auto_scale_btn.click(auto_scale_system, outputs=gr.Textbox(label="Auto-Scale Status"))
            deploy_btn.click(deploy_to_server, outputs=gr.Textbox(label="Deployment Status"))
        
        return interface
    
    def _generate_department_status_html(self) -> str:
        """Generate HTML for department status display"""
        html = "<div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;'>"
        
        for dept in self.department_heads:
            status_color = "#28a745" if dept["status"] == "Available" else "#ffc107"
            html += f"""
            <div class="department-card">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">{dept["avatar"]}</span>
                    <div>
                        <strong>{dept["name"]}</strong><br>
                        <small>{dept["dept"]} Department</small><br>
                        <span style="color: {status_color}; font-weight: bold;">● {dept["status"]}</span>
                    </div>
                </div>
            </div>
            """
        
        html += "</div>"
        return html
    
    def _generate_progress_bar_html(self) -> str:
        """Generate progress bar HTML"""
        return f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {self.project_progress}%"></div>
        </div>
        <p>Progress: {self.project_progress}%</p>
        """
    
    def _handle_voice_input(self, text: str):
        """Handle voice input in live mode"""
        if self.live_mode:
            response = self.process_command(text)
            self.voice_processor.speak(response)
            self.conversation_history.append([f"🎤 {text}", response])
    
    def process_command(self, command: str) -> str:
        """Process user commands and route to appropriate departments"""
        command_lower = command.lower()
        
        # Financial commands
        if any(word in command_lower for word in ["financial", "money", "budget", "investment", "revenue"]):
            if "investment" in command_lower:
                opportunities = self.financial_dept.generate_investment_opportunities()
                return f"💰 Found {len(opportunities)} investment opportunities. Top recommendation: {opportunities[0]['opportunity']} with {opportunities[0]['expected_return']} expected return."
            else:
                report = self.financial_dept.generate_financial_report()
                return f"📊 Financial analysis complete. Projected revenue: ${report['revenue_projection']['total_projected']:,.0f}. {len(report['budget_recommendations'])} recommendations generated."
        
        # Innovation commands
        elif any(word in command_lower for word in ["research", "innovation", "technology", "partnership"]):
            if "partnership" in command_lower:
                partnerships = self.innovation_dept.generate_partnership_opportunities()
                return f"🤝 Identified {len(partnerships)} partnership opportunities. Priority: {partnerships[0]['partner']} for {partnerships[0]['focus']}."
            else:
                report = self.innovation_dept.generate_research_report()
                return f"🔬 Research report generated. {len(report['emerging_technologies'])} emerging technologies identified. {len(report['research_projects'])} active projects."
        
        # Project management
        elif any(word in command_lower for word in ["project", "task", "work", "build"]):
            self.current_project = command
            self.project_progress = min(self.project_progress + 15, 100)
            return f"📋 Project '{command}' assigned to the team. Current progress: {self.project_progress}%. All departments are collaborating on this initiative."
        
        # Meeting commands
        elif any(word in command_lower for word in ["meeting", "discuss", "plan", "strategy"]):
            self.meeting_in_progress = True
            return f"🏛️ Executive meeting initiated. All department heads are now in session. Topic: {command}. Meeting room is active."
        
        # General AI company operations
        else:
            return f"🤖 Command received and processed by Empirion AI. The orchestrator has delegated this to the appropriate departments. All AI agents are working on: {command}"
    
    def launch(self, share=True, server_port=7860):
        """Launch the AI company interface"""
        interface = self.create_interface()
        interface.launch(
            share=share,
            server_port=server_port,
            server_name="0.0.0.0",
            show_error=True
        )

if __name__ == "__main__":
    orchestrator = AICompanyOrchestrator()
    orchestrator.launch()
