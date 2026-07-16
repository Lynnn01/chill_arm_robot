import openai

class RequestLLM:

    def __init__(self, base_url, model_name) -> None:
        # 记录上下文
        self.messages = []
        self.base_url = base_url
        self.model_name = model_name
        self.client = openai.OpenAI(api_key="AKjQv_QXHyStkKu5", base_url=self.base_url)

    def chat_nostream(self, prompt, stop=[]):
        self.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            stream=False,
            stop=stop
        )

        current_content = response.choices[0].message.content
        self.messages.append({'role': 'assistant', 'content': current_content})
        return current_content
    
    def chat_stream(self, prompt, stop=[]):
        self.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.messages,
            stream=True,
            stop=stop
        )
        
        current_content = ''
        for chunk in response:
            tmp = chunk.choices[0].delta.content
            if tmp is not None:
                current_content += tmp
                yield tmp

        self.messages.append({'role': 'assistant', 'content': current_content})
        
#sk-507e927245974e5897d9622140e69e0e
