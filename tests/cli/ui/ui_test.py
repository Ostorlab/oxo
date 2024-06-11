from click import testing
from pytest_mock import plugin

from ostorlab.cli import rootcli


def testServeOxoUi_always_shouldCallHttpServeWithRightParams(
    mocker: plugin.MockerFixture,
) -> None:
    """Ensure that the function call http.serve with the right params."""
    mocked_http_serve = mocker.patch(
        "http.server.HTTPServer.__init__", return_value=None
    )
    mocked_serve_forever = mocker.patch("http.server.HTTPServer.serve_forever")
    runner = testing.CliRunner()

    result = runner.invoke(rootcli.rootcli, ["ui", "--port=9090", "--host=127.0.0.1"])

    assert mocked_serve_forever.called is True
    assert mocked_http_serve.called is True
    assert mocked_http_serve.call_args[0][0] == ("127.0.0.1", 9090)
    assert "Serving UI on : http://127.0.0.1:9090 ..." in result.output
