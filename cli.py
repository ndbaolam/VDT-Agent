import asyncio
import uuid
from loguru import logger
from workflow import graph, Agents
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from rich.console import Console
from rich.spinner import Spinner
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

console = Console()


async def run_cli():
    await Agents.init()
    thread_id = str(uuid.uuid4())

    config: RunnableConfig = {
        "recursion_limit": 40,
        "thread_id": thread_id,
    }

    console.print("[bold green]🤖 Agent CLI ready![/bold green] Type 'exit' to quit.\n")

    while True:
        user_input = input("📝 You: ")
        if user_input.strip().lower() in ["exit", "quit", "q"]:
            console.print("[bold yellow]👋 Exiting agent CLI.[/bold yellow]")
            break

        inputs = {"input": user_input}

        with Live(Spinner("dots", text="Agent is thinking...\n\n"), refresh_per_second=10):
            try:
                response = await graph.ainvoke(inputs, config=config, stream_mode="values")
            except Exception as e:
                logger.error(e)

        # --- Handle interrupt safely ---
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
                    stream_mode="values"
                )
        except Exception as e:
            logger.log(e)

        # --- Agent response ---
        last_step = response.get("past_steps", [])[-1]
        _, result = last_step
        console.print(
            Panel(
                result, 
                title="[bold green]Agent Response[/]", 
                style="bold blue"
            )
        )

        console.print("[bold green]✅ Done.[/bold green]\n")


if __name__ == "__main__":
    asyncio.run(run_cli())
