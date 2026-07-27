from mistralai.client import Mistral
import os

api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)

websearch_agent = client.beta.agents.create(model="mistral-small-latest", description="Agent able to search information over the web, such as news, weather, sport results...", name="Websearch Agent", instructions="You are a general assistant. You have the ability to perform web searches with `web_search` to find up-to-date information. Keep your replies concise and to the point, with no markdown or code blocks.", tools=[{"type": "web_search"}],completion_args={"temperature": 0.3, "top_p": 0.95})

testo="Cosa sai di Pietro Paleocapa?"

response = client.beta.conversations.start(agent_id=websearch_agent.id, inputs=testo)

print(response.outputs[-1].content)
