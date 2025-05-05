import pytest
import json
from unittest.mock import patch, MagicMock
from source.invoke_cloud_agent import lambda_handler

@patch.dict('os.environ', {'AGENT_ID': 'test-agent-id', 'AGENT_ALIAS_ID': 'test-agent-alias'})
@patch('source.invoke_cloud_agent.run_agent')
def test_lambda_handler_success(mock_run_agent):
    mock_run_agent.return_value = {
        'response': 'Hello World!',
        'session_id': 'test-session-id'
    }

    event = {
        'user_input': 'Hi',
        'session_id': 'test_session',
        'end_session': False
    }

    response = lambda_handler(event, None)
    body = json.loads(response['body'] if isinstance(response['body'], str) else response['body'])
    assert response['statusCode'] == 200
    assert response['headers']['X-Session-Id'] == 'test-session-id'
    assert body['agent_response'] == 'Hello World!'

@patch.dict('os.environ', {'AGENT_ID': 'test-agent-id', 'AGENT_ALIAS_ID': 'test-agent-alias'})
def test_lambda_handler_missing_user_input():
    event = {
        'session_id': 'test_session',
        'end_session': False
    }

    response = lambda_handler(event, None)
    body = json.loads(response['body'] if isinstance(response['body'], str) else response['body'])
    assert response['statusCode'] == 400
    assert body['error'] == 'User input is required'

@patch.dict('os.environ', {'AGENT_ID': 'test-agent-id', 'AGENT_ALIAS_ID': 'test-agent-alias'})
@patch('source.invoke_cloud_agent.run_agent', side_effect=Exception('internal error'))
def test_lambda_handler_error(mock_run_agent):
    event = {
        'user_input': 'Hi',
        'session_id': 'test_session',
        'end_session': False
    }

    response = lambda_handler(event, None)
    body = json.loads(response['body'] if isinstance(response['body'], str) else response['body'])
    assert response['statusCode'] == 500
    assert body['error'] == 'internal error'