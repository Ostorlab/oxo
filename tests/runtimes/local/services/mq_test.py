from ostorlab.runtimes.local.services import mq


def testLocalRabbitMQStart_onOperationalConditions_rabbitMQServiceIsStarted():
    lrm = mq.LocalRabbitMQ(name='test_mq', network='test_network')
    lrm.start()

    assert lrm.is_healthy is True
    lrm.stop()

    assert lrm.is_healthy is False
