"""Tests for scan run file command."""

from click.testing import CliRunner

from ostorlab.cli import rootcli


def testScanRunFile_whenUrlIsProvided_callScanWithValidListOFAssets(
    mocker,
):
    """Test ostorlab scan run file command with --url option.Should call scan with valid list of assets."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan = mocker.patch("ostorlab.runtimes.local.LocalRuntime.scan", return_value=True)

    runner.invoke(
        rootcli.rootcli,
        [
            "scan",
            "run",
            "--agent=agent1 --agent=agent2",
            "file",
            "--url",
            "https://ostorlab.co",
            "--url",
            "https://hello.ostorlab.co",
        ],
    )

    assert scan.call_count == 1
    assert len(scan.call_args_list) == 1
    assert len(scan.call_args_list[0].kwargs.get("assets")) == 2
    assert (
        scan.call_args_list[0].kwargs.get("assets")[0].content_url
        == "https://ostorlab.co"
    )
    assert (
        scan.call_args_list[0].kwargs.get("assets")[1].content_url
        == "https://hello.ostorlab.co"
    )


def testScanRunFile_whenFileProvided_callScanWithValidListOFAssets(
    mocker,
):
    """Test ostorlab scan run file command with --file option.Should call scan with valid list of assets."""

    runner = CliRunner()
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.__init__", return_value=None)
    mocker.patch("ostorlab.runtimes.local.LocalRuntime.can_run", return_value=True)
    scan = mocker.patch("ostorlab.runtimes.local.LocalRuntime.scan", return_value=True)
    with runner.isolated_filesystem():
        with open('hello.txt', 'w') as f:
            f.write("May the Force be with you")
            f.seek(0)
        runner.invoke(
            rootcli.rootcli,
            [
                "scan",
                "run",
                "--agent=agent1 --agent=agent2",
                "file",
                "--file",
                'hello.txt',
            ],
        )
        assert scan.call_count == 1
        assert len(scan.call_args_list) == 1
        assert len(scan.call_args_list[0].kwargs.get("assets")) == 1
        assert (
                scan.call_args_list[0].kwargs.get("assets")[0].content
                == b"May the Force be with you"
        )
        assert scan.call_args_list[0].kwargs.get("assets")[0].path == 'hello.txt'
