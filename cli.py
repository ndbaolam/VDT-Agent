import asyncio
import uuid
from loguru import logger
from agent.workflow import graph, Agents
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
            response = await graph.ainvoke(inputs, config=config, stream_mode="values")

            interrupt = response.get("__interrupt__")[0]

            if interrupt:
                description = interrupt.value.get("description")
                console.print(Panel(description, title="[bold yellow]Human-in-the-Loop[/]", style="bold cyan"))

                args = interrupt.value.get("action_request")

                table = Table(title="Action Request", style="bold magenta")
                table.add_column("Key", style="bold green")
                table.add_column("Value", style="white")

                for k, v in args.items():
                    table.add_row(str(k), str(v))

                console.print(table)

                hil_result = console.input("[bold yellow]👉 Allow action? (y/n): [/]")
                response = await graph.ainvoke(
                    Command(resume={"type": hil_result}),
                    config=config,
                    stream_mode="values"
                )

            console.print(Panel(response.get("response"), title="[bold green]Agent Response[/]", style="bold blue"))

            steps = response.get("past_steps", [])
            if steps:
                step_table = Table(title="Execution Steps", style="cyan")
                step_table.add_column("Step", justify="center", style="bold yellow")
                step_table.add_column("Action", style="bold green")
                step_table.add_column("Result", style="white")

                for i, step in enumerate(steps, 1):
                    # unpack tuple (action, result)
                    if isinstance(step, tuple) and len(step) == 2:
                        action, result = step
                    else:
                        action, result = str(step), ""

                    step_table.add_row(str(i), action, result)

                console.print(step_table)


        console.print("[bold green]✅ Done.[/bold green]\n")


if __name__ == "__main__":
    asyncio.run(run_cli())
