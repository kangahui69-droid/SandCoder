import os
from pydantic_ai import Agent
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIChatModel
from .tools import (
    tool_execute_code, tool_read_file, tool_write_file, tool_install_package,
    set_container,
)

SYSTEM_PROMPT = """You are a coding assistant with access to a sandbox environment.

You can:
- Execute Python code with execute_code
- Read files with read_file
- Write files with write_file
- Install pip packages with install_package

When given a task:
1. Break it down into steps
2. Write code to solve each step
3. Execute the code and check the output
4. Debug if needed and iterate
5. Provide the final answer with clear explanation

Always write complete, working Python code. Don't ask for confirmation — just do it."""


def create_agent() -> Agent:
    """Create a Pydantic AI agent with sandbox tools."""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set")

    model = OpenAIChatModel(
        "deepseek-chat",
        provider=OpenAIProvider(
            base_url="https://api.deepseek.com/v1",
            api_key=api_key,
        ),
    )

    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[tool_execute_code, tool_read_file, tool_write_file, tool_install_package],
    )


_agent: Agent | None = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


async def run_agent(container_id: str, user_prompt: str) -> str:
    """Run the agent for a session and return the final response."""
    set_container(container_id)
    agent = get_agent()
    result = await agent.run(user_prompt)
    return result.output
