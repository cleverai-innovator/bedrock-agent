import boto3
import uuid
import pprint
import json
from typing import Dict, Any, Optional, Union
from source.common.logger_setup import get_logger

# Setting logger
logger = get_logger(__name__)

def run_agent(
    input_text: str, 
    agent_id: str,
    agent_alias_id: str,
    session_id: Optional[str] = None,
    enable_trace: Optional[bool] =True,
    end_session: Optional[bool] =False
    ) -> Union[str, Dict[str, Any]]:
        
    if not session_id:
        session_id = uuid.uuid4().hex
        
    #Invoke Agent via Boto3 API
    client = boto3.client('bedrock-agent-runtime')
    response = client.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id,
        enableTrace=enable_trace,
        endSession=end_session
    )
    logger.info(pprint.pformat(response))

    agent_response = ''
    event_stream = response.get('completion')
    if event_stream is None:
        logger.error("No response from the agent")
        return "No response from the agent"

    error_keys_error_level = {
        'accessDeniedException', 'conflictException',
        'dependencyFailedException', 'internalServerException', 'resourceNotFoundException',
        'invalidRequestException', 'serviceQuotaExceededException', 'validationException'
    }
    error_keys_warning_level = {
        'badGatewayException', 'throttlingException', 'modelNotReadyException'
    }

    try:
        for event in event_stream:

            # Handle the final answer from the agent
            if 'chunk' in event:
                data = event['chunk']['bytes']
                decoded_data = data.decode('utf-8')
                logger.info(f"Agent Final answer -> \n{decoded_data}")
                agent_response = decoded_data

            # Handle the trace from the agent
            elif 'trace' in event:
                logger.info(json.dumps(event['trace'], indent=2))
            
            elif any(key in event for key in error_keys_error_level):
                key = next(k for k in event if k in error_keys_error_level)
                error_msg = event[key].get('message', str(event[key]))
                logger.error(f"{key}: {error_msg}")
                agent_response = error_msg
            elif any(key in event for key in error_keys_warning_level):
                key = next(k for k in event if k in error_keys_warning_level)
                error_msg = event[key].get('message', str(event[key]))
                logger.warning(f"{key}: {error_msg}")
                agent_response = error_msg

            # Log unexpected events
            else:
                logger.warning(f"Unexpected event: {event}")
                agent_response = 'Unexpected error occurred'

    except Exception as e:
        logger.exception("Unexpected error occurred")
        agent_response = 'Unexpected error occurred'
        raise

    return agent_response

