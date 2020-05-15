import os
import shutil
import tempfile

from fairworkflows import project, config

PLEX = 'plex'
WORKFLOW = 'workflow'
WORKFLOW_NAME = 'my_workflow'

WORKFLOW_FILE = 'my_workflow.ttl'


def test_get_steps():
    # TODO: rdf module should be mocked
    with MockFileStructure() as project_path:
        steps = project.get_steps(project_path)

        assert steps.keys() == {'analyze_data', 'retrieve_data'}


class MockFileStructure():
    def __init__(self):
        self.project_dir = tempfile.mkdtemp()

        plex_dir = os.path.join(self.project_dir, PLEX)
        os.mkdir(plex_dir)

        self.workflow_file = os.path.join(plex_dir, f'{WORKFLOW_NAME}.ttl')
        shutil.copy(config.TESTS_RESOURCES / WORKFLOW_FILE, self.workflow_file)

    def __enter__(self):
        return self.project_dir

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Delete temporary directory
        :return:
        """
        shutil.rmtree(self.project_dir)
