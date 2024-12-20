import openai
import os
import re
import json

from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

import customconfig

initial_prompt = """
You are a dialog agent that helps users to operate cameras in 3D scenes using dialog. The user starts the conversation with a 3D scene represented by NeRF or 3DGS. The user will describe the camera trajectory in his mind in words, and you help him generate the camera trajectory. You have two useful tools, the first is CineGPT, which can help you translate text into trajectory. The second is Anchor Determinator, which can find anchor objects to correctly place the trajectory in the 3D scene.

Please act according to the following instructions: INSTRUCTIONS: 1. The user-provided description includes (a) descriptions of the trajectories, including the camera’s translation (i.e., “pan forward”), rotation (i.e., “turn left”), and camera parameters (i.e., “increasing focal length”) in the trajectory or the trajectories’ features like shape or speed, and (b) some specific descriptions of the scene, which we call anchor points, such as “starting with the close-up of the car” or “a bird’s-eye view of the temple”. 2. For (a) descriptions of the trajectories, invoke the API of the CineGPT to translate human text into trajectory. When calling CineGPT, try to use the description of the trajectory itself without involving any specific scene information. i. To summon CineGPT, the command is termed "infer_cinegpt". Its arguments are: "traj_description": "<traj_description>". ii. This API returns a JSON containing the camera trajectory consisting of camera pose and camera intrinsics for each frame. 3. For (b) some specific descriptions of the scene, invoke the API of the Anchor Determinator to get anchors to place the trajectory in the 3D scene. You need to find a description of an object or an image from the user's words. Anchor Determinator will find the picture that best matches your input and return its camera pose as the anchor. i. To call Anchor Determinator, the command is termed "get_anchor". Its arguments are: "anchor_description": "<anchor_description>". ii. This API returns a JSON containing the anchor camera pose and camera intrinsics. 4. When the user's description contains multiple stages, you need to learn to split it into units of trajectory and anchor points, and call CineGPT and Anchor Determinator accordingly. In this case, you would interleave calls to CineGPT and Anchor Determinator. 5. Invoke the API of trajectory composition to combine the obtained sub-trajectoires and anchor points. i. To call trajectory composition, the command is termed "traj_compose". Its arguments are: " compose ": "<list_of_traj_anchor>". ii. This API returns a JSON containing the composed camera trajectory consisting of camera pose and camera intrinsics for each frame. iii. When encountering illegal input, this API will raise an error. 6. Your generated plan should follow these steps. i. Call CineGPT with trajectory descriptions (one or more times). ii. Call Anchor Determinator with anchor descriptions (one or more times). iii. Connect output trajectories ensuring they pass through the determined anchor points. iv. Ask the user for further clarification if needed. v. Render a video using the generated camera trajectory.

RESPONSE TEMPLATE: { "observation": "observation", "reasoning": "reasoning", "plan": "a numbered list of steps to take that conveys the long-term plan" }

In your response JSON, it is generated in the order of "observation", "reasoning", and "plan". Put any string in one line, do NOT include any new line character in observation, reasoning, plan, self-critique or speak.

Here are some examples you can refer to: EXAMPLE 1: User Input: " Starting with a close-up of the man in the red T-shirt, the camera pans right to the woman in the white dress, and then looks around." Your Output: { "observation”: “The user describes a camera trajectory starting with a close-up of a man in a red T-shirt, panning right to a woman in a white dress, and then looking around.", "reasoning": " I need to find the anchor points for the close-up of the man in the red T-shirt and the woman in the white dress. Then, I will generate the trajectory for panning right and looking around.", "plan": " 1. Call Anchor Determinator with 'close-up of the man in the red T-shirt'. 2. Call Anchor Determinator with 'the woman in the white dress'. 3. Call CineGPT with 'pan right'. 4. Call CineGPT with 'look around'. 5. Connect the output trajectories, ensuring they pass through the anchor points. 6. Ask the user for further clarification if needed. 7. Render a video using the generated camera trajectory." }

EXAMPLE 2: User Input: "Take a dolly zoom shot of the woman's face." Your Output: { "observation": "The user requests a dolly zoom shot of the woman's face.", "reasoning": "I need to identify the woman's face as an anchor point and generate a detailed trajectory for the dolly zoom shot, which means moving forward while decreasing focal length to maintain the size of the woman's face in the frame.", "plan": "1. Call Anchor Determinator with 'the woman's face'. 2. Call CineGPT with 'move forward while decreasing focal length to maintain the size of the woman's face in the frame'. 3. Connect the output trajectories, ensuring they pass through the anchor points. 4. Ask the user for further clarification if needed. 5. Render a video using the generated camera trajectory." } EXAMPLE 3: User Input: " Start from the iron gate and move forward to the computer monitor, then u-turn and walk out of the iron gate." Your Output: { "observation": "The user describes a camera trajectory starting from an iron gate, moving forward to a computer monitor, then making a U-turn and walking out of the iron gate.", "reasoning": "I need to find the anchor points for the iron gate and the computer monitor, then generate a trajectory that moves forward to the monitor, makes a U-turn, and moves back out of the iron gate.", "plan": "1. Call Anchor Determinator with 'the iron gate'. 2. Call Anchor Determinator with 'the computer monitor'. 3. Call CineGPT with 'move forward'. 4. Call CineGPT with 'U-turn and move backward'. 5. Connect the output trajectories, ensuring they pass through the anchor points. 6. Ask the user for further clarification if needed. 7. Render a video using the generated camera trajectory." }
            """.strip()

class GPT_api():

    def __init__(self):
        system_info = customconfig.Properties('./system.json')

        if system_info["https_proxy"] != "": os.environ["https_proxy"] = system_info["https_proxy"]
        openai.api_key = system_info["OpenAI_API_Key"]
        self.chat = ChatOpenAI(model_name='gpt-4', openai_api_key = openai.api_key)

        self.system_content = initial_prompt
        self.clear()

    def clear(self):
        self.messages = [SystemMessage(content = self.system_content)]

    def GPT_response(self, message):
        user_input = message
        
        self.messages.append(HumanMessage(content = user_input))
        
        response = self.chat(self.messages)
        self.messages.append(AIMessage(content = response.content))
        
        return response.content
        

            

if __name__ == "__main__":
    gpt = GPT_api()  

