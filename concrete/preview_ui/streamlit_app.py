"""
Streamlit UI for MCP Workflow Agent with streaming markdown support.

This module provides a web interface using Streamlit for interacting with
the MCP workflow agent and visualizing workflow execution in real-time.

Requires Python 3.11+
"""

from __future__ import annotations

import time
from unittest.mock import Mock
from typing import Optional, Generator

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    # Mock streamlit for type checking when not available
    class MockStreamlit:
        def __init__(self):
            # Mock session_state to be a dynamic object like real Streamlit session_state
            self.session_state = Mock()
            
            # Mock sidebar to support context manager protocol
            self.sidebar = Mock()
            self.sidebar.__enter__ = Mock(return_value=self.sidebar)
            self.sidebar.__exit__ = Mock(return_value=None)

        def title(self, text): pass
        def markdown(self, text, unsafe_allow_html=False): pass
        def chat_message(self, role): return Mock()
        def chat_input(self, placeholder): return ""
        def selectbox(self, label, options, help=None): return options[0] if options else None
        def button(self, text): return False
        def write(self, text): pass
        def error(self, text): pass
        def spinner(self, text): 
            mock_spinner = Mock()
            mock_spinner.__enter__ = Mock(return_value=mock_spinner)
            mock_spinner.__exit__ = Mock(return_value=None)
            return mock_spinner
        def empty(self): return Mock()
        def columns(self, widths): 
            mock_cols = [Mock() for _ in widths]
            for col in mock_cols:
                col.__enter__ = Mock(return_value=col)
                col.__exit__ = Mock(return_value=None)
                col.metric = Mock() # Mock metric for columns as well
            return mock_cols
        def expander(self, title, expanded=False): 
            mock_expander = Mock()
            mock_expander.__enter__ = Mock(return_value=mock_expander)
            mock_expander.__exit__ = Mock(return_value=None)
            return mock_expander
        def subheader(self, text): pass
        def caption(self, text): pass
        def metric(self, label, value): pass
        def rerun(self): pass
        def set_page_config(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def json(self, data): pass
    
    st = MockStreamlit()

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Generator
import time
import traceback

# Add the project's root directory to sys.path for module discovery
# This is necessary for absolute imports to work when the script is run directly
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
sys.path.insert(0, project_root)

# Import our components
# Note: The agentic workflow components are not imported to keep this focused on streaming
from clients.preview_mcp.context import WorkflowContext, WorkflowStep, WorkflowStatus
from clients.preview_mcp.logging import create_workflow_logger, WorkflowLogger


class StreamlitWorkflowUI:
    """Streamlit UI for workflow visualization and agent interaction."""
    
    def __init__(self):
        """Initialize the Streamlit UI."""
        if not STREAMLIT_AVAILABLE:
            print("Warning: Streamlit not available. Install with: pip install streamlit")
            return
            
        # Simplified for GraphMCP integration - agentic workflow removed for now
        self.workflow_logger: Optional[WorkflowLogger] = None
        
    def _get_logger(self) -> WorkflowLogger:
        """Get or create workflow logger."""
        if not self.workflow_logger:
            workflow_id = getattr(st.session_state, 'workflow_id', 'streamlit-session')
            session_id = getattr(st.session_state, 'session_id', 'default')
            self.workflow_logger = create_workflow_logger(workflow_id, session_id)
        return self.workflow_logger
        
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if not STREAMLIT_AVAILABLE:
            return
            
        # Initialize workflow context
        if not hasattr(st.session_state, 'workflow_context'):
            st.session_state.workflow_context = WorkflowContext(
                workflow_id="streamlit-session"
            )
            st.session_state.workflow_id = "streamlit-session"
            st.session_state.session_id = "default"
        
        # Initialize conversation history
        if not hasattr(st.session_state, 'conversation_history'):
            st.session_state.conversation_history = []
            
        # Initialize current response
        if not hasattr(st.session_state, 'current_response'):
            st.session_state.current_response = ""
    
    def render_sidebar(self):
        """Render the sidebar with workflow controls."""
        if not STREAMLIT_AVAILABLE:
            return "default"
            
        with st.sidebar:
            st.title("🔄 Workflow Control")
            
            # Agent type selection
            agent_type = st.selectbox(
                "Agent Type",
                ["default", "analysis", "creative"],
                help="Select the type of agent for different capabilities"
            )
            
            # Workflow status display
            st.subheader("📊 Status")
            context = st.session_state.workflow_context
            
            status_icons = {
                WorkflowStatus.PENDING: "🟡",
                WorkflowStatus.IN_PROGRESS: "🔵", 
                WorkflowStatus.COMPLETED: "🟢",
                WorkflowStatus.FAILED: "🔴"
            }
            
            st.write(f"**Status:** {status_icons.get(context.status, '⚪')} {context.status.value}")
            st.write(f"**Steps:** {len(context.steps)}")
            st.write(f"**Started:** {context.created_at.strftime('%H:%M:%S')}")
            
            # Clear conversation button
            if st.button("🗑️ Clear Conversation"):
                st.session_state.conversation_history = []
                st.session_state.current_response = ""
                st.session_state.workflow_context = WorkflowContext(
                    workflow_id=f"streamlit-{int(time.time())}"
                )
                st.rerun()
                
            return agent_type
    
    def render_workflow_steps(self):
        """Render workflow steps visualization."""
        if not STREAMLIT_AVAILABLE:
            return
            
        context = st.session_state.workflow_context
        
        if context.steps:
            with st.expander(f"📋 Workflow Steps ({len(context.steps)})", expanded=False):
                for i, step in enumerate(context.steps):
                    status_icons = {
                        WorkflowStatus.PENDING: "⏳",
                        WorkflowStatus.IN_PROGRESS: "🔄",
                        WorkflowStatus.COMPLETED: "✅",
                        WorkflowStatus.FAILED: "❌"
                    }
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{i+1}.** {step.name}")
                        # Show input data as description if available
                        if step.input_data:
                            st.caption(f"Input: {list(step.input_data.keys())}")
                    with col2:
                        st.write(f"{status_icons.get(step.status, '⚪')} {step.status.value}")
                    
                    # Show step result if completed
                    if step.output_data and step.status == WorkflowStatus.COMPLETED:
                        with st.expander(f"View Result - Step {i+1}"):
                            st.json(step.output_data)
    
    def simulate_streaming_response(self, query: str, agent_type: str) -> Generator[str, None, None]:
        """Simulate streaming response for the agent."""
        try:
            logger = self._get_logger()
            logger.log_agent_action(agent_type, "process_query", {"query": query[:100]})
            
            # Create a simple response (in real implementation, this would call the agent)
            response_parts = [
                f"Processing Query with {agent_type.title()} Agent\n\n",
                f"**Query:** {query}\n\n",
                "**Analysis:**\n",
                "- Understanding the request...",
                "- Analyzing context and requirements...",
                "- Formulating comprehensive response...\n\n",
                "**Response:**\n\n",
                "I'm processing your request using the workflow agent. ",
                "This is a simulated streaming response that demonstrates ",
                "how markdown content can be streamed in real-time. ",
                "\n\n**Key Points:**\n",
                "- ✅ Streaming markdown rendering\n",
                "- ✅ Real-time workflow visualization\n",
                "- ✅ Agent interaction capabilities\n",
                "- ✅ Session state management\n\n",
                "The actual implementation would integrate with the LangChain agent ",
                "to provide intelligent responses based on your workflow context.",
            ]
            
            for part in response_parts:
                yield part
                time.sleep(0.1)  # Simulate streaming delay
                
        except Exception as e:
            yield f"\n\n**Error:** {str(e)}"
            logger = self._get_logger()
            logger.log_workflow_error(str(e))
    
    def render_chat_interface(self, agent_type: str):
        """Render the main chat interface with streaming."""
        if not STREAMLIT_AVAILABLE:
            return
            
        # Display conversation history
        for msg in st.session_state.conversation_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat input
        if query := st.chat_input("Ask me anything about workflows..."):
            # Add user message
            st.session_state.conversation_history.append({
                "role": "user",
                "content": query
            })
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(query)
            
            # Display assistant response with streaming
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    # Stream the response
                    for response_chunk in self.simulate_streaming_response(query, agent_type):
                        full_response += response_chunk
                        response_placeholder.markdown(full_response + "▌")  # Cursor effect
                    
                    # Final response without cursor
                    response_placeholder.markdown(full_response)
                    
                    # Add to conversation history
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": full_response
                    })
                    
                except Exception as e:
                    error_message = f"An error occurred: {str(e)}"
                    st.error(error_message)
                    self._get_logger().log_workflow_error(error_message)
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": f"**Error:** {error_message}"
                    })
        
    def render_metrics(self):
        """Render key metrics for the workflow."""
        if not STREAMLIT_AVAILABLE:
            return
            
        st.subheader("📊 Metrics")
        context = st.session_state.workflow_context
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total Steps", value=len(context.steps))
        with col2:
            completed_steps = sum(1 for step in context.steps if step.status == WorkflowStatus.COMPLETED)
            st.metric(label="Completed Steps", value=completed_steps)
            
        # Add more metrics as needed
        st.caption("Metrics update in real-time as the workflow progresses.")
        
    def run(self):
        """Run the Streamlit application."""
        if not STREAMLIT_AVAILABLE:
            st.error("Streamlit is not installed. Please install it with: pip install streamlit")
            return

        st.set_page_config(layout="wide", page_title="MCP Workflow Agent")

        # Custom CSS to reduce font size in the main chat panel
        st.markdown(
            """
            <style>
            /* Target chat message content */
            .st-chat-message-content p {
                font-size: 0.7em !important; /* Adjusted to be even smaller and forced */
            }
            /* Target code blocks in chat messages if present */
            .st-chat-message-content pre {
                font-size: 0.65em !important; /* Adjusted to be even smaller and forced */
            }
            /* Target markdown headers if present in chat messages */
            .st-chat-message-content h1, 
            .st-chat-message-content h2, 
            .st-chat-message-content h3, 
            .st-chat-message-content h4, 
            .st-chat-message-content h5, 
            .st-chat-message-content h6 {
                font-size: 0.8em !important; /* Adjusted to be even smaller and forced */
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        self.initialize_session_state()
        agent_type = self.render_sidebar()

        # Ensure agent_type is always a string
        if agent_type is None:
            agent_type = "default" # Fallback to a default agent type

        st.title("🤖 MCP Workflow Agent")

        self.render_chat_interface(agent_type)
        self.render_workflow_steps()
        self.render_metrics()


def main():
    if not STREAMLIT_AVAILABLE:
        print("Streamlit not available. Exiting.")
        return

    # Add this to load environment variables from .env file
    # This is useful for local development and should be done before initializing agents
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("Environment variables loaded from .env file.")
    except ImportError:
        print("python-dotenv not installed. Skipping .env loading.")
        print("Install with: pip install python-dotenv")
    except Exception as e:
        print(f"Error loading .env file: {e}")

    app = StreamlitWorkflowUI()
    app.run()


if __name__ == "__main__":
    main()