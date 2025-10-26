# Standard library imports
import os
import json
import maara
import pytz

# Third-party library imports
from openai import OpenAI
from typing import Dict, Set, List, Optional
from datetime import datetime
from database.pymongo_connection import mongo_db
from database.history_manager import insert_conversation_log
from translator import GoogleTranslator

  
translator = GoogleTranslator()
#translator
def translator_ins(input, language):
  return translator.translate(input, target_language=language)

#Batch translator
def translate_dialogue(dialogue, target_language):
    for message in dialogue:
        message['content'] = translator_ins(message['content'], target_language)
    return dialogue

# Instance creation and configurations
maara_db = mongo_db(os.environ["mongo_db"], "maara")
maara_db.connect()
collection = maara_db.get_collection("maara_conversation_history")


client = OpenAI()

System_prompt = maara.system_prompt(str(datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')))

def maara_ai_assistant(prompt,  conversation_id, user_data = None):
    results = collection.find({"conversation_id": conversation_id},{"role": 1, "content": 1, "_id": 0}).sort([("date", 1)])
    all_messages = list(results)
    historys = all_messages[-8:] if len(all_messages) > 8 else all_messages
    if user_data is not None:
        messages = [{"role": "system", "content": System_prompt},] + historys + [{ "role": "user", "content": user_data },]+[{ "role": "user", "content": prompt },]
    else:    
       messages = [{"role": "system", "content": System_prompt},] + historys + [{ "role": "user", "content": prompt },]
    while True:
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=messages,
            temperature=0,
            top_p=1,)
        response_text = response.choices[0].message.content
        action, action_input, thoughts, location = maara.extract_action_and_input(response_text)
        
        #Google search tool
        if action:
            if action[-1] == "Search":
                tool = maara.google_search
                if action_input:
                    observation = tool(action_input[-1])
                    messages.extend([
                        { "role": "system", "content": response_text },
                        { "role": "user", "content": f"Observation: {observation}" },
                    ])
        
        #Google search tool
            elif action[-1] == "Map":
                print("get_location_coordinates called")
                latitude, longitude = maara.get_location_coordinates(location)
                print("get_location_coordinates call sucessful")
                if latitude == None or longitude == None:
                  return "Unable to find the location. Would you please try entering the exact place?"
                if action_input:
                    print("search_place called")
                    observation = maara.search_place(action_input[-1], latitude, longitude)
                    print("search_place call successful")
                    messages.extend([
                        { "role": "system", "content": response_text },
                        { "role": "user", "content": f"Observation: {observation[0:5]}" },
                    ])

            elif action[-1] == "Response To Human":
                messages.extend([{ "role": "system", "content": action_input[-1] }])
                insert_conversation_log(collection, prompt, action_input[-1], conversation_id) 
                return action_input[-1]
                
        else:
            insert_conversation_log(collection, prompt, response_text, conversation_id)
            return response_text
        

def maara_ai_mulitlang_assistant(prompt, conversation_id, language, user_data = None):

    results = collection.find({"conversation_id": conversation_id},{"role": 1, "content": 1, "_id": 0}).sort([("date", 1)])
    all_messages = list(results)
    historys = all_messages[-8:] if len(all_messages) > 8 else all_messages 
    history = translate_dialogue(historys, "en")
    if user_data is not None:
        messages = [{"role": "system", "content": System_prompt},] + history + [{ "role": "user", "content": user_data },]+[{ "role": "user", "content": prompt },]
    else:    
       messages = [{"role": "system", "content": System_prompt},] + history + [{ "role": "user", "content": prompt },]

    while True:
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=messages,
            temperature=0,
            top_p=1,)
        response_text = response.choices[0].message.content
        action, action_input, thoughts, location = maara.extract_action_and_input(response_text)
        
        #Google search tool
        if action:
            if action[-1] == "Search":
                tool = maara.google_search
                if action_input:
                    observation = tool(action_input[-1])
                    messages.extend([
                        { "role": "system", "content": response_text },
                        { "role": "user", "content": f"Observation: {observation}" },
                    ])
        
        #Google search tool
            elif action[-1] == "Map":
                latitude, longitude = maara.get_location_coordinates(location)
                if action_input:
                    observation = maara.search_place(action_input[-1], latitude, longitude)
                    messages.extend([
                        { "role": "system", "content": response_text },
                        { "role": "user", "content": f"Observation: {observation[0:5]}" },
                    ])

            elif action[-1] == "Response To Human":
                response_text = translator_ins(action_input[-1], language)
                messages.extend([{ "role": "system", "content": response_text }])
                insert_conversation_log(collection, prompt, response_text, conversation_id)
                return response_text
                
        else:
            response_text = translator_ins(response_text, language)
            insert_conversation_log(collection, prompt, response_text, conversation_id)   
            return response_text