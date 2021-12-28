import datetime
import os
import threading
import time

import pytest

from ostorlab.agent import agent, message as agent_message
from ostorlab.runtimes import runtime


class StartTestAgent(agent.Agent):
    def start(self) -> None:
        self.emit('v3.healthcheck.ping', {'body': f'from test agent at {datetime.datetime.now()}'})


class ProcessTestAgent(agent.Agent):
    message = None
    def process(self, message: agent_message.Message) -> None:
        self.message = message


# @pytest.mark.timeout(60)
def testAgent_whenAnAgentSendAMessageFromStartAgent_listeningToMessageReceivesIt():
    start_agent = StartTestAgent(runtime.AgentDefinition(name='start_test_agent', out_selectors=['v3.healthcheck.ping']),
                        runtime.AgentInstanceSettings(
                            bus_url='amqp://guest:guest@localhost:5672/', bus_exchange_topic='ostorlab_test',
                            healthcheck_port=5301,
                        ))
    process_agent = ProcessTestAgent(runtime.AgentDefinition(name='process_test_agent', in_selectors=['v3.healthcheck.ping']),
                          runtime.AgentInstanceSettings(
                              bus_url='amqp://guest:guest@localhost:5672/', bus_exchange_topic='ostorlab_test', healthcheck_port=5302))
    threading.Thread(target=start_agent.run).start()
    threading.Thread(target=process_agent.run).start()

    time.sleep(60)
    assert process_agent.message is not None

#
# @pytest.mark.skip(reason='Timeout logik removed after changing mq implementation')
# def testAgentProcessMessage_whenAgentTimesout_agentTimeoutMessageSent():
#     # Set timeout to a small manageable value
#     os.environ['SCAN_ID'] = '1'
#     old_value = conf_test.Conf.AGENT_TIMEOUT
#     conf_test.Conf.AGENT_TIMEOUT = 3
#     test_obj = test_utils.AgentTest()
#     custom_agent = test_obj.run_custom_process_agent(agent_name='sleeper',
#                                                      process_message_func=lambda _: sleep(10),
#                                                      selector=ScanAgent.selector('report', 'vulnerabilities'))
#
#     vulnerabilities_queue = list()
#     vulnerabilities_queue.append({'title': 'fake_title',
#                                   'technical_detail': u'fake_detail',
#                                   'risk_rating': '',
#                                   'dna': '1234'})
#
#     selector = ScanAgent.selector('report', 'vulnerabilities')
#     serialized_message = ScanAgent.serialize(selector[:-2],
#                                              vulnerabilities=vulnerabilities_queue,
#                                              agent_name='agent_test',
#                                              agent_version='0.1',
#                                              scan_id=1)
#
#     test_obj.create_report_vulnerability(vulnerabilities_queue, 'unit_test', scan_id=5)
#     custom_agent._process_message(selector, serialized_message)
#
#     conf_test.Conf.AGENT_TIMEOUT = old_value
#     sent_messages = custom_agent._send_message_queue
#     exception_messages = [message for message in sent_messages
#                           if message.DESCRIPTOR.name == 'agent_timeout']
#     done_messages = [message for message in sent_messages
#                      if message.DESCRIPTOR.name == 'end_processing']
#
#     assert len(sent_messages) == 4
#     assert len(exception_messages) == 1
#     assert len(done_messages) == 1
#
#
# @pytest.mark.skip(reason='Timeout logic removed after changing mq implementation')
# def testAgentProcessMessage_whenAgentTimesoutAndChildProcessesRunning_allProcessChildKilled():
#     pids = []
#     os.environ['SCAN_ID'] = '1'
#
#     def timeout(message):
#         proc = mp.Process(target=sleep, args=(10,))
#         proc.start()
#         pids.append(proc.pid)
#         sleep(10)
#
#     # Set timeout to a small manageable value
#     old_value = conf_test.Conf.AGENT_TIMEOUT
#     conf_test.Conf.AGENT_TIMEOUT = 5
#     test_obj = test_utils.AgentTest()
#     custom_agent = test_obj.run_custom_process_agent(agent_name='sleeper',
#                                                      process_message_func=timeout,
#                                                      selector=ScanAgent.selector('report', 'vulnerabilities'))
#
#     vulnerabilities_queue = list()
#     vulnerabilities_queue.append({'title': 'fake_title',
#                                   'technical_detail': u'fake_detail',
#                                   'risk_rating': '',
#                                   'dna': '1234'})
#
#     selector = ScanAgent.selector('report', 'vulnerabilities')
#     serialized_message = ScanAgent.serialize(selector[:-2],
#                                              vulnerabilities=vulnerabilities_queue,
#                                              agent_name='agent_test',
#                                              agent_version='0.1',
#                                              scan_id=1)
#
#     test_obj.create_report_vulnerability(vulnerabilities_queue, 'unit_test', scan_id=5)
#     custom_agent._process_message(selector, serialized_message)
#
#     conf_test.Conf.AGENT_TIMEOUT = old_value
#     sended_messages = custom_agent._send_message_queue
#     exception_messages = [message for message in sended_messages
#                           if message.DESCRIPTOR.name == 'agent_timeout']
#     done_messages = [message for message in sended_messages
#                      if message.DESCRIPTOR.name == 'end_processing']
#
#     assert len(sended_messages) == 5
#     assert len(exception_messages) == 1
#     assert len(done_messages) == 1
#
#     for pid in pids:
#         assert psutil.pid_exists(pid) is False
#
#
# @pytest.mark.django_db
# def testAgentProcessMessage_whenExceptionRaised_agentExceptionMessageSent():
#     os.environ['SCAN_ID'] = '1'
#
#     def raise_exception(message):
#         raise Exception('custom exception')
#
#     test_obj = test_utils.AgentTest()
#     custom_agent = test_obj.run_custom_process_agent(agent_name='raiser_exception',
#                                                      process_message_func=raise_exception,
#                                                      selector=ScanAgent.selector('report', 'vulnerabilities'))
#
#     vulnerabilities_queue = list()
#     vulnerabilities_queue.append({'title': 'fake_title',
#                                   'technical_detail': u'fake_detail',
#                                   'risk_rating': '',
#                                   'dna': '1234'})
#
#     selector = ScanAgent.selector('report', 'vulnerabilities')
#     serialized_message = ScanAgent.serialize(selector[:-2],
#                                              vulnerabilities=vulnerabilities_queue,
#                                              agent_name='agent_test',
#                                              agent_version='0.1',
#                                              scan_id=1)
#
#     test_obj.create_report_vulnerability(vulnerabilities_queue, 'unit_test', scan_id=5)
#     custom_agent._process_message(selector, serialized_message)
#
#     sended_messages = custom_agent._send_message_queue
#     exception_messages = [message for message in sended_messages
#                           if message.DESCRIPTOR.name == 'agent_exception']
#
#     done_messages = [message for message in sended_messages
#                      if message.DESCRIPTOR.name == 'end_processing']
#
#     assert len(sended_messages) == 5
#     assert len(exception_messages) == 1
#     assert len(done_messages) == 1
#
#
# def testScanAgentIsTested_whenCalledMultipleTimes_returnsFalseFirstThenTrue():
#     os.environ['SCAN_ID'] = '1'
#
#     class CustomScanAgent(ScanAgent):
#         _name_ = 'CustomScanAgent'
#         _desc_ = 'A Custom Scan Agent'
#         _version_ = '0.1'
#         _selector_ = None
#
#         def __init__(self, *args, do_enable_healthcheck=False, start_status_agent=False, **kwargs):
#             super().__init__(*args, do_enable_healthcheck=do_enable_healthcheck, start_status_agent=start_status_agent,
#                              **kwargs)
#
#         def process_message(self, message):
#             pass
#
#     agent = CustomScanAgent()
#
#     dna = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
#     assert agent.is_or_mark_as_tested(dna) is False
#     assert agent.is_or_mark_as_tested(dna) is True
#     assert agent.is_or_mark_as_tested(dna) is True
#
#
# def testScanAgentIsTested_whenMultipleAgentsCallsTheSameDNA_returnsFalseForFirstCall():
#     os.environ['SCAN_ID'] = '1'
#
#     class CustomScanAgent1(ScanAgent):
#         _name_ = 'CustomScanAgent1'
#         _desc_ = 'A Custom Scan Agent'
#         _version_ = '0.1'
#         _selector_ = None
#
#         def __init__(self, *args, do_enable_healthcheck=False, start_status_agent=False, **kwargs):
#             super().__init__(*args, do_enable_healthcheck=do_enable_healthcheck, start_status_agent=start_status_agent,
#                              **kwargs)
#
#         def process_message(self, message):
#             pass
#
#     class CustomScanAgent2(ScanAgent):
#         _name_ = 'CustomScanAgent2'
#         _desc_ = 'A Custom Scan Agent'
#         _version_ = '0.1'
#         _selector_ = None
#
#         def __init__(self, *args, do_enable_healthcheck=False, start_status_agent=False, **kwargs):
#             super().__init__(*args, do_enable_healthcheck=do_enable_healthcheck, start_status_agent=start_status_agent,
#                              **kwargs)
#
#         def process_message(self, message):
#             pass
#
#     agent1 = CustomScanAgent1()
#     agent2 = CustomScanAgent2()
#
#     dna = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
#     assert agent1.is_or_mark_as_tested(dna) is False
#     assert agent1.is_or_mark_as_tested(dna) is True
#     assert agent2.is_or_mark_as_tested(dna) is False
#
#
# def testSelector_always_returnsVersionAndDottedTags():
#     assert ScanAgent.selector('a', 'b', 'c') == 'v2.a.b.c.#'
