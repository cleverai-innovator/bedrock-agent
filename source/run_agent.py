import boto3
import uuid
import pprint
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from common.logger_setup import get_logger

# Setting logger
logger = get_logger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

"""
Run Agent function:
    The function is used to invoke the Bedrock Agent via Boto3 API.
"""

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
        endSession=end_session,
        inputText=input_text
    )
    logger.info(pprint.pformat(response))

    agent_response = ''
    event_stream = response.get('completion')
    if event_stream is None:
        logger.error("No response from the agent")
        return "Something went wrong"

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
                logger.info(json.dumps(event['trace'], indent=2, cls=DateTimeEncoder))
            
            elif any(key in event for key in error_keys_error_level):
                key = next(k for k in event if k in error_keys_error_level)
                error_msg = event[key].get('message', str(event[key]))
                logger.error(f"{key}: {error_msg}")
                agent_response = "Something went wrong"
            elif any(key in event for key in error_keys_warning_level):
                key = next(k for k in event if k in error_keys_warning_level)
                error_msg = event[key].get('message', str(event[key]))
                logger.warning(f"{key}: {error_msg}")
                agent_response = "Something went wrong"

            # Log unexpected events
            else:
                logger.warning(f"Unexpected event: {event}")
                agent_response = 'Something went wrong'

    except Exception as e:
        logger.exception("Unexpected error occurred")
        agent_response = 'Something went wrong'
        raise

    return agent_response

"""
Run Lambda function:
    The function is used to invoke run_agent.
"""

def lambda_handler(event, context):
    try:
        # Default Agent Configuration
        AGENT_ID = os.environ['AGENT_ID']
        AGENT_ALIAS_ID = os.environ['AGENT_ALIAS_ID']
        
        # Extract inputs from the event
        user_input = event.get('user_input')
        session_id = event.get('session_id')
        end_session = event.get('end_session', False)

        if user_input is None:
            logger.error("User input is required. session_id:{session_id}")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'User input is required'})
            }
        
        # Call the run_agent function
        response = run_agent(
            input_text= user_input,
            agent_id= AGENT_ID,
            agent_alias_id= AGENT_ALIAS_ID,
            session_id= session_id,
            end_session= end_session
        )
        return{
            'statusCode': 200,
            'body': json.dumps({
                'session_id': session_id,
                'agent_response': response
            })
        }
    except Exception as e:
        logger.exception("Error in Lambda handler")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

run_agent(
    input_text= "when is my birthday",
    agent_id= "DGEW1P4VGX",
    agent_alias_id= "ZPWRQAJG5H"
)