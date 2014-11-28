# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from minion.plugins.base import ExternalProcessPlugin
import re
import socket
import uuid


class NullPlugin(ExternalProcessPlugin):

    PLUGIN_NAME = "Null Plugin"
    PLUGIN_VERSION = "0.0"
    PLUGIN_PATH = "ls"

    def do_start(self):

        ## Assign path of the dummy script
        path = self.locate_program(self.PLUGIN_PATH)

        if not path:
            raise Exception('Cannot find %s in path' % self.PLUGIN_PATH)

        args = []

        self.output = ""
        self.stderr = ""
        self.output_id = str(uuid.uuid4())

        self.report_progress(10, 'Starting Null Plugin')

        # Pull some variables from the plan configuration
        if 'parameter' in self.configuration:
            params = self.configuration.get('parameters')

            ### Put parameters into array
            params = params.split()

            args += params

        # Raise error to fail if needed
        if 'fail' in self.configuration and "true" in self.configuration.get('fail'):
            raise Exception('Failure triggered at do_start')

        self.spawn(self.PLUGIN_PATH, args)

    def do_stop(self):
        # Send a nice TERM signal so the dummy script can cleanup.
        self.process.signalProcess('TERM')

    def do_process_stdout(self, data):
        self.output += data

    def do_process_stderr(self, data):
        self.stderr += data

        error_regex = r".*Error_Trigger"
        if re.match(error_regex, data):
            raise Exception("Error triggered in stderr processing")

    def do_process_ended(self, status):
        if self.stopping and status == 9:
            self._save_artifacts()
            self.report_finish('STOPPED')
        elif status == 0:
            self.report_finish()
        else:
            self._save_artifacts()
            failure = {
                "hostname": socket.gethostname(),
                "exception": self.stderr,
                "message": "Plugin failed"
            }
            self.report_finish("FAILED", failure)

    def _save_artifacts(self):
        stdout_log = self.report_dir + "STDOUT_" + self.output_id + ".txt"
        stderr_log = self.report_dir + "STDERR_" + self.output_id + ".txt"
        output_artifacts = []

        if self.output:
            with open(stdout_log, 'w') as f:
                f.write(self.output)
            output_artifacts.append(stdout_log)
        if self.stderr:
            with open(stderr_log, 'w') as f:
                f.write(self.stderr)
            output_artifacts.append(stderr_log)

        if output_artifacts:
            self.report_artifacts("NullPlugin Output", output_artifacts)
