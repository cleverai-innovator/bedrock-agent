import unittest
from unittest.mock import MagicMock, patch
from source.run_agent import run_agent

class TestRunAgent(unittest.TestCase):

    @patch('boto3.client')
    def test_run_agent_success(self, mock_boto_client):
        # Mock the boto3 client
        mock_client_instance = MagicMock()
        mock_boto_client.return_value = mock_client_instance
        mock_client_instance.invoke_agent.return_value = {
            'completion': iter([
                {'chunk': {'bytes' : b'Hello, world!'}}
            ])
        }

        response = run_agent(
            input_text = 'Hi',
            agent_id = 'test-agent',
            agent_alias_id = 'test-alias',
            session_id = 'test-session',
            end_session = False
        )
        self.assertEqual(response, 'Hello, world!')
        
        
        