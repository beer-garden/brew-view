# -*- coding: utf-8 -*-
import json
from datetime import datetime

from mock import patch

from bg_utils.models import Job
from . import TestHandlerBase


class JobAPITest(TestHandlerBase):

    def setUp(self):
        self.ts_epoch = 1451606400000
        self.ts_dt = datetime(2016, 1, 1)
        self.job_dict = {
            'name': 'job_name',
            'trigger_type': 'cron',
            'trigger_args': {'minute': '*/5'},
            'request_template': {
                'system': 'system',
                'system_version': '1.0.0',
                'instance_name': 'default',
                'command': 'speak',
                'parameters': {'message': 'hey!'},
                'comment': 'hi!',
                'metadata': {'request': 'stuff'},
            },
            'misfire_grace_time': 3,
            'coalesce': True,
            'max_instances': 2,
            'next_run_time': self.ts_epoch,
        }
        self.job = Job(**self.job_dict)
        self.job.next_run_time = self.ts_dt
        super(JobAPITest, self).setUp()

    def tearDown(self):
        Job.objects.delete()

    def test_get_404(self):
        self.job.save()
        bad_id = ''.join(['1' for _ in range(24)])
        if bad_id == self.job.id:
            bad_id = ''.join(['2' for _ in range(24)])
        response = self.fetch('/api/v1/jobs/' + bad_id)
        self.assertEqual(404, response.code)

    def test_get(self):
        self.job.save()
        self.job_dict['id'] = str(self.job.id)
        response = self.fetch('/api/v1/jobs/' + str(self.job.id))
        self.assertEqual(200, response.code)
        self.assertEqual(json.loads(response.body.decode('utf-8')), self.job_dict)

    @patch('brew_view.scheduler')
    def test_delete(self, scheduler_mock):
        self.job.save()
        response = self.fetch('/api/v1/jobs/' + str(self.job.id), method='DELETE')
        self.assertEqual(204, response.code)
        scheduler_mock.remove_job.assert_called_with(str(self.job.id), jobstore='beer_garden')