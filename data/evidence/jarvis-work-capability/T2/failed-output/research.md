# Jarvis.ceo Desktop Task Architecture and Open-Source Integration

## Introduction and Features
https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/README.md

- Jarvis AI Assistant is a voice dictation app that is 100% open-source, 100% local-capable, and 100% free forever.
- It supports local Whisper and NVIDIA Parakeet models for offline use.
- It also allows for cloud-based Deepgram + Gemini for speed and accuracy.
- The app has zero tracking, zero telemetry, and zero subscriptions.
- Users can hold Fn and speak, with clean, punctuated text appearing anywhere.
- It removes fillers, fixes grammar, and supports full prompt engineering.

## Agent Manager and LLM Integration
https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/core/agent-manager.ts

- The AgentManager class initializes the UnifiedAgent, which uses LLM providers like Ollama, Gemini, and OpenAI.
- It supports local LLMs via Ollama and cloud-based models like Gemini.
- The system allows for customization of how Jarvis formats mail, cleans dictation, or behaves as an assistant.
- The app provides options to use local models for privacy or cloud models for speed and accuracy.
- The AgentManager can be initialized with OpenAI, Gemini, or Ollama providers.
- The AgentManager is a singleton that keeps the agent in memory.

## ReAct Agent Architecture
https://raw.githubusercontent.com/open-jarvis/OpenJarvis/0eb7811df96cf139e6bd6d7fcc9b5cc4ff1418ff/src/openjarvis/agents/native_react.py

- The NativeReActAgent is a ReAct agent that follows a Thought -\> Action -\> Observation loop.
- It uses tools and provides structured output with JSON formatting.
- The agent can perform actions based on its reasoning and provide final answers.
- The agent supports various inference engines and models.
- It is designed for tasks that require both thought and action.
- The agent is part of the OpenJarvis project's native implementation.
