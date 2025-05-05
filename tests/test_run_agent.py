import pytest
from unittest.mock import MagicMock, patch
from source.invoke_cloud_agent import run_agent

@pytest.fixture
def mock_boto_client():
    with patch('boto3.client') as mock_client:
        yield mock_client

def test_run_agent_no_response(mock_boto_client):
    mock_client_instance = MagicMock()
    mock_boto_client.return_value = mock_client_instance
    mock_client_instance.invoke_agent.return_value = {
        'completion': None,
        'ResponseMetadata': {'HTTPHeaders': {'x-amz-bedrock-agent-session-id': 'test-session-id'}}
    }

    response = run_agent("Hi", "test-agent", "test-agent-alias")
    assert response['response'] == 'Something went wrong'
    assert response['session_id'] == 'test-session-id'

def test_run_agent_success(mock_boto_client):
    mock_client_instance = MagicMock()
    mock_boto_client.return_value = mock_client_instance

    mock_event_stream = [{'chunk': {'bytes': b'Hello World!'}}]
    mock_client_instance.invoke_agent.return_value = {
        'completion': mock_event_stream,
        'ResponseMetadata': {'HTTPHeaders': {'x-amz-bedrock-agent-session-id': 'test-session-id'}}
    }

    response = run_agent("Hi", "test-agent", "test-agent-alias")
    assert response['response'] == 'Hello World!'
    assert response['session_id'] == 'test-session-id'

def test_run_agent_trace(mock_boto_client):
    mock_client_instance = MagicMock()
    mock_boto_client.return_value = mock_client_instance
    mock_event_stream = [{'trace': {'failureTrace': {'traceId': '123456790', 'failureReason': 'Reason Not found'}}}]

    mock_client_instance.invoke_agent.return_value = {
        'completion': mock_event_stream,
        'ResponseMetadata': {'HTTPHeaders': {'x-amz-bedrock-agent-session-id': 'test-session-id'}}
    }

    response = run_agent("Hi", "test-agent", "test-agent-alias")
    assert response['response'] == 'Something went wrong'
    assert response['session_id'] == 'test-session-id'

def test_run_agent_error_event(mock_boto_client):
    mock_client_instance = MagicMock()
    mock_boto_client.return_value = mock_client_instance
    mock_event_stream = [{'internalServerException': {'message': 'Internal Server Error'}}]

    mock_client_instance.invoke_agent.return_value = {
        'completion': mock_event_stream,
        'ResponseMetadata': {'HTTPHeaders': {'x-amz-bedrock-agent-session-id': 'test-session-id'}}
    }

    response = run_agent("Hi", "test-agent", "test-agent-alias")
    assert response['response'] == 'Something went wrong'
    assert response['session_id'] == 'test-session-id'

def test_run_agent_warning_event(mock_boto_client):
    mock_client_instance = MagicMock()
    mock_boto_client.return_value = mock_client_instance
    mock_event_stream = [{'throttlingException': {'message': 'Throttling Exception'}}]

    mock_client_instance.invoke_agent.return_value = {
        'completion': mock_event_stream,
        'ResponseMetadata': {'HTTPHeaders': {'x-amz-bedrock-agent-session-id': 'test-session-id'}}
    }

    response = run_agent("Hi", "test-agent", "test-agent-alias")
    assert response['response'] == 'Something went wrong'
    assert response['session_id'] == 'test-session-id'

def test_run_agent_unexpected_event(mock_boto_client):
    mock_client_instance = MagicMock()
    mock_boto_client.return_value = mock_client_instance
    mock_event_stream = [{'invalid_event': 'this will cause an error'}]

    mock_client_instance.invoke_agent.return_value = {
        'completion': mock_event_stream,
        'ResponseMetadata': {'HTTPHeaders': {'x-amz-bedrock-agent-session-id': 'test-session-id'}}
    }

    response = run_agent("Hi", "test-agent", "test-agent-alias")
    assert response['response'] == 'Something went wrong'
    assert response['session_id'] == 'test-session-id'