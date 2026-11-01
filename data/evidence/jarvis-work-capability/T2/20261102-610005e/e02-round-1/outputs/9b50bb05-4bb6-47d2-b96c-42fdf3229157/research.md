# Jarvis.ceo Desktop Task Architecture and Open Source Integration

## Overview of Jarvis AI Assistant
https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/README.md

- Jarvis AI Assistant is a voice dictation app that allows users to speak and have clean, punctuated text appear anywhere.
- It is 100% open-source, 100% local-capable, and 100% free forever.
- Jarvis is built by one developer who hates subscriptions and is funded by no VC money.
- It supports local Whisper and NVIDIA Parakeet models for offline use.
- It also supports cloud-based Deepgram + Gemini for faster performance with free tokens.
- Zero tracking, zero telemetry, and zero bullshit are core principles of Jarvis.

## Agent Manager and LLM Providers
https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/core/agent-manager.ts

- The AgentManager class initializes the UnifiedAgent with an LLM provider, either Ollama, Gemini, or OpenAI.
- The OllamaProvider is currently the only fully implemented provider, with GeminiProvider and OpenAIProvider being in development.
- The UnifiedAgent is designed to be flexible and supports different LLMs through provider abstraction.
- The AgentManager ensures that the agent is initialized only once and provides a singleton instance for use throughout the application.
- The initialization process logs information about the provider being used and checks for any errors during setup.

## ReAct Agent and Task Execution
https://raw.githubusercontent.com/open-jarvis/OpenJarvis/0eb7811df96cf139e6bd6d7fcc9b5cc4ff1418ff/src/openjarvis/agents/native_react.py

- The NativeReActAgent is a ReAct agent that follows a Thought-Action-Observation loop.
- It uses structured JSON responses to parse the output and determine the next action or final answer.
- The agent can use different tools and supports both skill-based and procedural instructions.
- The ReAct agent is designed to work with the OpenJarvis framework and is a native implementation, not an integration with an external project.
- The agent can be configured with different models, tools, and parameters to suit various tasks and environments.
