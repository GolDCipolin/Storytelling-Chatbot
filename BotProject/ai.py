import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GOOGLE_GEMINI_KEY"))
genai.GenerationConfig()

# Create the model
generation_config = genai.GenerationConfig(
    temperature=1,
    top_p=0.95,
    top_k=40,
    max_output_tokens=8192,
    response_mime_type="text/plain"
)

# model = genai.GenerativeModel(
#         model_name="gemini-2.0-flash",
#         system_instruction="You are a story telling chatbot made for kids where you will be given prompts and you will make stories based on it.",
#         generation_config=generation_config,
# ) not used

# chat_session = model.start_chat(
#   history=[
#   ]
# ) not used

# OTHER

def continue_story(user_id, additional_prompt, cursor):
    cursor.execute("SELECT story_text FROM story WHERE user_id = ? ORDER BY story_id DESC LIMIT 1", (user_id,))
    previous_story = cursor.fetchone()

    if previous_story:
        full_prompt = previous_story[0] + "\n\n" + additional_prompt #adds additional prompt
    else:
        full_prompt = additional_prompt

    response = chat_session.send_message(full_prompt)
    return response.text

def age_system_instruction(age: int):
    if age <= 7:
        return "You are a storytelling chatbot for very young children. Your stories must be extremely simple, positive, and age-appropriate for kids under 7 based on the given prompts."
    elif 8 <= age <= 12:
        return "You are a storytelling chatbot for older children. Your stories can include more detailed plots and mild adventure, suitable for ages 8 to 12 based on the given prompts."
    elif 13 <= age <= 17:
        return "You are a storytelling chatbot for teenagers. Your stories can include deeper themes and moral lessons, appropriate for ages 13 to 17 based on the given prompts."
    else:
        return "You are a story telling chatbot made for kids where you will be given prompts and you will make stories based on it."

def model_age(age: int):
    instruction = age_system_instruction(age)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=instruction,
        generation_config=generation_config,
    )
    return model.start_chat(history=[])

chat_session = model_age(10) #default age

# response = chat_session.send_message("A story about a small little Brazilian boy named Antony and winning World Cups and Champions League with his special ability 'SPIN!'")
#
# print(response.text)