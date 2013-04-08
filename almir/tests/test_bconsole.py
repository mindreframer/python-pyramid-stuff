import time
import unittest2
from subprocess import Popen, PIPE

from pyramid import testing
from mock import patch

from almir.lib.bconsole import BConsole


class TestBConsole(unittest2.TestCase):

    def setUp(self):
        request = testing.DummyRequest()
        self.config = testing.setUp(request=request)

    def tearDown(self):
        testing.tearDown()

    def test_is_running(self):
        b = BConsole()
        with patch.object(b, 'start_process') as mock_method:
            start_process = mock_method.return_value
            start_process.communicate.return_value = ('Version', '')
            self.assertTrue(b.is_running())

        with patch.object(b, 'start_process') as mock_method:
            start_process = mock_method.return_value
            start_process.communicate.return_value = ('error', 'error')
            self.assertFalse(b.is_running())

    def test_from_temp_config(self):
        output = \
"""# generated by almir, you should never edit this file. Do:
# vim buildout.cfg
# bin/buildout
# bin/supervisorctl restart all

Director {
    Name = test
    DIRport = 12345
    address = add
    Password = "qweqwe"
}
"""
        with BConsole.from_temp_config(
            name='test',
            address='add',
            port='12345',
            password='qweqwe'
        ) as b:
            expected = open(b.config_file).read()
            self.assertEqual(expected.replace(' ', '').replace('\r', ''),
                             output.replace(' ', '').replace('\r', ''))

    def test_get_upcoming_jobs(self):
        b = BConsole()
        with patch.object(b, 'start_process') as mock_method:
            start_process = mock_method.return_value
            start_process.communicate.return_value = ("""
Scheduled Jobs:
Level          Type     Pri  Scheduled          Name               Volume
===================================================================================
               Admin      8  18-Apr-12 20:30    UpdateSlots
Differential   Backup    10  18-Mar-12 23:05    BackupClient1      *unknown*
Full           Backup    11  18-Mar-12 23:10    BackupCatalog      *unknown*
====
""", '')

            jobs = b.get_upcoming_jobs()
            self.assertEqual(jobs, [{'date': '18-Apr-12',
                                     'level': '',
                                     'name': 'UpdateSlots',
                                     'time': '20:30',
                                     'priority': '8',
                                     'type': 'Admin',
                                     'volume': ''},
                                    {'date': '18-Mar-12',
                                     'level': 'Differential',
                                     'name': 'BackupClient1',
                                     'priority': '10',
                                     'time': '23:05',
                                     'type': 'Backup',
                                     'volume': '*unknown*'},
                                    {'date': '18-Mar-12',
                                     'level': 'Full',
                                     'name': 'BackupCatalog',
                                     'priority': '11',
                                     'time': '23:10',
                                     'type': 'Backup',
                                     'volume': '*unknown*'}])

    def test_send_command_by_polling(self):
        b = BConsole()
        with patch.object(b, 'start_process') as mock_method:
            mock_method.return_value = Popen(['cat'], stdout=PIPE, stdin=PIPE, stderr=PIPE)

            process, outputs = b.send_command_by_polling('version')
            self.assertEqual(outputs['commands'][0], 'version<br />')

            process.kill()
            time.sleep(1)
            process, outputs = b.send_command_by_polling('version', process)
            self.assertTrue('error' in outputs)

        with patch.object(b, 'start_process') as mock_method:
            start_process = mock_method.return_value
            start_process.communicate.return_value = ('error', 'error')

            process, outputs = b.send_command_by_polling('quit')
            self.assertEqual(outputs['commands'][0], 'Try harder.')
