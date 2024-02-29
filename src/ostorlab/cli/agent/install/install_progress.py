"""Display the agent install progress."""

from typing import Dict, Iterator

from rich import progress

from ostorlab.cli import console as cli_console


console = cli_console.Console()


class AgentInstallProgress(progress.Progress):
    """Class reponsible for displaying the progress of the agent installation."""

    def __init__(self):
        super().__init__(
            "[progress.description]{task.description}",
            progress.BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            progress.DownloadColumn(),
            "•",
            progress.TransferSpeedColumn(),
            "•",
            progress.TimeRemainingColumn(),
        )

    def display(self, logs_generator: Iterator[Dict]) -> None:
        """Display the progress of the agent install command.

        Args:
            logs_generator: generator of the agent install command logs.
        """
        download_tasks = {}
        extract_tasks = {}

        with self as prg:
            for log in logs_generator:
                if "Downloading" in log.get("status", []):
                    task_id = log["id"]
                    if task_id not in download_tasks:
                        task = prg.add_task(
                            f"[red]Download : {task_id}",
                            total=log.get("progressDetail", {}).get("total"),
                        )
                        download_tasks[task_id] = task
                    task = download_tasks[task_id]
                    current_progress = log.get("progressDetail", {}).get("current")
                    prg.update(task, completed=current_progress)

                elif "Download complete" in log.get("status", []):
                    task_id = log["id"]
                    if task_id in download_tasks:
                        task = download_tasks[task_id]
                        prg.update(task, total=100.0)

                elif "Extracting" in log.get("status", []):
                    task_id = log["id"]
                    if task_id not in extract_tasks:
                        task = prg.add_task(
                            f"[red]Extract : {task_id}",
                            total=log.get("progressDetail", {}).get("total"),
                        )
                        extract_tasks[task_id] = task
                    task = extract_tasks[task_id]
                    current_progress = log.get("progressDetail", {}).get("current")
                    prg.update(task, completed=current_progress)

        console.success("Installation successful")
