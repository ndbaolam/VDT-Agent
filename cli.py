import asyncio
import uuid
from loguru import logger
from agent.workflow_v2 import graph, Agents
from langchain_core.messages import HumanMessage
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from rich.console import Console
from rich.spinner import Spinner
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

console = Console()


async def run_cli():    
    available_models = [
        "openai:gpt-4.1-mini",
        "openai:gpt-4o",
        "ollama:qwen3:4b",
    ]
    
    console.print("[bold cyan]🛠️ Select a model to use:[/bold cyan]")
    for i, m in enumerate(available_models, start=1):
        console.print(f"[bold green]{i}[/bold green]. [magenta]{m}[/magenta]")
    
    while True:
        choice = console.input("[bold yellow]Enter number of model (default 1): [/bold yellow]") or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(available_models):
            model_input = available_models[int(choice) - 1]
            break
        console.print("[bold red]Invalid selection, try again.[/bold red]")

    console.print(f"[bold green]Selected model:[/bold green] [magenta]{model_input}[/magenta]\n")
    
    # If you are using deepseek, you need to set the DEEPSEEK_API_KEY environment variable.
    # For example: export DEEPSEEK_API_KEY="your_api_key"
    await Agents.init(model=model_input)

    thread_id = str(uuid.uuid4())
    config: RunnableConfig = {
        "recursion_limit": 20,
        "thread_id": thread_id,
    }

    console.print(
        f"[bold green]🤖 Agent CLI ready![/bold green] "
        "Type 'exit' to quit.\n"
    )

    while True:
        user_input = console.input("[bold yellow]📝 You:[/bold yellow] ")
        if user_input.strip().lower() in ["exit", "quit", "q"]:
            console.print("[bold red]👋 Exiting agent CLI.[/bold red]")
            break

        message = HumanMessage(content=user_input)
        
        with Live(Spinner("dots", text="[bold blue]Agent is thinking...[/bold blue]\n\n"), refresh_per_second=10):
            try:
                response = await graph.ainvoke({"messages": [message]}, config=config)
            except Exception as e:
                logger.error(f"Execution error: {e}")
                continue
        
        try:
            interrupts = response.get("__interrupt__") or []
            interrupt = interrupts[0] if interrupts else None

            if interrupt:
                description = interrupt.value.get("description", "No description")
                console.print(
                    Panel(description, title="[bold yellow]Human-in-the-Loop[/bold yellow]", style="bold cyan")
                )

                args = interrupt.value.get("action_request") or {}
                if args:
                    table = Table(title="[bold magenta]Action Request[/bold magenta]", style="bold magenta")
                    table.add_column("[bold green]Key[/bold green]", style="green")
                    table.add_column("[bold white]Value[/bold white]", style="white")
                    for k, v in args.items():
                        table.add_row(str(k), str(v))
                    console.print(table)

                hil_result = console.input("[bold yellow]👉 Allow action? (y/n): [/bold yellow]") or "n"
                response = await graph.ainvoke(
                    Command(resume={"type": hil_result}), config=config
                )

        except Exception as e:
            logger.exception(f"Interrupt handling failed: {e}")
        
        messages = response.get("messages") or []
        if messages:
            last_message = messages[-1]
            result = last_message.content if hasattr(last_message, "content") else str(last_message)
        else:
            result = "[bold red]Something went wrong! Please try again.[/bold red]"

        console.print(
            Panel(result, title="[bold green]Agent Response[/bold green]", style="bold blue")
        )
        console.print("[bold green]✅ Done.[/bold green]\n")


if __name__ == "__main__":
    asyncio.run(run_cli())
