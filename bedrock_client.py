import boto3
from botocore.exceptions import ClientError
import config

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name=config.AWS_REGION,
    aws_access_key_id=config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
)

def call_bedrock(messages, system_prompt=None):
    try:
        kwargs = {
            "modelId": config.BEDROCK_MODEL_ID,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 2048,
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        if system_prompt:
            kwargs["system"] = [{"text": system_prompt}]

        response = bedrock_runtime.converse(**kwargs)
        
        output_message = response['output']['message']
        response_text = ""
        
        for block in output_message['content']:
            if 'text' in block:
                response_text += block['text']
                
        return response_text

    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', str(e))
        return f"⚠️ AWS Bedrock Error ({error_code}): {error_message}"
    except Exception as e:
        return f"⚠️ Terjadi kesalahan internal: {str(e)}"
