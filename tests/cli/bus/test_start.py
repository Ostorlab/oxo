import pytest

from ostorlab.cli.bus import start
from ostorlab.apis.runners import authenticated_runner


@pytest.mark.asyncio
async def testConnectNats_whenScannerConfig_subscribeNats(requests_mock, mocker, event_loop):

    nats_connect_mock = mocker.patch("ostorlab.cli.bus.handler.ClientBusHandler.connect")
    mocker.patch("ostorlab.cli.bus.start.asyncio.events.AbstractEventLoop.run_forever", side_effect=Exception)
    mocker.patch("ostorlab.cli.bus.handler.ClientBusHandler.add_stream")
    mocker.patch("ostorlab.cli.bus.handler.BusHandler.subscribe")
    data_dict = {
                  "data": {
                    "scanners": {
                      "scanners": [
                        {
                          "id": "1",
                          "name": "5485",
                          "uuid": "a1ffcc25-3aa2-4468-ba8f-013d17acb443",
                          "description": "dsqd",
                          "config": {
                              "busUrl": "nats://nats.nats",
                              "busClusterId": "cluster_id",
                              "busClientName": "bus_name",
                              "subjectBusConfigs": {
                                  "subjectBusConfigs": [
                                    {
                                      "subject": "scan_engine.scan_saved",
                                      "queue": "1"
                                    },
                                    {
                                      "subject": "test1",
                                      "queue": "2"
                                    }
                                  ]
                                }
                          }
                        }
                      ]
                    }
                  }
                }
    requests_mock.post(
        authenticated_runner.AUTHENTICATED_GRAPHQL_ENDPOINT,
        json=data_dict,
        status_code=200,
    )

    config = start.ScannerConfig.from_json(data_dict)
    await start.connect_nats(config=config, scanner_id="GGBD-DJJD-DKJK-DJDD")
    assert nats_connect_mock.call_count == 1
