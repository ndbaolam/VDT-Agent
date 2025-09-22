import asyncio
import uuid
from loguru import logger
from agent.workflow import build_graph
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
    graph = build_graph()

    thread_id = str(uuid.uuid4())

    config: RunnableConfig = {
        "recursion_limit": 20,
        "thread_id": thread_id,
    }

    console.print("[bold green]🤖 Agent CLI ready![/bold green] Type 'exit' to quit.\n")

    while True:
        user_input = input("📝 You: ")
        if user_input.strip().lower() in ["exit", "quit", "q"]:
            console.print("[bold yellow]👋 Exiting agent CLI.[/bold yellow]")
            break

        message = HumanMessage(content=user_input)
        
        with Live(Spinner("dots", text="Agent is thinking...\n\n"), refresh_per_second=10):
            try:
                response = await graph.ainvoke(
                    {"messages": [message]},
                    config=config,
                )
            except Exception as e:
                logger.error(f"Execution error: {e}")
                continue
        
        try:
            interrupts = response.get("__interrupt__") or []
            interrupt = interrupts[0] if interrupts else None

            if interrupt:
                description = interrupt.value.get("description", "No description")
                console.print(Panel(description, title="[bold yellow]Human-in-the-Loop[/]", style="bold cyan"))

                args = interrupt.value.get("action_request") or {}
                if args:
                    table = Table(title="Action Request", style="bold magenta")
                    table.add_column("Key", style="bold green")
                    table.add_column("Value", style="white")

                    for k, v in args.items():
                        table.add_row(str(k), str(v))

                    console.print(table)

                hil_result = console.input("[bold yellow]👉 Allow action? (y/n): [/]") or "n"
                response = await graph.ainvoke(
                    Command(resume={"type": hil_result}),
                    config=config,
                )
        except Exception as e:
            logger.exception(f"Interrupt handling failed: {e}")
        
        messages = response.get("messages") or []
        if messages:
            last_message = messages[-1]
            result = last_message.content if hasattr(last_message, "content") else str(last_message)
        else:
            result = "Something went wrong! Please try again."

        console.print(
            Panel(
                result,
                title="[bold green]Agent Response[/]",
                style="bold blue",
            )
        )

        console.print("[bold green]✅ Done.[/bold green]\n")


if __name__ == "__main__":
    asyncio.run(run_cli())